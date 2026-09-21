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
| `projects_stock_test.py` | project/sale form, stock deduction & return, handover PDF markup |
| `docno_and_history_test.py` | SO/PJ document numbers, warehouse withdrawal history |
| `paging_test.py` | 10/20/50/100 rows per page and the page buttons on every list |
| `pdf_test.py` | prints the handover document and the Action Plan through Chromium's PDF engine and checks fonts, page size and orientation |
| `sample_set_test.py` | the 10-per-menu sample generator (`fixtures/`) produces consistent stock, numbers and alert variety |

`fixtures/` holds the sample generators. The same files were used to seed the live site with `[ตัวอย่าง]` rows (`sample: true`).

Things the mock cannot check: **Firestore security rules** (`firestore.rules` is only exercised by hand against the real project) and a real printer/PDF viewer.
