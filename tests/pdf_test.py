import os, sys, tempfile
import sys, os, re, http.server, threading, functools, datetime
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from harness import new_page, REPO_ROOT
from playwright.sync_api import sync_playwright

TMP = os.path.join(tempfile.gettempdir(), "pdf_check"); os.makedirs(TMP, exist_ok=True)
APP = REPO_ROOT

class Q(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a): pass
class Multi(Q):
    def translate_path(self, path):
        if path.startswith('/tmp/'): return os.path.join(TMP, path[5:])
        return super().translate_path(path)
h = functools.partial(Multi, directory=APP)
srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), h); threading.Thread(target=srv.serve_forever, daemon=True).start()
base = f"http://127.0.0.1:{srv.server_address[1]}"
today = datetime.date.today()
D = lambda n: (today + datetime.timedelta(days=n)).isoformat()

def rasterize(pdf_name, pages, scale=2.0):
    """render pages of a PDF to PNGs with pdf.js so the result can be looked at"""
    out = []
    with sync_playwright() as pw:
        b = pw.chromium.launch(); pg = b.new_page(viewport={"width": 1800, "height": 2000})
        pg.goto(f"{base}/index.html")   # any page on this origin so /tmp/ files are same-origin
        pg.set_content("<html><body style='margin:0;background:#888'><canvas id='c'></canvas></body></html>")
        pg.add_script_tag(url="https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.min.js")
        info = pg.evaluate(f"""async () => {{
          pdfjsLib.GlobalWorkerOptions.workerSrc = 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js';
          const bytes = new Uint8Array(await (await fetch('{base}/tmp/{pdf_name}')).arrayBuffer());
          window.__doc = await pdfjsLib.getDocument({{ data: bytes }}).promise;
          return window.__doc.numPages;
        }}""") if False else None
        # the page origin above is about:blank after set_content, so fetch from Python instead
        data = open(os.path.join(TMP, pdf_name), "rb").read()
        import base64
        pg.evaluate("""async (b64) => {
          pdfjsLib.GlobalWorkerOptions.workerSrc = 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js';
          const bin = atob(b64), u = new Uint8Array(bin.length); for (let i = 0; i < bin.length; i++) u[i] = bin.charCodeAt(i);
          window.__doc = await pdfjsLib.getDocument({ data: u }).promise;
        }""", base64.b64encode(data).decode())
        n = pg.evaluate("window.__doc.numPages")
        for i in range(1, min(n, pages) + 1):
            pg.evaluate("""async ([i, scale]) => { const p = await window.__doc.getPage(i), vp = p.getViewport({scale}), c = document.getElementById('c'); c.width = vp.width; c.height = vp.height; await p.render({canvasContext: c.getContext('2d'), viewport: vp}).promise; }""", [i, scale])
            path = os.path.join(TMP, f"{pdf_name}.p{i}.png"); pg.locator('#c').screenshot(path=path); out.append(path)
        b.close()
    return n, out

