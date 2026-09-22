import os, sys, http.server, threading, functools, datetime
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from harness import new_page, REPO_ROOT, goto_tab
class Q(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a): pass
h = functools.partial(Q, directory=REPO_ROOT)
srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), h); threading.Thread(target=srv.serve_forever, daemon=True).start()
base = f"http://127.0.0.1:{srv.server_address[1]}"
HERE = os.path.dirname(os.path.abspath(__file__))
GEN = open(os.path.join(HERE, 'fixtures', 'samples10.js'), encoding='utf-8').read()
RUN = open(os.path.join(HERE, 'fixtures', 'seed10_run.js'), encoding='utf-8').read()
TODAY = datetime.date.today().isoformat()

with new_page(viewport={"width": 1440, "height": 900}) as (page, errors):
    page.goto(f"{base}/index.html"); page.wait_for_timeout(500)
    page.evaluate("() => localStorage.setItem('pm-sale-login-ts', String(Date.now()))")
    page.evaluate("() => window.__authListeners[0]({uid:'admin1', email:'admin@a.com', displayName:'Admin One'})"); page.wait_for_timeout(900)
    page.evaluate("""() => { db.runTransaction = async fn => { const writes = []; const tx = { get: ref => ref.get(), update: (ref, d) => writes.push(() => ref.update(d)), set: (ref, d) => writes.push(() => ref.set(d)) }; const r = await fn(tx); for (const w of writes) await w(); return r; }; }""")
    fn = "(" + RUN.strip() + ")"
    res = page.evaluate(fn, [GEN, TODAY]); page.wait_for_timeout(1000)
    assert res['companies'] == 10 and res['customers'] == 10 and res['warehouse'] == 10 and res['projects'] == 10 and res['sales'] == 10 and res['invites'] == 10 and res['trash'] == 9

    # one REAL (non-sample) row in each affected collection, so the button must leave these completely alone
    page.evaluate("""async () => {
      await db.collection('pm_customers').doc('real_c').set({name:'ลูกค้าจริง', type:'private', createdBy:'admin1'});
      await db.collection('pm_companies').doc('real_co').set({name:'บริษัทจริง'});
      await db.collection('pm_warehouse').doc('real_w').set({part:'REAL-1', name:'ของจริง', quantity:1, serials:[], createdBy:'admin1'});
      await db.collection('pm_projects').doc('real_p').set({jobType:'sale', docNo:'REAL1', name:'งานจริง', customerId:'real_c', customerName:'ลูกค้าจริง', startDate:'2026-09-01', endDate:'2026-09-01', items:[], createdBy:'admin1'});
      await db.collection('pm_pendingRoles').doc('real@example.com').set({name:'คนจริง', role:'user'}); }""")
    page.wait_for_timeout(500)

    # ---- the button lives on the (admin-only) Trash page ----
    goto_tab(page, 'trash'); page.wait_for_timeout(500)
    assert page.is_visible('#deleteSampleDataBtn')
    trash_before = page.locator('#trashBody tr').count()
    assert trash_before >= 9

    page.click('#deleteSampleDataBtn'); page.wait_for_timeout(200)
    assert page.is_visible('#confirmModal')
    page.click('#confirmModalOkBtn'); page.wait_for_timeout(1000)

    # every "sample" row is gone from its live collection...
    remaining = page.evaluate("""() => ({
      companies: data.companies.filter(c => c.sample).length,
      customers: data.customers.filter(c => c.sample).length,
      warehouse: data.warehouse.filter(w => w.sample).length,
      projects: data.projects.filter(p => p.sample).length,
    })""")
    assert remaining == {'companies': 0, 'customers': 0, 'warehouse': 0, 'projects': 0}, remaining

    # ...and gone from the Trash bucket too (the pre-deleted sample rows), while the real, non-sample rows are untouched everywhere
    loadTrash_check = page.evaluate("""async () => {
      const snap = await db.collection('pm_customers').where('sample', '==', true).get();
      return snap.docs.length;
    }""")
    assert loadTrash_check == 0
    page.click('#trashRefreshBtn'); page.wait_for_timeout(500)
    assert 'ตัวอย่าง' not in page.inner_text('#trashBody')

    real_left = page.evaluate("""() => ({
      customer: !!data.customers.find(c => c.id === 'real_c'),
      company: !!data.companies.find(c => c.id === 'real_co'),
      warehouse: !!data.warehouse.find(w => w.id === 'real_w'),
      project: !!data.projects.find(p => p.id === 'real_p'),
    })""")
    assert all(real_left.values()), real_left
    pending = page.evaluate("async () => (await db.collection('pm_pendingRoles').get()).docs.map(d => d.id)")
    assert pending == ['real@example.com'], pending

    assert 'ลบข้อมูลตัวอย่างแล้ว' in page.inner_text('#toast')
    assert page.evaluate("data.audit.some(a => a.action === 'ลบข้อมูลตัวอย่างทั้งหมด')")

    print("errors:", errors); assert not errors
print("OK")
