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
      // a second project with NO plan at all, to confirm the card shows no ring/bars rather than an empty/0% one
      await db.collection('pm_projects').doc('p2').set({
        jobType:'project', docNo:'PJ2', name:'โครงการไม่มีแผน', customerId:'c1', customerName:'ลูกค้า ก',
        startDate: ymd(today), endDate: ymd(addDays(today, 30)), createdBy:'admin1', items:[], warrantyMonths:1, plan:[]
      });
    }""")
    page.wait_for_timeout(500)

    page.click('.nav-item[data-tab="actionplan"]'); page.wait_for_timeout(300)

    # ---------------- ring + stat line, read directly off the LIST card (no navigation into the detail view) ----------------
    card = page.locator('.plan-card:has-text("โครงการทดสอบความคืบหน้า")')
    assert card.locator('.plan-card-progress').is_visible(), "the compact progress widget renders on the card for a project that has plan topics"
    assert card.locator('.plan-card-ring-pct').inner_text().strip() == '50%'
    stat_text = card.locator('.plan-card-stat').inner_text()
    assert '2' in stat_text and '4' in stat_text and 'ดำเนินการแล้ว' in stat_text and 'ขั้นตอน' in stat_text, stat_text
    assert '4' in stat_text and 'หัวข้อใหญ่' in stat_text, stat_text
    ring_circles = card.locator('.plan-card-ring circle')
    assert ring_circles.count() == 2, "track circle + one progress arc, same technique as the dashboard's own donut"
    # the existing topic tracker still renders below the new widget, unchanged
    assert card.locator('.plan-track').is_visible()

    # ---------------- weekly bars: today's own column reflects the 2 steps due today; all 7 days render ----------------
    bar_cols = card.locator('.plan-card-weekly-bars .plan-card-bar-col')
    assert bar_cols.count() == 7, "Mon-Sun, always 7 columns regardless of which day today is"
    current_col = card.locator('.plan-card-weekly-bars .plan-card-bar-col.current')
    assert current_col.count() == 1, "exactly one column is marked as today"
    assert '2 ขั้นตอน' in (current_col.get_attribute('title') or ''), current_col.get_attribute('title')

    # ---------------- a project with no plan topics at all shows no ring/bars (nothing to show progress of yet) ----------------
    empty_card = page.locator('.plan-card:has-text("โครงการไม่มีแผน")')
    assert not empty_card.locator('.plan-card-progress').count(), "no plan topics yet -> the card shows no progress widget at all"
    assert empty_card.locator('.dash-empty').is_visible()

    # ---------------- the per-project DETAIL view is back to its original content, no widget there any more ----------------
    card.click(); page.wait_for_timeout(300)
    assert not page.locator('#planProgressWidget').count(), "the widget's old container div is gone from the detail view"
    assert not page.is_visible('.plan-progress-widget')
    meta_text = page.inner_text('#planMeta')
    assert 'ดำเนินการแล้ว' in meta_text and '2/4' in meta_text and '50%' in meta_text, meta_text
    page.click('#planBackBtn'); page.wait_for_timeout(200)

    # ---------------- English mode: the card's own composite stat lines switch too, not just the static dictionary strings ----------------
    page.evaluate("() => applyLanguage('en')"); page.wait_for_timeout(300)
    en_stat_text = page.locator('.plan-card:has-text("โครงการทดสอบความคืบหน้า")').locator('.plan-card-stat').inner_text()
    assert '2/4' in en_stat_text and 'steps done' in en_stat_text and 'topics' in en_stat_text, en_stat_text
    assert 'ขั้นตอนเสร็จแล้ว' not in en_stat_text and 'หัวข้อใหญ่' not in en_stat_text, en_stat_text
    page.evaluate("() => applyLanguage('th')"); page.wait_for_timeout(300)   # back to Thai, so this test doesn't leak language state into the next one

    print("errors:", errors); assert not errors
print("OK")