with new_page(viewport={"width": 1500, "height": 1000}) as (page, errors):
    page.goto(f"{base}/index.html"); page.wait_for_timeout(500)
    page.evaluate("() => localStorage.setItem('pm-sale-login-ts', String(Date.now()))")
    page.evaluate("() => window.__authListeners[0]({uid:'admin1', email:'admin@a.com', displayName:'Admin One'})")
    page.wait_for_timeout(800)
    page.evaluate("""async ([s, e, d1, d2]) => {
      await db.collection('pm_customers').doc('c1').set({name:'การไฟฟ้านครหลวง', type:'gov', address:'30 ถนนชิดลม แขวงลุมพินี เขตปทุมวัน กรุงเทพฯ 10330', contactName:'คุณวิภา รักงาน', contactPhone:'02-256-3000', createdBy:'admin1'});
      const cv = document.createElement('canvas'); cv.width = cv.height = 96; const cx = cv.getContext('2d'); cx.fillStyle = '#3B82F6'; cx.fillRect(0,0,96,96); cx.fillStyle = '#fff'; cx.font = 'bold 40px Arial'; cx.textAlign = 'center'; cx.fillText('BU', 48, 62);
      await db.collection('pm_companies').doc('co1').set({name:'บริษัท บียู เอบีบี เทคโนโลยี จำกัด', address:'99/9 ถนนสุขุมวิท แขวงคลองเตย เขตคลองเตย กรุงเทพฯ 10110', phone:'02-123-4567', taxId:'0105560123456', logoBase64: cv.toDataURL('image/png')});
      const it = (part, brand, name, type, sers, qty, st) => ({rid:Math.random().toString(36), whId:'', part, brand, name, type, serials:sers, qty, status:st});
      await db.collection('pm_projects').doc('p1').set({jobType:'project', docNo:'PJ20260921-001', name:'ติดตั้งระบบ CCTV ทางหลวงสายหลัก (ตัวอย่างชื่อโครงการที่ยาว)', customerId:'c1', customerName:'การไฟฟ้านครหลวง', companyId:'co1',
        contractNo:'MEA-CCTV-69/01', startDate:s, endDate:e, notes:'ส่งมอบเป็นงวด งวดแรกภายใน 30 วัน', installLocation:'ทล.1 กม.30-60 และสถานีย่อยบางกะปิ', warrantyMonths:12, createdBy:'admin1', createdAt:'2026-09-21T00:00:00Z',
        items:[ it('C9200-24P','Cisco','Catalyst 9200 24-port PoE+','Switch',['FOC2201A0001','FOC2201A0002','FOC2201A0003'],3,'done'), it('RB4011','MikroTik','RB4011iGS+RM','Router',[],5,'pending'),
                it('DS-2CD2143G2','Hikvision','DS-2CD2143G2-I IP Camera 4MP','Camera',[],20,'pending'), it('IE-3300-8T2S','Cisco','IE-3300 Industrial Ethernet Switch','Industrial',['FDO2301D0001'],1,'pending'),
                it('OPT7010','Dell','OptiPlex 7010 (ชุดคอมพิวเตอร์)','Computer Set',['DL7010-0001','DL7010-0002'],2,'pending'), it('FG-100F','Fortinet','FortiGate 100F','Firewall',[],1,'pending') ],
        plan:[{title:'เตรียมงาน', owner:'ผู้จัดการ', start:d1, end:d2, done:true, subs:[{title:'สำรวจหน้างาน', owner:'ทีมติดตั้ง', start:d1, end:d1, done:true},{title:'ออกแบบระบบ', owner:'ผู้จัดการ', start:d1, end:d2, done:true}]},
              {title:'จัดซื้ออุปกรณ์', owner:'ฝ่ายขาย', start:d2, end:e, done:false, subs:[]}, {title:'ติดตั้งและทดสอบ', owner:'ทีมติดตั้ง', start:d2, end:e, done:false, subs:[]}]});
      await db.collection('pm_projects').doc('s1').set({jobType:'sale', docNo:'SO20260921-001', name:'ขายสวิตช์ให้ กฟน.', customerId:'c1', customerName:'การไฟฟ้านครหลวง', companyId:'co1', startDate:s, endDate:s, installLocation:'คลังสินค้า บางกะปิ', warrantyMonths:24, createdBy:'admin1',
        items:[ it('C9200-24P','Cisco','Catalyst 9200 24-port PoE+','Switch',['FOC2201A0001'],1,'pending') ]});
    }""", ['2026-08-01', '2026-12-31', '2026-08-05', '2026-09-10'])
    page.wait_for_timeout(500)
    page.evaluate("window.print = () => {}")

    def make_pdf(label, js, name, landscape=False):
        page.evaluate(js); page.wait_for_timeout(300)
        page.evaluate("Promise.all([document.fonts.load('400 16pt Sarabun', 'ก Aa 0'), document.fonts.load('700 18pt Sarabun', 'ก Aa 0')])"); page.wait_for_timeout(600)
        path = os.path.join(TMP, name)
        page.pdf(path=path, prefer_css_page_size=True, print_background=True)
        raw = open(path, 'rb').read()
        fonts = sorted(set(re.findall(rb'/BaseFont\s*/[A-Z]{6}\+([A-Za-z\-]+)', raw)))
        print(label, "->", name, len(raw), "bytes | fonts:", [f.decode() for f in fonts])
        page.evaluate("window.dispatchEvent(new Event('afterprint'))")
        return path, [f.decode() for f in fonts]

    # portrait project document
    path, fonts = make_pdf("project", "printProject('p1')", "project.pdf")
    assert any('Sarabun' in f for f in fonts), fonts
    # portrait sale document
    make_pdf("sale", "printProject('s1')", "sale.pdf")
    # landscape action-plan document (printActionPlan builds the area + injects the landscape @page)
    page.evaluate("selectedPlanProjectId = 'p1'")
    path, fonts = make_pdf("plan", "printActionPlan()", "plan.pdf")
    assert any('Sarabun' in f for f in fonts), fonts
    # stale landscape style (plan printed, no afterprint) must not leak into the next sale/project printout
    page.evaluate("selectedPlanProjectId = 'p1'; printActionPlan()"); page.wait_for_timeout(300)
    assert page.evaluate("document.querySelectorAll('#printPageStyle').length") == 1
    page.evaluate("printProject('p1')"); page.wait_for_timeout(300)
    css = page.evaluate("[...document.querySelectorAll('style#printPageStyle')].map(x => x.textContent)")
    assert len(css) == 1 and 'portrait' in css[0], css
    page.wait_for_timeout(600)
    page.pdf(path=os.path.join(TMP, "stale.pdf"), prefer_css_page_size=True, print_background=True)
    raw = open(os.path.join(TMP, "stale.pdf"), 'rb').read()
    import re as _re
    mb = _re.search(rb'/MediaBox\s*\[\s*0\s+0\s+([0-9.]+)\s+([0-9.]+)', raw); w, h = float(mb.group(1)), float(mb.group(2)); print("stale pdf page", w, h); assert h > w
    page.evaluate("window.dispatchEvent(new Event('afterprint'))")
    assert page.evaluate("document.querySelectorAll('#printPageStyle').length") == 0
    print("errors:", errors); assert not errors
for name, pages in [("project.pdf", 3), ("sale.pdf", 1), ("plan.pdf", 2)]:
    n, imgs = rasterize(name, pages); print(name, "pages:", n, imgs)
print("OK")
