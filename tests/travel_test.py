import os, sys, http.server, threading, functools, base64
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from harness import new_page, REPO_ROOT, goto_tab
class Q(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a): pass
h = functools.partial(Q, directory=REPO_ROOT)
srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), h); threading.Thread(target=srv.serve_forever, daemon=True).start()
base = f"http://127.0.0.1:{srv.server_address[1]}"

PNG = base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII=')
TMP_IMG = os.path.join(os.environ.get('TEMP', REPO_ROOT), 'travel_test_upload.png')
with open(TMP_IMG, 'wb') as f: f.write(PNG)

with new_page(viewport={"width": 1500, "height": 950}) as (page, errors):
    page.goto(f"{base}/index.html"); page.wait_for_timeout(500)
    page.evaluate("() => localStorage.setItem('pm-sale-login-ts', String(Date.now()))")
    page.evaluate("() => window.__authListeners[0]({uid:'admin1', email:'admin@a.com', displayName:'Admin One'})"); page.wait_for_timeout(900)

    goto_tab(page, 'travel'); page.wait_for_timeout(300)
    assert page.inner_text('#pageTitle') == 'ค่าเดินทาง'
    month_th = page.evaluate("MONTH_TH_FULL[new Date().getMonth()]")
    year_be = page.evaluate("new Date().getFullYear() + 543")
    # locked header spacing per the real reference spreadsheet: no space after "เดือน", "ปี" glued directly to the year digits
    assert f"ค่าเดินทางประจำเดือน{month_th} ปี{year_be} ของนาย ชวนนท์ ตันชัยฤทธิกุล" == page.inner_text('#travelHeaderPreview')
    assert 'ยังไม่มีรายการเดินทางในเดือนนี้' in page.inner_text('#travelBody')

    # ---------------- add a trip: addable selects (shared from/to pool) + auto-computed rate/total ----------------
    page.click('#travelCreateBtn'); page.wait_for_timeout(300)
    today = page.evaluate("() => new Date().toISOString().slice(0,10)")
    page.fill('#travelDate', today)
    assert page.inner_text('#travelDateText') != 'dd/mm/yyyy'
    page.click('#travelFromAddBtn'); page.fill('#travelFromNew', 'สำนักงานใหญ่'); page.click('#travelFromNewOk')
    page.click('#travelToAddBtn'); page.fill('#travelToNew', 'บริษัท ลูกค้า เอ จำกัด'); page.click('#travelToNewOk')
    page.click('#travelCustomerAddBtn'); page.fill('#travelCustomerNew', 'บริษัท ลูกค้า เอ จำกัด'); page.click('#travelCustomerNewOk')
    page.click('#travelTaskAddBtn'); page.fill('#travelTaskNew', 'เข้าพบเพื่อเสนอราคา'); page.click('#travelTaskNewOk')
    page.fill('#travelDistance', '50'); page.fill('#travelToll', '90'); page.fill('#travelParking', '20'); page.fill('#travelOther', '10')
    assert page.input_value('#travelRate') == '6', "ค่าระยะทาง is always 6, never editable"
    assert page.evaluate("document.getElementById('travelRate').disabled") is True
    assert page.input_value('#travelTotal') == '420.00', "(50*6)+90+20+10 = 420"
    assert page.evaluate("document.getElementById('travelTotal').disabled") is True
    page.click('#travelSaveBtn'); page.wait_for_timeout(500)
    assert 'บันทึกรายการเดินทางแล้ว' in page.inner_text('#toast')

    t = page.evaluate("data.travel[0]")
    assert t['distanceKm'] == 50 and t['rate'] == 6 and t['tollFee'] == 90 and t['parkingFee'] == 20 and t['otherFee'] == 10 and t['total'] == 420
    assert t['fromLocation'] == 'สำนักงานใหญ่' and t['toLocation'] == 'บริษัท ลูกค้า เอ จำกัด'
    assert not t.get('roundTrip')
    assert not t.get('photoData')

    # a second trip re-picking the SAME from/to pool (shared between the two dropdowns) - options should already include both places
    page.click('#travelCreateBtn'); page.wait_for_timeout(300)
    from_opts = page.evaluate("[...document.querySelectorAll('#travelFrom option')].map(o => o.textContent)")
    to_opts = page.evaluate("[...document.querySelectorAll('#travelTo option')].map(o => o.textContent)")
    assert 'บริษัท ลูกค้า เอ จำกัด' in from_opts, "สถานที่เริ่มต้น/ปลายทาง share one addable pool"
    assert 'สำนักงานใหญ่' in to_opts
    page.select_option('#travelFrom', 'บริษัท ลูกค้า เอ จำกัด'); page.select_option('#travelTo', 'สำนักงานใหญ่')
    page.fill('#travelDate', today); page.fill('#travelDistance', '20')
    page.click('#travelSaveBtn'); page.wait_for_timeout(500)
    assert len(page.evaluate("data.travel")) == 2

    # every row shows the ไป/กลับ column and only a real ("ไป") row is clickable/has row-actions
    legs = page.evaluate("[...document.querySelectorAll('#travelBody tr td:nth-child(2)')].map(td => td.textContent.trim())")
    assert legs == ['ไป', 'ไป'], legs

    # ---------------- list: totals row sums every numeric column across the filtered month ----------------
    foot = page.inner_text('#travelFoot')
    assert 'รวมทั้งเดือน' in foot and '540' in foot  # 420 + 120 (20km*6)

    # ---------------- click a row -> read-only view, "แก้ไข" switches it into the editable form in place ----------------
    page.click('#travelBody tr:first-child'); page.wait_for_timeout(200)
    assert page.inner_text('#travelModalTitle') == 'รายละเอียดการเดินทาง'
    assert page.is_disabled('#travelDistance')
    assert not page.is_visible('#travelSaveBtn')
    page.click('#travelViewEditBtn'); page.wait_for_timeout(150)
    assert page.inner_text('#travelModalTitle') == 'แก้ไขรายการเดินทาง'
    assert not page.is_disabled('#travelDistance')
    page.click('#travelCancelBtn'); page.wait_for_timeout(150)

    # ---------------- month filter: a month with nothing in it shows the empty state and a zero-row print refuses ----------------
    other_month = page.evaluate("(() => { const m = new Date().getMonth() + 1; return m === 1 ? 2 : 1; })()")
    page.select_option('#travelMonthFilter', str(other_month)); page.wait_for_timeout(200)
    assert 'ยังไม่มีรายการเดินทางในเดือนนี้' in page.inner_text('#travelBody')
    page.evaluate("window.print = () => { window.__printed = true; }")
    page.click('#travelPrintBtn'); page.wait_for_timeout(200)
    assert 'ไม่มีรายการเดินทางในเดือนนี้ให้พิมพ์' in page.inner_text('#toast')
    page.select_option('#travelMonthFilter', str(page.evaluate("new Date().getMonth() + 1"))); page.wait_for_timeout(200)

    # ---------------- print: locked header line + landscape + no letterhead + no separate ไป/กลับ column ----------------
    page.click('#travelPrintBtn'); page.wait_for_timeout(200)
    printed = page.inner_html('#printArea')
    assert f"ค่าเดินทางประจำเดือน{month_th} ปี{year_be} ของนาย ชวนนท์ ตันชัยฤทธิกุล" in printed
    assert 'pr-head' not in printed, "no company letterhead, per the user's own request"
    assert 'ไป/กลับ' not in printed, "no dedicated ไป/กลับ column on the printed sheet"
    assert '540' in printed and printed.count('<tr>') >= 3   # 2 data rows + 1 total row
    page.evaluate("window.dispatchEvent(new Event('afterprint'))")
    assert page.inner_html('#printArea') == ''

    # ---------------- photos: exactly ONE photo per trip, attached via a small modal off the main row's own button ----------------
    row0_id = page.evaluate("data.travel[0].id")
    assert page.inner_text('#travelBody tr:first-child .row-actions button:has-text("รูปภาพ")').strip() == 'รูปภาพ', "no checkmark before any photo exists"
    page.click('#travelBody tr:first-child .row-actions button:has-text("รูปภาพ")'); page.wait_for_timeout(300)
    assert page.is_visible('#travelPhotoModal')
    assert 'ยังไม่มีรูปภาพ' in page.inner_text('#travelPhotoGrid')
    assert page.is_visible('#travelPhotoAddLabel')
    page.set_input_files('#travelPhotoInput', TMP_IMG); page.wait_for_timeout(700)
    assert page.locator('#travelPhotoGrid .photo-item').count() == 1
    assert page.evaluate("data.travel.find(t => t.id === '%s').photoData" % row0_id) is not None
    assert not page.is_visible('#travelPhotoAddLabel'), "only one photo allowed - the add control hides once one exists"
    page.click('#travelPhotoCloseBtn'); page.wait_for_timeout(200)
    assert page.inner_text('#travelBody tr:first-child .row-actions button:has-text("รูปภาพ")').strip() == 'รูปภาพ ✓'

    # delete it -> back to empty, add control reappears
    page.click('#travelBody tr:first-child .row-actions button:has-text("รูปภาพ")'); page.wait_for_timeout(300)
    page.click('#travelPhotoGrid .photo-item .delete-btn'); page.wait_for_timeout(200)
    page.click('#confirmModalOkBtn'); page.wait_for_timeout(400)
    assert 'ยังไม่มีรูปภาพ' in page.inner_text('#travelPhotoGrid')
    assert page.is_visible('#travelPhotoAddLabel')
    assert page.evaluate("data.travel.find(t => t.id === '%s').photoData" % row0_id) is None
    page.click('#travelPhotoCloseBtn'); page.wait_for_timeout(200)

    # only the MAIN row (never a "กลับ" sub-row) carries รูปภาพ/ลบ row-actions - verified fully below in the ไป-กลับ section

    # ---------------- delete -> Trash -> restore, via the fully generic ENTITY_LABEL/COL mechanism ----------------
    page.click('#travelBody tr:first-child .row-actions button:has-text("ลบ")'); page.wait_for_timeout(150)
    assert page.is_visible('#confirmModal') and 'ค่าเดินทาง' in page.inner_text('#confirmModalMsg')
    page.click('#confirmModalOkBtn'); page.wait_for_timeout(500)
    assert len(page.evaluate("data.travel")) == 1
    goto_tab(page, 'trash'); page.wait_for_timeout(500)
    assert 'ค่าเดินทาง' in page.inner_text('#trashBody')
    page.click('#trashBody tr:has-text("ค่าเดินทาง") button:has-text("กู้คืน")'); page.wait_for_timeout(400)
    goto_tab(page, 'travel'); page.wait_for_timeout(300)
    assert len(page.evaluate("data.travel")) == 2

    # ---------------- ไป-กลับ: ONE document, rendered as TWO rows sharing one ลำดับ number, กลับ row has REAL numbers ----------------
    before = len(page.evaluate("data.travel"))
    page.click('#travelCreateBtn'); page.wait_for_timeout(300)
    assert page.is_visible('#travelRoundTripField'), "only offered while adding, not editing"
    assert not page.is_visible('#travelReturnFeesField'), "return-leg fee inputs stay hidden until ไป-กลับ is checked"
    page.fill('#travelDate', today)
    page.select_option('#travelFrom', 'สำนักงานใหญ่'); page.select_option('#travelTo', 'บริษัท ลูกค้า เอ จำกัด')
    page.fill('#travelDistance', '30'); page.fill('#travelToll', '15')
    page.check('#travelRoundTrip')
    assert page.is_visible('#travelReturnFeesField'), "checking ไป-กลับ reveals the return-leg fee inputs"
    page.fill('#travelReturnToll', '25'); page.fill('#travelReturnParking', '10'); page.fill('#travelReturnOther', '5')
    page.click('#travelSaveBtn'); page.wait_for_timeout(500)
    assert 'บันทึกรายการเดินทางแล้ว' in page.inner_text('#toast')
    assert len(page.evaluate("data.travel")) == before + 1, "ไป-กลับ is one document, not two"
    trip = page.evaluate("data.travel.find(t => t.distanceKm === 30 && t.tollFee === 15)")
    assert trip['roundTrip'] is True
    assert trip['fromLocation'] == 'สำนักงานใหญ่' and trip['toLocation'] == 'บริษัท ลูกค้า เอ จำกัด'
    assert trip['returnTollFee'] == 25 and trip['returnParkingFee'] == 10 and trip['returnOtherFee'] == 5

    # find its two rendered rows (ไป then กลับ, in that order, right after each other) - matched by its own total (195 =
    # 30*6+15), unique to this trip, since another already-existing trip happens to share the same from/to locations
    row_texts = page.evaluate("""() => [...document.querySelectorAll('#travelBody tr')].map(tr => [...tr.children].map(td => td.textContent.trim()))""")
    pair_idx = next(i for i, r in enumerate(row_texts) if r[1] == 'ไป' and r[12] == '195')
    go_row, back_row = row_texts[pair_idx], row_texts[pair_idx + 1]
    assert back_row[1] == 'กลับ'
    assert go_row[0] != '' and back_row[0] == '', "the กลับ row's ลำดับ number is left blank"
    assert go_row[3] == 'สำนักงานใหญ่' and go_row[4] == 'บริษัท ลูกค้า เอ จำกัด'
    assert back_row[3] == 'บริษัท ลูกค้า เอ จำกัด' and back_row[4] == 'สำนักงานใหญ่', "locations swap on the กลับ row"
    assert back_row[5] == '' and back_row[6] == '', "ลูกค้า/รายการปฏิบัติงาน stay blank on the กลับ row"
    # ระยะทาง/ค่า-กม. are MIRRORED from the ไป leg (same distance/rate, per "ไป ระบุไว้ 20 กลับก็ต้อง 20"); ทางด่วน/ที่จอดรถ/
    # อื่นๆ are the return leg's OWN independently-entered values; รวม = 30*6+25+10+5 = 220
    assert back_row[7] == '30' and back_row[8] == '6', "ระยะทาง/ค่า-กม. mirror the ไป leg, not blank"
    assert back_row[9] == '25' and back_row[10] == '10' and back_row[11] == '5', "the กลับ leg's own independently-entered fees"
    assert back_row[12] == '220', "the กลับ leg's own computed total (30*6+25+10+5)"
    # only the "ไป" (main) row carries row-actions
    go_tr = page.locator('#travelBody tr').nth(pair_idx)
    back_tr = page.locator('#travelBody tr').nth(pair_idx + 1)
    assert go_tr.locator('.row-actions button').count() == 2
    assert back_tr.locator('.row-actions').count() == 0

    # the list's own grand total now includes the กลับ leg's own distance/fees/total too, not just the ไป leg's
    expected_total = page.evaluate("""() => data.travel
      .filter(t => t.date && t.date.slice(0,7) === new Date().toISOString().slice(0,7))
      .reduce((s,t) => s + t.total + (t.roundTrip ? travelReturnTotal(t) : 0), 0)""")
    sums = page.evaluate("travelSums(travelRowsForMonth(new Date().getMonth()+1, new Date().getFullYear()))")
    assert sums['total'] == expected_total

    # editing an existing trip never shows the ไป-กลับ checkbox (regenerating a return leg from an edit wouldn't make sense)
    go_tr.click(); page.wait_for_timeout(200)
    page.click('#travelViewEditBtn'); page.wait_for_timeout(150)
    assert not page.is_visible('#travelRoundTripField')
    page.click('#travelCancelBtn'); page.wait_for_timeout(150)

    # ---------------- print: photo appendix is a book-style spread, exactly 2 trips per page (left/right halves), each
    # a card with a labeled ลำดับ/วันที่/จาก/ถึง info table above a "รูปภาพ"-labeled photo ----------------
    trip_id = trip['id']
    page.evaluate("openTravelPhotoModal('%s')" % trip_id); page.wait_for_timeout(300)
    page.set_input_files('#travelPhotoInput', TMP_IMG); page.wait_for_timeout(700)
    page.click('#travelPhotoCloseBtn'); page.wait_for_timeout(200)
    page.click('#travelPrintBtn'); page.wait_for_timeout(200)
    printed2 = page.inner_html('#printArea')
    assert page.locator('#printArea .pr-travel-photo-page').count() == 1, "only 1 photo so far -> one spread, with the second half left empty"
    assert page.locator('#printArea .pr-travel-photo-half').count() == 1
    assert 'pr-travel-photo-info' in printed2, "each card has its own labeled info table, per the reference docx"
    assert '# ลำดับ' in printed2 and 'วันที่' in printed2 and 'สถานที่เริ่มต้น' in printed2 and 'สถานที่ปลายทาง' in printed2
    assert 'รูปภาพ' in printed2, "the photo area itself is labeled รูปภาพ, matching the reference docx"
    assert f">{trip['fromLocation']}<" in printed2 and f">{trip['toLocation']}<" in printed2

    # attach a second photo (to the first non-round-trip trip) -> now 2 photos -> both fill ONE spread's two halves
    other_id = page.evaluate("data.travel.find(t => t.id !== '%s' && !t.deletedAt).id" % trip_id)
    page.evaluate("openTravelPhotoModal('%s')" % other_id); page.wait_for_timeout(300)
    page.set_input_files('#travelPhotoInput', TMP_IMG); page.wait_for_timeout(700)
    page.click('#travelPhotoCloseBtn'); page.wait_for_timeout(200)
    page.click('#travelPrintBtn'); page.wait_for_timeout(200)
    assert page.locator('#printArea .pr-travel-photo-page').count() == 1, "2 photos still fit on one spread (2 per page)"
    assert page.locator('#printArea .pr-travel-photo-half').count() == 2
    page.evaluate("window.dispatchEvent(new Event('afterprint'))")
    assert page.inner_html('#printArea') == ''

    # ---------------- admin-only: showTab() redirects a non-admin session away ----------------
    page.evaluate("currentUserRole = 'user'; showTab('travel')"); page.wait_for_timeout(200)
    assert page.evaluate("currentTab") == 'dashboard', "a non-admin can never land on ค่าเดินทาง"
    page.evaluate("currentUserRole = 'admin'")

    print("errors:", errors); assert not errors
print("OK")
