import os, sys, http.server, threading, functools
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from harness import new_page, REPO_ROOT, goto_tab
class Q(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a): pass
h = functools.partial(Q, directory=REPO_ROOT)
srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), h); threading.Thread(target=srv.serve_forever, daemon=True).start()
base = f"http://127.0.0.1:{srv.server_address[1]}"
PIXEL_PNG_B64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII="

with new_page(viewport={"width": 1400, "height": 900}) as (page, errors):
    page.goto(f"{base}/index.html"); page.wait_for_timeout(500)
    page.evaluate("() => localStorage.setItem('pm-sale-login-ts', String(Date.now()))")
    page.evaluate("() => window.__authListeners[0]({uid:'admin1', email:'admin@a.com', displayName:'Admin One'})"); page.wait_for_timeout(900)
    page.evaluate("""async () => {
      await db.collection('pm_customers').doc('c1').set({name:'ลูกค้า ก', type:'gov', createdBy:'admin1'});
      // s1 has photos saved (closeable); s2 has none yet (not closeable); p1 is a project (never gets the button at all)
      await db.collection('pm_projects').doc('s1').set({jobType:'sale', docNo:'SO1', name:'ขายพร้อมปิดงาน', customerId:'c1', customerName:'ลูกค้า ก',
        startDate:'2026-09-01', endDate:'2026-09-01', items:[], createdBy:'admin1', photoCounts:{equipment:1, install:0}});
      await db.collection('pm_projects').doc('s2').set({jobType:'sale', docNo:'SO2', name:'ขายยังไม่มีรูป', customerId:'c1', customerName:'ลูกค้า ก',
        startDate:'2026-09-02', endDate:'2026-09-02', items:[], createdBy:'admin1'});
      await db.collection('pm_projects').doc('p1').set({jobType:'project', docNo:'PJ1', name:'โครงการทดสอบ', customerId:'c1', customerName:'ลูกค้า ก',
        startDate:'2026-09-01', endDate:'2026-12-31', items:[], createdBy:'admin1', photoCounts:{equipment:1, install:1}}); }""")
    page.wait_for_timeout(500)

    # ---- ซื้อขาย only: a project row never gets the ปิดงาน button at all ----
    goto_tab(page, 'projects'); page.wait_for_timeout(300)
    assert page.locator('#projectsBody tr:has-text("โครงการทดสอบ") button:has-text("ปิดงาน")').count() == 0

    goto_tab(page, 'sales'); page.wait_for_timeout(300)
    # s2 has no photos yet: the button is disabled with an explanatory tooltip, not hidden
    btn2 = page.locator('#salesBody tr:has-text("ขายยังไม่มีรูป") button:has-text("ปิดงาน")')
    assert btn2.count() == 1 and btn2.is_disabled()
    assert 'รูปภาพ' in (btn2.get_attribute('title') or '')

    # s1 has photos saved: the button is enabled
    btn1 = page.locator('#salesBody tr:has-text("ขายพร้อมปิดงาน") button:has-text("ปิดงาน")')
    assert btn1.count() == 1 and not btn1.is_disabled()
    btn1.click(); page.wait_for_timeout(200)
    assert page.is_visible('#closeJobModal')
    assert 'ขายพร้อมปิดงาน' in page.inner_text('#closeJobSub')
    today = page.evaluate("todayStr()")
    assert page.input_value('#closeJobDate') == today
    assert 'ยังไม่ได้แนบไฟล์' in page.inner_text('#closeJobFileInfo')

    # can't confirm without the signed document
    page.click('#closeJobSaveBtn'); page.wait_for_timeout(200)
    assert 'แนบเอกสาร' in page.inner_text('#toast') and page.is_visible('#closeJobModal')

    # backdate the closing date, then attach the signed document and confirm
    backdate = '2026-08-20'
    page.fill('#closeJobDate', backdate)
    page.set_input_files('#closeJobFileInput', {"name": "signed.pdf", "mimeType": "application/pdf", "buffer": __import__("base64").b64decode(PIXEL_PNG_B64)})
    assert 'signed.pdf' in page.inner_text('#closeJobFileInfo')
    page.click('#closeJobSaveBtn'); page.wait_for_timeout(500)
    assert not page.is_visible('#closeJobModal')
    assert 'ปิดงานแล้ว' in page.inner_text('#toast')

    saved = page.evaluate("data.projects.find(p => p.id === 's1')")
    assert saved['closedAt'] == backdate and saved['closedBy'] == 'admin1'
    assert page.evaluate("projectStatus(data.projects.find(p => p.id === 's1'))") == 'ended'
    assert 'ปิดงานแล้ว' in page.inner_text('#salesBody tr:has-text("ขายพร้อมปิดงาน")')

    # the button itself becomes the "ปิดงานแล้ว" badge and is disabled - clicking it again does nothing
    btn1 = page.locator('#salesBody tr:has-text("ขายพร้อมปิดงาน") button:has-text("ปิดงานแล้ว")')
    assert btn1.count() == 1 and btn1.is_disabled()

    # a closed sale can no longer be deleted - the "ลบ" button is disabled, and deleteEntity() itself refuses too
    del_btn = page.locator('#salesBody tr:has-text("ขายพร้อมปิดงาน") button:has-text("ลบ")')
    assert del_btn.is_disabled() and 'ปิดงานแล้ว' in (del_btn.get_attribute('title') or '')
    page.evaluate("deleteEntity('projects', 's1')"); page.wait_for_timeout(200)
    assert 'ลบไม่ได้' in page.inner_text('#toast') and not page.is_visible('#confirmModal')
    assert page.evaluate("!data.projects.find(p => p.id === 's1').deletedAt")

    # the signed document is a real pm_files row (role:'closing'), scoped to this job, exactly one of them
    closing = page.evaluate("""async () => {
      const snap = await db.collection('pm_files').where('projectId', '==', 's1').where('role', '==', 'closing').get();
      return snap.docs.map(d => d.data());
    }""")
    assert len(closing) == 1 and closing[0]['name'] == 'signed.pdf' and closing[0]['ownerId'] == 'admin1'

    # ...but it never shows up in (or counts toward) the general "ไฟล์แนบ" list on the edit form
    page.click('#salesBody tr:has-text("ขายพร้อมปิดงาน") button:has-text("แก้ไข")'); page.wait_for_timeout(400)
    assert 'signed.pdf' not in page.inner_text('#prjFilesList')
    assert page.inner_text('#prjFilesCount').strip() == ''
    page.click('#projectCancelBtn')

    print("errors:", errors); assert not errors
print("OK")
