import os
import sys, os, http.server, threading, functools
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from harness import new_page, REPO_ROOT
class Q(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a): pass
h = functools.partial(Q, directory=REPO_ROOT)
srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), h); threading.Thread(target=srv.serve_forever, daemon=True).start()
base = f"http://127.0.0.1:{srv.server_address[1]}"

with new_page(viewport={"width": 1440, "height": 900}) as (page, errors):
    page.goto(f"{base}/index.html"); page.wait_for_timeout(500)
    page.evaluate("() => localStorage.setItem('pm-sale-login-ts', String(Date.now()))")
    page.evaluate("() => window.__authListeners[0]({uid:'admin1', email:'admin@a.com', displayName:'Admin One'})"); page.wait_for_timeout(900)
    page.evaluate("""async () => {
      await db.collection('pm_customers').doc('c1').set({name:'ลูกค้า ก', type:'gov', createdBy:'admin1'});
      // p1: 4 installments, 2 delivered (next due = 3) | p2: 2 installments, both delivered (fully done, stays at stage 2) | p3: not split | p4: 5 installments, none delivered (next due = 1)
      await db.collection('pm_projects').doc('p1').set({jobType:'project', docNo:'PJ1', name:'สี่งวด', customerId:'c1', customerName:'ลูกค้า ก', startDate:'2026-09-01', endDate:'2026-12-31', items:[], createdBy:'admin1',
        installmentTotal: 4, installmentNo: 2, deliveries:[{no:1,total:4},{no:2,total:4}]});
      await db.collection('pm_projects').doc('p2').set({jobType:'project', docNo:'PJ2', name:'สองงวดครบ', customerId:'c1', customerName:'ลูกค้า ก', startDate:'2026-09-01', endDate:'2026-12-31', items:[], createdBy:'admin1',
        installmentTotal: 2, installmentNo: 2, deliveries:[{no:1,total:2},{no:2,total:2}]});
      await db.collection('pm_projects').doc('p3').set({jobType:'project', docNo:'PJ3', name:'ไม่แบ่งงวด', customerId:'c1', customerName:'ลูกค้า ก', startDate:'2026-09-01', endDate:'2026-12-31', items:[], createdBy:'admin1'});
      await db.collection('pm_projects').doc('p4').set({jobType:'project', docNo:'PJ4', name:'ห้างวดยังไม่ส่ง', customerId:'c1', customerName:'ลูกค้า ก', startDate:'2026-09-01', endDate:'2026-12-31', items:[], createdBy:'admin1', installmentTotal: 5});
      await db.collection('pm_projects').doc('s1').set({jobType:'sale', docNo:'SO1', name:'ขาย', customerId:'c1', customerName:'ลูกค้า ก', startDate:'2026-09-02', endDate:'2026-09-02', items:[], createdBy:'admin1'}); }""")
    page.wait_for_timeout(500)
    page.evaluate("showTab('projects')"); page.wait_for_timeout(300)

    # column order: เลขที่เอกสาร, งวดงาน, ชื่อโครงการ ...
    heads = page.evaluate("[...document.querySelectorAll('#tab-projects thead th')].map(t => t.textContent.trim())")
    assert heads[:3] == ['เลขที่เอกสาร', 'งวดงาน', 'ชื่อโครงการ'], heads
    R = lambda name, c: page.inner_text(f'#projectsBody tr:has-text("{name}") td:nth-child({c})')
    assert '2/4' in R('สี่งวด', 2) and 'รอส่งงวดที่ 3' in R('สี่งวด', 2)
    assert '2/2' in R('สองงวดครบ', 2) and 'ครบทุกงวด' in R('สองงวดครบ', 2)
    assert R('ไม่แบ่งงวด', 2).strip() == '-'
    assert '0/5' in R('ห้างวดยังไม่ส่ง', 2) and 'รอส่งงวดที่ 1' in R('ห้างวดยังไม่ส่ง', 2)

    # dropdown options: max total among visible projects is 5 (p4) -> "ทั้งหมด" + 1..5
    opts = page.evaluate("[...document.querySelectorAll('#projectsInstallmentFilter option')].map(o => o.textContent.trim())")
    assert opts == ['ทั้งหมด', 'งวดที่ 1', 'งวดที่ 2', 'งวดที่ 3', 'งวดที่ 4', 'งวดที่ 5'], opts
    assert page.locator('#tab-sales select').count() == 1, "the sale menu has no installment filter"

    # filtering: "งวดที่ 3" -> only the project whose next due installment is 3 (p1)
    page.select_option('#projectsInstallmentFilter', '3'); page.wait_for_timeout(200)
    body = page.inner_text('#projectsBody')
    assert 'สี่งวด' in body and 'สองงวดครบ' not in body and 'ไม่แบ่งงวด' not in body and 'ห้างวดยังไม่ส่ง' not in body
    assert page.inner_text('#projectsCount') == '1'

    # "งวดที่ 2" -> the fully-delivered 2-installment project (its stage stays at its last one)
    page.select_option('#projectsInstallmentFilter', '2'); page.wait_for_timeout(200)
    body = page.inner_text('#projectsBody')
    assert 'สองงวดครบ' in body and 'สี่งวด' not in body

    # "งวดที่ 1" -> the untouched 5-installment project (next due = 1)
    page.select_option('#projectsInstallmentFilter', '1'); page.wait_for_timeout(200)
    assert 'ห้างวดยังไม่ส่ง' in page.inner_text('#projectsBody') and page.inner_text('#projectsCount') == '1'

    # a project with no installments never matches a specific number, only "ทั้งหมด"
    for n in ['1','2','3','4','5']:
        page.select_option('#projectsInstallmentFilter', n); page.wait_for_timeout(150)
        assert 'ไม่แบ่งงวด' not in page.inner_text('#projectsBody')
    page.select_option('#projectsInstallmentFilter', 'all'); page.wait_for_timeout(200)
    assert page.inner_text('#projectsCount') == '4' and 'ไม่แบ่งงวด' in page.inner_text('#projectsBody')

    # เคลียร์ resets it, and it participates in the disabled/enabled state of the button
    page.select_option('#projectsInstallmentFilter', '3'); page.wait_for_timeout(200)
    assert not page.is_disabled('#projectsClearBtn')
    page.click('#projectsClearBtn'); page.wait_for_timeout(200)
    assert page.input_value('#projectsInstallmentFilter') == 'all' and page.inner_text('#projectsCount') == '4'

    # the search box and status filter narrow the visible ROWS, but the dropdown's own option list is scoped to every visible project
    # (not just the ones matching the current search/status), so it doesn't reshuffle every keystroke; a stale selection resets if it
    # deletes/becomes-invalid rather than "temporarily has 0 matches"
    page.select_option('#projectsInstallmentFilter', '5'); page.wait_for_timeout(200)
    page.fill('#projectsSearch', 'สี่งวด'); page.wait_for_timeout(200)   # only the 4-installment project's name matches, 0 rows for "งวดที่ 5"
    opts2 = page.evaluate("[...document.querySelectorAll('#projectsInstallmentFilter option')].map(o => o.value)")
    assert opts2 == ['all', '1', '2', '3', '4', '5'], "the option list itself doesn't depend on the search box"
    assert page.input_value('#projectsInstallmentFilter') == '5' and page.inner_text('#projectsCount') == '0', "a real (if temporarily empty) selection is kept, not reset"
    page.fill('#projectsSearch', ''); page.select_option('#projectsInstallmentFilter', 'all')
    # deleting the project that had the highest total (5) really does shrink the option list and resets an out-of-range selection
    page.select_option('#projectsInstallmentFilter', '5'); page.wait_for_timeout(200)
    page.evaluate("db.collection('pm_projects').doc('p4').update({ deletedAt: '2026-09-22T00:00:00Z', deletedBy: 'admin1' })"); page.wait_for_timeout(400)
    opts3 = page.evaluate("[...document.querySelectorAll('#projectsInstallmentFilter option')].map(o => o.value)")
    assert opts3 == ['all', '1', '2', '3', '4'], opts3
    assert page.input_value('#projectsInstallmentFilter') == 'all', "an option that no longer exists at all resets to all"

    print("errors:", errors); assert not errors
print("OK")
