import os, sys, tempfile
import sys, os, http.server, threading, functools
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from harness import new_page, REPO_ROOT

class Q(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a): pass
h = functools.partial(Q, directory=REPO_ROOT)
srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), h)
threading.Thread(target=srv.serve_forever, daemon=True).start()
base = f"http://127.0.0.1:{srv.server_address[1]}"

with new_page(viewport={"width": 1500, "height": 1000}) as (page, errors):
    page.goto(f"{base}/index.html"); page.wait_for_timeout(500)
    page.evaluate("() => localStorage.setItem('pm-sale-login-ts', String(Date.now()))")
    page.evaluate("() => window.__authListeners[0]({uid:'admin1', email:'admin@a.com', displayName:'Admin One'})")
    page.wait_for_timeout(800)
    # 14 deleted customers, 3 deleted companies, 2 deleted warehouse items, 1 deleted catalog with 2 stored pieces
    page.evaluate("""async () => {
      const del = { deletedAt:'2026-09-01T00:00:00Z', deletedBy:'admin1' };
      for (let i = 1; i <= 14; i++) await db.collection('pm_customers').doc('c' + i).set({ name:'ลูกค้า ' + i, type:'private', createdBy:'admin1', ...del });
      for (let i = 1; i <= 3; i++) await db.collection('pm_companies').doc('co' + i).set({ name:'บริษัท ' + i, ...del });
      for (let i = 1; i <= 2; i++) await db.collection('pm_warehouse').doc('w' + i).set({ name:'อุปกรณ์ ' + i, part:'P' + i, ...del });
      await db.collection('pm_catalogs').doc('cat1').set({ title:'แคตตาล็อก', name:'แคตตาล็อก', chunks:2, ...del });
      await db.collection('pm_catalogChunks').doc('cat1_0').set({ catalogId:'cat1', n:0, data:'x' });
      await db.collection('pm_catalogChunks').doc('cat1_1').set({ catalogId:'cat1', n:1, data:'y' });
    }""")
    page.click('.nav-item[data-tab="trash"]'); page.wait_for_timeout(800)
    cb = lambda: page.locator('#trashBody .trash-cb').count()
    checked = lambda: page.locator('#trashBody .trash-cb:checked').count()
    assert page.inner_text('#trashCount') == '20' and cb() == 10
    # checkbox column sits in front of "ประเภท"
    heads = page.evaluate("[...document.querySelectorAll('#tab-trash thead th')].map(t => t.textContent.trim())")
    assert heads[0] == '' and heads[1] == 'ประเภท', heads
    assert not page.is_visible('#trashBulkBar')

    # some rows
    page.locator('#trashBody .trash-cb').nth(0).check(); page.locator('#trashBody .trash-cb').nth(1).check()
    assert page.is_visible('#trashBulkBar') and page.inner_text('#trashSelCount') == '2'
    assert page.evaluate("document.getElementById('trashSelAll').indeterminate") is True
    # rows are not re-rendered by ticking (no fade-in replay): the same DOM node survives
    page.evaluate("window.__row0 = document.querySelector('#trashBody tr')"); page.locator('#trashBody .trash-cb').nth(2).check()
    assert page.evaluate("window.__row0 === document.querySelector('#trashBody tr')")
    page.click('#trashBulkClearBtn'); assert checked() == 0 and not page.is_visible('#trashBulkBar')

    # all: header box selects every row across pages, not just the visible 10
    page.check('#trashSelAll'); assert page.inner_text('#trashSelCount') == '20' and checked() == 10
    page.click('#trashPager .page-btn:has-text("2")'); assert checked() == 10, "page 2 rows are ticked too"
    page.click('#trashPager .page-btn:has-text("1")')
    # un-ticking one row on page 1 -> 19 selected, header is indeterminate again
    page.locator('#trashBody .trash-cb').nth(0).uncheck(); assert page.inner_text('#trashSelCount') == '19'
    assert page.evaluate("document.getElementById('trashSelAll').indeterminate") is True
    page.uncheck('#trashSelAll') if page.evaluate("document.getElementById('trashSelAll').checked") else None
    page.click('#trashBulkClearBtn')

    # the type filter limits "all" to that type, and hidden selections are forgotten
    page.select_option('#trashTypeFilter', 'companies'); page.wait_for_timeout(200)
    assert cb() == 3
    page.check('#trashSelAll'); assert page.inner_text('#trashSelCount') == '3'
    page.select_option('#trashTypeFilter', 'customers'); page.wait_for_timeout(200)
    assert page.inner_text('#trashSelCount') in ('0',) and not page.is_visible('#trashBulkBar'), "companies selection must not follow into the customers view"

    # bulk restore (some rows): 2 companies come back and vanish from the trash
    page.select_option('#trashTypeFilter', 'companies'); page.wait_for_timeout(200)
    page.locator('#trashBody .trash-cb').nth(0).check(); page.locator('#trashBody .trash-cb').nth(1).check()
    page.click('#trashBulkRestoreBtn'); page.wait_for_timeout(600)
    assert cb() == 1 and page.inner_text('#trashCount') == '1' and not page.is_visible('#trashBulkBar')
    left = page.evaluate("[...window.__mockStore['pm_companies'].values()].filter(d => d.deletedAt).length")
    assert left == 1, left
    assert page.evaluate("data.companies.length") == 2, "restored companies are live again"

    # bulk permanent delete (all of a type) goes through the confirm dialog; a catalog takes its stored pieces with it
    page.select_option('#trashTypeFilter', 'all'); page.wait_for_timeout(200)
    page.check('#trashSelAll'); assert page.inner_text('#trashSelCount') == '18'
    page.click('#trashBulkPurgeBtn'); assert page.is_visible('#confirmModal')
    msg = page.inner_text('#confirmModalMsg') if page.locator('#confirmModalMsg').count() else page.inner_text('#confirmModal')
    assert '18' in msg and 'ลูกค้า 14' in msg, msg
    page.click('#confirmModalOkBtn'); page.wait_for_timeout(800)
    assert page.inner_text('#trashCount') == '0' and 'ถังขยะว่างเปล่า' in page.inner_text('#trashBody')
    assert page.evaluate("window.__mockStore['pm_customers'].size") == 0
    assert page.evaluate("(window.__mockStore['pm_catalogChunks'] || new Map()).size") == 0, "catalog pieces removed with the catalog"
    audits = page.evaluate("[...window.__mockStore['pm_auditLog'].values()].map(a => a.action)")
    assert 'กู้คืนหลายรายการ' in audits and 'ลบถาวรหลายรายการ' in audits, audits
    print("errors:", errors); assert not errors
print("OK")
