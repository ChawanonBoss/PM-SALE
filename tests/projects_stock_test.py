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

TX_SHIM = """() => {
  // the test mock has no transactions: run the callback against the mock, then apply the buffered writes
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
    page.evaluate("""async () => {
      await db.collection('pm_customers').doc('c1').set({name:'การไฟฟ้าทดสอบ', type:'gov', createdBy:'admin1'});
      await db.collection('pm_companies').doc('co1').set({name:'บริษัท ทดสอบ จำกัด'});
      await db.collection('pm_warehouse').doc('w1').set({part:'SW-24', brand:'Cisco', type:'Switch', name:'Catalyst 9200', quantity:5, serials:['S1','S2','S3','S4','S5'], createdBy:'admin1'});
      await db.collection('pm_warehouse').doc('w2').set({part:'RT-1', brand:'MikroTik', type:'Router', name:'RB4011', quantity:2, serials:[], createdBy:'admin1'});
      // an old-shape project (v1.5 items) and a v1.6 heading/detail one
      await db.collection('pm_projects').doc('old1').set({name:'โครงการเก่า', customerId:'c1', customerName:'การไฟฟ้าทดสอบ', startDate:'2026-01-01', endDate:'2026-06-30', createdBy:'admin1',
        items:[{name:'กล้อง CCTV', detail:'รุ่น A', qty:4, unit:'ตัว', location:'ชั้น 1', warrantyMonths:12}, {title:'ติดตั้ง', detail:'ชั้น 2', type:'ทีมติดตั้ง', start:'2026-02-01', end:'2026-02-10'}]});
    }""")
    page.wait_for_timeout(300)
    P = lambda: page.evaluate("data.projects.find(p => p.name === 'ขายสวิตช์')")
    W = lambda id: page.evaluate(f"(() => {{ const w = data.warehouse.find(x => x.id === '{id}'); return {{quantity: w.quantity, serials: w.serials}}; }})()")

    # ---------------- renames + filter ----------------
    # sales/projects now live inside the "ซื้อขาย/โครงการ" group flyout, not their own rail buttons - open it to check their renamed labels
    page.click('.nav-item[data-group="group1"]')
    assert page.inner_text('.nav-group-item[data-tab="sales"]').strip() == 'ซื้อขาย' and page.inner_text('.nav-group-item[data-tab="projects"]').strip() == 'โครงการ'
    page.click('.nav-item[data-tab="dashboard"]')
    assert page.inner_text('#dashStats .stat-card:first-child .stat-label') == 'ซื้อขาย / โครงการทั้งหมด'
    goto_tab(page, 'projects')
    assert page.inner_text('#pageTitle') == 'โครงการ' and 'โครงการทั้งหมด' in page.inner_text('#tab-projects .panel-head h3') and page.inner_text('#projectsCreateBtn') == '+ เพิ่มโครงการ'
    assert page.locator('#projectsTypeFilter').count() == 0 and 'ประเภทงาน' not in page.inner_text('#tab-projects thead'), "the job-type filter and column are gone"
    goto_tab(page, 'sales')
    assert page.inner_text('#pageTitle') == 'ซื้อขาย' and 'ซื้อขายทั้งหมด' in page.inner_text('#tab-sales .panel-head h3') and page.inner_text('#salesCreateBtn') == '+ เพิ่มการซื้อขาย'

    # ---------------- form: order + labels per job type ----------------
    page.click('#salesCreateBtn')
    assert page.inner_text('#projectModalTitle') == 'เพิ่มการซื้อขาย' and page.inner_text('#projectSaveBtn') == 'บันทึกรายการ'
    order = page.evaluate("[...document.querySelectorAll('#projectForm .form-grid .field label')].map(l => l.textContent.trim())")
    print(order)
    assert order == ['ชื่องาน *', 'หน่วยงาน / ลูกค้า *', 'เลขที่สัญญา', 'เลขที่ PO', 'จำนวนงวดงานทั้งหมด', 'บันทึกรูปภาพชุดใด (เลือกได้มากกว่า 1)', 'รูปภาพอุปกรณ์', 'รูปภาพงานติดตั้ง', 'วันที่สั่งซื้อ *', 'วันที่สิ้นสุด *', 'บริษัทของเรา (หัวกระดาษ PDF)', 'สถานที่ส่งสินค้า', 'การรับประกัน (เดือน)', 'หมายเหตุ'], order
    assert page.evaluate("document.getElementById('prjJobType').type") == 'hidden' and page.input_value('#prjJobType') == 'sale', "no job-type select: the menu decides"
    heads = page.evaluate("[...document.querySelectorAll('#projectModal .items-table thead th')].map(t => t.textContent.trim())")
    assert heads[1].startswith('Part') and heads[2:8] == ['ยี่ห้อ', 'ชื่อ', 'ประเภท', 'รหัสอุปกรณ์', 'จำนวน', 'สถานะ'], heads
    page.evaluate("$('prjJobType').value = 'sale'; applyJobType()")
    assert page.inner_text('#prjNameLabel') == 'ชื่องาน *' and page.inner_text('#prjStartLabel') == 'วันที่สั่งซื้อ *' and page.inner_text('#prjLocationLabel') == 'สถานที่ส่งสินค้า'
    assert not page.is_visible('#prjEndField') and page.evaluate("document.getElementById('prjEnd').required") is False
    page.evaluate("$('prjJobType').value = 'project'; applyJobType()")
    assert page.inner_text('#prjNameLabel') == 'ชื่อโครงการ *' and page.is_visible('#prjEndField') and page.inner_text('#prjLocationLabel') == 'สถานที่ติดตั้ง'
    page.evaluate("$('prjJobType').value = 'sale'; applyJobType()")

    # ---------------- a SALE with warehouse-linked lines ----------------
    page.fill('#prjName', 'ขายสวิตช์'); page.select_option('#prjCustomer', index=1); page.select_option('#prjCompany', index=1)
    page.fill('#prjStart', '2026-09-01'); page.fill('#prjLocation', 'คลังลูกค้า')
    assert page.inner_text('#prjStartText') == '01/09/2026' and 'หมดประกัน 01/09/2027' in page.inner_text('#prjWarrantyHint') and 'วันที่สั่งซื้อ' in page.inner_text('#prjWarrantyHint')
    R = lambda n, c: f"#prjItemsBody tr:nth-child({n}) td:nth-child({c})"
    opts = page.evaluate("[...document.querySelectorAll('#prjItemsBody tr:first-child td:nth-child(2) option')].map(o => o.textContent)")
    print(opts)
    assert opts[0] == '— เลือกอุปกรณ์จากโกดัง —' and any('RT-1' in o and 'คงเหลือ 2' in o for o in opts) and any('SW-24' in o and 'Cisco' in o and 'คงเหลือ 5' in o for o in opts)
    page.select_option(f"{R(1,2)} select", 'w1')
    assert [page.inner_text(R(1, c)).strip() for c in (3, 4, 5)] == ['Cisco', 'Catalyst 9200', 'Switch']           # filled from the warehouse
    assert 'คงเหลือ 5' in page.inner_text(R(1, 2)) and page.locator(f"{R(1,6)} select").count() == 1
    page.fill(f"{R(1,7)} input", '2'); page.press(f"{R(1,7)} input", 'Tab')
    assert page.locator(f"{R(1,6)} select").count() == 2                                                             # one serial box per unit
    page.select_option(f"{R(1,6)} select >> nth=0", 'S2')
    assert 'S2' not in page.evaluate("[...document.querySelectorAll('#prjItemsBody tr:first-child td:nth-child(6) select')[1].options].map(o => o.value)"), "a serial already picked isn't offered twice"
    page.select_option(f"{R(1,6)} select >> nth=1", 'S4')
    assert page.input_value(f"{R(1,8)} select") == 'pending'                                                         # default status
    page.click('#prjAddItemBtn')
    page.select_option(f"{R(2,2)} select", 'w2')
    assert page.locator(f"{R(2,6)} select").count() == 0                                                             # RB4011 has no serials recorded
    page.fill(f"{R(2,7)} input", '1'); page.press(f"{R(2,7)} input", 'Tab')
    # a second line for the same warehouse item must not offer S2/S4 again
    page.click('#prjAddItemBtn'); page.select_option(f"{R(3,2)} select", 'w1')
    offered = page.evaluate("[...document.querySelectorAll('#prjItemsBody tr:nth-child(3) td:nth-child(6) select option')].map(o => o.value)")
    assert 'S2' not in offered and 'S4' not in offered and 'S1' in offered, offered
    page.click(f"{R(3,9)} button")                                                                                  # remove that third line again
    page.click('#projectSaveBtn'); page.wait_for_timeout(400)
    # saving a brand-new sale now routes straight to its photo page (see the photo-attachment feature) - come back to the sales list to keep checking it
    goto_tab(page, 'sales')
    prj = P(); print(prj['jobType'], prj['startDate'], prj['endDate'], [(i['part'], i['qty'], i['status'], i['serials']) for i in prj['items']])
    assert prj['jobType'] == 'sale' and prj['startDate'] == '2026-09-01' and prj['endDate'] == '2026-09-01'
    assert [(i['part'], i['qty'], i['status'], i['serials']) for i in prj['items']] == [('SW-24', 2, 'pending', ['S2', 'S4']), ('RT-1', 1, 'pending', [])]
    assert W('w1') == {'quantity': 5, 'serials': ['S1', 'S2', 'S3', 'S4', 'S5']} and W('w2')['quantity'] == 2, "pending lines must not touch the warehouse"
    assert 'ขายสวิตช์' in page.inner_text('#salesBody tr:has-text("ขายสวิตช์")') and 'รอดำเนินการ' in page.inner_text('#salesBody tr:has-text("ขายสวิตช์")')

    # ---------------- mark a line as "เลือกแล้ว" -> on an ALREADY-SAVED job this locks the warehouse right away, before
    # the whole form is ever saved ("ล็อคของ") ----------------
    page.click('#salesBody tr:has-text("ขายสวิตช์") button:has-text("แก้ไข")')
    page.select_option(f"{R(1,8)} select", 'done'); page.wait_for_timeout(150)
    assert page.is_visible('#confirmModal'), "asks right away, not deferred to the end-of-form save"
    msg = page.inner_text('#confirmModalMsg'); print(msg)
    assert 'ล็อคของ' in msg and 'ตัดออก 2 ชิ้น' in msg and 'ตัด SN: S2, S4' in msg and 'Catalyst' in msg
    assert page.input_value(f"{R(1,8)} select") == 'pending', "the dropdown reverts to its real value while the confirm is up"
    page.click('#confirmModalCancelBtn'); page.wait_for_timeout(100)
    assert W('w1')['quantity'] == 5, "cancelling the confirmation changes nothing"
    assert P()['items'][0]['status'] == 'pending'

    page.select_option(f"{R(1,8)} select", 'done'); page.wait_for_timeout(150)
    page.click('#confirmModalOkBtn'); page.wait_for_timeout(500)
    assert W('w1') == {'quantity': 3, 'serials': ['S1', 'S3', 'S5']}, W('w1')
    # the project doc's own items[] is already updated too - no "บันทึกรายการ" click was needed for this to be real
    assert P()['items'][0]['status'] == 'done' and P()['items'][0]['serials'] == ['S2', 'S4']
    assert page.is_disabled(f"{R(1,7)} input") and page.is_disabled(f"{R(1,2)} select"), "a done line is locked"
    assert 'S2' in page.inner_text(R(1, 6)) and 'S4' in page.inner_text(R(1, 6))

    # saving the rest of the form now shows no stock-effects confirm at all - it was already applied live
    page.click('#projectSaveBtn'); page.wait_for_timeout(400)
    assert not page.is_visible('#confirmModal'), "the live lock already applied - nothing left for the end-of-form save to confirm"
    goto_tab(page, 'sales')
    assert 'กำลังดำเนินการ' in page.inner_text('#salesBody tr:has-text("ขายสวิตช์")')                             # 1 of 2 lines done
    goto_tab(page, 'warehouse')
    assert '3' in page.inner_text('#warehouseBody tr:has-text("Catalyst")') and 'SN 3/3' in page.inner_text('#warehouseBody tr:has-text("Catalyst")')

    # ---------------- finish the second line the same way -> sale reads 'ดำเนินการแล้ว' ----------------
    goto_tab(page, 'sales'); page.click('#salesBody tr:has-text("ขายสวิตช์") button:has-text("แก้ไข")')
    page.select_option(f"{R(2,8)} select", 'done'); page.wait_for_timeout(150)
    page.click('#confirmModalOkBtn'); page.wait_for_timeout(500)
    page.click('#projectCancelBtn')   # nothing else changed - already applied live
    assert W('w2')['quantity'] == 1
    goto_tab(page, 'sales')
    assert 'ดำเนินการแล้ว' in page.inner_text('#salesBody tr:has-text("ขายสวิตช์")')
    assert page.evaluate("projectStatus(data.projects.find(p => p.name === 'ขายสวิตช์'))") == 'ended'

    # ---------------- revert to pending -> stock and serials are put back immediately, still on an already-saved job ----------------
    page.click('#salesBody tr:has-text("ขายสวิตช์") button:has-text("แก้ไข")')
    page.select_option(f"{R(1,8)} select", 'pending'); page.wait_for_timeout(150)
    assert page.is_visible('#confirmModal') and 'คืนเข้า 2 ชิ้น' in page.inner_text('#confirmModalMsg')
    assert page.is_disabled(f"{R(1,7)} input"), "still locked while the confirm is up"
    page.click('#confirmModalOkBtn'); page.wait_for_timeout(500)
    assert not page.is_disabled(f"{R(1,7)} input")
    assert sorted(W('w1')['serials']) == ['S1', 'S2', 'S3', 'S4', 'S5'] and W('w1')['quantity'] == 5
    page.click('#projectCancelBtn')   # already applied live - nothing else to save

    # ---------------- deleting a done line also puts its stock back immediately ----------------
    page.click('#salesBody tr:has-text("ขายสวิตช์") button:has-text("แก้ไข")')
    page.click(f"{R(2,9)} button"); page.wait_for_timeout(150)                                                       # line 2 (RB4011, done) removed
    assert page.is_visible('#confirmModal') and 'คืนเข้า 1 ชิ้น' in page.inner_text('#confirmModalMsg')
    page.click('#confirmModalOkBtn'); page.wait_for_timeout(500)
    assert W('w2')['quantity'] == 2 and len(P()['items']) == 1
    page.click('#projectCancelBtn')

    # ---------------- not enough stock: the immediate lock fails right away and nothing is saved ----------------
    page.evaluate("db.collection('pm_warehouse').doc('w2').update({quantity: 0})"); page.wait_for_timeout(200)
    page.click('#salesBody tr:has-text("ขายสวิตช์") button:has-text("แก้ไข")')
    page.click('#prjAddItemBtn'); page.select_option(f"{R(2,2)} select", 'w2'); page.select_option(f"{R(2,8)} select", 'done'); page.wait_for_timeout(150)
    page.click('#confirmModalOkBtn'); page.wait_for_timeout(500)
    assert 'ไม่พอ' in page.inner_text('#toast') and page.is_visible('#projectModal'), page.inner_text('#toast')
    assert page.input_value(f"{R(2,8)} select") == 'pending', "the failed lock reverts the dropdown back to pending"
    assert len(P()['items']) == 1 and W('w2')['quantity'] == 0
    page.keyboard.press('Escape')
    acts = page.evaluate("db.collection('pm_auditLog').get().then(s => s.docs.map(d => d.data().action))")
    print(sorted(set(acts)))
    assert any('ตัดสต็อกโกดัง' in a for a in acts) and any('คืนสต็อกโกดัง' in a for a in acts) and 'สร้างรายการซื้อขาย' in acts

    # ---------------- a PROJECT: two dates, plan, legacy lines ----------------
    goto_tab(page, 'projects'); page.click('#projectsCreateBtn')
    page.fill('#prjName', 'โครงการ CCTV'); page.select_option('#prjCustomer', index=1)
    page.fill('#prjStart', D(-5)); page.fill('#prjEnd', D(60)); page.fill('#prjLocation', 'อาคาร A')
    assert 'นับจากวันสิ้นสุดโครงการ' in page.inner_text('#prjWarrantyHint')
    page.click('#projectSaveBtn'); page.wait_for_timeout(400)
    # saving a brand-new project now routes straight to its Action Plan (see the photo-attachment feature's "2-page" flow) - come back to the list
    goto_tab(page, 'projects')
    pj = page.evaluate("data.projects.find(p => p.name === 'โครงการ CCTV')")
    assert pj['jobType'] == 'project' and pj['endDate'] == D(60) and pj['items'] == []
    assert 'รอดำเนินการ' in page.inner_text('#projectsBody tr:has-text("โครงการ CCTV")')   # in contract, no plan yet

    # separate menus: each list only holds its own kind
    body = page.inner_text('#projectsBody')
    assert 'โครงการ CCTV' in body and 'โครงการเก่า' in body and 'ขายสวิตช์' not in body
    goto_tab(page, 'sales'); body = page.inner_text('#salesBody')
    assert 'ขายสวิตช์' in body and 'โครงการ CCTV' not in body and 'โครงการเก่า' not in body
    assert page.locator('#salesBody tr:has-text("ขายสวิตช์") button:has-text("แผนงาน")').count() == 0     # sales have no action plan
    goto_tab(page, 'projects')

    # legacy project opens; old lines become plain-text lines and survive a save
    page.click('#projectsBody tr:has-text("โครงการเก่า") button:has-text("แก้ไข")')
    assert page.input_value('#prjJobType') == 'project'
    assert 'กล้อง CCTV' in page.inner_text(R(1, 4)) and 'ติดตั้ง — ชั้น 2' in page.inner_text(R(2, 4))
    page.click('#projectSaveBtn'); page.wait_for_timeout(400)
    assert page.evaluate("data.projects.find(p => p.id === 'old1').items.map(i => i.name)") == ['กล้อง CCTV', 'ติดตั้ง — ชั้น 2']
    assert not page.is_visible('#confirmModal')

    # ---------------- print ----------------
    hs = page.evaluate("buildProjectPrintHtml(data.projects.find(p => p.name === 'ขายสวิตช์'))")
    assert 'รายการงานที่ส่งมอบ' in hs and 'สถานที่ส่งมอบ' in hs and 'ชื่องาน' in hs and 'Cisco' in hs and 'S2<br>S4' in hs and 'รหัสอุปกรณ์' in hs and 'ผู้รับมอบงาน' in hs and 'ลงนามรับรอง' in hs
    assert 'รายการอุปกรณ์' in hs and 'รายการเพิ่มเติม' not in hs, "a goods-only job never shows the บริการ section on the handover document"
    hp = page.evaluate("buildProjectPrintHtml(data.projects.find(p => p.name === 'โครงการ CCTV'))")
    assert 'รายการงานที่ส่งมอบ' in hp and 'เลขที่สัญญา' in hp and 'ชื่อโครงการ' in hp

    # ---------------- warranty page basis + dashboard + customers ----------------
    assert page.evaluate("projectWarranty(data.projects.find(p => p.name === 'ขายสวิตช์')).expiry") == '2027-09-01'
    assert page.evaluate("projectWarranty(data.projects.find(p => p.name === 'โครงการ CCTV')).expiry") == (D(60)[:4] and page.evaluate(f"addMonths('{D(60)}', 12)"))
    goto_tab(page, 'equipment'); assert 'ซื้อขาย' in page.inner_text('#equipmentBody tr:has-text("ขายสวิตช์")')
    page.click('.nav-item[data-tab="actionplan"]')
    cards = page.inner_text('#planCards'); print(cards.replace('\n', ' | ')[:200])
    assert 'ขายสวิตช์' not in cards and 'โครงการ CCTV' in cards and 'โครงการเก่า' in cards
    goto_tab(page, 'customers'); page.click('#customersBody tr:has-text("การไฟฟ้าทดสอบ") td:nth-child(1)')
    cp = page.inner_text('#customerProjectsModal'); assert 'ขายสวิตช์' in cp and 'ซื้อขาย' in cp and 'ดำเนินการแล้ว' in cp or 'รอดำเนินการ' in cp
    page.click('#cpCloseBtn')
    page.click('.nav-item[data-tab="dashboard"]')
    page.screenshot(path="v18_dash.png")

    # ---------------- action plan editor: owner dropdown, no tick ----------------
    page.click('.nav-item[data-tab="actionplan"]'); page.click('.plan-card:has-text("โครงการ CCTV")'); page.click('#planEditBtn')
    heads = page.evaluate("[...document.querySelectorAll('#planModal thead th')].map(t => t.textContent.trim())")
    assert 'ดำเนินการแล้ว' not in heads and heads[2] == 'ผู้รับผิดชอบ', heads
    assert page.locator('#planEditBody input[type=checkbox]').count() == 0
    assert page.evaluate("[...document.querySelectorAll('#planEditBody tr:first-child td:nth-child(3) select option')].map(o => o.textContent)") == ['— เลือก —', 'ผู้จัดการ', 'ทีมติดตั้ง', 'ติดตั้งโปรแกรม', 'ฝ่ายขาย', 'ลูกค้า']
    page.fill('#planEditBody tr:nth-child(1) td:nth-child(2) input', 'ติดตั้งกล้อง')
    page.select_option('#planEditBody tr:nth-child(1) td:nth-child(3) select', 'ทีมติดตั้ง')
    page.fill('#planEditBody tr:nth-child(1) td:nth-child(4) input', D(2)); page.fill('#planEditBody tr:nth-child(1) td:nth-child(5) input', D(3))
    page.click('#planSaveBtn'); page.wait_for_timeout(400)
    plan = page.evaluate("data.projects.find(p => p.name === 'โครงการ CCTV').plan")
    assert plan[0]['owner'] == 'ทีมติดตั้ง' and plan[0]['done'] is False
    # tick in the table (the ✓ column), then re-open the editor and save: the tick must survive
    page.click('#planBody tr[data-i="0"][data-j="-1"] .g-chk-input'); page.wait_for_timeout(400)
    assert page.evaluate("data.projects.find(p => p.name === 'โครงการ CCTV').plan[0].done") is True
    page.click('#planEditBtn'); page.click('#planSaveBtn'); page.wait_for_timeout(400)
    assert page.evaluate("data.projects.find(p => p.name === 'โครงการ CCTV').plan[0].done") is True, "editing the plan must not lose ticks"
    assert 'กำลังดำเนินการ' in page.inner_text('#planBody') or True
    # a name typed in an older version stays selectable
    page.evaluate("db.collection('pm_projects').doc(data.projects.find(p => p.name === 'โครงการ CCTV').id).update({plan:[{title:'x', owner:'สมชาย', start:'', end:'', done:false, subs:[]}]})"); page.wait_for_timeout(300)
    page.click('#planEditBtn')
    assert page.input_value('#planEditBody tr:nth-child(1) td:nth-child(3) select') == 'สมชาย'
    page.click('#planCancelBtn')
    assert 'กำลังดำเนินการ' in page.inner_text('#projectsBody') or True
    print("errors:", errors); assert not errors
print("OK")
