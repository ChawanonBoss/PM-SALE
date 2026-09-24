import os, sys, http.server, threading, functools
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from harness import new_page, REPO_ROOT, goto_tab
class Q(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a): pass
h = functools.partial(Q, directory=REPO_ROOT)
srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), h); threading.Thread(target=srv.serve_forever, daemon=True).start()
base = f"http://127.0.0.1:{srv.server_address[1]}"

with new_page(viewport={"width": 1600, "height": 1000}) as (page, errors):
    page.goto(f"{base}/index.html"); page.wait_for_timeout(500)
    page.evaluate("() => localStorage.setItem('pm-sale-login-ts', String(Date.now()))")
    page.evaluate("() => window.__authListeners[0]({uid:'admin1', email:'admin@a.com', displayName:'Admin One'})"); page.wait_for_timeout(900)
    # no customers/companies seeded on purpose - the button must create its own sample company too, since none exist yet
    goto_tab(page, 'projects'); page.wait_for_timeout(300)

    assert page.is_visible('#projectsAddSampleBtn'), "admin sees the sample-data button"
    page.click('#projectsAddSampleBtn'); page.wait_for_timeout(200)
    page.click('#confirmModalOkBtn'); page.wait_for_timeout(800)

    added = page.evaluate("data.projects.filter(p => p.sample)")
    assert len(added) == 5, added
    for p in added:
        assert p['jobType'] == 'project' and p['name'].startswith('[ตัวอย่าง]')
        assert all(p.get(k) for k in ('docNo', 'contractNo', 'poNo', 'customerId', 'customerName', 'companyId', 'startDate', 'endDate', 'installLocation', 'notes'))
        assert p['warrantyMonths'] == 12
        assert len(p['items']) == 1 and p['items'][0]['status'] == 'done' and all(p['items'][0].get(k) for k in ('part', 'brand', 'name', 'type'))
        assert len(p['items'][0]['serials']) == p['items'][0]['qty']
        assert len(p['plan']) == 5 and all(s['done'] for s in p['plan']) and all(s.get('owner') for s in p['plan'])
        total = p['installmentTotal']
        assert p['installmentNo'] == total - 1 and len(p['deliveries']) == total - 1, p
        assert p['photoCounts']['equipment'] == 1 and p['photoCounts']['install'] == 1

    # a sample company was created too, since none existed
    assert any(c.get('sample') for c in page.evaluate("data.companies")), "no company existed yet, so a throwaway sample one was made"
    assert any(c.get('sample') for c in page.evaluate("data.customers"))

    # "งวดงาน" reads as ready for the LAST installment (currentInstallmentStage = the next undelivered one)
    total0 = added[0]['installmentTotal']
    row = page.locator(f'#projectsBody tr:has-text("{added[0]["name"]}")')
    assert f'รอส่งงวดที่ {total0}' in row.inner_text()

    # the "รูปภาพ" page shows real photos, not just a ticked checkbox with nothing behind it
    row.click(); page.click('#prjViewPhotosBtn'); page.wait_for_timeout(400)
    assert page.locator('#photosEquipGrid .photo-item').count() == 1 and page.locator('#photosInstallGrid .photo-item').count() == 1
    assert added[0]['items'][0]['brand'] in page.inner_text('#photosEquipGrid')
    page.click('#photosBackBtn'); page.wait_for_timeout(300)
    page.click('#projectCancelBtn'); page.wait_for_timeout(200)   # "กลับ" reopened the read-only view modal (opened from there) - close it before continuing

    # clicking again does not duplicate the set
    page.click('#projectsAddSampleBtn'); page.wait_for_timeout(200)
    assert 'มีข้อมูลตัวอย่างชุดนี้อยู่แล้ว' in page.inner_text('#toast')
    assert len(page.evaluate("data.projects.filter(p => p.sample)")) == 5

    # "ลบข้อมูลตัวอย่างทั้งหมด" sweeps the projects, the customer/company it made, AND the real photo rows (no orphans left behind)
    photo_ids = [p['id'] for p in added]
    goto_tab(page, 'trash'); page.wait_for_timeout(300)
    page.click('#deleteSampleDataBtn'); page.wait_for_timeout(200)
    page.click('#confirmModalOkBtn'); page.wait_for_timeout(800)
    assert page.evaluate("data.projects.filter(p => p.sample).length") == 0
    assert page.evaluate("data.companies.filter(c => c.sample).length") == 0
    assert page.evaluate("data.customers.filter(c => c.sample).length") == 0
    remaining_photos = page.evaluate(f"""async () => {{
      let n = 0;
      for (const id of {photo_ids}) {{
        const snap = await db.collection('pm_photos').where('projectId', '==', id).get();
        n += snap.docs.length;
      }}
      return n;
    }}""")
    assert remaining_photos == 0, "no orphaned pm_photos rows left behind for the deleted sample projects"

    print("errors:", errors); assert not errors
print("OK")
