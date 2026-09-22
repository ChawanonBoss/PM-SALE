# PM-SALE - working notes

Single-file app: everything lives in `index.html` (HTML + CSS + JS). Deployed by pushing to `main` (GitHub Pages). Firebase project `bu-abb`, collections `pm_*`.

## Rules of the road
- **Version**: bump `APP_VERSION` on every push. Not structural -> last digit; structural (new page/collection/data field) -> middle digit, last reset to 0.
- **Firestore rules** live in the Console, not in this repo. `firestore.rules` here is the PM-SALE block only; the full file to paste is `Web/firestore.rules` in the BU-ABB working copy. Client queries and rules change together
  (a non-admin's listeners use `.where('createdBy','==',uid)`; `pm_files` queries add `ownerId`). Always tell the user to publish the rules after changing them, and re-test with throw-away `pmtest.*@example.com` accounts.
- Reply in Thai, short. Decide instead of asking when a sensible default exists; confirm before destructive actions on real data.
- Patch `index.html` with small Python scripts that assert exact match counts; avoid bash heredocs with mixed quotes (write files with the editor tools). After a big edit run `python tests/static_test.py` (a bad replace once left `class="tab-panel"...` visible on the dashboard).

## Data model (short)
`pm_projects` (`jobType` sale | project; items[] link to `pm_warehouse`; plan[] for projects; `docNo`, `contractNo`, `poNo`; project installments: `installmentTotal`, `installmentNo` (last delivered, printed as "3/4"), `deliveries[]` written by the "ส่งงาน" dialog; the โครงการ list's own "งวดงาน" column/filter reads `currentInstallmentStage()` - the next undelivered installment, or the last one once everything is in - not `installmentNo` directly), `pm_customers`, `pm_companies`, `pm_warehouse` (quantity, serials[], history[] capped 500),
`pm_counters` (SO/PJ + yyyymmdd -> n; the admin session raises them via `syncDocCounters()`), `pm_catalogs` + `pm_catalogChunks`, `pm_files` (attachments, base64, <=650 KB each, 8 per project), `pm_photos` (handover photos, base64 <=900 KB each - see "Handover photos" below), `pm_users` (`status` approved|pending|rejected; no status = approved),
`pm_pendingRoles` (invites), `pm_auditLog`/`pm_errorLog` (immutable). Soft delete = `deletedAt`; the Trash tab (admin) restores / purges.

## Menus
ซื้อขาย (`tab-sales`, `#salesBody`) and โครงการ (`tab-projects`, `#projectsBody`) are separate menus over the same `pm_projects` collection; `renderJobs(kind)` draws both. There is no job-type select/filter/column any more: `openProjectForm(id, kind)` sets the hidden `#prjJobType` from the menu.
The Dashboard switch, the Warranty page and the Customer pop-up still mix both kinds.

## โครงการ list: "สถานะงาน" status columns + column picker
Three read-only, never-clickable `<input type="checkbox" disabled>` columns under one grouped `<thead>` header ("สถานะงาน" spanning "แผนการดำเนินงาน" /
"รูปภาพอุปกรณ์" / "รูปภาพงานติดตั้ง") show whether a project's plan (`(p.plan||[]).length>0`) and each photo set (`p.photoCounts.equipment`/`.install > 0`)
have actually been saved - there is no way to tick them by hand, only by really saving that data. `computeColumnLabels()` (near `labelCardCells`) walks the
2-row `<thead>` grid so the mobile card view still labels each cell correctly. `#projectsColumnsBtn` opens `#projectColumnsModal`, a checkbox list backed by
`PROJECT_COLUMNS` / `projectColumnPrefs` (localStorage `pm-sale-project-columns`, per-browser only, not synced) that toggles `data-hide` on `#projectsTable`;
"สร้างโดย" defaults OFF (hidden even for admin) and every other column defaults ON. The ซื้อขาย list is untouched - single-row header, no status columns, no picker.

## Handover photos
`pm_photos` holds one document per photo (`projectId`, `ownerId` = the parent job's `createdBy`, `set: 'equipment'|'install'`, base64 `data`, `size`, `type`,
`createdBy`, `createdAt`), scoped/rule-gated exactly like `pm_files` (see `firestore.rules`). `photoCounts.equipment`/`photoCounts.install` on the parent
`pm_projects` doc is kept in sync via `firebase.firestore.FieldValue.increment(±1)` on every add/delete - that field is what the status-column checkboxes
above read, so the โครงการ/ซื้อขาย list never has to load actual photos just to know whether any exist. `openPhotosPage(id)` -> `showTab('photos')` renders
`#tab-photos`: a header (job type + `docNo` + customer) and up to two sections ("ชุดที่ 1: รูปภาพอุปกรณ์" / "ชุดที่ 2: รูปภาพงานติดตั้ง"), each a
`resizeImageToDataUrl(file, 1280, 'image/jpeg', 0.72)` upload + thumbnail grid + delete. A โครงการ always shows both sections; a ซื้อขาย only shows whichever
set(s) were picked on its own create form (`doc.photoSets`, sale-only field, checkboxes default both-checked, hidden entirely for a project since a project
always gets both). Saving a **brand-new** record (`isNew` only - never on an edit) routes onward: a new project -> `openActionPlan(ref.id)` (Action Plan gained
a "รูปภาพ →" button, `#planPhotosBtn`, to reach the photo page from there - this is the "2-page" flow: Action Plan first, then photos); a new sale ->
straight to `openPhotosPage(ref.id)`. Every job row also has its own "รูปภาพ" button regardless of job type. **Any test that clicks a real create-form save
button for the first time needs the `db.runTransaction` shim** (see `docno_and_history_test.py`'s `TX_SHIM`) since `commitProject()` always saves through a
transaction and the mock doesn't implement one; the mock's `FieldValue` also had to gain `increment()` (dotted-path aware, e.g. `photoCounts.equipment`)
alongside its existing `delete()` for this feature - a real gap in the persisted mock, now fixed there permanently rather than worked around per-test.

## Printing
Browser print -> "Save as PDF". `setPrintPage(css)` sets one `<style id="printPageStyle">` per print (portrait for the handover document, landscape for the Action Plan) and it is removed afterwards.
The handover document follows `docs/handover-template.docx` (measured with Word: TH Sarabun New, navy #1F3A5F, gold #B08D57, label cells #EEF2F7). Page 1 has the letterhead in the flow; pages 2+ get a running header and every page a footer + "หน้า x / y" through page-margin boxes (Chromium).
`thead` repeat of an outer wrapper table did NOT work in Chromium, and `position:fixed` headers do not repeat either - hence the margin boxes.

## Sample data
Rows tagged `sample: true` / names starting `[ตัวอย่าง]` are test data (generators in `tests/fixtures/`); delete by that tag. Audit-log rows written while seeding cannot be deleted (rules).
