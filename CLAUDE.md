# PM-SALE - working notes

Single-file app: everything lives in `index.html` (HTML + CSS + JS). Deployed by pushing to `main` (GitHub Pages). Firebase project `bu-abb`, collections `pm_*`.

## Rules of the road
- **Version**: bump `APP_VERSION` on every push. Not structural -> last digit; structural (new page/collection/data field) -> middle digit, last reset to 0.
- **Firestore rules** live in the Console, not in this repo. `firestore.rules` here is the PM-SALE block only; the full file to paste is `Web/firestore.rules` in the BU-ABB working copy. Client queries and rules change together
  (a non-admin's listeners use `.where('createdBy','==',uid)`; `pm_files` queries add `ownerId`). Always tell the user to publish the rules after changing them, and re-test with throw-away `pmtest.*@example.com` accounts.
- Reply in Thai, short. Decide instead of asking when a sensible default exists; confirm before destructive actions on real data.
- Patch `index.html` with small Python scripts that assert exact match counts; avoid bash heredocs with mixed quotes (write files with the editor tools). After a big edit run `python tests/static_test.py` (a bad replace once left `class="tab-panel"...` visible on the dashboard).

## Data model (short)
`pm_projects` (`jobType` sale | project; items[] link to `pm_warehouse`; plan[] for projects; `docNo`, `contractNo`, `poNo`; project installments: `installmentTotal`, `installmentNo` (last delivered, printed as "3/4"), `deliveries[]` written by the "ส่งงาน" dialog), `pm_customers`, `pm_companies`, `pm_warehouse` (quantity, serials[], history[] capped 500),
`pm_counters` (SO/PJ + yyyymmdd -> n; the admin session raises them via `syncDocCounters()`), `pm_catalogs` + `pm_catalogChunks`, `pm_files` (attachments, base64, <=650 KB each, 8 per project), `pm_users` (`status` approved|pending|rejected; no status = approved),
`pm_pendingRoles` (invites), `pm_auditLog`/`pm_errorLog` (immutable). Soft delete = `deletedAt`; the Trash tab (admin) restores / purges.

## Menus
ซื้อขาย (`tab-sales`, `#salesBody`) and โครงการ (`tab-projects`, `#projectsBody`) are separate menus over the same `pm_projects` collection; `renderJobs(kind)` draws both. There is no job-type select/filter/column any more: `openProjectForm(id, kind)` sets the hidden `#prjJobType` from the menu.
The Dashboard switch, the Warranty page and the Customer pop-up still mix both kinds.

## Printing
Browser print -> "Save as PDF". `setPrintPage(css)` sets one `<style id="printPageStyle">` per print (portrait for the handover document, landscape for the Action Plan) and it is removed afterwards.
The handover document follows `docs/handover-template.docx` (measured with Word: TH Sarabun New, navy #1F3A5F, gold #B08D57, label cells #EEF2F7). Page 1 has the letterhead in the flow; pages 2+ get a running header and every page a footer + "หน้า x / y" through page-margin boxes (Chromium).
`thead` repeat of an outer wrapper table did NOT work in Chromium, and `position:fixed` headers do not repeat either - hence the margin boxes.

## Sample data
Rows tagged `sample: true` / names starting `[ตัวอย่าง]` are test data (generators in `tests/fixtures/`); delete by that tag. Audit-log rows written while seeding cannot be deleted (rules).
