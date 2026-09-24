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
    # no customers/companies/warehouse/serviceWarehouse seeded on purpose - the button must create all of that itself
    goto_tab(page, 'projects'); page.wait_for_timeout(300)

    assert page.is_visible('#projectsAddSampleBtn'), "admin sees the sample-data button"
    page.click('#projectsAddSampleBtn'); page.wait_for_timeout(200)
    page.click('#confirmModalOkBtn'); page.wait_for_timeout(1500)

    all_sample = page.evaluate("data.projects.filter(p => p.sample)")
    projects = [p for p in all_sample if p['jobType'] == 'project']
    sales = [p for p in all_sample if p['jobType'] == 'sale']
    assert len(projects) == 5, projects
    assert len(sales) == 5, sales

    for p in projects:
        assert p['name'].startswith('[ตัวอย่าง]')
        assert all(p.get(k) for k in ('docNo', 'contractNo', 'poNo', 'customerId', 'customerName', 'companyId', 'startDate', 'endDate', 'installLocation', 'notes'))
        assert p['warrantyMonths'] == 12
        goods = [it for it in p['items'] if it['kind'] == 'good']
        services = [it for it in p['items'] if it['kind'] == 'service']
        assert len(goods) == 3 and len(services) == 1, p['items']   # richer than the old single-item set, per the "too few when testing" report
        for it in goods:
            assert it['status'] == 'done' and all(it.get(k) for k in ('part', 'brand', 'name', 'type'))
            assert len(it['serials']) == it['qty']
        assert services[0]['status'] == 'done' and all(services[0].get(k) for k in ('part', 'brand', 'name', 'type'))
        assert len(p['plan']) == 5 and all(s['done'] for s in p['plan']) and all(s.get('owner') for s in p['plan'])
        with_subs = [s for s in p['plan'] if s.get('subs')]
        assert len(with_subs) == 2, "some topics carry their own sub-items, not just plain leaves"
        for s in with_subs:
            assert all(sub['done'] and sub.get('owner') for sub in s['subs'])
        total = p['installmentTotal']
        assert p['installmentNo'] == total - 1 and len(p['deliveries']) == total - 1, p
        assert p['photoCounts']['equipment'] == 1 and p['photoCounts']['install'] == 1

    for s in sales:
        assert s['name'].startswith('[ตัวอย่าง]')
        assert all(s.get(k) for k in ('docNo', 'poNo', 'customerId', 'customerName', 'companyId', 'startDate', 'endDate'))
        assert not s.get('plan') and not s.get('installmentTotal'), "a sale has no Action Plan / installments"
        goods = [it for it in s['items'] if it['kind'] == 'good']
        services = [it for it in s['items'] if it['kind'] == 'service']
        assert len(goods) == 3 and len(services) == 1, s['items']
        assert s['photoCounts']['equipment'] == 1 and s['photoCounts']['install'] == 1

    # 3 sample customers (spread across the 10 sample jobs), the usual throwaway sample company, and both sample warehouses
    sample_customers = page.evaluate("data.customers.filter(c => c.sample)")
    assert len(sample_customers) == 3, sample_customers
    assert any(c.get('sample') for c in page.evaluate("data.companies")), "no company existed yet, so a throwaway sample one was made"
    assert len(page.evaluate("data.warehouse.filter(w => w.sample)")) == 5
    assert len(page.evaluate("data.serviceWarehouse.filter(s => s.sample)")) == 5

    # "งวดงาน" reads as ready for the LAST installment (currentInstallmentStage = the next undelivered one)
    total0 = projects[0]['installmentTotal']
    row = page.locator(f'#projectsBody tr:has-text("{projects[0]["name"]}")')
    assert f'รอส่งงวดที่ {total0}' in row.inner_text()

    # the "รูปภาพ" page shows real photos, not just a ticked checkbox with nothing behind it
    row.click(); page.click('#prjViewPhotosBtn'); page.wait_for_timeout(400)
    assert page.locator('#photosEquipGrid .photo-item').count() == 1 and page.locator('#photosInstallGrid .photo-item').count() == 1
    first_good = next(it for it in projects[0]['items'] if it['kind'] == 'good')
    assert first_good['brand'] in page.inner_text('#photosEquipGrid')
    page.click('#photosBackBtn'); page.wait_for_timeout(300)
    page.click('#projectCancelBtn'); page.wait_for_timeout(200)   # "กลับ" reopened the read-only view modal (opened from there) - close it before continuing

    # clicking again does not duplicate the set (warehouse/serviceWarehouse guard themselves too, even called a second time)
    page.click('#projectsAddSampleBtn'); page.wait_for_timeout(200)
    assert 'มีข้อมูลตัวอย่างชุดนี้อยู่แล้ว' in page.inner_text('#toast')
    assert len(page.evaluate("data.projects.filter(p => p.sample)")) == 10
    assert len(page.evaluate("data.warehouse.filter(w => w.sample)")) == 5
    assert len(page.evaluate("data.serviceWarehouse.filter(s => s.sample)")) == 5

    # "ลบข้อมูลตัวอย่างทั้งหมด" sweeps sales, projects, both warehouses, the customers/company it made, AND the real photo rows
    photo_ids = [p['id'] for p in all_sample]
    goto_tab(page, 'trash'); page.wait_for_timeout(300)
    page.click('#deleteSampleDataBtn'); page.wait_for_timeout(200)
    page.click('#confirmModalOkBtn'); page.wait_for_timeout(1000)
    assert page.evaluate("data.projects.filter(p => p.sample).length") == 0
    assert page.evaluate("data.companies.filter(c => c.sample).length") == 0
    assert page.evaluate("data.customers.filter(c => c.sample).length") == 0
    assert page.evaluate("data.warehouse.filter(w => w.sample).length") == 0
    assert page.evaluate("data.serviceWarehouse.filter(s => s.sample).length") == 0
    remaining_photos = page.evaluate(f"""async () => {{
      let n = 0;
      for (const id of {photo_ids}) {{
        const snap = await db.collection('pm_photos').where('projectId', '==', id).get();
        n += snap.docs.length;
      }}
      return n;
    }}""")
    assert remaining_photos == 0, "no orphaned pm_photos rows left behind for the deleted sample jobs"

    print("errors:", errors); assert not errors
print("OK")
