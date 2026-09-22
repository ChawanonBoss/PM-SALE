import os, sys, http.server, threading, functools
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from harness import new_page, REPO_ROOT, goto_tab
class Q(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a): pass
h = functools.partial(Q, directory=REPO_ROOT)
srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), h); threading.Thread(target=srv.serve_forever, daemon=True).start()
base = f"http://127.0.0.1:{srv.server_address[1]}"

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
    page.evaluate("() => window.__authListeners[0]({uid:'admin1', email:'admin@a.com', displayName:'Admin One'})"); page.wait_for_timeout(900)
    page.evaluate(TX_SHIM)
    page.evaluate("""async () => {
      await db.collection('pm_customers').doc('c1').set({name:'ลูกค้า ก', type:'gov', createdBy:'admin1'});
      await db.collection('pm_warehouse').doc('w1').set({part:'SW-1', brand:'Cisco', type:'Switch', name:'Catalyst 9200', quantity:5, serials:['S1','S2'], createdBy:'admin1'}); }""")
    page.wait_for_timeout(500)

    # ---- โกดังบริการ page: same shape as โกดังสินค้า but no quantity/Serial columns at all ----
    goto_tab(page, 'serviceWarehouse'); page.wait_for_timeout(300)
    assert page.inner_text('#pageTitle') == 'โกดังบริการ'
    heads = page.evaluate("[...document.querySelectorAll('#tab-serviceWarehouse thead th')].map(t => t.textContent.trim())")
    assert heads == ['Part', 'ซัพพลายเออร์', 'ประเภทงาน', 'ชื่อบริการ', 'หมายเหตุ', ''], heads
    assert 'จำนวน' not in page.inner_text('#tab-serviceWarehouse thead') and 'Serial' not in page.inner_text('#tab-serviceWarehouse thead')
    assert 'ยังไม่มีบริการ' in page.inner_text('#serviceWarehouseBody')

    # ---- create one: Part/ServiceName required, Supplier/JobType are addable-selects (same "+" pattern as โกดังสินค้า) ----
    page.click('#serviceWarehouseCreateBtn'); page.wait_for_timeout(200)
    assert page.inner_text('#serviceWarehouseModalTitle') == 'เพิ่มบริการ'
    modal_html = page.inner_html('#serviceWarehouseModal')
    assert 'จำนวน' not in modal_html and 'Serial' not in modal_html, "a service has no stock/serial fields to fill in"
    page.click('#serviceWarehouseSaveBtn')   # Part is required and empty - browser-native validation blocks the submit
    assert page.is_visible('#serviceWarehouseModal')
    page.fill('#svcPart', 'SVC-1')
    page.click('#svcBrandAddBtn'); page.fill('#svcBrandNew', 'บริษัท ติดตั้ง จำกัด'); page.click('#svcBrandNewOk')
    page.click('#svcTypeAddBtn'); page.fill('#svcTypeNew', 'ติดตั้งระบบ'); page.click('#svcTypeNewOk')
    page.fill('#svcName', 'ติดตั้งกล้องวงจรปิด')
    page.fill('#svcNote', 'ทดสอบ')
    page.click('#serviceWarehouseSaveBtn'); page.wait_for_timeout(400)
    assert not page.is_visible('#serviceWarehouseModal')
    row_text = page.inner_text('#serviceWarehouseBody')
    assert all(v in row_text for v in ('SVC-1', 'บริษัท ติดตั้ง จำกัด', 'ติดตั้งระบบ', 'ติดตั้งกล้องวงจรปิด'))

    # ---- edit it: fields come back pre-filled, addable-selects keep the value already in use ----
    page.click('#serviceWarehouseBody .icon-btn:has-text("แก้ไข")'); page.wait_for_timeout(200)
    assert page.inner_text('#serviceWarehouseModalTitle') == 'แก้ไขบริการ'
    assert page.input_value('#svcPart') == 'SVC-1' and page.input_value('#svcBrand') == 'บริษัท ติดตั้ง จำกัด' and page.input_value('#svcType') == 'ติดตั้งระบบ'
    page.fill('#svcNote', 'แก้ไขแล้ว')
    page.click('#serviceWarehouseSaveBtn'); page.wait_for_timeout(400)
    assert 'แก้ไขแล้ว' in page.inner_text('#serviceWarehouseBody')

    # ---- delete -> Trash (soft delete, same generic path as everything else in ENTITY_LABEL) ----
    page.click('#serviceWarehouseBody .icon-btn:has-text("ลบ")'); page.wait_for_timeout(200)
    page.click('#confirmModalOkBtn'); page.wait_for_timeout(400)
    assert 'ยังไม่มีบริการ' in page.inner_text('#serviceWarehouseBody')
    goto_tab(page, 'trash'); page.wait_for_timeout(500)
    assert 'บริการในโกดังบริการ' in page.inner_text('#trashBody') and 'ติดตั้งกล้องวงจรปิด' in page.inner_text('#trashBody')
    page.click('#trashBody .icon-btn:has-text("กู้คืน")'); page.wait_for_timeout(400)
    goto_tab(page, 'serviceWarehouse'); page.wait_for_timeout(300)
    assert 'ติดตั้งกล้องวงจรปิด' in page.inner_text('#serviceWarehouseBody'), "restored from trash"

    # ---- ซื้อขาย/โครงการ form: สินค้า and บริการ are two separate tables/buttons, sharing one flat items[] on save ----
    goto_tab(page, 'sales'); page.wait_for_timeout(200)
    page.click('#salesCreateBtn'); page.wait_for_timeout(200)
    assert page.inner_text('#prjAddItemBtn') == '+ เพิ่มสินค้า' and page.inner_text('#prjAddServiceBtn') == '+ เพิ่มบริการ'
    assert page.locator('#prjItemsBody tr').count() == 1, "a new job still starts with one blank goods row, same as before"
    assert 'ยังไม่มีรายการบริการ' in page.inner_text('#prjServicesBody')

    page.click('#prjAddServiceBtn'); page.wait_for_timeout(200)
    svc_opts = page.evaluate("[...document.querySelectorAll('#prjServicesBody tr:first-child td:nth-child(2) option')].map(o => o.textContent)")
    assert any('SVC-1' in o and 'ติดตั้งกล้องวงจรปิด' in o for o in svc_opts), svc_opts
    page.select_option('#prjServicesBody tr:first-child td:nth-child(2) select', label=next(o for o in svc_opts if 'SVC-1' in o))
    assert [page.inner_text(f'#prjServicesBody tr:first-child td:nth-child({c})').strip() for c in (3, 4, 5)] == ['บริษัท ติดตั้ง จำกัด', 'ติดตั้งกล้องวงจรปิด', 'ติดตั้งระบบ']
    page.fill('#prjServicesBody tr:first-child td:nth-child(6) input', '2')

    # fill the (still-blank, unlinked) goods row's part manually and the rest of the required fields, then save
    page.fill('#prjName', 'ขายพร้อมบริการติดตั้ง')
    page.select_option('#prjCustomer', 'c1')
    page.fill('#prjStart', '2026-09-10')
    page.click('#projectSaveBtn'); page.wait_for_timeout(600)
    assert not page.is_visible('#confirmModal'), "a service line must never trigger the warehouse stock-effects confirm dialog"
    saved = page.evaluate("data.projects.find(p => p.name === 'ขายพร้อมบริการติดตั้ง')")
    assert saved and len(saved['items']) == 1 and saved['items'][0]['kind'] == 'service' and saved['items'][0]['qty'] == 2
    assert saved['items'][0]['brand'] == 'บริษัท ติดตั้ง จำกัด' and saved['items'][0]['name'] == 'ติดตั้งกล้องวงจรปิด'

    # reopen it: the only saved line was the service - it round-trips back into #prjServicesBody, #prjItemsBody shows its empty state
    page.evaluate(f"openProjectForm('{saved['id']}')"); page.wait_for_timeout(300)
    assert 'ยังไม่มีรายการสินค้า' in page.inner_text('#prjItemsBody'), "the unlinked blank goods row was never saved, so none comes back"
    assert page.locator('#prjServicesBody tr').count() == 1
    assert 'ติดตั้งกล้องวงจรปิด' in page.inner_text('#prjServicesBody')
    page.click('#projectCancelBtn')

    # ---- a job mixing a DONE goods line with a service line still only deducts stock for the goods line ----
    # (saving a NEW sale above routed on to its photo page - CLAUDE.md's documented post-save flow - so back to the sales list first)
    goto_tab(page, 'sales'); page.wait_for_timeout(200)
    page.click('#salesCreateBtn'); page.wait_for_timeout(200)
    page.select_option('#prjItemsBody tr:first-child td:nth-child(2) select', 'w1')
    page.select_option('#prjItemsBody tr:first-child td:nth-child(8) select', 'done')
    page.click('#prjAddServiceBtn')
    page.select_option('#prjServicesBody tr:first-child td:nth-child(2) select', label=next(o for o in svc_opts if 'SVC-1' in o))
    page.select_option('#prjServicesBody tr:first-child td:nth-child(7) select', 'done')
    page.fill('#prjName', 'ขายผสมสินค้าและบริการ')
    page.select_option('#prjCustomer', 'c1')
    page.fill('#prjStart', '2026-09-11')
    page.click('#projectSaveBtn'); page.wait_for_timeout(300)
    assert page.is_visible('#confirmModal') and 'Cisco' in page.inner_text('#confirmModal'), "the goods line alone must still ask to confirm the stock change"
    assert 'ติดตั้งกล้องวงจรปิด' not in page.inner_text('#confirmModal'), "a service line is never part of the warehouse stock-effects prompt"
    page.click('#confirmModalOkBtn'); page.wait_for_timeout(500)
    w1_after = page.evaluate("data.warehouse.find(w => w.id === 'w1')")
    assert w1_after['quantity'] == 4, "only the goods line's quantity (1) came out of the warehouse; the service line never touches it"

    print("errors:", errors); assert not errors
print("OK")
