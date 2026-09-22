import os, sys, tempfile
import sys, os, http.server, threading, functools
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from harness import new_page, REPO_ROOT, goto_tab
class Q(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a): pass
h = functools.partial(Q, directory=REPO_ROOT)
srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), h); threading.Thread(target=srv.serve_forever, daemon=True).start()
base = f"http://127.0.0.1:{srv.server_address[1]}"

with new_page(viewport={"width": 1440, "height": 900}) as (page, errors):
    page.goto(f"{base}/index.html"); page.wait_for_timeout(500)
    page.evaluate("() => localStorage.setItem('pm-sale-login-ts', String(Date.now()))")
    sign_in = lambda uid, email, name: (page.evaluate(f"() => window.__authListeners[0]({{uid:'{uid}', email:'{email}', displayName:'{name}'}})"), page.wait_for_timeout(1000))
    sign_out = lambda: (page.evaluate("auth.signOut()"), page.wait_for_timeout(400))
    user_doc = lambda uid: page.evaluate(f"(() => {{ const d = window.__mockStore['pm_users'].get('{uid}'); return d ? {{...d}} : null; }})()")

    # 1. first-ever user: admin, approved at once, sees the app
    sign_in('admin1', 'admin@a.com', 'Admin One')
    d = user_doc('admin1'); assert d['role'] == 'admin' and d['status'] == 'approved', d
    assert page.is_visible('#sidebar') and not page.is_visible('#approvalGate')
    # a legacy profile (no status field at all) counts as approved
    page.evaluate("db.collection('pm_users').doc('old1').set({email:'old@a.com', name:'Old User', role:'user'})")
    # a pre-invited person is approved at once
    page.evaluate("db.collection('pm_pendingRoles').doc('invited@a.com').set({role:'user', name:'Invited'})")
    sign_out()

    # 2. an ordinary new sign-up waits
    sign_in('u2', 'u2@a.com', 'User Two')
    d = user_doc('u2'); assert d['role'] == 'user' and d['status'] == 'pending', d
    assert page.is_visible('#approvalGate') and not page.is_visible('#sidebar') and 'รอผู้ดูแลระบบอนุมัติ' in page.inner_text('#approvalGate')
    assert page.evaluate("data.projects.length + data.customers.length + data.warehouse.length") == 0, "no listeners attached for a pending account"
    assert page.evaluate("currentUserStatus") == 'pending'
    sign_out(); assert not page.is_visible('#approvalGate') and page.is_visible('#gate')

    # 3. pre-invited + legacy accounts get straight in
    sign_in('inv1', 'invited@a.com', 'Invited'); d = user_doc('inv1'); assert d['status'] == 'approved' and not page.is_visible('#approvalGate') and page.is_visible('#sidebar'); sign_out()
    sign_in('old1', 'old@a.com', 'Old User'); assert page.is_visible('#sidebar') and not page.is_visible('#approvalGate'); sign_out()

    # a third sign-up, to be rejected
    sign_in('u3', 'u3@a.com', 'User Three'); assert page.is_visible('#approvalGate'); sign_out()

    # 4. admin sees them, pending first, with a badge on the users icon
    sign_in('admin1', 'admin@a.com', 'Admin One'); page.wait_for_timeout(500)
    # ผู้ใช้งาน now lives inside the ตั้งค่า group flyout, not its own rail button - the group button carries the same aggregate badge
    assert page.inner_text('#settingsNavBadge') == '2' and page.is_visible('#settingsNavBadge')
    goto_tab(page, 'users'); page.wait_for_timeout(400)
    rows = page.evaluate("[...document.querySelectorAll('#usersBody tr')].map(r => r.innerText.replace(/\s+/g,' ').trim())")
    assert 'รออนุมัติ' in rows[0] and 'รออนุมัติ' in rows[1], rows
    assert page.locator('#usersBody tr:has-text("User Two") button:has-text("อนุมัติ")').count() >= 1
    # approve u2
    page.locator('#usersBody tr:has-text("User Two") button:text-is("อนุมัติ")').click(); page.wait_for_timeout(500)
    assert user_doc('u2')['status'] == 'approved' and page.inner_text('#settingsNavBadge') == '1'
    # reject u3 (only offered while pending)
    page.locator('#usersBody tr:has-text("User Three") button:text-is("ไม่อนุมัติ")').click(); page.wait_for_timeout(500)
    assert user_doc('u3')['status'] == 'rejected'
    assert not page.is_visible('#settingsNavBadge')
    assert page.locator('#usersBody tr:has-text("User Three") button:text-is("อนุมัติ")').count() == 1, "a rejected account can still be approved later"
    audits = page.evaluate("[...window.__mockStore['pm_auditLog'].values()].map(a => a.action)")
    assert 'อนุมัติผู้ใช้' in audits and 'ไม่อนุมัติผู้ใช้' in audits, audits
    sign_out()

    # 5. approved account gets in; rejected one sees the refusal
    sign_in('u2', 'u2@a.com', 'User Two'); assert page.is_visible('#sidebar') and not page.is_visible('#approvalGate'); sign_out()
    sign_in('u3', 'u3@a.com', 'User Three'); assert page.is_visible('#approvalGate') and 'ไม่ได้รับอนุญาต' in page.inner_text('#approvalGate') and not page.is_visible('#sidebar'); sign_out()

    # 6. a waiting account is let in live the moment an admin approves (page reloads into the app)
    sign_in('u4', 'u4@a.com', 'User Four'); assert page.is_visible('#approvalGate')
    navs = []; page.on("framenavigated", lambda f: navs.append(f.url))
    page.evaluate("db.collection('pm_users').doc('u4').update({status:'approved'})"); page.wait_for_timeout(1200)
    assert navs, "gate should reload once approved"
    print("errors:", errors); assert not errors
print("OK")
