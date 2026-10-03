"""Locks in the "blob subcollection" / "history subcollection" performance fix (see CLAUDE.md's "Project attachments:
blob subcollection" and "Warehouse: withdrawal history subcollection" sections): a NEW pm_files attachment's bytes and a
NEW pm_warehouse withdrawal/return entry are no longer stored inline on the document the shared listeners load, so
opening a project's read-only VIEW (or just having the warehouse list open) never has to carry those heavy fields along
for the ride - they're fetched separately, one record at a time, only when actually needed (download / the serial-
history modal). Also checks the backward-compatible read path for OLD-shaped rows saved before this change existed."""
import os, sys, base64
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from harness import new_page, REPO_ROOT, goto_tab
import http.server, threading, functools

class Q(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a): pass
h = functools.partial(Q, directory=REPO_ROOT)
srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), h); threading.Thread(target=srv.serve_forever, daemon=True).start()
base = f"http://127.0.0.1:{srv.server_address[1]}"

PDF_B64 = base64.b64encode(b"%PDF-1.4 new-style attachment").decode()
LEGACY_B64 = base64.b64encode(b"%PDF-1.4 legacy inline attachment").decode()

with new_page(viewport={"width": 1440, "height": 900}) as (page, errors):
    page.goto(f"{base}/index.html"); page.wait_for_timeout(500)
    page.evaluate("() => localStorage.setItem('pm-sale-login-ts', String(Date.now()))")
    page.evaluate("() => window.__authListeners[0]({uid:'admin1', email:'admin@a.com', displayName:'Admin One'})"); page.wait_for_timeout(900)

    # ---- seed: a project (for the pm_files half) and two warehouse items (for the pm_warehouse half) ----
    page.evaluate("""async ([pdfB64, legacyB64]) => {
      await db.collection('pm_customers').doc('c1').set({name:'ลูกค้า ก', type:'private', createdBy:'admin1'});
      await db.collection('pm_projects').doc('p1').set({jobType:'project', docNo:'PJ1', name:'โครงการทดสอบ', customerId:'c1', customerName:'ลูกค้า ก',
        startDate:'2026-09-01', endDate:'2026-12-01', items:[], plan:[], createdBy:'admin1'});
      // a NEW-style attachment: written through the app's own createFileRecord() helper, exactly like a real upload would
      await createFileRecord({ projectId:'p1', ownerId:'admin1', name:'new.pdf', size:30, type:'application/pdf', createdBy:'admin1', createdAt:'2026-09-02T00:00:00Z' }, pdfB64);
      // an OLD-style attachment: bytes written inline on the metadata doc directly, exactly like a row saved before this change
      await db.collection('pm_files').add({ projectId:'p1', ownerId:'admin1', name:'legacy.pdf', size:31, type:'application/pdf', data: legacyB64, createdBy:'admin1', createdAt:'2026-09-01T00:00:00Z' });

      // w1: a brand-new item (no inline `history` field at all) with two withdrawal/return entries in its history SUBcollection
      await db.collection('pm_warehouse').doc('w1').set({ part:'P1', brand:'B', type:'Switch', name:'ของใหม่', quantity:3, serials:['S1','S2','S3'], createdBy:'admin1' });
      await db.collection('pm_warehouse').doc('w1').collection('history').add({ at:'2026-09-01T00:00:00Z', projectId:'p1', docNo:'PJ1', projectName:'โครงการทดสอบ', jobType:'project', by:'admin1', byName:'Admin One', type:'out', qty:2, serials:['S1','S2'] });

      // w2: an OLD item saved with the pre-existing inline `history[]` shape, PLUS one new entry in the subcollection
      // (simulating an item that existed before this change and was touched again after it) - both must show up merged.
      await db.collection('pm_warehouse').doc('w2').set({ part:'P2', brand:'B', type:'Switch', name:'ของเก่า', quantity:5, serials:['X1','X2','X3','X4','X5'],
        history:[{ at:'2026-01-01T00:00:00Z', projectId:'p0', docNo:'PJ0', projectName:'งานเก่า', jobType:'project', by:'admin1', byName:'Admin One', type:'out', qty:1, serials:['X1'] }], createdBy:'admin1' });
      await db.collection('pm_warehouse').doc('w2').collection('history').add({ at:'2026-09-03T00:00:00Z', projectId:'p1', docNo:'PJ1', projectName:'โครงการทดสอบ', jobType:'project', by:'admin1', byName:'Admin One', type:'out', qty:1, serials:['X2'] });
    }""", [PDF_B64, LEGACY_B64])
    page.wait_for_timeout(700)

    # ============================================================================================
    # pm_files: a project VIEW never holds a NEW attachment's bytes in memory, only its metadata
    # ============================================================================================
    goto_tab(page, 'projects')
    page.click('tr.job-row:has-text("โครงการทดสอบ")'); page.wait_for_timeout(500)   # row click -> read-only VIEW mode
    assert page.is_visible('#projectModal') and page.evaluate("document.getElementById('prjFormFieldset').disabled") is True
    files = page.evaluate("projectFiles")
    newRow = next(f for f in files if f['name'] == 'new.pdf')
    legacyRow = next(f for f in files if f['name'] == 'legacy.pdf')
    assert 'data' not in newRow, "a NEW-style attachment's metadata must never carry its own bytes in memory"
    assert legacyRow.get('data'), "an OLD-style row still carries its bytes inline - unavoidable without a migration, and fine to read"

    # the view's own "ดาวน์โหลด"/"ลบ" buttons live inside #prjFormFieldset, disabled along with the rest of the read-only
    # view - "แก้ไข" flips the SAME modal into the editable form in place (see "click-a-row to view, edit-in-place" in
    # CLAUDE.md) without re-fetching projectFiles, so the metadata loaded above is exactly what a real download reads from.
    page.click('#prjViewEditBtn'); page.wait_for_timeout(100)
    assert page.evaluate("document.getElementById('prjFormFieldset').disabled") is False

    # downloading still works for BOTH shapes: the new one fetches its blob subcollection doc on demand, the old one just uses what's already there
    with page.expect_download(timeout=10000) as dl:
        page.click('#prjFilesList tr:has-text("new.pdf") button:has-text("ดาวน์โหลด")')
    assert dl.value.suggested_filename == 'new.pdf'
    dl.value.save_as('/tmp/new_back.pdf' if os.name != 'nt' else os.path.join(os.environ.get('TEMP', '.'), 'new_back.pdf'))
    with page.expect_download(timeout=10000) as dl2:
        page.click('#prjFilesList tr:has-text("legacy.pdf") button:has-text("ดาวน์โหลด")')
    assert dl2.value.suggested_filename == 'legacy.pdf'

    # the new attachment's row in the raw store has no `data` key; its bytes sit in the sibling blob/content doc instead
    rec = page.evaluate("""() => { for (const [id, r] of window.__mockStore['pm_files'].entries()) if (r.name === 'new.pdf') return [id, r]; }""")
    nid, nrec = rec
    assert 'data' not in nrec
    blob = page.evaluate(f"window.__mockStore['pm_files/{nid}/blob'].get('content')")
    assert base64.b64decode(blob['data']) == b"%PDF-1.4 new-style attachment"
    page.click('#projectCancelBtn')

    # ============================================================================================
    # pm_warehouse: the shared listener's own in-memory cache never carries a NEW item's withdrawal/return log at all
    # ============================================================================================
    goto_tab(page, 'warehouse')
    w1 = page.evaluate("data.warehouse.find(w => w.id === 'w1')")
    assert not w1.get('history'), "a brand-new item's withdrawal/return entries must never ride along on the shared pm_warehouse listener"
    w2 = page.evaluate("data.warehouse.find(w => w.id === 'w2')")
    assert len(w2.get('history') or []) == 1, "an item's OWN pre-existing inline history[] (legacy, frozen) is untouched and still readable"

    # opening the serial/history modal fetches the subcollection on demand and merges it with whatever legacy inline history exists
    page.click('#warehouseBody tr:has-text("ของใหม่") td:nth-child(4)'); page.wait_for_timeout(300)
    hist1 = page.inner_text('#serialHistoryBody')
    assert 'เบิกออก' in hist1 and 'PJ1' in hist1 and page.locator('#serialHistoryBody tr').count() == 1
    page.click('#serialCloseBtn')

    page.click('#warehouseBody tr:has-text("ของเก่า") td:nth-child(4)'); page.wait_for_timeout(300)
    hist2 = page.inner_text('#serialHistoryBody')
    assert 'PJ0' in hist2 and 'PJ1' in hist2 and page.locator('#serialHistoryBody tr').count() == 2, "legacy inline entry + new subcollection entry both show, merged"
    page.click('#serialCloseBtn')

    print("errors:", errors); assert not errors
print("OK")
