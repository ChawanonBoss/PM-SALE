import sys, os, http.server, threading, functools
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from harness import new_page, REPO_ROOT, goto_tab
class Q(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a): pass
h = functools.partial(Q, directory=REPO_ROOT)
srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), h); threading.Thread(target=srv.serve_forever, daemon=True).start()
base = f"http://127.0.0.1:{srv.server_address[1]}"
OUT = os.path.join(os.environ["TEMP"], "pdf_check")
PIXEL_PNG_B64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII="

with new_page(viewport={"width": 1400, "height": 900}) as (page, errors):
    page.goto(f"{base}/index.html"); page.wait_for_timeout(500)
    page.evaluate("() => localStorage.setItem('pm-sale-login-ts', String(Date.now()))")
    page.evaluate("() => window.__authListeners[0]({uid:'admin1', email:'admin@a.com', displayName:'Admin One'})"); page.wait_for_timeout(900)
    page.evaluate("""async () => {
      await db.collection('pm_customers').doc('c1').set({name:'ลูกค้า ก', type:'gov', createdBy:'admin1'});
      await db.collection('pm_companies').doc('co1').set({name:'บริษัท ทดสอบ จำกัด', address:'กรุงเทพฯ', phone:'02-000-0000', taxId:'1234567890123'});
      await db.collection('pm_projects').doc('p1').set({jobType:'project', docNo:'PJ1', name:'โครงการทดสอบรูป', customerId:'c1', customerName:'ลูกค้า ก', contractNo:'CT-99', companyId:'co1', startDate:'2026-09-01', endDate:'2026-12-31',
        items:[{rid:'r1', whId:'', part:'P1', brand:'Yeti', name:'เราเตอร์ XR500', type:'', serials:['SN-001'], qty:1, status:'pending'}], createdBy:'admin1'});
      await db.collection('pm_projects').doc('s1').set({jobType:'sale', docNo:'SO1', name:'ขายทดสอบรูป', customerId:'c1', customerName:'ลูกค้า ก', startDate:'2026-09-02', endDate:'2026-09-02', items:[], createdBy:'admin1', photoSets:['equipment']}); }""")
    page.wait_for_timeout(500)
    # commitProject() saves through a real Firestore transaction, which this mock doesn't implement - shim it the same way docno_and_history_test.py does
    page.evaluate("""() => {
      db.runTransaction = async fn => {
        const writes = [];
        const tx = { get: ref => ref.get(), update: (ref, d) => writes.push(() => ref.update(d)), set: (ref, d) => writes.push(() => ref.set(d)) };
        const r = await fn(tx);
        for (const w of writes) await w();
        return r;
      };
    }""")

    # ---- โครงการ: opens with both sets, uploads to each, checkbox status updates on the list, delete works ----
    page.evaluate("showTab('projects')"); page.wait_for_timeout(300)
    page.click('tr:has-text("โครงการทดสอบรูป") .icon-btn:has-text("รูปภาพ")'); page.wait_for_timeout(300)
    assert page.evaluate("currentTab") == 'photos'
    assert 'โครงการ' in page.inner_text('#photosMeta') and 'PJ1' in page.inner_text('#photosMeta')
    assert page.is_visible('#photosEquipPanel') and page.is_visible('#photosInstallPanel')

    def upload(input_id, filename="a.png"):
        page.set_input_files(f'#{input_id}', {"name": filename, "mimeType": "image/png", "buffer": __import__("base64").b64decode(PIXEL_PNG_B64)})
        page.wait_for_timeout(700)

    # equipment picker is built from the job's own items[] (rid+serial) - pick the one line this job actually has before attaching
    opt_labels = page.evaluate("[...document.querySelectorAll('#photosEquipItemSel option')].map(o => o.textContent)")
    assert any('Yeti' in l and 'SN-001' in l for l in opt_labels)
    page.select_option('#photosEquipItemSel', 'r1::SN-001')
    upload('photosEquipInput')
    assert page.locator('#photosEquipGrid .photo-item').count() == 1
    assert 'Yeti' in page.inner_text('#photosEquipGrid') and 'SN-001' in page.inner_text('#photosEquipGrid')
    upload('photosInstallInput')   # left as "ไม่ระบุอุปกรณ์" - install panel's own select was never touched
    assert page.locator('#photosInstallGrid .photo-item').count() == 1
    assert 'ไม่ระบุอุปกรณ์' in page.inner_text('#photosInstallGrid')
    page.wait_for_timeout(300)

    # ---- print PDF: header pulls its fields straight from the system record (docNo/type/name/customer/contract/company letterhead), not typed in ----
    page.evaluate("window.print = () => {}")
    page.click('#photosPrintBtn'); page.wait_for_timeout(200)
    printed = page.inner_html('#printArea')
    assert 'ภาพถ่ายการส่งมอบงาน' not in printed, "generic title was dropped in favor of per-photo equipment captions"
    for expect in ('PJ1', 'โครงการ', 'โครงการทดสอบรูป', 'ลูกค้า ก', 'CT-99', 'บริษัท ทดสอบ จำกัด', '2 รูป', 'ชุดที่ 1: รูปภาพอุปกรณ์', 'ชุดที่ 2: รูปภาพงานติดตั้ง'):
        assert expect in printed, expect
    assert page.locator('#printArea .pr-photo-cell').count() == 2
    # the tagged equipment photo prints the equipment line, not its filename; the untagged install photo falls back to its filename
    assert page.locator('#printArea .pr-photo-cap:has-text("Yeti")').count() == 1
    assert page.locator('#printArea .pr-photo-cap:has-text("SN-001")').count() == 1
    assert page.locator('#printArea .pr-photo-cap:has-text("a.png")').count() == 1
    page.evaluate("window.dispatchEvent(new Event('afterprint'))")   # runs printPhotos()'s own restore() so #printArea is cleared for what follows
    assert page.inner_html('#printArea') == ''

    page.click('#photosBackBtn'); page.wait_for_timeout(400)
    assert page.evaluate("currentTab") == 'projects'
    chks = page.locator('tr:has-text("โครงการทดสอบรูป") td[data-col="workstatus"] input')
    assert [chks.nth(i).is_checked() for i in range(chks.count())] == [False, True, True], "plan not done, but both photo sets now show saved"

    # go back in and delete the equipment photo -> status column reflects it going back to unchecked
    page.click('tr:has-text("โครงการทดสอบรูป") .icon-btn:has-text("รูปภาพ")'); page.wait_for_timeout(300)
    page.click('#photosEquipGrid .delete-btn'); page.wait_for_timeout(200)
    page.click('#confirmModalOkBtn')   # the app's own confirmAction() modal, not a native confirm()
    page.wait_for_timeout(500)
    assert page.locator('#photosEquipGrid .photo-item').count() == 0
    page.click('#photosBackBtn'); page.wait_for_timeout(400)
    chks = page.locator('tr:has-text("โครงการทดสอบรูป") td[data-col="workstatus"] input')
    assert [chks.nth(i).is_checked() for i in range(chks.count())] == [False, False, True]

    # ---- ซื้อขาย: only the equipment set was chosen at creation, so the install panel is hidden ----
    goto_tab(page, 'sales'); page.wait_for_timeout(300)
    page.click('tr:has-text("ขายทดสอบรูป") .icon-btn:has-text("รูปภาพ")'); page.wait_for_timeout(300)
    assert 'ซื้อขาย' in page.inner_text('#photosMeta') and 'SO1' in page.inner_text('#photosMeta')
    assert page.is_visible('#photosEquipPanel') and not page.is_visible('#photosInstallPanel')
    page.click('#photosBackBtn'); page.wait_for_timeout(300)
    assert page.evaluate("currentTab") == 'sales'

    # ---- create form: photo-set checkboxes only show for a sale, default checked, and route to the photo page after a NEW save ----
    page.click('#salesCreateBtn'); page.wait_for_timeout(200)
    assert page.is_visible('#prjPhotoSetsField')
    assert page.is_checked('#prjPhotoEquip') and page.is_checked('#prjPhotoInstall')
    page.uncheck('#prjPhotoInstall')
    page.fill('#prjName', 'ขายใหม่จากฟอร์ม')
    page.select_option('#prjCustomer', 'c1')
    page.fill('#prjStart', '2026-09-20')
    page.click('#projectSaveBtn'); page.wait_for_timeout(600)
    assert page.evaluate("currentTab") == 'photos', "saving a NEW sale should route straight to its photo page"
    assert page.is_visible('#photosEquipPanel') and not page.is_visible('#photosInstallPanel')
    new_sale = page.evaluate("data.projects.find(p => p.name === 'ขายใหม่จากฟอร์ม')")
    assert new_sale['photoSets'] == ['equipment']

    goto_tab(page, 'projects'); page.wait_for_timeout(200)
    assert not page.is_visible('#prjPhotoSetsField'), "a project never shows the set-picker (it always gets both sets)"

    # ---- Action Plan header: "รูปภาพ ->" opens the same photo page for the project currently open ----
    page.click('.nav-item[data-tab="actionplan"]'); page.wait_for_timeout(300)
    page.click('.plan-card:has-text("โครงการทดสอบรูป")'); page.wait_for_timeout(300)
    page.click('#planPhotosBtn'); page.wait_for_timeout(300)
    assert page.evaluate("currentTab") == 'photos' and page.evaluate("photosProjectId") == 'p1'

    page.screenshot(path=os.path.join(OUT, "photos_page.png"))
    print("errors:", errors); assert not errors
print("OK")
