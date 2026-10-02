import os, sys, http.server, threading, functools
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from harness import new_page, REPO_ROOT
class Q(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a): pass
h = functools.partial(Q, directory=REPO_ROOT)
srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), h); threading.Thread(target=srv.serve_forever, daemon=True).start()
base = f"http://127.0.0.1:{srv.server_address[1]}"

with new_page(viewport={"width": 1500, "height": 1000}) as (page, errors):
    page.goto(f"{base}/index.html"); page.wait_for_timeout(500)
    page.evaluate("() => localStorage.setItem('pm-sale-login-ts', String(Date.now()))")
    page.evaluate("() => window.__authListeners[0]({uid:'admin1', email:'admin@a.com', displayName:'Admin One'})"); page.wait_for_timeout(900)

    # a project with 4 leaf steps: 2 already done (in the past), 2 still pending and both due TODAY (so the weekly
    # bar chart's own "current day" column has a real, known count regardless of which real weekday the suite runs on)
    page.evaluate("""async () => {
      const ymd = d => `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')}`;
      const addDays = (d, n) => { const x = new Date(d); x.setDate(x.getDate() + n); return x; };
      const today = new Date();
      await db.collection('pm_customers').doc('c1').set({name:'ลูกค้า ก', type:'gov', createdBy:'admin1'});
      await db.collection('pm_projects').doc('p1').set({
        jobType:'project', docNo:'PJ1', name:'โครงการทดสอบความคืบหน้า', customerId:'c1', customerName:'ลูกค้า ก',
        startDate: ymd(addDays(today, -10)), endDate: ymd(addDays(today, 15)),
        createdBy:'admin1', items:[], warrantyMonths:1,
        plan: [
          { title:'หัวข้อ 1', owner:'ทีมติดตั้ง', start: ymd(addDays(today, -10)), end: ymd(addDays(today, -5)), done:true, subs:[] },
          { title:'หัวข้อ 2', owner:'ทีมติดตั้ง', start: ymd(addDays(today, -5)), end: ymd(addDays(today, -1)), done:true, subs:[] },
          { title:'หัวข้อ 3', owner:'ทีมติดตั้ง', start: ymd(today), end: ymd(today), done:false, subs:[] },
          { title:'หัวข้อ 4', owner:'ทีมติดตั้ง', start: ymd(today), end: ymd(today), done:false, subs:[] }
        ]
      });
      // a second project with NO plan at all, to confirm the widget stays absent rather than showing an empty/0% ring
      await db.collection('pm_projects').doc('p2').set({
        jobType:'project', docNo:'PJ2', name:'โครงการไม่มีแผน', customerId:'c1', customerName:'ลูกค้า ก',
        startDate: ymd(today), endDate: ymd(addDays(today, 30)), createdBy:'admin1', items:[], warrantyMonths:1, plan:[]
      });
    }""")
    page.wait_for_timeout(500)

    page.click('.nav-item[data-tab="actionplan"]'); page.wait_for_timeout(300)
    page.click('.plan-card:has-text("โครงการทดสอบความคืบหน้า")'); page.wait_for_timeout(300)

    # ---------------- ring + stat line read from the SAME planSummary() the rest of the page already uses ----------------
    assert page.is_visible('.plan-progress-widget'), "the progress widget renders for a project that has plan topics"
    assert page.locator('.plan-progress-widget .dash-donut-num').inner_text().strip() == '50%'
    stat_text = page.inner_text('.plan-progress-stat-row')
    assert '2' in stat_text and '4' in stat_text and 'ขั้นตอนเสร็จแล้ว' in stat_text, stat_text
    ring_circles = page.locator('.plan-progress-widget .dash-donut circle')
    assert ring_circles.count() == 2, "track circle + one progress arc, same technique as the dashboard's own donut"

    # ---------------- weekly bars: today's own column reflects the 2 steps due today; all 7 days render ----------------
    bar_cols = page.locator('.plan-progress-weekly .dash-bar-col')
    assert bar_cols.count() == 7, "Mon-Sun, always 7 columns regardless of which day today is"
    current_col = page.locator('.plan-progress-weekly .dash-bar-col.current')
    assert current_col.count() == 1, "exactly one column is marked as today"
    assert '2 ขั้นตอน' in (current_col.get_attribute('title') or ''), current_col.get_attribute('title')

    # ---------------- a project with no plan topics at all shows no ring (nothing to show progress of yet) ----------------
    page.click('#planBackBtn'); page.wait_for_timeout(200)
    page.click('.plan-card:has-text("โครงการไม่มีแผน")'); page.wait_for_timeout(300)
    assert not page.is_visible('.plan-progress-widget'), "no plan topics yet -> the widget stays out of the page entirely"

    print("errors:", errors); assert not errors
print("OK")
