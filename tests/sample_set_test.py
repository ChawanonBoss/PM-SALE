import os, sys, tempfile
import sys, os, http.server, threading, functools, datetime, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from harness import new_page, REPO_ROOT
class Q(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a): pass
h = functools.partial(Q, directory=REPO_ROOT)
srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), h); threading.Thread(target=srv.serve_forever, daemon=True).start()
base = f"http://127.0.0.1:{srv.server_address[1]}"
HERE = os.path.dirname(os.path.abspath(__file__))
GEN = open(os.path.join(HERE, 'fixtures', 'samples10.js'), encoding='utf-8').read()
RUN = open(os.path.join(HERE, 'fixtures', 'seed10_run.js'), encoding='utf-8').read()
TODAY = datetime.date.today().isoformat()

with new_page(viewport={"width": 1440, "height": 900}) as (page, errors):
    page.goto(f"{base}/index.html"); page.wait_for_timeout(500)
    page.evaluate("() => localStorage.setItem('pm-sale-login-ts', String(Date.now()))")
    page.evaluate("() => window.__authListeners[0]({uid:'admin1', email:'admin@a.com', displayName:'Admin One'})"); page.wait_for_timeout(900)
    page.evaluate("""() => { db.runTransaction = async fn => { const writes = []; const tx = { get: ref => ref.get(), update: (ref, d) => writes.push(() => ref.update(d)), set: (ref, d) => writes.push(() => ref.set(d)) }; const r = await fn(tx); for (const w of writes) await w(); return r; }; }""")
    fn = "(" + RUN.strip() + ")"
    res = page.evaluate(fn, [GEN, TODAY]); page.wait_for_timeout(1500)
    print({k: v for k, v in res.items() if k != 'docNos'}); print(res['docNos'])
    assert res['companies'] == 10 and res['customers'] == 10 and res['warehouse'] == 10 and res['projects'] == 10 and res['sales'] == 10 and res['invites'] == 10 and res['trash'] == 9
    assert len(set(res['docNos'])) == 20
    # stock stays consistent: what left the warehouse equals the sum of the recorded withdrawals, serials stay unique, nothing negative
    bad = page.evaluate("""() => data.warehouse.filter(w => w.sample).filter(w => { const out = (w.history || []).reduce((s, h) => s + (h.type === 'out' ? h.qty : -h.qty), 0);
        return w.quantity < 0 || new Set(w.serials).size !== w.serials.length || (w.serials.length && w.serials.length > w.quantity); }).map(w => w.part)""")
    assert not bad, bad
    # every equipment line linked to the warehouse points at a real item
    orphan = page.evaluate("data.projects.flatMap(p => p.items.filter(i => i.whId && !data.warehouse.some(w => w.id === i.whId))).length"); assert orphan == 0
    stats = page.evaluate("""() => { const c = {}; data.projects.filter(p => p.sample).forEach(p => { const k = (isSale(p) ? 'sale:' : 'project:') + projectStatus(p); c[k] = (c[k] || 0) + 1; });
      const w = {}; getWarrantyRows().forEach(r => { w[r.wstatus] = (w[r.wstatus] || 0) + 1; }); const a = getDashAlerts(); return { status: c, warranty: w, alerts: { ending: a.endingSoon.length, warrantySoon: a.warrantySoon.length, planSoon: a.planSoon, planLate: a.planLate } }; }""")
    print(json.dumps(stats, ensure_ascii=False))
    assert stats['alerts']['planLate'] > 0 and stats['alerts']['ending'] > 0 and stats['alerts']['warrantySoon'] > 0
    counts = {t: page.evaluate(f"(showTab('{t}'), 1) && document.querySelector('#{t}Count') ? document.querySelector('#{t}Count').textContent : ''") for t in ['projects', 'equipment', 'warehouse', 'customers', 'companies', 'users']}
    print(counts)
    print("errors:", errors); assert not errors
print("OK")
