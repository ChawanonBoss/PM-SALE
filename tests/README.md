# PM-SALE tests

Playwright scripts that drive `index.html` against a **mock of the Firebase SDK** (`firebase_mock.js`), so nothing touches the real database.
`harness.py` serves the repo root on a random port and installs the mock for every page.

```
pip install playwright esprima
python -m playwright install chromium
python tests/run_all.py            # everything
python tests/run_all.py approval   # only files whose name contains "approval"
```

| file | what it locks in |
|---|---|
| `static_test.py` | no markup leaked out as visible text; inline scripts parse (needs `esprima`) |
| `approval_test.py` | new sign-ups wait as `pending`, admin approve/reject, invited people are approved at once, the waiting page reloads into the app |
| `trash_selection_test.py` | Trash checkboxes: some / all rows, type filter, bulk restore, bulk permanent delete (catalog pieces go too) |
| `mobile_cards_and_counters_test.py` | phone card layout, unlinked equipment lines in the edit form, admin keeps `pm_counters` in step |
| `po_excel_attachments_test.py` | PO number, งวดงานที่, Excel export, project attachments, accessible names, no built-in sample catalogs |
| `projects_stock_test.py` | separate ซื้อขาย / โครงการ menus and forms, stock deduction & return, handover PDF markup |
| `installments_test.py` | project installments: total in the form, the "ส่งงาน" dialog (e.g. 3/4), history, PDF shows 3/4, Excel column |
| `menu_installment_filter_test.py` | โครงการ list: งวดงาน is column 2, its filter dropdown options/reset, and matching by current stage |
| `docno_and_history_test.py` | SO/PJ document numbers, warehouse withdrawal history |
| `paging_test.py` | 10/20/50/100 rows per page and the page buttons on every list |
| `pdf_test.py` | prints the handover document and the Action Plan through Chromium's PDF engine and checks fonts, page size and orientation |
| `sample_set_test.py` | the 10-per-menu sample generator (`fixtures/`) produces consistent stock, numbers and alert variety |
| `project_status_columns_test.py` | โครงการ's and ซื้อขาย's own grouped "สถานะงาน" checkbox columns (unclickable, reflect real saved data only; a sale's not-chosen photo set renders a blank cell, not an unticked box), each list's own column-visibility picker and localStorage key (โครงการ's toolbar button vs ซื้อขาย's in-header ⚙), "สร้างโดย" hidden by default in both |
| `photos_test.py` | handover photo upload/delete for both sets, sale-only photo-set picker on the create form, tagging a photo with equipment from the job's own items[] (and the PDF caption/grid falling back to the filename when untagged), equipment selection now mandatory (blocked both via the button and via the file input directly, and the add button/select disabled outright when the job has no items), post-save routing (new project -> Action Plan -> "รูปภาพ →"; new sale -> photo page directly) |
| `nav_groups_test.py` | sidebar group flyouts (which pages list under which group, open/close/outside-click, active state, badge aggregation), ตั้งค่า hidden for non-admin, mobile drawer closes on a flyout pick |
| `service_warehouse_test.py` | โกดังบริการ page CRUD (no quantity/Serial columns at all) and its own addable-selects, Trash round-trip, the ซื้อขาย/โครงการ form's separate "+ เพิ่มสินค้า"/"+ เพิ่มบริการ" tables sharing one flat items[] on save, a service line never triggering the warehouse stock-effects confirm dialog (even mixed with a goods line that does) |
| `delete_sample_data_test.py` | Trash page's "ลบข้อมูลตัวอย่างทั้งหมด" button hard-deletes every `sample: true` row across all 5 affected collections, including ones already sitting in the Trash, while real (non-sample) rows in the same collections are left alone |

`fixtures/` holds the sample generators. The same files were used to seed the live site with `[ตัวอย่าง]` rows (`sample: true`).

Things the mock cannot check: **Firestore security rules** (`firestore.rules` is only exercised by hand against the real project) and a real printer/PDF viewer.
