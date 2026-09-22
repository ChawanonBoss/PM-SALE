import os
import sys, os, http.server, threading, functools
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from harness import new_page, REPO_ROOT, goto_tab
class Q(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a): pass
h = functools.partial(Q, directory=REPO_ROOT)
srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), h); threading.Thread(target=srv.serve_forever, daemon=True).start()
base = f"http://127.0.0.1:{srv.server_address[1]}"
OUT = os.path.join(os.environ["TEMP"], "pdf_check")

with new_page(viewport={"width": 1600, "height": 900}) as (page, errors):
    page.goto(f"{base}/index.html"); page.wait_for_timeout(500)
    page.evaluate("() => localStorage.setItem('pm-sale-login-ts', String(Date.now()))")
    page.evaluate("() => window.__authListeners[0]({uid:'admin1', email:'admin@a.com', displayName:'Admin One'})"); page.wait_for_timeout(900)
    page.evaluate("""async () => {
      await db.collection('pm_customers').doc('c1').set({name:'ลูกค้า ก', type:'gov', createdBy:'admin1'});
      // p1: nothing saved yet | p2: plan only | p3: plan + equipment photos | p4: everything
      await db.collection('pm_projects').doc('p1').set({jobType:'project', docNo:'PJ1', name:'ยังไม่ทำอะไร', customerId:'c1', customerName:'ลูกค้า ก', startDate:'2026-09-01', endDate:'2026-12-31', items:[], createdBy:'admin1'});
      await db.collection('pm_projects').doc('p2').set({jobType:'project', docNo:'PJ2', name:'มีแผนแล้ว', customerId:'c1', customerName:'ลูกค้า ก', startDate:'2026-09-01', endDate:'2026-12-31', items:[], createdBy:'admin1',
        plan:[{title:'x', owner:'', start:'2026-09-01', end:'2026-09-05', done:false, subs:[]}]});
      await db.collection('pm_projects').doc('p3').set({jobType:'project', docNo:'PJ3', name:'มีรูปอุปกรณ์แล้ว', customerId:'c1', customerName:'ลูกค้า ก', startDate:'2026-09-01', endDate:'2026-12-31', items:[], createdBy:'admin1',
        plan:[{title:'x', owner:'', start:'2026-09-01', end:'2026-09-05', done:false, subs:[]}], photoCounts:{equipment:2, install:0}});
      await db.collection('pm_projects').doc('p4').set({jobType:'project', docNo:'PJ4', name:'ครบทุกอย่าง', customerId:'c1', customerName:'ลูกค้า ก', startDate:'2026-09-01', endDate:'2026-12-31', items:[], createdBy:'admin1',
        plan:[{title:'x', owner:'', start:'2026-09-01', end:'2026-09-05', done:false, subs:[]}], photoCounts:{equipment:1, install:3}});
      await db.collection('pm_projects').doc('s1').set({jobType:'sale', docNo:'SO1', name:'ขาย', customerId:'c1', customerName:'ลูกค้า ก', startDate:'2026-09-02', endDate:'2026-09-02', items:[], createdBy:'admin1'});
      // s2 chose only the equipment photo set on its own create form - its "รูปภาพงานติดตั้ง" column has nothing to show (not just unticked)
      await db.collection('pm_projects').doc('s2').set({jobType:'sale', docNo:'SO2', name:'ขาย2', customerId:'c1', customerName:'ลูกค้า ก', startDate:'2026-09-02', endDate:'2026-09-02', items:[], createdBy:'admin1',
        photoSets:['equipment'], photoCounts:{equipment:1}}); }""")
    page.wait_for_timeout(500)
    page.evaluate("localStorage.removeItem('pm-sale-project-columns')")   # start from the real defaults
    page.evaluate("showTab('projects')"); page.wait_for_timeout(300)

    # 2-row grouped header: "สถานะงาน" spans 3 sub-columns
    grp = page.locator('#projectsTable thead tr:first-child th:has-text("สถานะงาน")')
    assert grp.count() == 1 and grp.get_attribute('colspan') == '3'
    sub = page.evaluate("[...document.querySelectorAll('#projectsTable thead tr:last-child th')].map(t => t.textContent.trim())")
    assert sub == ['แผนการดำเนินงาน', 'รูปภาพอุปกรณ์', 'รูปภาพงานติดตั้ง'], sub

    page.screenshot(path=os.path.join(OUT, "status_columns_initial.png"))
    # checkbox state per project, and they are truly disabled (can't be clicked into changing anything)
    def chks(name):
        loc = page.locator(f'#projectsBody tr:has-text("{name}") td[data-col="workstatus"] input')
        return [loc.nth(i).is_checked() for i in range(loc.count())]
    assert chks('ยังไม่ทำอะไร') == [False, False, False]
    assert chks('มีแผนแล้ว') == [True, False, False]
    assert chks('มีรูปอุปกรณ์แล้ว') == [True, True, False]
    assert chks('ครบทุกอย่าง') == [True, True, True]
    assert page.evaluate("[...document.querySelectorAll('#projectsBody input[type=checkbox]')].every(c => c.disabled)")
    # clicking one does nothing (it's disabled - the browser itself refuses the click, state is unchanged)
    box = page.locator('#projectsBody tr:has-text("ยังไม่ทำอะไร") td[data-col=workstatus] input').first
    box.click(force=True); page.wait_for_timeout(100)
    assert box.is_checked() is False

    # "สร้างโดย" is hidden by default, even for this admin session
    assert not page.is_visible('#projectsTable thead th[data-col="creator"]')
    assert not page.is_visible('#projectsBody tr:first-child td[data-col="creator"]')   # present in the DOM (has real content), just hidden by CSS

    # the column picker: open it, everything reflects current prefs, toggling one hides/shows it live and survives a reload
    page.click('#projectsColumnsBtn'); page.wait_for_timeout(200)
    assert page.is_visible('#projectColumnsModal')
    labels = page.evaluate("[...document.querySelectorAll('#projectColumnsList label')].map(l => l.textContent.trim())")
    assert any('สร้างโดย' in l for l in labels) and any('สถานะงาน' in l for l in labels)
    creator_cb = page.locator('#projectColumnsList label:has-text("สร้างโดย") input')
    assert not creator_cb.is_checked()   # off by default
    creator_cb.check(); page.wait_for_timeout(200)
    assert page.is_visible('#projectsTable thead th[data-col="creator"]') and 'Admin One' in page.inner_text('#projectsBody tr:first-child td[data-col="creator"]')
    workstatus_cb = page.locator('#projectColumnsList label:has-text("สถานะงาน") input'); workstatus_cb.uncheck(); page.wait_for_timeout(200)
    assert not page.is_visible('#projectsTable thead th:has-text("สถานะงาน")') and not page.is_visible('#projectsBody td[data-col="workstatus"]')
    page.click('#projectColumnsCloseBtn'); assert not page.is_visible('#projectColumnsModal')

    # ซื้อขาย menu: same idea as โครงการ but only 2 sub-columns (no "แผนการดำเนินงาน" - a sale has no plan), and its own column picker/localStorage key.
    # Runs before the reload below, since that reload wipes the mock's seeded documents (s1/s2) along with everything else in the page's JS state.
    goto_tab(page, 'sales'); page.wait_for_timeout(300)
    sgrp = page.locator('#salesTable thead tr:first-child th:has-text("สถานะงาน")')
    assert sgrp.count() == 1 and sgrp.get_attribute('colspan') == '2'
    ssub = page.evaluate("[...document.querySelectorAll('#salesTable thead tr:last-child th')].map(t => t.textContent.trim())")
    assert ssub == ['รูปภาพอุปกรณ์', 'รูปภาพงานติดตั้ง'], ssub

    # s1 chose no set at all on its (pre-feature) create form -> photoSetsFor() falls back to both, neither ever attached -> both unticked
    # (matched by docNo, not name - "ขาย" is a substring of s2's own name "ขาย2")
    def schks(doc_no):
        loc = page.locator(f'#salesBody tr:has-text("{doc_no}") td[data-col="workstatus"] input')
        return [loc.nth(i).is_checked() for i in range(loc.count())]
    assert schks('SO1') == [False, False]

    # s2 chose only the equipment set: its equipment column is a ticked (real, saved) checkbox, but the install column is BLANK -
    # not just an unticked checkbox, since that set was never applicable to this record at all
    s2_cells = page.locator('#salesBody tr:has-text("SO2") td[data-col="workstatus"]')
    assert s2_cells.count() == 2
    assert s2_cells.nth(0).locator('input').count() == 1 and s2_cells.nth(0).locator('input').is_checked()
    assert s2_cells.nth(1).locator('input').count() == 0 and s2_cells.nth(1).inner_text().strip() == ''

    # "สร้างโดย" hidden by default here too, and the ⚙ column picker (in the table header, not the toolbar) has its own modal/prefs
    assert not page.is_visible('#salesTable thead th[data-col="creator"]')
    page.click('#salesColumnsBtn'); page.wait_for_timeout(200)
    assert page.is_visible('#salesColumnsModal')
    slabels = page.evaluate("[...document.querySelectorAll('#salesColumnsList label')].map(l => l.textContent.trim())")
    assert any('สร้างโดย' in l for l in slabels) and any('สถานะงาน' in l for l in slabels)
    screator_cb = page.locator('#salesColumnsList label:has-text("สร้างโดย") input')
    assert not screator_cb.is_checked()
    screator_cb.check(); page.wait_for_timeout(200)
    assert page.is_visible('#salesTable thead th[data-col="creator"]') and 'Admin One' in page.inner_text('#salesBody tr:has-text("SO2") td[data-col="creator"]')
    page.click('#salesColumnsCloseBtn'); assert not page.is_visible('#salesColumnsModal')
    goto_tab(page, 'projects'); page.wait_for_timeout(300)
    assert not page.is_visible('#projectsTable thead th:has-text("สถานะงาน")'), "โครงการ's own column prefs are unaffected by the ซื้อขาย picker"

    # preference survives a reload (localStorage), and a fresh session with no saved prefs falls back to the documented defaults
    page.reload(wait_until="load"); page.wait_for_timeout(600)
    page.evaluate("() => window.__authListeners[0]({uid:'admin1', email:'admin@a.com', displayName:'Admin One'})"); page.wait_for_timeout(900)
    page.evaluate("showTab('projects')"); page.wait_for_timeout(300)
    assert page.is_visible('#projectsTable thead th[data-col="creator"]'), "creator column choice persisted"
    assert not page.is_visible('#projectsTable thead th:has-text("สถานะงาน")'), "workstatus hide choice persisted"
    goto_tab(page, 'sales'); page.wait_for_timeout(300)
    assert page.is_visible('#salesTable thead th[data-col="creator"]'), "ซื้อขาย's own creator column choice persisted separately"
    goto_tab(page, 'projects'); page.wait_for_timeout(300)

    # a non-admin never sees สร้างโดย regardless of the preference (even though the pref itself says "show")
    page.evaluate("currentUserRole = 'user'; renderProjects()"); page.wait_for_timeout(200)
    assert not page.is_visible('#projectsTable thead th[data-col="creator"]')
    page.evaluate("currentUserRole = 'admin'; renderProjects()")

    page.screenshot(path=os.path.join(OUT, "status_columns.png"))
    print("errors:", errors); assert not errors
print("OK")
