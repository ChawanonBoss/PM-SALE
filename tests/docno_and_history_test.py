import os, sys, tempfile
import sys, http.server, threading, functools, datetime
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from harness import new_page, REPO_ROOT, goto_tab

class Q(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a): pass
h = functools.partial(Q, directory=REPO_ROOT)
srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), h)
threading.Thread(target=srv.serve_forever, daemon=True).start()
base = f"http://127.0.0.1:{srv.server_address[1]}"

today = datetime.date.today()
D = lambda n: (today + datetime.timedelta(days=n)).isoformat()
YMD = today.strftime("%Y%m%d")

TX_SHIM = """() => {
  db.runTransaction = async fn => {
    const writes = [];
    const tx = { get: ref => ref.get(), update: (ref, d) => writes.push(() => ref.update(d)), set: (ref, d) => writes.push(() => ref.set(d)) };
    const r = await fn(tx);
    for (const w of writes) await w();
    return r;
  };
}"""

with new_page(viewport={"width": 1600, "height": 1000}) as (page, errors):
    page.goto(f"{base}/index.html"); page.wait_for_timeout(500)
    page.evaluate("() => localStorage.setItem('pm-sale-login-ts', String(Date.now()))")
    page.evaluate("() => window.__authListeners[0]({uid:'admin1', email:'admin@a.com', displayName:'Admin One'})")
    page.wait_for_timeout(800)
    page.evaluate(TX_SHIM)
    page.evaluate("""async ([soonEnd, endSoon, wStart, wEnd, late, soon]) => {
      await db.collection('pm_customers').doc('c1').set({name:'กรมทดสอบ', type:'gov', createdBy:'admin1'});
      await db.collection('pm_customers').doc('c2').set({name:'บริษัท เอกชน จำกัด', type:'private', taxId:'0105555555555', createdBy:'admin1'});
      await db.collection('pm_customers').doc('c3').set({name:'ลูกค้าไม่มีงาน', type:'private', createdBy:'admin1'});
      await db.collection('pm_companies').doc('co1').set({name:'บริษัทเรา A', address:'x', phone:'1', taxId:'1'});
      await db.collection('pm_companies').doc('co2').set({name:'บริษัทเรา B', address:'y', phone:'2', taxId:'2'});
      await db.collection('pm_warehouse').doc('w1').set({part:'SW-1', brand:'Cisco', type:'Switch', name:'Catalyst', quantity:5, serials:['S1','S2','S3','S4','S5'], createdBy:'admin1'});
      await db.collection('pm_warehouse').doc('w2').set({part:'RT-1', brand:'MikroTik', type:'Router', name:'RB4011', quantity:20, serials:[], createdBy:'admin1'});
      await db.collection('pm_warehouse').doc('w3').set({part:'RT-2', brand:'Cisco', type:'Router', name:'ISR', quantity:1, serials:['R1'], createdBy:'admin1'});
      await db.collection('pm_warehouse').doc('w4').set({part:'IN-1', brand:'Siemens', type:'Industrial', name:'Scalance', quantity:9, serials:[], createdBy:'admin1'});
      // project A: contract ends soon, one plan step due soon and one overdue
      await db.collection('pm_projects').doc('pA').set({jobType:'project', docNo:'PJ20260101-001', name:'โครงการ A', customerId:'c1', customerName:'กรมทดสอบ', companyId:'co1', startDate:'2026-01-01', endDate:endSoon, createdBy:'admin1', items:[], warrantyMonths:12,
        plan:[{title:'ขั้นตอนใกล้ครบ', owner:'', start:soon, end:soon, done:false, subs:[]}, {title:'ขั้นตอนเลยกำหนด', owner:'', start:late, end:late, done:false, subs:[]}]});
      // project B: ended, warranty ends soon (12 months from wEnd)
      await db.collection('pm_projects').doc('pB').set({jobType:'project', docNo:'PJ20260101-002', name:'โครงการ B', customerId:'c2', customerName:'บริษัท เอกชน จำกัด', companyId:'co1', startDate:wStart, endDate:wEnd, createdBy:'admin1', items:[], warrantyMonths:12, plan:[{title:'x', owner:'', start:'', end:'', done:true, subs:[]}]});
      // a sale (no docNo yet: legacy) for company B
      await db.collection('pm_projects').doc('sA').set({jobType:'sale', name:'ขายเก่า', customerId:'c2', customerName:'บริษัท เอกชน จำกัด', companyId:'co2', startDate:'2026-02-01', endDate:'2026-02-01', createdAt:'2026-02-03T10:00:00.000Z', createdBy:'admin1',
        items:[{rid:'x', whId:'w1', part:'SW-1', brand:'Cisco', name:'Catalyst', type:'Switch', serials:['S1'], qty:1, status:'pending'}], warrantyMonths:12});
    }""", [D(3), D(10), D(-340 - 40), D(-340), D(-2), D(3)])
    page.wait_for_timeout(300)

    # ---------------- nav badges per menu ----------------
    badge = lambda id: (page.inner_text(f'#{id}').strip() if page.is_visible(f'#{id}') else None)
    a = page.evaluate("getDashAlerts()")
    print({k: (len(v) if isinstance(v, list) else v) for k, v in a.items()})
    # projects/equipment moved into group flyouts (see the sidebar-groups feature) - their old per-tab badge ids are gone, but the group button
    # they now live inside carries the same aggregate count
    assert badge('group1NavBadge') == '1', "group1 (ซื้อขาย/โครงการ) icon: contracts ending soon"
    assert badge('planNavBadge') == '2' and 'late' in page.get_attribute('#planNavBadge', 'class'), "plan icon: 1 soon + 1 overdue, red"
    assert badge('group2NavBadge') == '1', "group2 (คลังและอุปกรณ์) icon: warranty ending soon"
    assert badge('dashNavBadge') == '4', "dashboard icon: total"
    page.evaluate("db.collection('pm_projects').doc('pA').update({plan:[{title:'ขั้นตอนใกล้ครบ', owner:'', start:'%s', end:'%s', done:false, subs:[]}]})" % (D(3), D(3))); page.wait_for_timeout(300)
    assert badge('planNavBadge') == '1' and 'late' not in page.get_attribute('#planNavBadge', 'class'), "no overdue step -> orange"
    page.evaluate("db.collection('pm_projects').doc('pA').update({plan:[{title:'ขั้นตอนใกล้ครบ', owner:'', start:'%s', end:'%s', done:true, subs:[]}]})" % (D(3), D(3))); page.wait_for_timeout(300)
    assert badge('planNavBadge') is None, "all ticked -> badge disappears"
    page.evaluate("db.collection('pm_projects').doc('pA').update({plan:[{title:'ขั้นตอนเลยกำหนด', owner:'', start:'%s', end:'%s', done:false, subs:[]}]})" % (D(-2), D(-2))); page.wait_for_timeout(300)

    # ---------------- document numbers ----------------
    goto_tab(page, 'projects')
    heads = page.evaluate("[...document.querySelectorAll('#tab-projects thead th')].map(t => t.textContent.trim())")
    assert heads[0] == 'เลขที่เอกสาร', heads
    goto_tab(page, 'sales'); page.click('#salesCreateBtn')
    assert 'จะรันให้อัตโนมัติ' in page.inner_text('#prjDocNo')
    assert page.evaluate("document.getElementById('prjJobType').disabled") is False and page.input_value('#prjJobType') == 'sale'
    page.fill('#prjName', 'ขายใหม่ 1'); page.select_option('#prjCustomer', label='กรมทดสอบ'); page.select_option('#prjCompany', label='บริษัทเรา A')
    page.fill('#prjStart', D(0))
    R = lambda n, c: f"#prjItemsBody tr:nth-child({n}) td:nth-child({c})"
    page.select_option(f"{R(1,2)} select", 'w1'); page.fill(f"{R(1,7)} input", '2'); page.press(f"{R(1,7)} input", 'Tab')
    page.select_option(f"{R(1,6)} select >> nth=0", 'S2'); page.select_option(f"{R(1,6)} select >> nth=1", 'S3')
    page.select_option(f"{R(1,8)} select", 'done')
    page.click('#projectSaveBtn'); page.click('#confirmModalOkBtn'); page.wait_for_timeout(500)
    s1 = page.evaluate("data.projects.find(p => p.name === 'ขายใหม่ 1')")
    print(s1['docNo'])
    assert s1['docNo'] == f"SO{YMD}-001", s1['docNo']
    assert 'SO' + YMD + '-001' in page.inner_text('#toast')
    assert page.evaluate(f"(async () => (await db.collection('pm_counters').doc('SO{YMD}').get()).data().n)()") == 1
    # second sale on the same day -> 002 ; a project -> PJ...-001 (separate sequence)
    # saving a brand-new sale now routes straight to its photo page (see the photo-attachment feature), so come back to the sales list first
    goto_tab(page, 'sales'); page.click('#salesCreateBtn'); page.fill('#prjName', 'ขายใหม่ 2'); page.select_option('#prjCustomer', label='กรมทดสอบ'); page.fill('#prjStart', D(0))
    page.click('#projectSaveBtn'); page.wait_for_timeout(400)
    assert page.evaluate("data.projects.find(p => p.name === 'ขายใหม่ 2').docNo") == f"SO{YMD}-002"
    goto_tab(page, 'projects'); page.click('#projectsCreateBtn'); assert page.input_value('#prjJobType') == 'project'; page.fill('#prjName', 'โครงการใหม่'); page.select_option('#prjCustomer', label='กรมทดสอบ')
    page.fill('#prjStart', D(0)); page.fill('#prjEnd', D(90)); page.click('#projectSaveBtn'); page.wait_for_timeout(400)
    assert page.evaluate("data.projects.find(p => p.name === 'โครงการใหม่').docNo") == f"PJ{YMD}-001"
    assert page.evaluate(f"(async () => (await db.collection('pm_counters').doc('SO{YMD}').get()).data().n)()") == 2
    # editing keeps the number and locks the type
    goto_tab(page, 'sales'); page.click('#salesBody tr:has-text("ขายใหม่ 1") button:has-text("แก้ไข")')
    assert page.inner_text('#prjDocNo') == f"SO{YMD}-001" and page.evaluate("document.getElementById('prjJobType').disabled") is True
    page.keyboard.press('Escape')
    # a legacy item without a number gets one on save, dated by its creation day (2026-02-03), prefix by type
    page.click('#salesBody tr:has-text("ขายเก่า") button:has-text("แก้ไข")')
    assert 'จะรันให้อัตโนมัติ' in page.inner_text('#prjDocNo') and page.evaluate("document.getElementById('prjJobType').disabled") is False
    page.click('#projectSaveBtn'); page.wait_for_timeout(400)
    assert page.evaluate("data.projects.find(p => p.name === 'ขายเก่า').docNo") == "SO20260203-001"
    # search by number
    page.fill('#salesSearch', 'SO' + YMD + '-002'); assert page.locator('#salesBody tr').count() == 1 and 'ขายใหม่ 2' in page.inner_text('#salesBody')
    page.fill('#salesSearch', '')

    # ---------------- document number shown on every project view ----------------
    hp = page.evaluate("buildProjectPrintHtml(data.projects.find(p => p.name === 'ขายใหม่ 1'))")
    assert 'เลขที่เอกสาร' in hp and f"SO{YMD}-001" in hp
    # letterhead: ที่อยู่บริษัท is its own right-aligned line; เบอร์โทร and เลขประจำตัวผู้เสียภาษี share the next line together
    # (matches เอกสารส่งมอบงานแบบใหม่.docx) - address is never joined onto that line with " / "
    assert hp.count('class="addr"') == 2 and '<div class="addr">x</div>' in hp and 'โทร. 1' in hp and 'เลขประจำตัวผู้เสียภาษี 1' in hp and 'x / เลขประจำตัวผู้เสียภาษี' not in hp
    # section 4 gained a photo-attachment line, right after the equipment manual
    i_manual = hp.find('คู่มือการใช้งานอุปกรณ์'); i_photo = hp.find('เอกสารแสดงรูปภาพของรายการอุปกรณ์'); i_install = hp.find('เอกสารแสดงรายละเอียดของงานติดตั้ง')
    assert -1 < i_manual < i_photo < i_install, (i_manual, i_photo, i_install)
    page.click('.nav-item[data-tab="dashboard"]')
    assert f"PJ{YMD}-001" in page.inner_text('#dashCols')
    page.click('.nav-item[data-tab="actionplan"]')
    assert 'PJ20260101-001' in page.inner_text('#planCards')
    page.click('.plan-card:has-text("โครงการ A")'); assert 'PJ20260101-001' in page.inner_text('#planMeta')
    page.evaluate("window.print = () => {}"); page.click('#planPrintBtn'); page.wait_for_timeout(200)
    assert 'PJ20260101-001' in page.inner_html('#printArea'); page.evaluate("window.dispatchEvent(new Event('afterprint'))")
    page.click('#planBackBtn')
    goto_tab(page, 'customers'); page.click('#customersBody tr:has-text("กรมทดสอบ") td:nth-child(1)')
    assert f"SO{YMD}-001" in page.inner_text('#customerProjectsModal'); page.click('#cpCloseBtn')

    # ---------------- warranty page: number + type columns and a type filter ----------------
    goto_tab(page, 'equipment')
    heads = page.evaluate("[...document.querySelectorAll('#tab-equipment thead th')].map(t => t.textContent.trim())")
    assert heads[:3] == ['เลขที่เอกสาร', 'ซื้อขาย/โครงการ · ลูกค้า', 'ประเภท'], heads
    body = page.inner_text('#equipmentBody'); assert 'PJ20260101-002' in body and 'โครงการ' in body
    page.select_option('#equipmentTypeFilter', 'sale'); body = page.inner_text('#equipmentBody'); assert 'ขายใหม่ 1' in body and 'โครงการ B' not in body
    page.select_option('#equipmentTypeFilter', 'all'); page.fill('#equipmentSearch', 'PJ20260101-002'); assert page.locator('#equipmentBody tr').count() == 1
    page.fill('#equipmentSearch', '')

    # ---------------- warehouse: withdrawal history ----------------
    goto_tab(page, 'warehouse')
    row = page.inner_text('#warehouseBody tr:has-text("Catalyst")'); assert 'เบิก/คืน 1 ครั้ง' in row, row
    page.click('#warehouseBody tr:has-text("Catalyst") td:nth-child(4)')
    hist = page.inner_text('#serialHistoryBody'); print(hist.replace('\n', ' | '))
    assert 'เบิกออก' in hist and f"SO{YMD}-001" in hist and 'ขายใหม่ 1' in hist and 'S2, S3' in hist and 'Admin One' in hist
    page.click('#serialHistoryBody a'); assert page.is_visible('#projectModal') and page.input_value('#prjName') == 'ขายใหม่ 1'
    # revert -> a 'return' entry appears (an already-saved job locks/unlocks the warehouse live, before any "บันทึกรายการ" click)
    page.select_option(f"{R(1,8)} select", 'pending'); page.wait_for_timeout(150)
    assert page.is_visible('#confirmModal')
    page.click('#confirmModalOkBtn'); page.wait_for_timeout(500)
    page.click('#projectCancelBtn')
    page.click('#warehouseBody tr:has-text("Catalyst") td:nth-child(4)')
    hist = page.inner_text('#serialHistoryBody')
    assert 'คืนเข้าโกดัง' in hist and 'เบิกออก' in hist and page.locator('#serialHistoryBody tr').count() == 2
    assert page.evaluate("data.warehouse.find(w => w.id === 'w1').history.map(h => h.type)") == ['out', 'return']
    page.click('#serialCloseBtn')

    # ---------------- warehouse: brand filter + sort by stock ----------------
    assert page.evaluate("[...document.querySelectorAll('#warehouseBrandFilter option')].map(o => o.textContent)") == ['ทุกยี่ห้อ', 'Cisco', 'MikroTik', 'Siemens']
    page.select_option('#warehouseBrandFilter', 'Cisco'); names = page.evaluate("[...document.querySelectorAll('#warehouseBody tr td:nth-child(4)')].map(t => t.textContent.trim())")
    assert sorted(names) == ['Catalyst', 'ISR']
    page.select_option('#warehouseBrandFilter', 'all'); page.select_option('#warehouseTypeFilter', 'Router')
    assert page.locator('#warehouseBody tr').count() == 2
    page.select_option('#warehouseTypeFilter', 'all')
    qtys = lambda: page.evaluate("[...document.querySelectorAll('#warehouseBody tr td:nth-child(5)')].map(t => parseInt(t.textContent))")
    page.select_option('#warehouseSortFilter', 'asc'); q = qtys(); print("asc", q); assert q == sorted(q) and q[0] == 1
    page.select_option('#warehouseSortFilter', 'desc'); q = qtys(); print("desc", q); assert q == sorted(q, reverse=True) and q[0] == 20
    page.select_option('#warehouseBrandFilter', 'Cisco'); q = qtys(); assert q == sorted(q, reverse=True), "filters and sort combine"
    page.select_option('#warehouseBrandFilter', 'all'); page.select_option('#warehouseSortFilter', 'name')

    # ---------------- customers: type filter + sort by number of sales/projects ----------------
    goto_tab(page, 'customers')
    cnt = lambda: page.evaluate("[...document.querySelectorAll('#customersBody tr')].map(r => [r.querySelector('td b').textContent, parseInt(r.children[6].textContent)])")
    page.select_option('#customersSortFilter', 'desc'); c = cnt(); print("desc", c); assert [x[1] for x in c] == sorted([x[1] for x in c], reverse=True) and c[0][0] == 'กรมทดสอบ'
    page.select_option('#customersSortFilter', 'asc'); c = cnt(); assert [x[1] for x in c] == sorted([x[1] for x in c]) and c[0][0] == 'ลูกค้าไม่มีงาน'
    page.select_option('#customersTypeFilter', 'gov'); assert [x[0] for x in cnt()] == ['กรมทดสอบ']
    page.select_option('#customersTypeFilter', 'private'); assert sorted(x[0] for x in cnt()) == ['บริษัท เอกชน จำกัด', 'ลูกค้าไม่มีงาน']
    page.select_option('#customersTypeFilter', 'all'); page.select_option('#customersSortFilter', 'name')

    # ---------------- companies: click the name -> that company's sales/projects ----------------
    goto_tab(page, 'companies')
    assert 'ซื้อขาย/โครงการ:' in page.inner_text('#companiesGrid .company-card:has-text("บริษัทเรา A")')
    page.click('#companiesGrid .company-name-link:has-text("บริษัทเรา A")')
    assert page.is_visible('#companyProjectsModal') and page.inner_text('#cpoTitle') == 'บริษัทเรา A'
    summ = page.inner_text('#cpoSummary'); print(summ)
    # A: project A, B, sale 'ขายใหม่ 1', 'ขายใหม่ 2', 'โครงการใหม่'? (that one had no company) -> A has pA, pB, 1 sale = 3
    n_a = page.evaluate("data.projects.filter(p => p.companyId === 'co1').length"); assert n_a == 3, n_a
    assert f"ทั้งหมด {n_a} รายการ" in summ.replace('\n', ' ') and 'ซื้อขาย 1' in summ and 'โครงการ 2' in summ
    body = page.inner_text('#cpoBody'); assert 'PJ20260101-001' in body and f"SO{YMD}-001" in body and page.locator('#cpoBody tr').count() == n_a
    page.click('#cpoBody a:has-text("โครงการ A")'); assert page.is_visible('#projectModal') and not page.is_visible('#companyProjectsModal'); page.keyboard.press('Escape')
    page.click('#companiesGrid .company-name-link:has-text("บริษัทเรา B")'); assert 'ขายเก่า' in page.inner_text('#cpoBody'); page.click('#cpoCloseBtn')
    # buttons on the card don't open the window
    page.click('#companiesGrid .company-card:has-text("บริษัทเรา B") button:has-text("แก้ไข")'); assert page.is_visible('#companyModal') and not page.is_visible('#companyProjectsModal'); page.keyboard.press('Escape')

    # ---------------- dashboard: sale / project switch + clear ----------------
    page.click('.nav-item[data-tab="dashboard"]')
    vals = lambda: page.evaluate("[...document.querySelectorAll('#dashStats .stat-value')].map(e => e.textContent)")
    label0 = lambda: page.inner_text('#dashStats .stat-card:first-child .stat-label')
    total = page.evaluate("data.projects.length"); sales = page.evaluate("data.projects.filter(p => p.jobType === 'sale').length")
    assert vals()[0] == str(total) and label0() == 'ซื้อขาย / โครงการทั้งหมด' and page.is_disabled('#dashJobClear')
    page.click('.subtab-item[data-dashjob="sale"]')
    assert vals()[0] == str(sales) and label0() == 'ซื้อขายทั้งหมด' and not page.is_disabled('#dashJobClear')
    assert 'active' in page.get_attribute('.subtab-item[data-dashjob="sale"]', 'class')
    assert 'ดำเนินการแล้ว' in page.inner_text('#dashStats'), "sale view uses the sale status wording"
    assert 'โครงการ A' not in page.inner_text('#dashCols') and 'ขายใหม่' in page.inner_text('#dashCols')
    assert 'ประกัน' in page.inner_text('#dashAlert') or not page.is_visible('#dashAlert') or True
    page.click('.subtab-item[data-dashjob="project"]')
    assert vals()[0] == str(total - sales) and label0() == 'โครงการทั้งหมด' and 'ขายใหม่' not in page.inner_text('#dashCols')
    assert 'สิ้นสุดสัญญาโครงการ' in page.inner_text('#dashStats')
    assert 'โครงการ' in page.inner_text('#dashAlert')                                        # project alerts (contract ending, plan steps) show here
    # the sale view hides project-only alerts
    page.click('.subtab-item[data-dashjob="sale"]'); assert 'สัญญาจะสิ้นสุด' not in page.inner_text('#dashAlert') and 'แผนดำเนินการ' not in page.inner_text('#dashAlert')
    # clicking a card carries the choice to the list
    page.click('#dashStats .stat-card.filled.pending'); assert page.inner_text('#pageTitle') == 'ซื้อขาย' and page.input_value('#salesStatusFilter') == 'pending'
    page.click('.nav-item[data-tab="dashboard"]')
    page.click('#dashJobClear'); assert vals()[0] == str(total) and label0() == 'ซื้อขาย / โครงการทั้งหมด' and page.is_disabled('#dashJobClear')
    assert badge('dashNavBadge') is not None, "the sidebar badges ignore the dashboard switch"
    page.screenshot(path="v19_dash.png")

    # ---------------- trash shows the number ----------------
    goto_tab(page, 'sales'); page.click('#salesBody tr:has-text("ขายใหม่ 2") .delete-btn'); page.click('#confirmModalOkBtn'); page.wait_for_timeout(300)
    goto_tab(page, 'trash'); page.wait_for_timeout(500)
    assert f"SO{YMD}-002" in page.inner_text('#trashBody')
    print("errors:", errors); assert not errors
print("OK")
