# PM-SALE - working notes

Single-file app: everything lives in `index.html` (HTML + CSS + JS). Deployed by pushing to `main` (GitHub Pages). Firebase project `bu-abb`, collections `pm_*`.

## Rules of the road
- **Version**: bump `APP_VERSION` on every push. Not structural -> last digit; structural (new page/collection/data field) -> middle digit, last reset to 0.
- **Firestore rules** live in the Console, not in this repo. `firestore.rules` here is the PM-SALE block only; the full file to paste is `Web/firestore.rules` in the BU-ABB working copy. Client queries and rules change together
  (a non-admin's listeners use `.where('createdBy','==',uid)`; `pm_files` queries add `ownerId`). Always tell the user to publish the rules after changing them, and re-test with throw-away `pmtest.*@example.com` accounts.
- Reply in Thai, short. Decide instead of asking when a sensible default exists; confirm before destructive actions on real data.
- Patch `index.html` with small Python scripts that assert exact match counts; avoid bash heredocs with mixed quotes (write files with the editor tools). After a big edit run `python tests/static_test.py` (a bad replace once left `class="tab-panel"...` visible on the dashboard).

## Data model (short)
`pm_projects` (`jobType` sale | project; items[] link to `pm_warehouse` (goods, `kind:'good'`) or `pm_serviceWarehouse` (services, `kind:'service'`, `svcId` instead of
`whId` - see "Service warehouse" below); plan[] for projects; `docNo`, `contractNo`, `poNo`; project installments: `installmentTotal`, `installmentNo` (last delivered,
printed as "3/4"), `deliveries[]` written by the "ส่งงาน" dialog; the โครงการ list's own "งวดงาน" column/filter reads `currentInstallmentStage()` - the next undelivered
installment, or the last one once everything is in - not `installmentNo` directly), `pm_customers`, `pm_companies`, `pm_warehouse` (quantity, serials[], history[] capped
500), `pm_serviceWarehouse` (same shape minus quantity/serials/history - services aren't stocked),
`pm_counters` (SO/PJ + yyyymmdd -> n; the admin session raises them via `syncDocCounters()`), `pm_catalogs` + `pm_catalogChunks`, `pm_files` (attachments, base64, <=650 KB each, 8 per project), `pm_photos` (handover photos, base64 <=900 KB each - see "Handover photos" below), `pm_users` (`status` approved|pending|rejected; no status = approved),
`pm_pendingRoles` (invites), `pm_auditLog`/`pm_errorLog` (immutable). Soft delete = `deletedAt`; the Trash tab (admin) restores / purges.

## Menus
ซื้อขาย (`tab-sales`, `#salesBody`) and โครงการ (`tab-projects`, `#projectsBody`) are separate menus over the same `pm_projects` collection; `renderJobs(kind)` draws both. There is no job-type select/filter/column any more: `openProjectForm(id, kind)` sets the hidden `#prjJobType` from the menu.
The Dashboard switch, the Warranty page and the Customer pop-up still mix both kinds.

## Sidebar groups
Most of the rail's pages are folded into 4 group buttons (`.nav-item[data-group]`) instead of each having its own permanent icon: clicking one opens
`#navGroupPopover`, a `position:fixed` flyout (fixed rather than the plain-`absolute` `.rail-menu-popover` gear popover, because these buttons sit inside
the scrollable `#railNavScroll` and a plain-absolute popover would get clipped the same way `.nav-tooltip` did before - see the "Sidebar: icon rail" note
in the sibling BU-ABB app's CLAUDE.md for the original bug this mirrors) listing that group's real pages, built fresh on each click by
`renderGroupPopover()` from `NAV_GROUPS`/`NAV_ICONS`/`NAV_LABELS`. Groups (names picked freely, per explicit user permission - content was specified,
labels were not): **ซื้อขาย/โครงการ** (sales, projects), **คลังและอุปกรณ์** (warehouse, serviceWarehouse, catalog, equipment), **ลูกค้าและบริษัท** (customers, companies),
and **ตั้งค่า** (users, audit, trash - admin-only, name given explicitly by the user). `dashboard` and `actionplan` stay as their own permanent
top-level buttons - the user's own grouping list never mentioned moving them. A group button's own badge (`group1NavBadge`/`group2NavBadge`/
`settingsNavBadge`) is a live aggregate of whatever alert numbers its members would have shown individually (`navAlertCache`, filled by
`updateNavBadge()`); the same numbers are baked directly into each flyout item's markup when the popover renders, rather than kept as their own
persistent DOM elements - a badge span that only exists while its parent innerHTML happens to be freshly rebuilt would be a fragile thing for
`setNavBadge()` to keep reaching for on every render tick, so the group button is the one truly-persistent badge. Trash's `loadTrash()` (a one-time
fetch, not a live listener) used to be wired to a click listener on trash's own permanent nav button; since that button no longer exists, `showTab()`
itself now calls `loadTrash()` when `tab === 'trash'`, which also makes it more robust to any future `showTab('trash')` call from elsewhere in the
code. Tests reach a grouped tab through the `goto_tab(page, tab)` helper in `harness.py` (opens the right group first via `NAV_GROUP_OF`, then clicks
the flyout item) rather than clicking `.nav-item[data-tab=...]` directly - use it for any new test that navigates to sales/projects/warehouse/serviceWarehouse/catalog/
equipment/customers/companies/users/audit/trash, and keep `NAV_GROUP_OF` in sync with `NAV_GROUPS` if a tab ever changes group.

## Handover photos: print to PDF
`#photosPrintBtn` (next to the back button, in the same `.plan-head` row style as Action Plan's own print button) calls `printPhotos()`, which follows
the exact same `letterheadHtml(co)` + `.pr-info` system already used by `printActionPlan()` - same fonts/margins/print-only CSS, so it looks like the same
document family rather than a bolted-on export (there is no generic `.pr-title` heading above the info table any more - it was dropped since the header's
own info table already says ชื่องาน/ชื่อโครงการ, and a page-wide title added nothing per-photo captions didn't already say better). The header's fields are
all pulled from the record itself, never typed by hand: เลขที่เอกสาร, ชื่องาน/ชื่อโครงการ, หน่วยงาน/ลูกค้า, เลขที่สัญญา (only if set - a sale rarely has one),
and จำนวนรูปภาพ (count actually being printed) - ประเภทงาน and วันที่พิมพ์ used to be in this list too but were dropped as not useful on the printed sheet.
Below that, each visible set (per `photoSetsFor()` - a
sale only prints the set(s) it chose, a project always offers both) gets its own heading and a 2-column `.pr-photo-grid` of images
(`buildPhotosPrintHtml()`, `.pr-photo-*` CSS added to the shared `@media print` block). Each photo's caption is `equipCaption(p)` - "ยี่ห้อ ชื่ออุปกรณ์ — SN
xxx" from whichever equipment line it was tagged with (see "Handover photos" below) - falling back to the photo's own filename only if it was never tagged
(older photos, or one left as "ไม่ระบุอุปกรณ์"). Refuses with a toast if there are no photos at all to print.

## โครงการ/ซื้อขาย lists: "สถานะงาน" status columns + column picker
Read-only, never-clickable `<input type="checkbox" disabled>` columns under one grouped `<thead>` header ("สถานะงาน") show whether real data behind each
one has actually been saved - there is no way to tick them by hand, only by really saving that data. `computeColumnLabels()` (near `labelCardCells`) walks
the 2-row `<thead>` grid so the mobile card view still labels each cell correctly. Both lists have their own picker, independent localStorage key, and
independent column set - they are NOT the same list of toggles:
- **โครงการ** (`#projectsTable`): 3 sub-columns ("แผนการดำเนินงาน" / "รูปภาพอุปกรณ์" / "รูปภาพงานติดตั้ง") reading `(p.plan||[]).length>0` and
  `p.photoCounts.equipment`/`.install > 0`. `#projectsColumnsBtn` (a toolbar button, in the filter-bar) opens `#projectColumnsModal`, backed by
  `PROJECT_COLUMNS` / `projectColumnPrefs` (localStorage `pm-sale-project-columns`).
- **ซื้อขาย** (`#salesTable`): only 2 sub-columns ("รูปภาพอุปกรณ์" / "รูปภาพงานติดตั้ง" - a sale has no plan, so no first column). Its column-picker
  trigger lives inside the table header itself instead (the rightmost `<th>`, a small `⚙` icon button, `#salesColumnsBtn`) rather than the toolbar, opening
  `#salesColumnsModal`, backed by its own `SALES_COLUMNS` / `salesColumnPrefs` (localStorage `pm-sale-sales-columns`).
- A sale only ever offers whichever photo set(s) it chose on its own create form (`photoSetsFor(rec)`), so for a sale row, a set that was never chosen
  renders as a **blank `<td>`, not an unchecked checkbox** (`photoChk()` inside `renderJobs`) - the column has nothing to say about a set that record
  never had in the first place. A โครงการ always has both sets, so this never actually blanks out for a project.

In both lists, "สร้างโดย" defaults OFF (hidden even for admin) and every other column defaults ON.

## Handover photos
`pm_photos` holds one document per photo (`projectId`, `ownerId` = the parent job's `createdBy`, `set: 'equipment'|'install'`, base64 `data`, `size`, `type`,
`equipBrand`/`equipName`/`equipSerial` (see below), `createdBy`, `createdAt`), scoped/rule-gated exactly like `pm_files` (see `firestore.rules`; the create
rule has no `hasOnly()` on keys, so these extra fields needed no rules change). `photoCounts.equipment`/`photoCounts.install` on the parent `pm_projects`
doc is kept in sync via `firebase.firestore.FieldValue.increment(±1)` on every add/delete - that field is what the status-column checkboxes above read, so
the โครงการ/ซื้อขาย list never has to load actual photos just to know whether any exist. `openPhotosPage(id)` -> `showTab('photos')` renders `#tab-photos`:
a header (job type + `docNo` + customer) and up to two sections ("ชุดที่ 1: รูปภาพอุปกรณ์" / "ชุดที่ 2: รูปภาพงานติดตั้ง"), each a
`resizeImageToDataUrl(file, 1280, 'image/jpeg', 0.72)` upload + thumbnail grid + delete. A โครงการ always shows both sections; a ซื้อขาย only shows whichever
set(s) were picked on its own create form (`doc.photoSets`, sale-only field, checkboxes default both-checked, hidden entirely for a project since a project
always gets both). Saving a **brand-new** record (`isNew` only - never on an edit) routes onward: a new project -> `openActionPlan(ref.id)` (Action Plan gained
a "รูปภาพ →" button, `#planPhotosBtn`, to reach the photo page from there - this is the "2-page" flow: Action Plan first, then photos); a new sale ->
straight to `openPhotosPage(ref.id)`. Every job row also has its own "รูปภาพ" button regardless of job type. **Any test that clicks a real create-form save
button for the first time needs the `db.runTransaction` shim** (see `docno_and_history_test.py`'s `TX_SHIM`) since `commitProject()` always saves through a
transaction and the mock doesn't implement one; the mock's `FieldValue` also had to gain `increment()` (dotted-path aware, e.g. `photoCounts.equipment`)
alongside its existing `delete()` for this feature - a real gap in the persisted mock, now fixed there permanently rather than worked around per-test.

Each of the two panels (equipment/install) carries its own `<select>` (`#photosEquipItemSel` / `#photosInstallItemSel`, next to its "+ เพิ่มรูปภาพ" button,
filled by `fillPhotoItemSelect()` from `equipmentOptionsFor(rec)`) listing every serial on the job's own **goods** `items[]` lines (one option per `rid`+serial,
or one per item with no serials at all - a `kind:'service'` line is filtered out here, since a service isn't something you photograph) - this is how a photo
gets tagged with which real piece of equipment it shows, rather than typed free-text. **Picking one is mandatory**: `fillPhotoItemSelect()` disables the select
(and `renderPhotos()` disables the "+ เพิ่มรูปภาพ" button, with the hint text explaining why) when the job has no goods items to pick from at all, and both the
button's own click handler and `addProjectPhotos()` itself refuse (toast "กรุณาเลือกอุปกรณ์ก่อนแนบรูป") if nothing is picked - this was tightened after photos kept
getting attached with the wrong equipment info (or none). Whatever is selected when "+ เพิ่มรูปภาพ" is used applies to every file picked in that one action
(`equipFromSelection()` inside `addProjectPhotos()`); there is **no edit-after-the-fact UI** - a wrong pick means deleting the photo and re-attaching it, chosen
deliberately so this needed no `pm_photos` rules change (the `allow update: if false` on `pm_photos` stays exactly as-is). `equipCaption(p)` turns those three
fields into the one line used both under each thumbnail in the grid ("ไม่ระบุอุปกรณ์" if left blank - only reachable now on photos attached before this became
mandatory) and as the photo's caption in the printed PDF (see above).

## Service warehouse
`pm_serviceWarehouse` (`part`, `brand` = ซัพพลายเออร์, `type` = ประเภทงาน, `name` = ชื่อบริการ, `note`, `createdBy`/`createdAt`) is a second, parallel "warehouse" for
services rather than stocked goods - same field names as `pm_warehouse` on purpose (just relabelled in the UI) so every generic place that already reads
`w.part`/`w.brand`/`w.name`/`w.type` needed no change, and the same rule shape, `deleteEntity()`/Trash handling (both are driven entirely by `ENTITY_LABEL`/`COL`,
so adding `serviceWarehouse` to those two maps was enough - no Trash-specific code exists per collection), and `makeAddableSelect()` pattern (`svcBrandSel`/`svcTypeSel`)
apply unchanged. It has no quantity/serials/history at all - a service isn't something you count into or out of stock. Its own page (`tab-serviceWarehouse`, in the
คลังและอุปกรณ์ group, right after โกดังสินค้า) is a near-identical copy of the warehouse page minus the quantity/serial UI and the quantity sort dropdown.

On the ซื้อขาย/โครงการ form, "รายละเอียดของงาน" is now two separate tables under their own "สินค้า"/"บริการ" headings, each with its own add button
(`#prjAddItemBtn` "+ เพิ่มสินค้า" / `#prjAddServiceBtn` "+ เพิ่มบริการ") and its own tbody (`#prjItemsBody` / `#prjServicesBody`) - a deliberate choice over one
merged table with a per-row toggle, so the two kinds of line are never confused while picking. Both tables read from and write into the **same flat
`editingItems` array** (`renderItemRows()` filters it into `goods`/`services` by `it.kind`, keeping each row's real index into that flat array for its onchange
handlers, since a row's position within its own table is not its index in `editingItems`); `removeItemRow()` doesn't care which table a row came from. A goods
row keeps its existing shape (`kind:'good'`, `whId`, `serials[]`); a service row reuses `brand`/`name`/`type`/`part`/`qty`/`status` for the same generic
display/PDF/Excel code paths but carries `svcId` instead of `whId` and never a `serials[]` - `stockEffects()`/`commitProject()` only ever key off `whId`, so a
service line is automatically invisible to the warehouse stock-deduction transaction with no code change there at all. `pickItemService()` mirrors `pickItemWh()`
one-for-one, reading from `data.serviceWarehouse` instead of `data.warehouse`. `toItemRow()` carries `kind`/`svcId` through and had one existing bug fixed while
this was added: it used to blank out `type` for any line with no `whId` (meant for old freeform/unlinked goods lines), which would have wrongly blanked a
service line's ประเภทงาน too since a service never has a `whId` either - the condition is now `(it.whId || service)`.

## Catalog: หมวดสินค้า
`#catCategory` in the upload/edit form is an addable-select (`catCategorySel`, same `makeAddableSelect()` "+" pattern as โกดังสินค้า's ยี่ห้อ/ประเภท) rather
than the plain text+`<datalist>` input it used to be - adding a new category is now an explicit, visible action instead of only discoverable by typing past
the suggestions. `ยี่ห้อ` (`#catBrand`) on the same form was left as its original text+datalist input (not asked for, so not touched) - the two fields are
intentionally inconsistent with each other for now. Suggested/existing values still come from the same two sources as before (`data.catalogs.map(c =>
c.category)` and `data.warehouse.map(w => w.type)`), just read by `used()` inside the addable-select instead of building a `<datalist>`.

## Printing
Browser print -> "Save as PDF". `setPrintPage(css)` sets one `<style id="printPageStyle">` per print (portrait for the handover document, landscape for the Action Plan) and it is removed afterwards.
The handover document follows `docs/handover-template.docx` (measured with Word: TH Sarabun New, navy #1F3A5F, gold #B08D57, label cells #EEF2F7). Page 1 has the letterhead in the flow; pages 2+ get a running header and every page a footer + "หน้า x / y" through page-margin boxes (Chromium).
`thead` repeat of an outer wrapper table did NOT work in Chromium, and `position:fixed` headers do not repeat either - hence the margin boxes.
When the user says the template docx "has been edited," re-read it (`python-docx`, or unzip + diff `word/document.xml`/`header1.xml`/`footer1.xml` against the previous copy - Word re-splits unrelated text into more `<w:r>` runs on every save, so diff the *joined* text per paragraph, not the raw XML, or real edits get lost in run-fragmentation noise) and reconcile `buildProjectPrintHtml()` against whatever actually changed, then overwrite `docs/handover-template.docx` with the new file so it stays the one live reference copy. The page-1 letterhead's ที่อยู่บริษัท is its own `.addr` div, on the line below the company name; เบอร์โทร and เลขประจำตัวผู้เสียภาษี share the NEXT line
together (`phoneTax`, same `' &nbsp;|&nbsp; '` join as the sibling `letterheadHtml()` uses elsewhere for the same two fields) rather than each getting
its own line - only address gets split out on its own. Either line is skipped entirely when nothing in it is set; `phoneTax` itself must be computed
inside a `co ? ... : ''`-style guard (or guarded some other way) since `co` (the job's company) can be `undefined` when no company was picked - a plain
top-level `co.phone` reference blows up `buildProjectPrintHtml()` for that case where the old code never touched `co` at all until inside the ternary.
`.ho-head .addr` (not just `.co`) needs its own `text-align:right`: the info block sits flush against the page's right margin via the row's
`justify-content:space-between` regardless, but a shorter line left unstyled would sit at the LEFT edge of that block's own (content-sized) box, not the
page's right margin - it only reads as right-aligned once every line in the block shares the same `text-align:right`.

## Sample data
Rows tagged `sample: true` / names starting `[ตัวอย่าง]` are test data (generators in `tests/fixtures/`). `#deleteSampleDataBtn` on the (admin-only) Trash page
hard-deletes every `sample: true` doc across `SAMPLE_DATA_COLS` (`pm_companies`, `pm_customers`, `pm_warehouse`, `pm_projects`, `pm_pendingRoles`) in one go,
whether that row is currently live or already sitting in the Trash - it queries each collection directly (`where('sample','==',true)`), not through the
Trash's own `deletedAt` listing, so a soft-deleted sample row is caught too. No rules change was needed: admin already has unconditional delete on all five of
those collections. Real, non-sample rows are matched by the same tag and are never touched. Audit-log rows written while seeding still cannot be deleted
(rules) - this button doesn't try to.

`#warehouseAddSampleBtn` on the โกดังสินค้า page (admin-only, same visibility toggle pattern as `#catalogUploadBtn`) is a matching one-click **add**: a fixed
`SAMPLE_WAREHOUSE_SET` of 5 real-looking items (3 CCTV, 2 Switch; every field filled in, including a full set of unique serials sized to each item's own
quantity), tagged `sample: true` and named `[ตัวอย่าง] ...` so it's picked up by `#deleteSampleDataBtn` above like any other sample row, and just as
deletable one at a time through the page's own normal "ลบ" -> Trash flow. Guards against creating the set twice (checks `data.warehouse` for any of its
five `part` codes first) since, unlike the bulk generators in `tests/fixtures/`, this one is meant to be clicked from the live production site by an
admin, not just seeded once for a test run. Written directly with `history: []` and `sample: true` as extra keys beyond `pm_warehouse`'s non-admin
`hasOnly()` create rule - safe only because the button itself is admin-only, since `pmIsAdmin()` bypasses that key restriction entirely.
