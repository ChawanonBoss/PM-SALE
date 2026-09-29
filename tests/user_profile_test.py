import os, sys, http.server, threading, functools
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from harness import new_page, REPO_ROOT, goto_tab
class Q(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a): pass
h = functools.partial(Q, directory=REPO_ROOT)
srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), h); threading.Thread(target=srv.serve_forever, daemon=True).start()
base = f"http://127.0.0.1:{srv.server_address[1]}"

with new_page(viewport={"width": 1500, "height": 950}) as (page, errors):
    page.goto(f"{base}/index.html"); page.wait_for_timeout(500)
    page.evaluate("() => localStorage.setItem('pm-sale-login-ts', String(Date.now()))")
    sign_in = lambda uid, email, name: (page.evaluate(f"() => window.__authListeners[0]({{uid:'{uid}', email:'{email}', displayName:'{name}'}})"), page.wait_for_timeout(900))
    sign_out = lambda: (page.evaluate("auth.signOut()"), page.wait_for_timeout(400))

    # first-ever sign-in becomes the admin
    sign_in('admin1', 'admin@a.com', 'Admin One')

    # ---------------- add-user is now a popup modal, not the old inline collapsible panel ----------------
    goto_tab(page, 'users'); page.wait_for_timeout(300)
    assert page.inner_text('#usersPanelTitle').strip().startswith('ผู้ใช้งานทั้งหมด')
    page.click('#userCreateToggleBtn'); page.wait_for_timeout(200)
    assert page.is_visible('#userAddModal')

    page.fill('#addUsrThaiFirst', 'สมชาย')
    page.fill('#addUsrThaiLast', 'ใจดี')
    page.fill('#addUsrEngFirst', 'Somchai')
    page.fill('#addUsrEngLast', 'Jaidee')
    # phone auto-formats to xxx-xxx-xxxx as digits are typed
    page.fill('#addUsrPhone', '0812345678')
    page.dispatch_event('#addUsrPhone', 'input')
    assert page.input_value('#addUsrPhone') == '081-234-5678', page.input_value('#addUsrPhone')
    page.fill('#addUsrEmailLocal', 'somchai')
    assert page.evaluate("document.getElementById('addUsrEmailDomain').options.length") >= 1, "gmail.com is a builtin option"
    page.select_option('#addUsrEmailDomain', 'gmail.com')
    page.click('#addUsrPositionAddBtn'); page.fill('#addUsrPositionNew', 'ช่างเทคนิค'); page.click('#addUsrPositionNewOk')
    assert page.input_value('#addUsrPosition') == 'ช่างเทคนิค'
    page.select_option('#usrRole', 'user')
    page.click('#userAddForm button[type="submit"]'); page.wait_for_timeout(500)
    assert 'เพิ่มผู้ใช้งานแล้ว' in page.inner_text('#toast')
    assert not page.is_visible('#userAddModal')

    pending = page.evaluate("window.__mockStore['pm_pendingRoles'].get('somchai@gmail.com')")
    assert pending is not None, "the composed local@domain email is the pending doc's own id"
    assert pending['thaiFirstName'] == 'สมชาย' and pending['thaiLastName'] == 'ใจดี'
    assert pending['engFirstName'] == 'Somchai' and pending['engLastName'] == 'Jaidee'
    assert pending['phone'] == '081-234-5678'
    assert pending['position'] == 'ช่างเทคนิค'
    assert pending['role'] == 'user'
    assert pending['name'] == 'สมชาย ใจดี', "the old freeform name field is auto-derived from the Thai first+last name"
    sign_out()

    # ---------------- that invited person signs in -> the pending invite's extra fields land on the real pm_users doc ----------------
    sign_in('u2', 'somchai@gmail.com', 'Somchai Jaidee')
    u2doc = page.evaluate("window.__mockStore['pm_users'].get('u2')")
    assert u2doc['role'] == 'user' and u2doc['status'] == 'approved'
    assert u2doc['thaiFirstName'] == 'สมชาย' and u2doc['thaiLastName'] == 'ใจดี'
    assert u2doc['engFirstName'] == 'Somchai' and u2doc['engLastName'] == 'Jaidee'
    assert u2doc['phone'] == '081-234-5678' and u2doc['position'] == 'ช่างเทคนิค'
    assert page.is_visible('#sidebar') and not page.is_visible('#approvalGate'), "pre-invited -> straight in, unchanged"

    # ---------------- ผู้ใช้งาน page: a non-admin sees ONLY their own row, no role control, just แก้ไข ----------------
    goto_tab(page, 'users'); page.wait_for_timeout(300)
    assert page.evaluate("currentTab") == 'users', "the users tab is no longer admin-only"
    assert page.inner_text('#usersPanelTitle').strip().startswith('ข้อมูลของฉัน')
    assert not page.is_visible('#userCreateToggleBtn') and not page.is_visible('#usersSearch') and not page.is_visible('#usersClearBtn')
    rows = page.locator('#usersBody tr')
    assert rows.count() == 1, "a non-admin never sees anyone else's row here"
    assert 'สมชาย ใจดี' in rows.nth(0).inner_text()
    assert rows.nth(0).locator('select').count() == 0, "no role <select> is ever rendered for a non-admin - not even disabled"
    assert rows.nth(0).locator('button:has-text("แก้ไข")').count() == 1
    assert rows.nth(0).locator('button:has-text("ลบ")').count() == 0

    # editing own profile: the 4 name fields only
    rows.nth(0).locator('button:has-text("แก้ไข")').click(); page.wait_for_timeout(200)
    assert page.is_visible('#userEditModal')
    assert page.input_value('#usrEditThaiFirst') == 'สมชาย'
    page.fill('#usrEditThaiLast', 'ใจดีมาก')
    page.click('#userEditForm button[type="submit"]'); page.wait_for_timeout(400)
    assert 'บันทึกข้อมูลแล้ว' in page.inner_text('#toast')
    assert page.evaluate("window.__mockStore['pm_users'].get('u2').thaiLastName") == 'ใจดีมาก'
    assert page.evaluate("window.__mockStore['pm_users'].get('u2').name") == 'สมชาย ใจดีมาก', "the plain name field stays in sync with the Thai name"

    # a non-admin cannot promote themselves - the app never even offers the control, and setUserRole() itself still refuses
    page.evaluate("setUserRole('u2', false, 'admin')"); page.wait_for_timeout(200)
    assert 'ไม่สามารถเปลี่ยนสิทธิ์ของตัวเอง' in page.inner_text('#toast')
    assert page.evaluate("window.__mockStore['pm_users'].get('u2').role") == 'user'

    # ---------------- ค่าเดินทาง is now open to every approved user, each keeping their OWN personal log ----------------
    goto_tab(page, 'travel'); page.wait_for_timeout(300)
    assert page.evaluate("currentTab") == 'travel'
    assert 'ยังไม่มีรายการเดินทางในเดือนนี้' in page.inner_text('#travelBody'), "u2's own travel log starts empty, separate from admin's"
    month_th = page.evaluate("MONTH_TH_FULL[new Date().getMonth()]")
    year_be = page.evaluate("new Date().getFullYear() + 543")
    assert page.inner_text('#travelHeaderPreview') == f"ค่าเดินทางประจำเดือน{month_th} ปี{year_be} ของสมชาย ใจดีมาก", \
        "the claim header now shows the CURRENT signed-in user's own Thai name, not a hardcoded owner"

    page.click('#travelCreateBtn'); page.wait_for_timeout(300)
    today = page.evaluate("() => new Date().toISOString().slice(0,10)")
    page.fill('#travelDate', today)
    page.click('#travelFromAddBtn'); page.fill('#travelFromNew', 'บ้าน'); page.click('#travelFromNewOk')
    page.click('#travelToAddBtn'); page.fill('#travelToNew', 'ลูกค้า X'); page.click('#travelToNewOk')
    page.fill('#travelDistance', '10')
    page.click('#travelSaveBtn'); page.wait_for_timeout(500)
    assert len(page.evaluate("data.travel")) == 1
    u2trip_id = page.evaluate("data.travel[0].id")
    assert page.evaluate(f"window.__mockStore['pm_travelExpenses'].get('{u2trip_id}').createdBy") == 'u2'
    sign_out()

    # admin's own travel log is a SEPARATE personal log - u2's trip above must not leak into it
    sign_in('admin1', 'admin@a.com', 'Admin One')
    goto_tab(page, 'travel'); page.wait_for_timeout(300)
    assert len(page.evaluate("data.travel")) == 0, "admin's own travel log starts empty too - own-createdBy scoping applies to every role, admin included"
    assert not any(t['id'] == u2trip_id for t in page.evaluate("data.travel")), "u2's trip must not be visible in admin's own list"

    print("errors:", errors); assert not errors
print("OK")
