// Runs inside the app page: writes the sample set built by samples10.js. Argument: [generatorSource, todayISO]
async ([gen, today]) => {
  const uid = currentUserUid, uname = currentUserName || currentUserEmail || '';
  const g = eval(gen)(uid, uname, today, null);
  const logo = (i, ch) => { const cv = document.createElement('canvas'); cv.width = cv.height = 96; const cx = cv.getContext('2d');
    cx.fillStyle = ['#3B82F6', '#22B573', '#FF9F43', '#8B7CF6', '#F0618B'][i % 5]; cx.fillRect(0, 0, 96, 96); cx.fillStyle = '#fff'; cx.font = 'bold 44px Arial'; cx.textAlign = 'center'; cx.fillText(ch, 48, 64); return cv.toDataURL('image/png'); };
  const out = { companies: 0, customers: 0, warehouse: 0, projects: 0, sales: 0, invites: 0, trash: 0 };
  const coIds = [], cuIds = [];
  for (const [i, c] of g.companies.entries()){ const { _logo, ...doc } = c; if (_logo) doc.logoBase64 = logo(i, String.fromCharCode(65 + i)); coIds.push((await db.collection('pm_companies').add(doc)).id); out.companies++; }
  for (const c of g.customers){ cuIds.push((await db.collection('pm_customers').add(c)).id); out.customers++; }
  const whRefs = g.wh.map(() => db.collection('pm_warehouse').doc());
  // document numbers continue after whatever the counters / existing docs already hold
  const t = new Date(today + 'T00:00:00'), day = `${t.getFullYear()}${String(t.getMonth() + 1).padStart(2, '0')}${String(t.getDate()).padStart(2, '0')}`;
  const start = {};
  for (const pre of ['SO', 'PJ']){
    let n = 0; const ctr = await db.collection('pm_counters').doc(pre + day).get({ source: 'server' }); if (ctr.exists) n = Number(ctr.data().n) || 0;
    (await db.collection('pm_projects').get({ source: 'server' })).docs.forEach(d => { const m = new RegExp('^' + pre + day + '-(\\d+)$').exec(d.data().docNo || ''); if (m) n = Math.max(n, Number(m[1])); });
    start[pre] = n;
  }
  for (const p of g.projects){
    const pre = p.doc.jobType === 'sale' ? 'SO' : 'PJ'; start[pre]++;
    p.doc.docNo = `${pre}${day}-${String(start[pre]).padStart(3, '0')}`;
    p.doc.customerId = cuIds[Number(p.doc.customerId.slice(2))]; p.doc.companyId = coIds[Number(p.doc.companyId.slice(3))];
    p.doc.items.forEach(it => { if (it.whId && it.whId[0] === '#') it.whId = whRefs[Number(it.whId.slice(1))].id; });
    g.wh.forEach(w => w.doc.history.forEach(h => { if (h.projectId === p.id) h.docNo = p.doc.docNo; }));
  }
  let batch = db.batch(), n = 0;
  const flush = async () => { if (n) { await batch.commit(); batch = db.batch(); n = 0; } };
  const put = async (ref, doc) => { batch.set(ref, doc); if (++n >= 60) await flush(); };
  for (const [i, w] of g.wh.entries()){ await put(whRefs[i], w.doc); out.warehouse++; }
  for (const p of g.projects){ await put(db.collection('pm_projects').doc(p.id), p.doc); p.doc.jobType === 'sale' ? out.sales++ : out.projects++; }
  for (const inv of g.invites){ await put(db.collection('pm_pendingRoles').doc(inv.email), inv.doc); out.invites++; }
  for (const [col, doc] of g.trash){ await put(db.collection(col).doc(), doc); out.trash++; }
  await flush();
  out.docNos = g.projects.map(p => p.doc.docNo);
  return out;
}
