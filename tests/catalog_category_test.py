import os, sys, http.server, threading, functools
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from harness import new_page, REPO_ROOT, goto_tab
class Q(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a): pass
h = functools.partial(Q, directory=REPO_ROOT)
srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), h); threading.Thread(target=srv.serve_forever, daemon=True).start()
base = f"http://127.0.0.1:{srv.server_address[1]}"

with new_page(viewport={"width": 1400, "height": 900}) as (page, errors):
    page.goto(f"{base}/index.html"); page.wait_for_timeout(500)
    page.evaluate("() => localStorage.setItem('pm-sale-login-ts', String(Date.now()))")
    page.evaluate("() => window.__authListeners[0]({uid:'admin1', email:'admin@a.com', displayName:'Admin One'})"); page.wait_for_timeout(900)
    page.evaluate("""async () => {
      await db.collection('pm_catalogs').doc('cat1').set({title:'Catalog ทดสอบ', name:'Catalog ทดสอบ', brand:'ยี่ห้อ ก', category:'หมวดเดิม', thumb:'', chunks:0, createdBy:'admin1'});
      await db.collection('pm_warehouse').doc('w1').set({part:'W1', brand:'B1', type:'ประเภทจากโกดัง', name:'ของ', quantity:1, serials:[], createdBy:'admin1'}); }""")
    page.wait_for_timeout(500)

    # ---- หมวดสินค้า is now an addable-select (same "+" pattern as โกดังสินค้า's ยี่ห้อ/ประเภท), not a plain text box ----
    goto_tab(page, 'catalog'); page.wait_for_timeout(300)
    page.click('.postcard .icon-btn:has-text("แก้ไข")'); page.wait_for_timeout(200)
    assert page.evaluate("document.getElementById('catCategory').tagName") == 'SELECT'
    assert page.input_value('#catCategory') == 'หมวดเดิม', "existing value comes back pre-selected"
    opts = page.evaluate("[...document.querySelectorAll('#catCategory option')].map(o => o.value)")
    assert 'หมวดเดิม' in opts and 'ประเภทจากโกดัง' in opts, "options are seeded from both existing catalogs and warehouse types, like before"

    # add a brand-new one via "+" and save
    page.click('#catCategoryAddBtn'); page.wait_for_timeout(100)
    page.fill('#catCategoryNew', 'หมวดใหม่ที่เพิ่มเอง')
    page.click('#catCategoryNewOk'); page.wait_for_timeout(100)
    assert page.input_value('#catCategory') == 'หมวดใหม่ที่เพิ่มเอง'
    page.click('#catalogSaveBtn'); page.wait_for_timeout(400)
    assert not page.is_visible('#catalogModal')
    saved = page.evaluate("data.catalogs.find(c => c.id === 'cat1')")
    assert saved['category'] == 'หมวดใหม่ที่เพิ่มเอง', saved

    # reopening now offers the newly-added category among the options too
    page.click('.postcard .icon-btn:has-text("แก้ไข")'); page.wait_for_timeout(200)
    opts2 = page.evaluate("[...document.querySelectorAll('#catCategory option')].map(o => o.value)")
    assert 'หมวดใหม่ที่เพิ่มเอง' in opts2 and page.input_value('#catCategory') == 'หมวดใหม่ที่เพิ่มเอง'
    page.click('#catalogCancelBtn')

    print("errors:", errors); assert not errors
print("OK")
