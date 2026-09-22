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
    goto_tab(page, 'warehouse'); page.wait_for_timeout(300)

    assert page.is_visible('#warehouseAddSampleBtn'), "admin sees the sample-data button"
    page.click('#warehouseAddSampleBtn'); page.wait_for_timeout(200)
    page.click('#confirmModalOkBtn'); page.wait_for_timeout(600)

    added = page.evaluate("data.warehouse.filter(w => w.sample)")
    assert len(added) == 5, added
    cctv = [w for w in added if w['type'] == 'CCTV']
    switches = [w for w in added if w['type'] == 'Switch']
    assert len(cctv) == 3 and len(switches) == 2, (len(cctv), len(switches))
    # every field is filled in on all 5, and each carries its own set of serials matching its quantity
    for w in added:
        assert all(w.get(k) for k in ('part', 'brand', 'type', 'name', 'note')), w
        assert w['quantity'] > 0 and len(w['serials']) == w['quantity'] and len(set(w['serials'])) == w['quantity'], w
        assert w['name'].startswith('[ตัวอย่าง]')
    assert len({w['part'] for w in added}) == 5, "all 5 parts are distinct"

    # clicking again does not duplicate the set
    page.click('#warehouseAddSampleBtn'); page.wait_for_timeout(200)
    assert 'มีข้อมูลตัวอย่างชุดนี้อยู่แล้ว' in page.inner_text('#toast')
    assert len(page.evaluate("data.warehouse.filter(w => w.sample)")) == 5

    # deletable individually via the normal warehouse "ลบ" -> Trash flow
    row = page.locator(f'#warehouseBody tr:has-text("{cctv[0]["name"]}")')
    row.locator('.icon-btn:has-text("ลบ")').click(); page.wait_for_timeout(200)
    page.click('#confirmModalOkBtn'); page.wait_for_timeout(400)
    assert page.locator(f'#warehouseBody tr:has-text("{cctv[0]["name"]}")').count() == 0
    goto_tab(page, 'trash'); page.wait_for_timeout(500)
    assert cctv[0]['name'] in page.inner_text('#trashBody'), "the deleted sample item shows up in the Trash like any other deleted warehouse row"

    # and the rest are covered by the existing bulk "ลบข้อมูลตัวอย่างทั้งหมด" cleanup
    page.click('#deleteSampleDataBtn'); page.wait_for_timeout(200)
    page.click('#confirmModalOkBtn'); page.wait_for_timeout(600)
    assert page.evaluate("data.warehouse.filter(w => w.sample).length") == 0

    # a non-admin never sees the button
    page.evaluate("currentUserRole = 'user'; renderWarehouse()"); page.wait_for_timeout(200)
    assert not page.is_visible('#warehouseAddSampleBtn')

    print("errors:", errors); assert not errors
print("OK")
