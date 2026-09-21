// Builds the long-form sample docs (returns plain objects, nothing is written here).
(uid, nextDocNo) => {
  const now = new Date().toISOString();
  const base = { sample: true, createdBy: uid, createdAt: now };
  const rid = () => Math.random().toString(36).slice(2, 10);
  const d = (y, m, day) => `${y}-${String(m).padStart(2, '0')}-${String(day).padStart(2, '0')}`;

  const company = { ...base, name: '[ตัวอย่าง] บริษัท เอสไอ เน็ตเวิร์ค โซลูชั่นส์ จำกัด', address: '88/8 ถนนรัชดาภิเษก แขวงดินแดง เขตดินแดง กรุงเทพฯ 10400', phone: '02-555-0101', taxId: '0105561000888', logoBase64: '' };
  const customer = { ...base, name: '[ตัวอย่าง] องค์การบริหารส่วนจังหวัดตัวอย่าง', type: 'gov', taxId: '', address: '1 ถนนกลางเมือง ตำบลในเมือง อำเภอเมือง จังหวัดตัวอย่าง 10000', contactName: 'คุณสมศักดิ์ ใจดี', contactPhone: '081-234-5678' };

  // ---- equipment catalogue used by both documents ----
  const cat = [
    ['C9200-24P', 'Cisco', 'Catalyst 9200 24-port PoE+', 'Switch', 'FOC2210'],
    ['C9300-48P', 'Cisco', 'Catalyst 9300 48-port PoE+', 'Switch', 'FCW2311'],
    ['IE-3300-8T2S', 'Cisco', 'IE-3300 Industrial Ethernet Switch', 'Industrial', 'FDO2401'],
    ['ISR1100-4G', 'Cisco', 'ISR 1100 4-port Gigabit Router', 'Router', 'FGL2402'],
    ['RB4011', 'MikroTik', 'RB4011iGS+RM Router', 'Router', 'MT4011'],
    ['CCR2004', 'MikroTik', 'Cloud Core Router CCR2004-16G-2S+', 'Router', 'MT2004'],
    ['DS-2CD2143G2-I', 'Hikvision', 'AcuSense Dome IP Camera 4MP', 'Camera', 'HK2143'],
    ['DS-2CD2T47G2-L', 'Hikvision', 'ColorVu Bullet IP Camera 4MP', 'Camera', 'HK2T47'],
    ['DS-7608NI-K2', 'Hikvision', 'Network Video Recorder 8 ช่อง', 'NVR', 'HK7608'],
    ['DS-7732NI-K4', 'Hikvision', 'Network Video Recorder 32 ช่อง', 'NVR', 'HK7732'],
    ['FG-100F', 'Fortinet', 'FortiGate 100F Firewall', 'Firewall', 'FT100F'],
    ['FAP-231F', 'Fortinet', 'FortiAP 231F Wi-Fi 6 Access Point', 'Access Point', 'FP231F'],
    ['OPT7010', 'Dell', 'OptiPlex 7010 (ชุดคอมพิวเตอร์)', 'Computer Set', 'DL7010'],
    ['PRO400G9', 'HP', 'ProDesk 400 G9 (ชุดคอมพิวเตอร์)', 'Computer Set', 'HP400G'],
    ['SCALANCE-XB008', 'Siemens', 'SCALANCE XB008 Unmanaged Switch', 'Industrial', 'SX8008'],
    ['UPS-3KVA', 'APC', 'Smart-UPS 3000VA Rack', 'UPS', 'APC3K0'],
  ];
  const mkItem = (i, status, serialMax) => {
    const c = cat[i % cat.length];
    const qty = 1 + ((i * 7) % 9);
    const nSer = Math.min(qty, serialMax, 1 + (i % 6));
    const serials = Array.from({ length: nSer }, (_, k) => `${c[4]}${String(1000 + i * 10 + k)}`);
    return { rid: rid(), whId: '', part: c[0], brand: c[1], name: c[2], type: c[3], serials, qty, status };
  };

  // ---- Project: long Action Plan (12 topics x 4 sub-steps) + 26 equipment lines ----
  const topics = [
    ['ประชุมเริ่มโครงการและวางแผนงาน', ['ประชุมเปิดโครงการร่วมกับผู้ว่าจ้าง', 'จัดทำแผนงานและตารางเวลาโดยละเอียด', 'แต่งตั้งคณะทำงานและกำหนดผู้รับผิดชอบ', 'ส่งมอบแผนงานให้ผู้ว่าจ้างอนุมัติ']],
    ['สำรวจพื้นที่และออกแบบระบบ', ['สำรวจอาคารที่ว่าการและสถานีย่อย 12 แห่ง', 'วัดระยะและตรวจสอบเส้นทางเดินสายสัญญาณ', 'ออกแบบผังเครือข่ายและผังกล้องวงจรปิด', 'ส่งแบบให้ผู้ว่าจ้างตรวจรับและอนุมัติแก้ไข']],
    ['จัดซื้อและนำเข้าอุปกรณ์', ['ออกใบสั่งซื้ออุปกรณ์เครือข่ายจากผู้ผลิต', 'ออกใบสั่งซื้อกล้องและเครื่องบันทึกภาพ', 'ติดตามการขนส่งและพิธีการนำเข้า', 'ตรวจรับอุปกรณ์เข้าคลังและบันทึก Serial Number']],
    ['เตรียมอุปกรณ์และตั้งค่าเบื้องต้น', ['ติดตั้ง Firmware และอัปเดตเวอร์ชันล่าสุด', 'ตั้งค่า VLAN, IP Address ตามแบบที่อนุมัติ', 'ตั้งค่ากล้องและเครื่องบันทึกภาพล่วงหน้า', 'ทดสอบอุปกรณ์ทั้งหมดในห้องปฏิบัติการ']],
    ['งานโครงสร้างพื้นฐาน (ท่อร้อยสายและตู้ Rack)', ['ติดตั้งท่อร้อยสายและรางสายไฟตามเส้นทาง', 'ติดตั้งตู้ Rack และระบบสำรองไฟ UPS', 'ตรวจสอบระบบไฟฟ้าและระบบกราวด์', 'ตรวจรับงานโครงสร้างพื้นฐานร่วมกับผู้ว่าจ้าง']],
    ['เดินสายสัญญาณและเข้าหัวสาย', ['เดินสาย UTP CAT6 ภายในอาคาร', 'เดินสายไฟเบอร์ออฟติกระหว่างอาคาร', 'เข้าหัวสายและทดสอบสายด้วย Fluke', 'จัดทำป้ายกำกับสายและเอกสารผลทดสอบ']],
    ['ติดตั้งอุปกรณ์เครือข่าย', ['ติดตั้ง Core Switch และ Distribution Switch', 'ติดตั้ง Access Switch ทุกชั้นทุกอาคาร', 'ติดตั้ง Firewall และเราเตอร์เชื่อมต่ออินเทอร์เน็ต', 'ติดตั้ง Access Point ระบบ Wi-Fi ภายในอาคาร']],
    ['ติดตั้งระบบกล้องวงจรปิด', ['ติดตั้งกล้องภายในอาคารและทางเข้าออก', 'ติดตั้งกล้องภายนอกและเสาสูง', 'ติดตั้งเครื่องบันทึกภาพและพื้นที่จัดเก็บข้อมูล', 'ปรับมุมกล้องและตั้งค่าการบันทึกภาพ']],
    ['ตั้งค่าระบบและเชื่อมต่อ', ['ตั้งค่า Routing และ Firewall Policy', 'ตั้งค่าระบบ Wi-Fi และการยืนยันตัวตนผู้ใช้', 'เชื่อมต่อระบบกล้องกับห้องควบคุมกลาง', 'ตั้งค่าระบบสำรองข้อมูลและระบบแจ้งเตือน']],
    ['ทดสอบระบบและแก้ไขข้อบกพร่อง', ['ทดสอบประสิทธิภาพเครือข่ายทุกจุด', 'ทดสอบการทำงานของกล้องและการเรียกดูย้อนหลัง', 'ทดสอบระบบสำรองและการสลับเส้นทาง', 'แก้ไขข้อบกพร่องที่พบและทดสอบซ้ำ']],
    ['อบรมและส่งมอบงาน', ['จัดอบรมผู้ดูแลระบบของหน่วยงาน', 'จัดอบรมผู้ใช้งานทั่วไป', 'จัดทำคู่มือการใช้งานและเอกสารส่งมอบ', 'ตรวจรับงานและลงนามส่งมอบงวดสุดท้าย']],
    ['บริการหลังการขายและรับประกัน', ['เริ่มระยะเวลารับประกันและแจ้งช่องทางติดต่อ', 'ตรวจเช็กระบบตามรอบรายเดือน', 'แก้ไขปัญหาตามใบแจ้งซ่อม', 'สรุปผลการดำเนินงานปีแรก']],
  ];
  const owners = ['ผู้จัดการ', 'ทีมติดตั้ง', 'ติดตั้งโปรแกรม', 'ฝ่ายขาย', 'ลูกค้า'];
  // topic i starts about 12 days after the previous one; sub-steps 4-8 days each. Steps before today are ticked, the two right after are late / due soon.
  const today = new Date(); today.setHours(0, 0, 0, 0);
  const iso = dt => `${dt.getFullYear()}-${String(dt.getMonth() + 1).padStart(2, '0')}-${String(dt.getDate()).padStart(2, '0')}`;
  const addDays = (dt, n) => { const x = new Date(dt); x.setDate(x.getDate() + n); return x; };
  let cursor = new Date(2026, 8, 1);   // 1 Sep 2026
  const plan = topics.map(([title, subs], i) => {
    const subRows = subs.map((st, j) => {
      const start = addDays(cursor, j * 5), end = addDays(start, 3 + ((i + j) % 4));
      return { title: st, owner: owners[(i + j) % owners.length], start: iso(start), end: iso(end), done: end < addDays(today, -3) };
    });
    cursor = addDays(cursor, 14);
    return { title: `${title}`, owner: owners[i % owners.length], start: subRows[0].start, end: subRows[subRows.length - 1].end, done: subRows.every(s => s.done), subs: subRows };
  });
  const lastEnd = plan[plan.length - 1].end;
  const project = {
    ...base, jobType: 'project', docNo: nextDocNo('PJ'), name: '[ตัวอย่าง] โครงการติดตั้งระบบเครือข่ายและกล้องวงจรปิด อบจ. (ข้อมูลยาว)',
    customerId: '', customerName: customer.name, companyId: '', contractNo: 'อบจ.ตย. 69/0421',
    startDate: '2026-09-01', endDate: lastEnd > '2027-03-31' ? lastEnd : '2027-03-31',
    notes: 'ส่งมอบเป็น 3 งวด งวดที่ 1 ภายใน 60 วันนับจากวันลงนามสัญญา', installLocation: 'ที่ว่าการ อบจ. และสถานีย่อย 12 แห่งทั่วจังหวัด', warrantyMonths: 24,
    items: Array.from({ length: 26 }, (_, i) => mkItem(i, i < 8 ? 'done' : 'pending', 6)), plan,
  };

  // ---- Sale: 30 equipment lines ----
  const sale = {
    ...base, jobType: 'sale', docNo: nextDocNo('SO'), name: '[ตัวอย่าง] ขายอุปกรณ์เครือข่ายและคอมพิวเตอร์ชุดใหญ่ (ข้อมูลยาว)',
    customerId: '', customerName: customer.name, companyId: '', startDate: '2026-09-15', endDate: '2026-09-15',
    installLocation: 'คลังพัสดุ อบจ. อาคาร 2 ชั้น 1', warrantyMonths: 12, notes: 'ส่งมอบครั้งเดียว ตรวจรับที่คลังพัสดุ',
    items: Array.from({ length: 30 }, (_, i) => mkItem(i + 5, i < 12 ? 'done' : 'pending', 6)),
  };
  return { company, customer, project, sale };
}
