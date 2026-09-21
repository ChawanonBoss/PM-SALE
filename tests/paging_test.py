import os, sys, tempfile
import sys, http.server, threading, functools
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from harness import new_page, REPO_ROOT

class Q(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a): pass
h = functools.partial(Q, directory=REPO_ROOT)
srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), h)
threading.Thread(target=srv.serve_forever, daemon=True).start()
base = f"http://127.0.0.1:{srv.server_address[1]}"

with new_page(viewport={"width": 1700, "height": 1000}) as (page, errors):
    page.goto(f"{base}/index.html"); page.wait_for_timeout(500)
    page.evaluate("() => localStorage.setItem('pm-sale-login-ts', String(Date.now()))")
    page.evaluate("() => window.__authListeners[0]({uid:'admin1', email:'admin@a.com', displayName:'Admin One'})")
    page.wait_for_timeout(800)
    # 123 projects (a few sales), 25 customers, 34 warehouse items, 12 companies, 15 audit rows, 11 errors, 13 pending invites
    page.evaluate("""async () => {
      for (let i = 1; i <= 25; i++) await db.collection('pm_customers').doc('c' + i).set({name:'ลูกค้า ' + String(i).padStart(2,'0'), type: i % 2 ? 'gov' : 'private', createdBy:'admin1'});
      for (let i = 1; i <= 123; i++) await db.collection('pm_projects').doc('p' + i).set({jobType: i % 5 === 0 ? 'sale' : 'project', name:'รายการ ' + String(i).padStart(3,'0'), customerId:'c1', customerName:'ลูกค้า 01',
        startDate:'2026-01-' + String((i % 28) + 1).padStart(2,'0'), endDate:'2027-12-31', createdBy:'admin1', items:[], plan: i % 5 === 0 ? [] : [{title:'x', owner:'', start:'', end:'', done:false, subs:[]}]});
      for (let i = 1; i <= 34; i++) await db.collection('pm_warehouse').doc('w' + i).set({part:'P' + i, brand:'B' + (i % 3), type:'T' + (i % 2), name:'อุปกรณ์ ' + String(i).padStart(2,'0'), quantity:i, serials:[], createdBy:'admin1'});
      for (let i = 1; i <= 12; i++) await db.collection('pm_companies').doc('co' + i).set({name:'บริษัท ' + String(i).padStart(2,'0'), address:'-', phone:'-', taxId:'-'});
      for (let i = 1; i <= 15; i++) await db.collection('pm_auditLog').add({action:'สร้างลูกค้า', entityLabel:'E' + i, details:'', changedBy:'admin1', changedByName:'Admin', timestamp:new Date(Date.now() - i * 1000).toISOString()});
      for (let i = 1; i <= 11; i++) await db.collection('pm_errorLog').add({message:'err ' + i, page:'x', userName:'u', timestamp:new Date(Date.now() - i * 1000).toISOString()});
      for (let i = 1; i <= 13; i++) await db.collection('pm_pendingRoles').doc('inv' + i + '@example.com').set({name:'เชิญ ' + i, role:'user'});
      for (let i = 1; i <= 23; i++) await db.collection('pm_customers').doc('d' + i).set({name:'ถังขยะ ' + i, type:'private', createdBy:'admin1', deletedAt:new Date(Date.now() - i * 1000).toISOString(), deletedBy:'admin1'});
    }""")
    page.wait_for_timeout(800)

    rows = lambda body: page.locator(f'#{body} > tr').count()
    pager = lambda id: page.inner_text(f'#{id}').replace('\n', ' ')
    nums = lambda id: page.evaluate(f"[...document.querySelectorAll('#{id} .pager-pages .page-btn')].map(b => b.textContent.trim())")
    active = lambda id: page.evaluate(f"(document.querySelector('#{id} .page-btn.active') || {{textContent:''}}).textContent.trim()")

    # ---------------- projects: 123 rows ----------------
    page.click('.nav-item[data-tab="projects"]')
    assert rows('projectsBody') == 10, "default: 10 rows"
    print(pager('projectsPager'))
    assert '1–10 จากทั้งหมด 123' in pager('projectsPager')
    assert nums('projectsPager') == ['‹', '1', '2', '3', '4', '5', '›'], nums('projectsPager')
    assert active('projectsPager') == '1' and page.evaluate("document.querySelector('#projectsPager .page-btn').disabled"), "‹ disabled on page 1"
    assert page.evaluate("[...document.querySelectorAll('#projectsPager select option')].map(o => o.textContent)") == ['10', '20', '50', '100']
    first_p1 = page.inner_text('#projectsBody tr:first-child td:nth-child(2)')
    page.click('#projectsPager .page-btn:has-text("3")')
    assert active('projectsPager') == '3' and rows('projectsBody') == 10 and '21–30' in pager('projectsPager')
    assert page.inner_text('#projectsBody tr:first-child td:nth-child(2)') != first_p1
    assert nums('projectsPager') == ['‹', '1', '2', '3', '4', '5', '›']
    page.click('#projectsPager .page-btn:has-text("5")')                             # window slides once you go past 5
    assert nums('projectsPager') == ['‹', '3', '4', '5', '6', '7', '›'], nums('projectsPager')
    page.click('#projectsPager .page-btn:has-text("›")'); assert active('projectsPager') == '6'
    page.click('#projectsPager .page-btn:has-text("‹")'); assert active('projectsPager') == '5'
    # jump to the last page: 123 rows -> 13 pages, last has 3 rows, "›" disabled
    for _ in range(8):
        page.click('#projectsPager .page-btn:has-text("›")')
    assert active('projectsPager') == '13' and rows('projectsBody') == 3 and '121–123' in pager('projectsPager')
    assert page.evaluate("[...document.querySelectorAll('#projectsPager .page-btn')].pop().disabled")
    assert nums('projectsPager') == ['‹', '9', '10', '11', '12', '13', '›'], nums('projectsPager')
    # page size: 20 -> back to page 1
    page.select_option('#projectsPager select', '20')
    assert rows('projectsBody') == 20 and active('projectsPager') == '1' and '1–20 จากทั้งหมด 123' in pager('projectsPager')
    assert nums('projectsPager')[1:-1] == ['1', '2', '3', '4', '5']
    page.select_option('#projectsPager select', '50'); assert rows('projectsBody') == 50 and nums('projectsPager')[1:-1] == ['1', '2', '3']
    page.select_option('#projectsPager select', '100'); assert rows('projectsBody') == 100 and nums('projectsPager')[1:-1] == ['1', '2']
    page.click('#projectsPager .page-btn:has-text("2")'); assert rows('projectsBody') == 23
    # filters reset to page 1 and shrink the pager; size survives
    page.select_option('#projectsTypeFilter', 'sale')
    assert active('projectsPager') == '1' and rows('projectsBody') == 24 and '1–24 จากทั้งหมด 24' in pager('projectsPager') and nums('projectsPager')[1:-1] == ['1']
    assert page.input_value('#projectsPager select') == '100'
    page.click('#projectsClearBtn')
    assert '1–100 จากทั้งหมด 123' in pager('projectsPager')
    page.select_option('#projectsPager select', '10')
    # search narrows -> fewer pages
    page.fill('#projectsSearch', 'รายการ 01'); assert '1–10 จากทั้งหมด 10' in pager('projectsPager') and nums('projectsPager')[1:-1] == ['1']   # 010..019 + ... ("รายการ 01x")
    page.fill('#projectsSearch', 'ไม่มีแน่นอน'); assert page.inner_text('#projectsPager').strip() == '' and 'ยังไม่มี' in page.inner_text('#projectsBody')
    page.click('#projectsClearBtn')
    # a delete that empties the last page clamps to the previous page
    page.select_option('#projectsPager select', '100'); page.click('#projectsPager .page-btn:has-text("2")'); assert rows('projectsBody') == 23
    for i in range(101, 124):
        page.evaluate(f"db.collection('pm_projects').doc('p{i}').update({{deletedAt:'2026-01-01'}})")
    page.wait_for_timeout(500)
    assert active('projectsPager') == '1' and rows('projectsBody') == 100 and '1–100 จากทั้งหมด 100' in pager('projectsPager'), pager('projectsPager')
    page.select_option('#projectsPager select', '10')

    # ---------------- every other list ----------------
    def check(tab, body, pager_id, total, expect_first_page=10):
        page.click(f'.nav-item[data-tab="{tab}"]'); page.wait_for_timeout(250)
        assert rows(body) == expect_first_page, (tab, rows(body))
        assert f'จากทั้งหมด {total}' in pager(pager_id), (tab, pager(pager_id))
        assert page.evaluate(f"[...document.querySelectorAll('#{pager_id} select option')].map(o => o.textContent)") == ['10', '20', '50', '100']
        pages = -(-total // 10)
        last = page.evaluate(f"[...document.querySelectorAll('#{pager_id} .page-btn')].map(b => b.textContent.trim())")
        assert last[1:-1] == [str(n) for n in range(1, min(5, pages) + 1)], (tab, last)
        page.click(f'#{pager_id} .page-btn:has-text("2")')
        assert rows(body) == min(10, total - 10) and active(pager_id) == '2', (tab, rows(body))
        page.click(f'#{pager_id} .page-btn:has-text("‹")')
        print("ok:", tab, total)
    check('equipment', 'equipmentBody', 'equipmentPager', 100)          # warranty page lists every project (100 left after the deletes)
    check('warehouse', 'warehouseBody', 'warehousePager', 34)
    check('customers', 'customersBody', 'customersPager', 25)
    page.click('.nav-item[data-tab="companies"]'); assert page.locator('#companiesGrid > .company-card').count() == 10 and 'จากทั้งหมด 12' in pager('companiesPager')
    page.click('#companiesPager .page-btn:has-text("2")'); assert page.locator('#companiesGrid > .company-card').count() == 2; page.click('#companiesPager .page-btn:has-text("‹")'); print("ok: companies (cards)")
    check('users', 'usersBody', 'usersPager', 14)                        # admin + u? + 13 invites (+ the signed-in admin's own profile)
    page.click('.nav-item[data-tab="actionplan"]')
    assert page.locator('#planCards > .plan-card').count() == 10 and 'จากทั้งหมด' in pager('planPager'); print("ok: plan cards", pager('planPager'))
    page.click('.nav-item[data-tab="audit"]')
    assert rows('auditBody') == 10 and 'จากทั้งหมด 15' in pager('auditPager'); page.click('#auditPager .page-btn:has-text("2")'); assert rows('auditBody') == 5
    page.click('.subtab-item[data-auditsub="errors"]'); assert rows('errorBody') == 10 and 'จากทั้งหมด 11' in pager('errorsPager'); print("ok: audit + errors")
    page.click('.nav-item[data-tab="trash"]'); page.wait_for_timeout(600)
    assert rows('trashBody') == 10 and 'จากทั้งหมด 46' in pager('trashPager') and nums('trashPager')[1:-1] == ['1', '2', '3', '4', '5']; print("ok: trash")
    # search resets the page on the warehouse list too
    page.click('.nav-item[data-tab="warehouse"]'); page.click('#warehousePager .page-btn:has-text("3")'); assert active('warehousePager') == '3'
    page.select_option('#warehouseSortFilter', 'desc'); assert active('warehousePager') == '1'
    page.screenshot(path="v192_pager.png")
    print("errors:", errors); assert not errors
print("OK")
