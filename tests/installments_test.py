import os, sys, tempfile
import sys, os, http.server, threading, functools
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from harness import new_page, REPO_ROOT
class Q(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a): pass
h = functools.partial(Q, directory=REPO_ROOT)
srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), h); threading.Thread(target=srv.serve_forever, daemon=True).start()
base = f"http://127.0.0.1:{srv.server_address[1]}"

with new_page(viewport={"width": 1440, "height": 900}) as (page, errors):
    page.goto(f"{base}/index.html"); page.wait_for_timeout(500)
    page.evaluate("() => localStorage.setItem('pm-sale-login-ts', String(Date.now()))")
    page.evaluate("() => window.__authListeners[0]({uid:'admin1', email:'admin@a.com', displayName:'Admin One'})"); page.wait_for_timeout(900)
    page.evaluate("""() => { db.runTransaction = async fn => { const writes = []; const tx = { get: ref => ref.get(), update: (ref, d) => writes.push(() => ref.update(d)), set: (ref, d) => writes.push(() => ref.set(d)) }; const r = await fn(tx); for (const w of writes) await w(); return r; }; }""")
    page.evaluate("""async () => {
      await db.collection('pm_customers').doc('c1').set({name:'ลูกค้า ก', type:'gov', address:'ที่อยู่', contactName:'คุณก', contactPhone:'081', createdBy:'admin1'});
      await db.collection('pm_companies').doc('co1').set({name:'บริษัทเรา'});
      await db.collection('pm_projects').doc('p1').set({jobType:'project', docNo:'PJ1', name:'โครงการแบ่งงวด', customerId:'c1', customerName:'ลูกค้า ก', companyId:'co1', startDate:'2026-09-01', endDate:'2026-12-31', items:[], plan:[], createdBy:'admin1'});
      await db.collection('pm_projects').doc('p2').set({jobType:'project', docNo:'PJ2', name:'โครงการไม่แบ่งงวด', customerId:'c1', customerName:'ลูกค้า ก', companyId:'co1', startDate:'2026-09-01', endDate:'2026-12-31', items:[], plan:[], createdBy:'admin1'});
      await db.collection('pm_projects').doc('s1').set({jobType:'sale', docNo:'SO1', name:'ขาย', customerId:'c1', customerName:'ลูกค้า ก', startDate:'2026-09-02', endDate:'2026-09-02', items:[], createdBy:'admin1'}); }""")
    page.wait_for_timeout(500)
    page.evaluate("showTab('projects')"); page.wait_for_timeout(300)
    row = lambda name: page.locator(f'#projectsBody tr:has-text("{name}")')

    # no installments set -> no "ส่งงาน" button, and none for a sale
    assert row('โครงการแบ่งงวด').locator('button:text-is("ส่งงาน")').count() == 0
    # menus are separate: the sale is not in the projects list, and its rows have no plan / deliver buttons
    assert row('ขาย').count() == 0 and 'ขาย' not in page.inner_text('#projectsBody')
    page.evaluate("showTab('sales')"); page.wait_for_timeout(300)
    assert page.locator('#salesBody tr').count() == 1 and page.locator('#salesBody button:text-is("ส่งงาน")').count() == 0 and page.locator('#salesBody button:text-is("แผนงาน")').count() == 0
    page.evaluate("showTab('projects')"); page.wait_for_timeout(300)

    # the form: field only for projects; a sale hides it
    page.evaluate("openProjectForm('p1')"); page.wait_for_timeout(300)
    assert page.is_visible('#prjInstallmentTotal') and page.get_attribute('#prjInstallmentTotal', 'type') == 'number'
    page.evaluate("$('prjJobType').value = 'sale'; applyJobType()"); assert not page.is_visible('#prjInstallmentTotal')
    page.evaluate("$('prjJobType').value = 'project'; applyJobType()"); assert page.is_visible('#prjInstallmentTotal')
    page.fill('#prjInstallmentTotal', '4'); page.click('#projectSaveBtn'); page.wait_for_timeout(700)
    assert page.evaluate("data.projects.find(p => p.id === 'p1').installmentTotal") == 4
    assert page.evaluate("data.projects.find(p => p.id === 'p1').installmentNo") is None
    assert 'ส่งงานแล้ว 0/4 งวด' in row('โครงการแบ่งงวด').inner_text()
    # PDF before any delivery: installment cell is "-"
    assert '<td>-</td>' in page.evaluate("buildProjectPrintHtml(data.projects.find(p => p.id === 'p1'))").split('งวดงานที่')[1][:80]

    # deliver batch 1 (default = first) then batch 3 by choosing it
    row('โครงการแบ่งงวด').locator('button:text-is("ส่งงาน")').click(); page.wait_for_timeout(300)
    assert page.is_visible('#deliveryModal') and page.input_value('#dlvNo') == '1'
    assert page.evaluate("[...document.querySelectorAll('#dlvNo option')].map(o => o.textContent.trim())") == ['1 / 4', '2 / 4', '3 / 4', '4 / 4']
    assert 'ยังไม่เคยส่งงาน' in page.inner_text('#dlvHistory')
    page.fill('#dlvNote', 'ชุดที่ 1'); page.click('#dlvSaveBtn'); page.wait_for_timeout(700)
    p1 = page.evaluate("data.projects.find(p => p.id === 'p1')")
    assert p1['installmentNo'] == 1 and len(p1['deliveries']) == 1 and p1['deliveries'][0]['note'] == 'ชุดที่ 1' and p1['deliveries'][0]['total'] == 4
    assert 'ส่งงานแล้ว 1/4 งวด' in row('โครงการแบ่งงวด').inner_text() and not page.is_visible('#deliveryModal')
    row('โครงการแบ่งงวด').locator('button:text-is("ส่งงาน")').click(); page.wait_for_timeout(300)
    assert page.input_value('#dlvNo') == '2', "default moves to the next installment"
    assert 'เคยส่งแล้ว' in page.evaluate("$('dlvNo').options[0].textContent") and 'ชุดที่ 1' in page.inner_text('#dlvHistory')
    page.select_option('#dlvNo', '3'); page.fill('#dlvDate', '2026-11-05'); page.click('#dlvSaveBtn'); page.wait_for_timeout(700)
    p1 = page.evaluate("data.projects.find(p => p.id === 'p1')")
    assert p1['installmentNo'] == 3 and len(p1['deliveries']) == 2 and p1['deliveries'][1]['date'] == '2026-11-05'
    audits = page.evaluate("[...window.__mockStore['pm_auditLog'].values()].filter(a => a.action === 'ส่งงาน').map(a => a.details)")
    assert audits and 'งวดที่ 3/4' in audits[-1], audits
    assert 'ส่งงานแล้ว 3/4 งวด' in row('โครงการแบ่งงวด').inner_text()

    # PDF shows 3/4 and the delivery date of that installment
    html = page.evaluate("buildProjectPrintHtml(data.projects.find(p => p.id === 'p1'))")
    seg = html.split('งวดงานที่')[1][:80]; assert '3/4' in seg, seg
    assert '5 พ.ย. 2569' in html.split('วันที่ส่งมอบ')[1][:120], html.split('วันที่ส่งมอบ')[1][:120]
    # "save and print" prints straight away with the new number
    page.evaluate("window.print = () => { window.__printed = document.getElementById('printArea').innerText; }")
    row('โครงการแบ่งงวด').locator('button:text-is("ส่งงาน")').click(); page.wait_for_timeout(300)
    assert page.input_value('#dlvNo') == '4'; page.click('#dlvSavePrintBtn'); page.wait_for_timeout(1500)
    assert '4/4' in page.evaluate("window.__printed || ''"), page.evaluate("window.__printed")
    page.evaluate("window.dispatchEvent(new Event('afterprint'))")

    # cannot shrink the total below what was already delivered
    page.evaluate("openProjectForm('p1')"); page.fill('#prjInstallmentTotal', '2'); page.click('#projectSaveBtn'); page.wait_for_timeout(500)
    assert page.evaluate("data.projects.find(p => p.id === 'p1').installmentTotal") == 4 and page.is_visible('#projectModal')
    assert 'ส่งงานแล้ว' in page.inner_text('#prjInstallmentHint')
    page.click('#projectCancelBtn')

    # the number typed before this feature ("งวดที่ 2") still prints as it was
    page.evaluate("db.collection('pm_projects').doc('p2').update({ installmentNo: 'งวดที่ 2' })"); page.wait_for_timeout(400)
    assert 'งวดที่ 2' in page.evaluate("buildProjectPrintHtml(data.projects.find(p => p.id === 'p2'))")
    # Excel column
    assert page.evaluate("(showTab('projects'), renderProjects(), EXPORTS.projects().find(r => r['เลขที่เอกสาร'] === 'PJ1')['งวดงาน'])") == '4/4'
    assert page.evaluate("(showTab('sales'), renderSales(), Object.keys(EXPORTS.sales()[0]))").count('งวดงาน') == 0, "the sales export has no installment column"
    print("errors:", errors); assert not errors
print("OK")
