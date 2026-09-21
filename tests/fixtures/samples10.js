// Builds the mixed sample set: 10 companies, 10 customers, 10 warehouse items, 10 projects + 10 sales, 10 invites, 10 trash rows.
// Pure data (nothing is written here). Warehouse stock is kept consistent with the lines marked done (quantity, serials and history).
(uid, uname, today, nextDocNo) => {
  const now = new Date().toISOString();
  const base = { sample: true, createdBy: uid, createdAt: now };
  const rid = () => Math.random().toString(36).slice(2, 10);
  const pad = n => String(n).padStart(2, '0');
  const iso = dt => `${dt.getFullYear()}-${pad(dt.getMonth() + 1)}-${pad(dt.getDate())}`;
  const T = new Date(today + 'T00:00:00');
  const off = n => { const x = new Date(T); x.setDate(x.getDate() + n); return iso(x); };
  const pick = (arr, i) => arr[i % arr.length];

  // ---------------- companies (letterheads) ----------------
  const companyNames = ['บียู เอบีบี เทคโนโลยี', 'พีเอ็ม ซัพพอร์ต', 'เน็ตเวิร์ค โปร โซลูชั่น', 'ไอที เซฟตี้ เอ็นจิเนียริ่ง', 'สมาร์ท ซิสเต็ม เซอร์วิส', 'ดาต้า เซ็นเตอร์ คอนซัลติ้ง', 'วิชั่น ซีซีทีวี', 'เอ็กซ์เพรส เทลคอม', 'ออลอินวัน เทคโนโลยี', 'พาวเวอร์ แอนด์ เน็ต'];
  const companies = companyNames.map((n, i) => ({ ...base, name: `[ตัวอย่าง] บริษัท ${n} จำกัด`, address: `${10 + i * 7}/${i + 1} ถนน${pick(['สุขุมวิท', 'รัชดาภิเษก', 'พระราม 9', 'ลาดพร้าว', 'บางนา-ตราด'], i)} แขวง${pick(['คลองเตย', 'ดินแดง', 'ห้วยขวาง', 'วังทองหลาง', 'บางนา'], i)} กรุงเทพฯ 10${100 + i * 30}`,
    phone: `02-${500 + i * 13}-${1000 + i * 111}`, taxId: `01055610${String(10000 + i * 37).slice(0, 5)}`, logoBase64: '', _logo: i % 2 === 0 }));

  // ---------------- customers ----------------
  const govs = ['กรมทางหลวง', 'เทศบาลนครเชียงใหม่', 'การไฟฟ้านครหลวง', 'องค์การบริหารส่วนจังหวัดขอนแก่น', 'โรงพยาบาลศูนย์ตัวอย่าง'];
  const privs = ['โรงแรมริเวอร์ไซด์ แกรนด์', 'บริษัท สยามอินดัสเทรียล จำกัด', 'บริษัท ไทยลอจิสติกส์ จำกัด', 'ห้างสรรพสินค้าเซ็นทรัลตัวอย่าง', 'บริษัท โรงงานอาหารสยาม จำกัด'];
  const customers = [...govs.map((n, i) => ({ ...base, name: `[ตัวอย่าง] ${n}`, type: 'gov', taxId: '', address: `${100 + i} หมู่ ${i + 1} ตำบลตัวอย่าง อำเภอเมือง จังหวัด${pick(['เชียงใหม่', 'ขอนแก่น', 'กรุงเทพฯ', 'ระยอง', 'ภูเก็ต'], i)} 1${i}000`, contactName: `คุณ${pick(['สมชาย', 'วิภา', 'นรินทร์', 'อรทัย', 'ประเสริฐ'], i)} ${pick(['ใจดี', 'รักงาน', 'มั่นคง', 'ศรีสุข', 'พัฒนา'], i)}`, contactPhone: `08${i}-234-56${70 + i}` })),
    ...privs.map((n, i) => ({ ...base, name: `[ตัวอย่าง] ${n}`, type: 'private', taxId: `01055${String(60000 + i * 111)}${i}`, address: `${20 + i} ซอยตัวอย่าง ${i + 1} ถนนเอกชน แขวง${pick(['ปทุมวัน', 'บางรัก', 'สาทร', 'จตุจักร', 'บางกะปิ'], i)} กรุงเทพฯ 10${i}00`, contactName: `คุณ${pick(['ธนา', 'มาลี', 'กิตติ', 'สุนีย์', 'ภาสกร'], i)} ${pick(['วงศ์ดี', 'แสงทอง', 'บุญมา', 'พึ่งพา', 'เจริญ'], i)}`, contactPhone: `09${i}-765-43${10 + i}` }))];

  // ---------------- warehouse ----------------
  const whDefs = [
    ['C9200-24P', 'Cisco', 'Switch', 'Catalyst 9200 24-port PoE+', 12, 'FOC22'], ['C9300-48P', 'Cisco', 'Switch', 'Catalyst 9300 48-port PoE+', 6, 'FCW23'],
    ['RB4011', 'MikroTik', 'Router', 'RB4011iGS+RM Router', 15, 'MT401'], ['DS-2CD2143G2-I', 'Hikvision', 'Camera', 'AcuSense Dome IP Camera 4MP', 40, 'HK214'],
    ['DS-7608NI-K2', 'Hikvision', 'NVR', 'Network Video Recorder 8 ช่อง', 8, 'HK760'], ['FG-100F', 'Fortinet', 'Firewall', 'FortiGate 100F Firewall', 5, 'FT100'],
    ['FAP-231F', 'Fortinet', 'Access Point', 'FortiAP 231F Wi-Fi 6', 20, 'FP231'], ['OPT7010', 'Dell', 'Computer Set', 'OptiPlex 7010 (ชุดคอมพิวเตอร์)', 10, 'DL701'],
    ['SCALANCE-XB008', 'Siemens', 'Industrial', 'SCALANCE XB008 Unmanaged Switch', 14, 'SX800'], ['UPS-3KVA', 'APC', 'UPS', 'Smart-UPS 3000VA Rack', 4, 'APC3K'] ];
  const wh = whDefs.map(([part, brand, type, name, qty, pre], i) => ({ id: '', doc: { ...base, part, brand, type, name, quantity: qty, serials: i % 3 === 2 ? [] : Array.from({ length: qty }, (_, k) => `${pre}${String(1000 + k)}`), note: i % 4 === 0 ? 'รับเข้าล็อตแรก ตรวจรับแล้ว' : '', history: [] } }));

  // ---------------- projects & sales ----------------
  const specs = [];   // [jobType, name, customerIdx, companyIdx, startOff, endOff|null, warrantyMonths, planStyle, lines]
  const P = (name, ci, coi, s, e, w, plan, lines, extra) => specs.push({ job: 'project', name, ci, coi, s, e, w, plan, lines, ...(extra || {}) });
  const S = (name, ci, coi, s, w, lines, extra) => specs.push({ job: 'sale', name, ci, coi, s, w, lines, ...(extra || {}) });
  // lines: [whIdx, qty, status]
  P('ติดตั้งระบบ CCTV ทางหลวงสายหลัก (แผนยาว)', 0, 0, -20, 160, 24, 'long', [[3, 10, 'done'], [4, 2, 'done'], [0, 3, 'pending'], [5, 1, 'pending']]);
  P('ปรับปรุงเครือข่ายเทศบาลนครเชียงใหม่ (เริ่มในอนาคต)', 1, 1, 12, 130, 12, 'normal', [[1, 2, 'pending'], [6, 6, 'pending']]);
  P('ระบบ Wi-Fi โรงพยาบาลศูนย์ (สัญญาใกล้สิ้นสุด)', 4, 2, -140, 18, 12, 'late', [[6, 8, 'done'], [0, 2, 'done']]);
  P('Server Room ไทยลอจิสติกส์ (ยังไม่มีแผน)', 7, 3, -5, 90, 12, 'none', [[9, 1, 'pending'], [5, 1, 'pending']]);
  P('โครงการระบบไฟฟ้าอัจฉริยะ (สิ้นสุดแล้ว)', 2, 4, -220, -40, 24, 'done', [[8, 6, 'done'], [2, 3, 'done']]);
  P('ระบบกล้องวงจรปิดสถานี (ใกล้หมดประกัน)', 3, 5, -520, -345, 12, 'done', [[3, 6, 'done'], [4, 1, 'done']]);
  P('เครือข่ายโรงงานอาหารสยาม (มีขั้นเลยกำหนด)', 9, 6, -45, 75, 12, 'late', [[2, 2, 'done'], [0, 2, 'pending']]);
  P('ระบบควบคุมอาคาร รพ. ตัวอย่าง', 4, 7, 3, 200, 36, 'normal', [[7, 4, 'pending']]);
  P('ติดตั้ง Access Point โรงแรมริเวอร์ไซด์', 5, 8, -60, -3, 12, 'done', [[6, 10, 'done'], [1, 1, 'done']]);
  P('ย้ายศูนย์ข้อมูลองค์การบริหารส่วนจังหวัด', 3, 9, -10, 60, 18, 'normal', [[5, 2, 'pending'], [9, 2, 'pending'], [1, 2, 'pending']]);
  S('ขายสวิตช์และเราเตอร์ให้ กฟน. (ส่งครบแล้ว)', 2, 0, -30, 12, [[0, 2, 'done'], [2, 2, 'done']]);
  S('ขายชุดคอมพิวเตอร์ให้โรงแรม (ส่งบางส่วน)', 5, 1, -12, 12, [[7, 3, 'done'], [7, 2, 'pending']]);
  S('ขายเราเตอร์อุตสาหกรรม (รอส่งของ)', 6, 2, -2, 12, [[8, 4, 'pending']]);
  S('ขายกล้องวงจรปิด 8 ตัว (ประกันใกล้หมด)', 8, 3, -350, 12, [[3, 8, 'done']]);
  S('ขาย UPS ห้อง Server (ไม่มีรายการอุปกรณ์)', 7, 4, -1, 12, []);
  S('ขายไฟร์วอลล์ให้เทศบาล', 1, 5, -90, 24, [[5, 1, 'done']]);
  S('ขาย NVR + กล้องชุดใหญ่ (ประกันหมดแล้ว)', 0, 6, -420, 12, [[4, 2, 'done'], [3, 4, 'done']], { });
  S('ขาย Access Point 6 ตัว (รอส่งบางรายการ)', 9, 7, -7, 12, [[6, 6, 'pending']]);
  S('ขายสวิตช์ Catalyst โรงพยาบาล', 4, 8, -18, 36, [[1, 1, 'done'], [0, 1, 'pending']]);
  S('ขายอุปกรณ์เครือข่ายชุดเล็ก (มีเลข PO)', 6, 9, -4, 12, [[2, 1, 'pending'], [8, 2, 'pending']], { po: 'PO-2569-0421' });

  const planOf = spec => {
    const mk = (title, subs, owner, start, len, done) => ({ title, owner, start: off(start), end: off(start + len), done: !!done, subs: (subs || []).map(([t, o, s, l, d]) => ({ title: t, owner: o, start: off(s), end: off(s + l), done: !!d })) });
    const s0 = spec.s;
    if (spec.plan === 'none') return [];
    if (spec.plan === 'done') return [mk('เตรียมงานและสำรวจ', [['สำรวจหน้างาน', 'ทีมติดตั้ง', s0, 5, true], ['ออกแบบระบบ', 'ผู้จัดการ', s0 + 6, 8, true]], 'ผู้จัดการ', s0, 14, true),
      mk('ติดตั้งและทดสอบ', [['ติดตั้งอุปกรณ์', 'ทีมติดตั้ง', s0 + 20, 30, true], ['ทดสอบระบบ', 'ติดตั้งโปรแกรม', s0 + 52, 10, true]], 'ทีมติดตั้ง', s0 + 20, 42, true),
      mk('ส่งมอบงาน', [], 'ลูกค้า', s0 + 70, 5, true)];
    if (spec.plan === 'late') return [mk('เตรียมงาน', [['สำรวจหน้างาน', 'ทีมติดตั้ง', s0, 4, true], ['ทำแบบและขออนุมัติ', 'ผู้จัดการ', s0 + 5, 9, true]], 'ผู้จัดการ', s0, 14, true),
      mk('จัดซื้ออุปกรณ์', [['ออกใบสั่งซื้อ', 'ฝ่ายขาย', s0 + 15, 5, false], ['ติดตามการส่งมอบ', 'ฝ่ายขาย', s0 + 21, 10, false]], 'ฝ่ายขาย', s0 + 15, 16, false),
      mk('ติดตั้งและทดสอบ', [['ติดตั้ง', 'ทีมติดตั้ง', spec.s + 40, 20, false], ['ทดสอบ', 'ติดตั้งโปรแกรม', spec.s + 62, 6, false]], 'ทีมติดตั้ง', spec.s + 40, 28, false)];
    return [mk('ประชุมเริ่มโครงการ', [['ประชุมเปิดโครงการ', 'ผู้จัดการ', s0, 2, false]], 'ผู้จัดการ', s0, 3, false),
      mk('เตรียมงานและจัดซื้อ', [['สำรวจ', 'ทีมติดตั้ง', s0 + 4, 6, false], ['สั่งซื้อ', 'ฝ่ายขาย', s0 + 11, 8, false]], 'ฝ่ายขาย', s0 + 4, 15, false),
      mk('ติดตั้ง', [['ติดตั้งอุปกรณ์', 'ทีมติดตั้ง', s0 + 25, 20, false], ['ตั้งค่าโปรแกรม', 'ติดตั้งโปรแกรม', s0 + 46, 10, false]], 'ทีมติดตั้ง', s0 + 25, 31, false),
      mk('อบรมและส่งมอบ', [], 'ลูกค้า', s0 + 60, 5, false)];
  };

  const projects = [];
  specs.forEach((sp, i) => {
    const id = 'sample_' + rid();
    const cu = customers[sp.ci], co = companies[sp.coi];
    const start = off(sp.s), end = sp.job === 'sale' ? start : off(sp.e);
    const items = sp.lines.map(([wi, qty, status]) => {
      const w = wh[wi].doc;
      let serials = [];
      if (status === 'done'){
        const take = Math.min(qty, w.quantity);
        if (w.serials.length) serials = w.serials.splice(0, Math.min(take, w.serials.length));
        w.quantity -= take;
        w.history.push({ at: new Date(T.getTime() + sp.s * 864e5 + 36e5).toISOString(), type: 'out', qty: take, serials, projectId: id, docNo: '', projectName: `[ตัวอย่าง] ${sp.name}`, jobType: sp.job, by: uid, byName: uname });
      }
      return { rid: rid(), whId: `#${wi}`, part: w.part, brand: w.brand, name: w.name, type: w.type, serials, qty, status };
    });
    projects.push({ id, wiRefs: sp.lines.map(l => l[0]), doc: { ...base, jobType: sp.job, docNo: '', name: `[ตัวอย่าง] ${sp.name}`, customerId: '#c' + sp.ci, customerName: cu.name, companyId: '#co' + sp.coi,
      contractNo: sp.job === 'project' ? `สญ.${2569}/${String(i + 1).padStart(3, '0')}` : '', installmentNo: sp.job === 'project' && i % 3 === 0 ? `งวดที่ ${1 + (i % 4)}` : '', poNo: sp.po || (i % 4 === 1 ? `PO-${7000 + i}` : ''), startDate: start, endDate: end,
      installLocation: sp.job === 'sale' ? `คลังพัสดุ ${cu.name.replace('[ตัวอย่าง] ', '')}` : `อาคารหลัก ${cu.name.replace('[ตัวอย่าง] ', '')}`, warrantyMonths: sp.w, notes: i % 3 === 0 ? 'ข้อมูลตัวอย่างสำหรับทดสอบระบบ' : '',
      items, ...(sp.job === 'project' ? { plan: planOf(sp) } : {}) } });
  });
  // the first project also gets the long plan (12 topics x 4 steps) and a long equipment list, for testing multi-page printouts
  const long = (() => {
    const topics = ['ประชุมเริ่มโครงการ', 'สำรวจพื้นที่', 'ออกแบบระบบ', 'จัดซื้ออุปกรณ์', 'เตรียมอุปกรณ์', 'งานโครงสร้างพื้นฐาน', 'เดินสายสัญญาณ', 'ติดตั้งเครือข่าย', 'ติดตั้งกล้อง', 'ตั้งค่าระบบ', 'ทดสอบระบบ', 'อบรมและส่งมอบ'];
    let c = -20;
    return topics.map((t, i) => { const subs = [0, 1, 2, 3].map(j => { const s = c + j * 5, e = s + 3 + ((i + j) % 4); return { title: `${t} — ขั้นตอนที่ ${j + 1}`, owner: pick(['ผู้จัดการ', 'ทีมติดตั้ง', 'ติดตั้งโปรแกรม', 'ฝ่ายขาย', 'ลูกค้า'], i + j), start: off(s), end: off(e), done: e < -3 }; });
      c += 13; return { title: t, owner: pick(['ผู้จัดการ', 'ทีมติดตั้ง', 'ฝ่ายขาย'], i), start: subs[0].start, end: subs[3].end, done: subs.every(x => x.done), subs }; });
  })();
  projects[0].doc.plan = long;
  projects[0].doc.endDate = long[long.length - 1].end;
  for (let k = 0; k < 18; k++){   // extra pending lines that are not linked to a warehouse item (typed-in equipment)
    const w = wh[k % wh.length].doc;
    projects[0].doc.items.push({ rid: rid(), whId: '', part: w.part, brand: w.brand, name: w.name, type: w.type, serials: Array.from({ length: 1 + (k % 4) }, (_, s) => `X${w.part.slice(0, 3)}${k}${s}`), qty: 1 + (k % 5), status: 'pending' });
  }

  // ---------------- invites (Users page) ----------------
  const invites = ['สมชาย ขายเก่ง', 'วิภา ผู้ดูแลโครงการ', 'นรินทร์ ทีมติดตั้ง', 'อรทัย ฝ่ายบัญชี', 'ประเสริฐ ช่างเทคนิค', 'มาลี ฝ่ายขาย', 'กิตติ วิศวกร', 'สุนีย์ ธุรการ', 'ภาสกร ผู้จัดการโครงการ', 'ธนา ฝ่ายจัดซื้อ'].map((n, i) => ({ email: `sample.user${i + 1}@example.com`, doc: { name: `[ตัวอย่าง] ${n}`, role: i === 8 ? 'admin' : 'user', sample: true } }));

  // ---------------- trash (soft-deleted rows of every kind) ----------------
  const del = { deletedAt: new Date(T.getTime() - 3 * 864e5).toISOString(), deletedBy: uid };
  const trash = [
    ['pm_customers', { ...base, ...del, name: '[ตัวอย่าง] ลูกค้าที่ถูกลบ 1', type: 'private', taxId: '0105500000001', address: '-', contactName: '-', contactPhone: '-' }],
    ['pm_customers', { ...base, ...del, name: '[ตัวอย่าง] ลูกค้าที่ถูกลบ 2 (หน่วยงานรัฐ)', type: 'gov', taxId: '', address: '-', contactName: '-', contactPhone: '-' }],
    ['pm_customers', { ...base, ...del, name: '[ตัวอย่าง] ลูกค้าที่ถูกลบ 3', type: 'private', taxId: '0105500000003', address: '-', contactName: '-', contactPhone: '-' }],
    ['pm_warehouse', { ...base, ...del, part: 'OLD-001', brand: 'Generic', type: 'Switch', name: '[ตัวอย่าง] อุปกรณ์ที่ถูกลบ 1', quantity: 1, serials: ['OLD-SN-1'], note: '', history: [] }],
    ['pm_warehouse', { ...base, ...del, part: 'OLD-002', brand: 'Generic', type: 'Router', name: '[ตัวอย่าง] อุปกรณ์ที่ถูกลบ 2', quantity: 3, serials: [], note: '', history: [] }],
    ['pm_projects', { ...base, ...del, jobType: 'project', docNo: '', name: '[ตัวอย่าง] โครงการที่ถูกลบ 1', customerName: '[ตัวอย่าง] ลูกค้าที่ถูกลบ 1', startDate: off(-90), endDate: off(-30), items: [], plan: [] }],
    ['pm_projects', { ...base, ...del, jobType: 'sale', docNo: '', name: '[ตัวอย่าง] งานขายที่ถูกลบ 2', customerName: '[ตัวอย่าง] ลูกค้าที่ถูกลบ 2', startDate: off(-60), endDate: off(-60), items: [] }],
    ['pm_projects', { ...base, ...del, jobType: 'project', docNo: '', name: '[ตัวอย่าง] โครงการที่ถูกลบ 3', customerName: '[ตัวอย่าง] ลูกค้าที่ถูกลบ 3', startDate: off(-120), endDate: off(-50), items: [], plan: [] }],
    ['pm_companies', { ...base, ...del, name: '[ตัวอย่าง] บริษัทที่ถูกลบ จำกัด', address: '-', phone: '-', taxId: '', logoBase64: '' }]
  ];
  return { companies, customers, wh, projects, invites, trash, docNo: nextDocNo };
}
