import os, sys, tempfile
import sys, os, http.server, threading, functools, base64, zipfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from harness import new_page, REPO_ROOT
class Q(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a): pass
h = functools.partial(Q, directory=REPO_ROOT)
srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), h); threading.Thread(target=srv.serve_forever, daemon=True).start()
base = f"http://127.0.0.1:{srv.server_address[1]}"
OUT = os.path.join(tempfile.gettempdir(), "pdf_check")
TX = """() => { db.runTransaction = async fn => { const writes = []; const tx = { get: ref => ref.get(), update: (ref, d) => writes.push(() => ref.update(d)), set: (ref, d) => writes.push(() => ref.set(d)) }; const r = await fn(tx); for (const w of writes) await w(); return r; }; }"""

with new_page(viewport={"width": 1440, "height": 900}) as (page, errors):
    page.goto(f"{base}/index.html"); page.wait_for_timeout(500)
    page.evaluate("() => localStorage.setItem('pm-sale-login-ts', String(Date.now()))")
    page.evaluate("() => window.__authListeners[0]({uid:'admin1', email:'admin@a.com', displayName:'Admin One'})"); page.wait_for_timeout(900)
    page.evaluate(TX)
    page.evaluate("""async () => {
      await db.collection('pm_customers').doc('c1').set({name:'ลูกค้า ก', type:'private', taxId:'0105', address:'ที่อยู่', contactName:'คุณก', contactPhone:'081', createdBy:'admin1'});
      await db.collection('pm_companies').doc('co1').set({name:'บริษัทเรา'});
      await db.collection('pm_warehouse').doc('w1').set({part:'P1', brand:'B', type:'Switch', name:'ของ', quantity:5, serials:['S1','S2'], createdBy:'admin1'});
      await db.collection('pm_projects').doc('p1').set({jobType:'project', docNo:'PJ1', name:'โครงการหนึ่ง', customerId:'c1', customerName:'ลูกค้า ก', companyId:'co1', contractNo:'C-1', poNo:'PO-77', startDate:'2026-09-01', endDate:'2026-12-01', items:[], plan:[], createdBy:'admin1'});
      await db.collection('pm_projects').doc('p2').set({jobType:'sale', docNo:'SO1', name:'ขายหนึ่ง', customerId:'c1', customerName:'ลูกค้า ก', startDate:'2026-09-02', endDate:'2026-09-02', items:[], createdBy:'admin1'}); }""")
    page.wait_for_timeout(500)

    # ---- PO number: form, list, search, PDF ----
    page.evaluate("showTab('projects')"); page.wait_for_timeout(300)
    assert 'PO PO-77' in page.inner_text('#projectsBody')
    page.fill('#projectsSearch', 'PO-77'); page.wait_for_timeout(200); assert page.locator('#projectsBody tr').count() == 1; page.click('#projectsClearBtn')
    page.evaluate("openProjectForm('p1')"); page.wait_for_timeout(300)
    assert page.input_value('#prjPo') == 'PO-77'
    page.fill('#prjPo', 'PO-99'); page.fill('#prjInstallment', 'งวดที่ 2'); page.click('#projectSaveBtn'); page.wait_for_timeout(700)
    assert page.evaluate("data.projects.find(p => p.id === 'p1').poNo") == 'PO-99'
    html = page.evaluate("buildProjectPrintHtml(data.projects.find(p => p.id === 'p1'))")
    assert 'PO PO-99' in html and 'งวดที่ 2' in html and 'งวดงานที่' in html
    assert 'PO ' not in page.evaluate("buildProjectPrintHtml(data.projects.find(p => p.id === 'p2'))").split('เลขที่สัญญา')[1][:200], "no PO text when there is no PO"

    # ---- Excel export: every filtered row, all four lists ----
    for tab, btn, name in [("projects", "projectsExportBtn", "ซื้อขาย-โครงการ"), ("equipment", "equipmentExportBtn", "อุปกรณ์และการรับประกัน"), ("warehouse", "warehouseExportBtn", "โกดังสินค้า"), ("customers", "customersExportBtn", "รายชื่อลูกค้า")]:
        page.evaluate(f"showTab('{tab}')"); page.wait_for_timeout(300)
        with page.expect_download(timeout=30000) as dl:
            page.click('#' + btn)
        fn = dl.value.suggested_filename
        assert fn.endswith('.xlsx') and name in fn, fn
        dl.value.save_as(os.path.join(OUT, f"export_{tab}.xlsx"))
    z = zipfile.ZipFile(os.path.join(OUT, "export_projects.xlsx")); shared = z.read('xl/worksheets/sheet1.xml').decode('utf-8')
    assert 'โครงการหนึ่ง' in shared and 'PO-99' in shared and 'เลขที่ PO' in shared
    print("excel ok:", fn)

    # ---- attachments ----
    page.evaluate("showTab('projects'); openProjectForm('p1')"); page.wait_for_timeout(600)
    assert 'ยังไม่มีไฟล์แนบ' in page.inner_text('#prjFilesList') and not page.is_disabled('#prjFileBtn')
    open(os.path.join(OUT, "a.pdf"), "wb").write(b"%PDF-1.4 test attachment " * 20)
    page.set_input_files('#prjFileInput', os.path.join(OUT, "a.pdf")); page.wait_for_timeout(800)
    assert 'a.pdf' in page.inner_text('#prjFilesList') and page.inner_text('#prjFilesCount') == '(1)'
    rec = page.evaluate("[...window.__mockStore['pm_files'].values()][0]")
    assert rec['projectId'] == 'p1' and rec['ownerId'] == 'admin1' and base64.b64decode(rec['data']).startswith(b'%PDF'), rec['name']
    with page.expect_download(timeout=10000) as dl:
        page.click('#prjFilesList button:has-text("ดาวน์โหลด")')
    assert dl.value.suggested_filename == 'a.pdf'
    dl.value.save_as(os.path.join(OUT, "a_back.pdf")); assert open(os.path.join(OUT, "a_back.pdf"), "rb").read() == open(os.path.join(OUT, "a.pdf"), "rb").read()
    # too big
    open(os.path.join(OUT, "big.bin"), "wb").write(b"x" * (700 * 1024))
    page.set_input_files('#prjFileInput', os.path.join(OUT, "big.bin")); page.wait_for_timeout(600)
    assert 'big.bin' not in page.inner_text('#prjFilesList') and page.evaluate("window.__mockStore['pm_files'].size") == 1
    page.locator('#prjFilesList button:has-text("ลบ")').click(); page.click('#confirmModalOkBtn'); page.wait_for_timeout(500)
    assert page.evaluate("window.__mockStore['pm_files'].size") == 0 and 'ยังไม่มีไฟล์แนบ' in page.inner_text('#prjFilesList')
    page.click('#projectCancelBtn')
    # a new (unsaved) project cannot take files yet
    page.evaluate("openProjectForm(null)"); page.wait_for_timeout(300)
    assert page.is_disabled('#prjFileBtn') and 'บันทึกรายการก่อน' in page.inner_text('#prjFilesList'); page.click('#projectCancelBtn')
    # purging a project from the Trash takes its files along
    page.evaluate("db.collection('pm_files').add({projectId:'p2', ownerId:'admin1', name:'z.txt', size:3, type:'text/plain', data:'eHl6', createdBy:'admin1', createdAt:'2026-09-21T00:00:00Z'})")
    page.evaluate("db.collection('pm_projects').doc('p2').update({deletedAt:'2026-09-21T00:00:00Z', deletedBy:'admin1'})"); page.wait_for_timeout(300)
    page.click('.nav-item[data-tab="trash"]'); page.wait_for_timeout(700)
    page.locator('#trashBody tr:has-text("ขายหนึ่ง") button:has-text("ลบถาวร")').click(); page.click('#confirmModalOkBtn'); page.wait_for_timeout(700)
    assert page.evaluate("window.__mockStore['pm_files'].size") == 0 and page.evaluate("window.__mockStore['pm_projects'].has('p2')") is False

    # ---- accessibility names ----
    page.evaluate("showTab('projects')"); page.wait_for_timeout(300)
    missing = page.evaluate("[...document.querySelectorAll('button')].filter(b => b.offsetParent !== null && !b.textContent.trim() && !b.getAttribute('aria-label')).length")
    assert missing == 0, missing
    assert page.get_attribute('.nav-item[data-tab="warehouse"]', 'aria-label') == 'โกดังสินค้า'
    page.evaluate("openProjectForm('p1')"); page.wait_for_timeout(300)
    assert page.evaluate("[...document.querySelectorAll('#prjItemsBody .delete-btn')].every(b => b.getAttribute('aria-label') === 'ลบ' || b.title)")
    page.click('#projectCancelBtn')

    # ---- no built-in sample catalogs any more ----
    page.evaluate("showTab('catalog')"); page.wait_for_timeout(300)
    assert page.locator('#catalogGrid .postcard').count() == 0 and page.locator('#catalogImportSamplesBtn').count() == 0
    assert page.evaluate("typeof SAMPLE_CATALOGS") == 'undefined'
    print("errors:", errors); assert not errors
print("OK")
