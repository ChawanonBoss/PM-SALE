import os, sys, tempfile
import sys, os, http.server, threading, functools
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from harness import new_page, REPO_ROOT
class Q(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a): pass
h = functools.partial(Q, directory=REPO_ROOT)
srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), h); threading.Thread(target=srv.serve_forever, daemon=True).start()
base = f"http://127.0.0.1:{srv.server_address[1]}"
GEN = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'fixtures', 'samples_long.js'), encoding='utf-8').read()
OUT = os.path.join(tempfile.gettempdir(), "pdf_check")
with new_page(viewport={"width": 390, "height": 844}) as (page, errors):
    page.goto(f"{base}/index.html"); page.wait_for_timeout(500)
    page.evaluate("() => localStorage.setItem('pm-sale-login-ts', String(Date.now()))")
    page.evaluate("() => window.__authListeners[0]({uid:'admin1', email:'admin@a.com', displayName:'Admin One'})"); page.wait_for_timeout(900)
    page.evaluate("""() => { db.runTransaction = async fn => { const writes = []; const tx = { get: ref => ref.get(), update: (ref, d) => writes.push(() => ref.update(d)), set: (ref, d) => writes.push(() => ref.set(d)) }; const r = await fn(tx); for (const w of writes) await w(); return r; }; }""")
    page.evaluate("""async (gen) => { const g = eval(gen)('admin1', p => p + '20260921-001');
      const cu = await db.collection('pm_customers').add(g.customer); window.__pid = (await db.collection('pm_projects').add({ ...g.project, customerId: cu.id })).id;
      await db.collection('pm_projects').add({ ...g.sale, customerId: cu.id }); window.__sid = 0;
      await db.collection('pm_projects').add({ jobType:'sale', docNo:'SO20260921-007', name:'x', customerName:'c', startDate:'2026-09-21', endDate:'2026-09-21', items:[], createdBy:'admin1' });
      await db.collection('pm_warehouse').add({ part:'W', brand:'B', type:'Switch', name:'W item', quantity:3, serials:['A','B','C'], createdBy:'admin1' }); }""", GEN)
    page.wait_for_timeout(700)

    # ---- mobile: rows are cards with labelled values, no horizontal scroll ----
    page.evaluate("showTab('projects')"); page.wait_for_timeout(500)
    cell = page.locator('#projectsBody tr').first.locator('td').nth(1)
    labels = page.evaluate("[...document.querySelectorAll('#projectsBody tr:first-child td')].map(td => td.dataset.label || '')")
    assert labels[:4] == ['เลขที่เอกสาร', 'ชื่องาน / โครงการ', 'ประเภทงาน', 'ลูกค้า'], labels
    assert page.evaluate("getComputedStyle(document.querySelector('#projectsBody tr')).display") == 'block'
    assert not page.evaluate("getComputedStyle(document.querySelector('#tab-projects thead')).display !== 'none'")
    assert page.evaluate("document.documentElement.scrollWidth <= document.documentElement.clientWidth")
    page.screenshot(path=os.path.join(OUT, "phaseA_projects_mobile.png"))
    for t in ["equipment", "warehouse", "customers", "users", "trash", "audit"]:
        page.evaluate(f"showTab('{t}')"); page.wait_for_timeout(300)
        assert page.evaluate("document.documentElement.scrollWidth <= document.documentElement.clientWidth"), t
    # plan editor + item editor as cards
    page.evaluate("showTab('actionplan'); openActionPlan(window.__pid)"); page.wait_for_timeout(400)
    page.evaluate("$('planEditBtn').click()"); page.wait_for_timeout(400)
    assert page.evaluate("[...document.querySelectorAll('#planEditBody tr:first-child td')].map(td => td.dataset.label).filter(Boolean).length") >= 5
    page.screenshot(path=os.path.join(OUT, "phaseA_planedit_mobile.png"))
    page.evaluate("closeModal('planModal')")

    # ---- unlinked equipment line keeps showing its part and serials ----
    page.evaluate("showTab('projects'); openProjectForm(window.__pid)"); page.wait_for_timeout(500)
    first = page.locator('#prjItemsBody tr').first
    txt = first.inner_text()
    assert 'C9200-24P' in txt and 'ไม่ได้ผูกกับอุปกรณ์ในโกดัง' in txt and 'FOC22101000' in txt, txt
    page.screenshot(path=os.path.join(OUT, "phaseA_items_mobile.png"))
    page.evaluate("closeModal('projectModal')")

    # ---- admin session raises the day's counters to the numbers already in use ----
    page.wait_for_timeout(500)
    ctr = page.evaluate("Object.fromEntries([...(window.__mockStore['pm_counters'] || new Map()).entries()].map(([k, v]) => [k, v.n]))")
    assert ctr.get('PJ20260921') == 1 and ctr.get('SO20260921') == 7, ctr
    # a later, higher number moves the counter; it never goes down
    page.evaluate("db.collection('pm_projects').add({ jobType:'sale', docNo:'SO20260921-009', name:'y', customerName:'c', startDate:'2026-09-21', endDate:'2026-09-21', items:[], createdBy:'admin1' })"); page.wait_for_timeout(700)
    assert page.evaluate("window.__mockStore['pm_counters'].get('SO20260921').n") == 9
    print("counters:", ctr, "errors:", errors); assert not errors
print("OK")
