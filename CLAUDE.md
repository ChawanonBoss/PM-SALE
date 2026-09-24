# PM-SALE - working notes

Single-file app: everything lives in `index.html` (HTML + CSS + JS). Deployed by pushing to `main` (GitHub Pages). Firebase project `bu-abb`, collections `pm_*`.

## Rules of the road
- **Version**: bump `APP_VERSION` on every push. Not structural -> last digit; structural (new page/collection/data field) -> middle digit, last reset to 0.
- **Firestore rules** live in the Console, not in this repo. `firestore.rules` here is the PM-SALE block only; the full file to paste is `Web/firestore.rules` in the BU-ABB working copy. Client queries and rules change together
  (a non-admin's listeners use `.where('createdBy','==',uid)`; `pm_files` queries add `ownerId`). Always tell the user to publish the rules after changing them, and re-test with throw-away `pmtest.*@example.com` accounts.
- Reply in Thai, short. Decide instead of asking when a sensible default exists; confirm before destructive actions on real data.
- Patch `index.html` with small Python scripts that assert exact match counts; avoid bash heredocs with mixed quotes (write files with the editor tools). After a big edit run `python tests/static_test.py` (a bad replace once left `class="tab-panel"...` visible on the dashboard).

## Design system: Neumorphism (Soft UI)
The whole app UI (not the printed PDF documents - see below) runs on a Neumorphism/Soft UI design system: every surface is "molded"
from one base colour (`--paper`/`--card`, both the same value - per the system's own anti-pattern rule "never a separate white/card
colour"), and shadows do all the work borders used to do. All the physics lives in `:root` as reusable tokens: `--shadow-ext`/
`-hover`/`-sm` (raised/"extruded" - the resting state for buttons, cards, panels, popovers) and `--shadow-inset`/`-deep`/`-sm`
(pressed/"carved" - wells for inputs, icon circles, the Gantt's scroll frame, and the `:active`/`.active` state of anything that
reads as "currently pressed or selected"). The shadow colour itself is two more tokens, `--sh-hi`/`--sh-lo` (RGB triples, not full
colours, so `rgba(var(--sh-lo),0.6)` composes cleanly) - dark mode only needs to override those two plus the base paper/ink colours,
and every `--shadow-*` token recomputes automatically since CSS custom properties resolve at use time, not at definition time.
`--line` is a soft translucent tint of `--ink-soft` - kept only for things that still want a plain divider (table row separators,
the Gantt's grid lines, a couple of `border-bottom` dividers in popovers) rather than a full shadow treatment, since those already
relied on `var(--line)` throughout the file and recolour themselves for free. `--paper-dim` is NOT identical to `--paper` (a
deliberate deviation from "same colour" for anything that must stay opaque against scrolled content behind it - the Gantt's sticky
frozen columns/header row, the sidebar strip, `.docno` chips) - it's a few percent darker, still visibly "the same material," but
solid enough that position:sticky cells don't let scrolled-past content show through a translucent fill.

**Palette history**: this started as a cool-grey palette (`#E0E5EC`/`#3D4852`/violet accent) taken from a Neumorphism moodboard.
The user later shared a separate warm-editorial design brief for the ปฏิทิน (Calendar) page (ivory canvas, terracotta accent,
sage/dusty-blue/amber categories) and then asked for that SAME warm palette across the whole app, with the Neumorphism shadow
system staying everywhere including the calendar - so the tokens were repainted warm rather than literally reusing the
calendar's own near-white `#faf7f2` - a base that light leaves too little headroom between its highlight and shadow tints for
the dual-shadow effect to read clearly, so it was deepened slightly while keeping the same warm hue. That first warm pass
(`--paper:#EFE7D9`) still read as "too orange/cream, hard on the eyes" once it covered the whole app rather than just one
page, so `--paper`/`--paper-dim`/`--card` were lightened and desaturated a second time to `#F6F2E9`/`#ECE4D3` - and the shadow
tone (`--sh-lo`) lightened and desaturated to match (`190,177,157`), since a paler base needs a softer shadow to stay
proportional. `--accent`/`--sun`/`--ok`/`--danger`/`--ink`/`--ink-soft` (`#C4623D`/`#CF9749`/`#7A8A6F`/`#AE4438`/
`#1A1714`/`#8B8178`) are unchanged - only the base surface moved, not the ink or accent colours. Dark mode follows the same
logic with a warm-espresso base (`#241C15`) instead of the earlier cool-slate one, and wasn't part of the "too orange" report
so its own tone is untouched.

**Checkboxes inside `.field`** (the photo-set pickers, `#prjPhotoEquip`/`#prjPhotoInstall`) must be excluded from the generic
`.field input{...}` text-input styling (`.field input:not([type="checkbox"]):not([type="radio"])`) - that rule's `width:100%`
+ `box-shadow:var(--shadow-inset)` turned every checkbox caught by it into a full-width rounded "well" with the tiny checkbox
lost inside it, reported directly from a screenshot. `.field input[type="checkbox"], .field input[type="radio"]` get their own
minimal reset instead (`width:16px; box-shadow:none; accent-color:var(--accent)`). Checked the rest of the app for the same
`.field`-wraps-a-checkbox trap; every other checkbox in the app lives outside a `.field` (`.cal-cat-row`, the column-picker
lists, `.trash-cb`, the Gantt's `.g-chk-input`, the disabled สถานะงาน cells) with its own dedicated, already-correct rule.

**Scrollbars** are restyled globally (`*{ scrollbar-width:thin; scrollbar-color:... }` for Firefox, `::-webkit-scrollbar*` for
Chromium) to a thin warm-toned thumb instead of the browser's flat default, which clashed with the rest of the palette on
every scrollable region at once (`.content`, `.cal-root`'s own scroll box, `.table-scroll`, the Gantt's `.plan-scroll` frame,
modals, popovers) - one global rule rather than restyling each scroll container individually.

**Fonts**: `Chillax` (Latin letters + numbers) paired with `RSU` (Thai) - both local font files under `fonts/` (the user's own,
loaded via `@font-face`, not a font pairing Claude picked), replacing the Google-Fonts pairs used earlier in the session. Every
font-family list puts Chillax first (`'Chillax','RSU',sans-serif`) - it has no Thai glyphs at all, so Thai text (nearly everything
in this app) falls straight through to RSU per-codepoint, while Chillax wins for the Latin/numeric text it does cover (doc numbers,
part codes, English labels). `Noto Sans Thai`/`Sarabun` are still loaded from Google Fonts, but ONLY as the printed handover
document's own fallback fonts (see "Printing" below) - the on-screen app no longer uses either. `.btn` (primary actions) takes the
system's `rounded-2xl` (16px) spec literally and is filled solid `--accent`; small inline pills that were already fully round
before this (`.icon-btn`, `.badge`, `.filter-control`, `.page-btn`, `.subtab-item`) kept their `rounded-full` shape, read as the
system's own "Inner Elements: 12px or rounded-full" token rather than the primary-button token. Status colours (`--sun`/`--ok`/
`--danger`/`--gray` and their `-soft` tints, `.badge.*`) keep their original semantic meaning (pending/active/ended/warning/danger)
- since every badge/status rule already reads from these variables rather than hard-coded hex, repainting the tokens re-skinned
all of them with no per-rule edits needed at all.

**Deliberately left outside this system**:
- **The printed handover document / Action Plan PDF** (`@media print`, every `.pr-*`/`.ho-*` rule) - untouched, including its own
  font-family list. It's a formal business document measured against `docs/handover-template.docx` (TH Sarabun New, navy/gold),
  not a screen surface, and Chromium's print engine doesn't render soft box-shadows the same way anyway.
- **Dense data tables** (`td`/`th`, list rows) - rows stay flat with a thin `var(--line)` divider inside one outer `--shadow-ext`/
  `--shadow-inset` panel/frame, rather than every row or cell getting its own dual shadow - real neumorphism examples nest a "flat"
  content region inside one raised/carved container rather than stacking shadows per row, and doing the latter here (hundreds of
  `<td>`s) would be both visually heavy and a real paint-cost concern.
- **The Gantt's per-task bar colours** (`PLAN_COLORS`) and the PDF viewer's own page canvas (`.pdf-page` stays literal white) -
  categorical/functional colours unrelated to the neutral chrome; recolouring a chart palette or making a rendered document page
  look tinted would hurt legibility for no visual-identity benefit.
- **Dark mode's exact shadow values** are this session's own extension, not part of any source spec (both palette briefs only ever
  gave a light version) - a lighter warm tint standing in for the "light source" shadow and near-black for the "falls away" shadow,
  following the same dual-shadow physics as light mode.

## Dashboard: donut gauge + monthly bar chart + segmented toggle
Reworked to echo a reference "UI Widgets" neumorphism moodboard the user shared, using the app's own real data rather than
copying the reference's own decorative widgets one-for-one (a heating-control icon, a heart/favourite toggle, a sign-up form etc.
have no PM-SALE equivalent, so weren't added). Three concrete pieces came out of it:
- **Status donut** (`renderStatusDonutArcs()`, `#dashDonutSvg`) replaces the old flat "สัดส่วนสถานะ" linear split-bar with a
  radial gauge - three stacked `<circle>` elements sharing one center/radius, each given a `stroke-dasharray`/`stroke-dashoffset`
  slice sized to its share of the total and rotated together via `transform="rotate(-90 60 60)"` so the first segment starts at
  12 o'clock, sitting over a plain `--paper-dim` track circle. The total count sits in the middle (`#dashDonutTotal`,
  absolutely-positioned over the SVG) - this is a genuine extension of the existing 3-way pending/active/ended split, not an
  invented metric, since a single-value gauge (like the reference's own "Peak Demand 88") doesn't fit data that's already a
  3-way breakdown. The legend beside it (`#dashSplitLegend`) is unchanged in content, just laid out in a column next to the
  gauge instead of below a bar.
- **Monthly bar chart** (`monthlyStartCounts()`, `#dashBars`) is the reference's weekly bar-chart widget, adapted to data this
  app actually has: PM-SALE jobs carry no day-of-week meaning of their own, so the 6 bars are the last 6 months by `startDate`
  count instead, with the current month highlighted in `--accent` (`.dash-bar-col.current`) the same way the reference
  highlights one weekday. Bar height is `count / max(counts) * 90px`, floored at 8px so an empty month still shows a visible nub.
- **Segmented toggle**: `.subtabs` (already shared by the dashboard's ซื้อขาย/โครงการ switch and the audit log's sub-tabs) changed
  from a row of separately-raised pills to a proper segmented control - the track itself is now one shallow inset groove
  (`box-shadow:var(--shadow-inset-sm)` on `.subtabs`) and the active option pops up out of it (`--shadow-ext-sm` on
  `.subtab-item.active`), matching the reference's ACCOUNT/CLIENT switcher and the same raised-vs-pressed language used
  everywhere else in the Neumorphism system above. Both existing call sites (`#dashJobBar`'s two buttons, now wrapped in a
  `.subtabs` div; the audit page, already wrapped) picked this up with no JS changes.

## แผนดำเนินงานโครงการ list: per-project topic tracker
Each card on the Action Plan LIST page (`renderPlanList()`, `#planCards` - not the Gantt chart you get after clicking
into one project) shows a compact vertical step tracker of that project's own plan topics (`planTrackHtml()`), replacing
what used to be a single "N หัวข้อ · ดำเนินการแล้ว X/Y" text line with nothing else - added after a screenshot-driven
UI-component brief (a shadcn-style "order/process tracker": done rows checked with a green connector, one live row with
a pulsing marker, pending rows muted), adapted to this app's own Neumorphism tokens rather than the brief's literal
light-mode palette, and confirmed with the user to apply to the LIST page's cards specifically, not the per-project
Gantt detail view. The project's own start–end date range line that used to sit under the customer line was dropped
entirely ("ส่วนเวลา เอาออก") - a tracker row shows only its state and title, not a date. Rows are the project's `plan[]`
topics **in their own existing order** ("ลำดับ อ้างอิงจากหัวข้อใหญ่ของโครงการ") - never re-sorted by date or urgency -
and each topic's state is one of `done` (checked wherever it falls, even if a later topic finished first out of order),
the single `live` row (the FIRST not-yet-done topic walking the list in order - there is always at most one), or
`pending` (every not-done topic after that one, muted). A topic that is itself `late`/`soon` (via the existing
`topicState()`) gets a small badge next to its title using the same `badge expired`/`badge soon` classes the old
summary line's late/soon counts used to show, so that signal wasn't lost, just moved onto the specific row it applies
to instead of a page-level count. Below each topic's title, its own sub-items (`t.subs[]`, หัวข้อย่อย) are listed as one
muted line joined by " · " ("ส่วนข้อความด้านล่างหัวข้อใหญ่ ให้แสดงหัวข้อย่อยของโครงการ") - plain descriptive text, not a
second level of tickable rows, since editing still happens in the full Gantt after clicking into the project. The
connector below a row's own marker (`.plan-track-marker-col::after`) is colored per that SAME row's state (green if it's
done, muted otherwise) rather than needing to know its neighbour's state, so a topic can be inserted or removed from
`plan[]` without any row needing to recompute another row's connector color - each row really does own its own
connector, per the original component brief's own implementation note.

## ปฏิทิน (Calendar)
A top-level page (its own permanent rail icon, next to แดชบอร์ด - not folded into a group, same reasoning as dashboard/Action
Plan). It shipped first as a deliberately separate "warm editorial" design system, then was folded into the shared Neumorphism
tokens above once the user asked for one consistent look everywhere - `.cal-root` (`= #tab-calendar`) now just reuses
`var(--paper)`/`var(--card)`/`var(--shadow-*)`/etc like every other page, plus two hue-only tokens for its own two categories
that don't already have a shared semantic colour (`--cal-blue` for โครงการ, `--cal-plum` for นัดหมาย - sale/plan/delivery reuse
`--accent`/`--ok`/`--sun` directly). `.cal-root{ margin:-32px -36px; }` still cancels out `.content`'s own padding so the page
reads as a full-bleed canvas; `.cal-topbar{ position:sticky; top:0; background:var(--paper); }` **must stay fully opaque** -
it briefly shipped with a translucent `rgba(...,0.92)` + `backdrop-filter:blur()` background (copied from the original design
brief) which let scrolled-away content underneath show through as a blurred, overlapping mess once the page had enough rows
to scroll - a real regression caught from a screenshot, not something a computed-style test would have flagged.

**`.cal-root` scrolls itself** (`height:calc(100% + 64px)` - the `+64px` exactly cancels `.content`'s own 32px top+bottom
padding so the box still coincides with `.content`'s edges rather than overflowing it; `+40px` in the `max-width:760px`
version, matching `.content`'s smaller 20px mobile padding; `overflow-y:auto` on `.cal-root` itself) instead of relying on
the shared `.content` scroll container the rest of the app uses. `position:sticky` needs an unambiguous nearest *scrolling*
ancestor to stick against, and depending on it also being `.content`'s job for every other tab made that ambiguous enough
that the sticky topbar worked in some viewports/checks (`scrollTop` assigned via JS) but not for the user's own real
mouse-wheel scroll in an actual browser - giving the calendar its own dedicated scroll box removed the ambiguity outright.
Verify a scroll-locked header like this with a real `page.mouse.wheel()` in a test, not just a JS-assigned `scrollTop` -
they can disagree on which element sticky treats as the scrolling ancestor.

Four of five event categories are derived, read-only, from records the app already has (`buildCalendarEvents()`):
- **ซื้อขาย** - a sale's own `startDate` ("สั่งซื้อ").
- **โครงการ** - a project's `startDate` ("เซ็นสัญญา") and `endDate` ("สิ้นสุดสัญญา").
- **แผนดำเนินการ** - every Action Plan leaf step's own due date, via the existing `planLeaves(p.plan)` helper (same one the
  Gantt chart uses), titled with the step's own name.
- **ส่งงาน/ประกัน** - each entry in a project's `deliveries[]` (by its own `date`) and the computed warranty expiry
  (`projectWarranty(p).expiry`) share one bucket, since both read as "something falls due" for the same audience.

Clicking one of those four calls `openProjectView(id)` - hands off to that job's own read-only view modal, same as clicking a
row on the ซื้อขาย/โครงการ list. Because none of these dates carry a time-of-day (`startDate`/`endDate`/etc. are plain
`YYYY-MM-DD` strings), the original reference design's hourly time-grid, current-time line, and side-by-side
overlapping-time-slot split were all left out - there's no time component to position them against - and every event instead
renders as a whole-day chip (`calChip()`) inside whichever view is active: **เดือน (month, default)** - a traditional 6-row
grid, up to 3 chips per cell plus a "+N เพิ่มเติม" overflow count; **สัปดาห์ (week)** - 7 day columns, each stacking that
day's chips vertically; **วัน (day)** - a single large-format agenda list for one day. The topbar's month/year title uses
`MONTH_TH_FULL` (full Thai month names) rather than the abbreviated `MONTH_TH` used everywhere else in the app (`fmtDate()`
etc.), since this page's own header was specifically asked to spell the month out in full.

**Jumping to an arbitrary date**: the calendar mark (`#calJumpBtn`, top-left) opens a native `<input type="month" id="calJumpDate">`
(`showPicker()`, sized to 1x1px and hidden - it's a real form control, just not one meant to be seen directly) rather than a
persistent mini-month grid in the sidebar - the sidebar's own mini-calendar was removed and "ปฏิทินของฉัน" moved up to take
its place, per the user's own call that a small always-visible grid wasn't worth the space next to a one-click native picker
that already handles jumping years back or forward faster than paging a mini-grid month by month. `type="month"` (not `date`,
the original choice) was asked for specifically so the picker itself only ever offers month+year, no day - its `value` is
`"YYYY-MM"`, so `calGoToDate()` gets `+'-01'` appended (jump to the 1st of that month) and `renderCalendar()` fills the
control back from `calRefDate` via `.slice(0,7)` rather than the full `calYMD()` string.

**นัดหมาย (appointment) is the fifth category, and the one real thing this page lets you create.** Unlike the other four, it
has an actual time-of-day and its own Firestore collection, `pm_appointments` (`title`, `date`, `time`, `customerId`/
`customerName`, `mode:'visit'|'online'`, `location` (mode `visit`) or `link`/`meetingId`/`passcode` (mode `online`),
`createdBy`/`createdAt`) - scoped and rule-gated exactly like `pm_customers` (own-`createdBy` read/write for a non-admin, admin
sees everything; see `firestore.rules` - **publish it before this feature works for a non-admin**). It has no soft-delete: an
appointment is a personal scheduling note, not business data, so "ลบ" in `#appointmentModal` calls `.delete()` for real rather
than routing through Trash. "+ รายการใหม่" opens that same modal directly (`openAppointmentModal(null, calYMD(calRefDate))`,
pre-filling the date/time inputs to whatever day is currently focused) - there's no dropdown to also create a sale/project from
here any more, since the page's purpose was reframed specifically around booking appointments, not general record creation.
The mode toggle (`#apptModeSwitch`) reuses the shared `.subtabs`/`.subtab-item` segmented-control classes directly; picking
"เข้าพบลูกค้า" shows only the location field, "ออนไลน์" shows link/meeting-ID/passcode instead (`setApptMode()` toggles both the
active class and each field group's `display`). Editing reopens the same modal pre-filled (`editingAppointmentId` set) rather
than a separate view-then-edit step like the ซื้อขาย/โครงการ pattern - a single-owner scheduling note doesn't carry the same
multi-editor risk that pattern exists to guard against. Its time is two plain `<select>`s (`#apptHour` 00-23, `#apptMinute`
00-59, joined as `"HH:MM"`) rather than `<input type="time">` - a native time input's displayed format (12h AM/PM vs 24h)
follows the browser/OS locale rather than anything the page controls, and the user specifically wants 24-hour shown
regardless of whoever's machine is looking at it.

"ปฏิทินของฉัน" category checklist (`calActiveCats`, a real filter - unticking a category hides it from the grid and the
up-next list) and "ถัดไป" mini-agenda (next 6 upcoming events, ignoring the search box but respecting the category filter)
are driven off the same single `calRefDate`/`calActiveCats`/`calSearchTerm` state and `buildCalendarEvents()` call - there's
no separate data path per widget. `calYMD()`/`calParseYMD()` format and parse `YYYY-MM-DD` using local date components
(never `toISOString()`, which converts through UTC and can roll the date back a day
depending on the browser's timezone offset).

## Language: English overlay
A toggle in the rail menu (`#langToggleBtn`, next to the dark-mode toggle - same `localStorage` persistence pattern,
`pm-sale-lang`) switches the whole on-screen app between Thai (the real, permanent content of every hardcoded string in
the HTML and every `render*()` function) and English. **The underlying content never becomes English** - rewriting every
one of the hundreds of Thai strings across a 5000+ line single file to route through a translation-key helper would be a
far larger, far riskier refactor (every future patch would touch a key AND a dictionary entry instead of just a string),
so English mode works as a dictionary-driven overlay instead: `I18N_EN` maps an exact Thai phrase to its English
translation, and `translatePage()` walks the live DOM (text nodes, plus `placeholder`/`title`/`aria-label` attributes)
swapping any EXACT match. The original Thai is stashed on the node itself (`node.__pmTh`) the first time it's touched, so
switching back to Thai is a plain restore from that stash, not a second dictionary or a page reload. Matching is
exact-string, never substring, specifically so a customer's or project's own typed name is only ever at risk of being
mistranslated if it happens to be byte-for-byte identical to a UI phrase like "บันทึก" - the same trade-off any
dictionary-overlay i18n approach accepts when it doesn't fully separate template from data (this is what "ยกเว้นข้อมูลที่
กรอกเอง" - except self-entered data - meant in practice: never touch dynamic data by construction, not by detection).

Because nearly everything in this app re-renders via fresh `innerHTML` throughout normal use, the SAME debounced
`MutationObserver` that already drives `applyAria()` (`document.body`, `childList`+`subtree`) also re-runs
`translatePage()` on whatever just changed, whenever `currentLang === 'en'` - this is what makes newly-created Thai
nodes (a freshly re-rendered table, a modal that just opened) get caught the moment they appear, with no need to hook
every individual `render*()` call site by hand.

`applyLanguage()` itself also calls `renderActiveTab()` (guarded by `if (currentUserUid)`, so it's a no-op at the
pre-login `applyLanguage(savedLang)` call that restores the saved language on page load) right after `translatePage()`.
This was added after a real report that toggling the language left some things showing the old language until the
person switched tabs and back - the pieces below that pick their own Thai/English string directly off `currentLang`
(rather than a fixed string translatePage() can match) only regenerate that string when their OWN render function
next runs, which otherwise wouldn't happen until something else (a filter change, a Firestore snapshot, navigating
away and back) re-rendered that specific tab. Re-rendering the currently-open tab on every toggle is what makes the
switch feel instant instead of lagging one navigation behind.

**Two kinds of string need a different fix, not the dictionary:**
- **Composite strings** that mix a translatable word with dynamic data in the same text node - `renderPager()`'s
  "5 รายการต่อหน้า · 1–10 จากทั้งหมด 23 รายการ" line, for instance - can never exactly match a dictionary key once the
  numbers are filled in. `renderPager()` picks its own words directly off `currentLang === 'en' ? ... : ...` instead of
  relying on the overlay; any other composite string added later should follow the same pattern rather than trying to
  force it through `I18N_EN`.
- **Thai month names inside `fmtDate()`-style output** ("24 ก.ย. 2569") hit the same problem constantly (dates appear
  everywhere), so they get their own substring pass, `translateMonths()` / `MONTH_SUBSTR_EN`, applied after the
  whole-node dictionary check - safe as a substring replace specifically because Thai month abbreviations/names are
  long, punctuation-bearing, unlikely tokens. Buddhist-era year numbers are left as-is in both languages - that's a
  calendar-system choice, not a language one, outside this feature's scope. Single-CHARACTER Thai tokens (the
  ปฏิทิน's own day-of-week headers, "จ"/"อ"/"พ"...) are deliberately NOT in the dictionary or given a substring pass -
  a bare one-character match is too collision-prone (a user's avatar-initial letter could coincidentally BE one of
  them) - `CAL_DOW`/the month-grid's day row pick `CAL_DOW_EN`/an English array directly off `currentLang` instead,
  the same targeted pattern as the pager.

**Search-box placeholders and the `<p class="panel-note">` explanatory paragraphs are now covered too** - both were
flagged directly as an incomplete-translation report ("ตรงช่องค้นหา กับคำอธิบายจะเป็นภาษาไทยอยู่"), reversing the
"known gap" this section used to describe. All 10 page-specific search placeholders (ซื้อขาย/โครงการ/แผนดำเนินการ/
equipment/warehouse/serviceWarehouse/catalog/customers/users/audit - the calendar's own `#calSearchInput` already had
one) and every static panel-note across the app were added to `I18N_EN`, extracted programmatically from the live HTML
(a small Python script, not hand-retyped) specifically so the Thai dictionary KEY is guaranteed byte-identical to what
`translatePage()` will actually look up - a hand-typed multi-clause Thai string is exactly the kind of key that silently
fails to match on a single mistyped character, with no error, just a paragraph that stays Thai. A panel-note wrapping
part of its text in `<b>` (the ซื้อขาย/โครงการ list notes' own `<b>ซื้อขาย</b>`/`<b>โครงการ</b>` lead-in, and the item-status
lock note's `<b>ล็อคของ</b>`/`<b>ทันที</b>`) splits into MULTIPLE sibling text nodes at each tag boundary, each needing
its own dictionary entry - and since Thai has no inter-word spaces but English does, a fragment translation needs an
explicit trailing/leading space of its own at that boundary (`'immediately '`, `'...to '`) or the reassembled English
reads as one run-on word ("warehouseimmediately") - trimmed only for the dictionary LOOKUP, not for what actually gets
written back into the node's rendered text. The two `photosEquipHint`/`photosInstallHint` panel-notes are NOT static -
`addProjectPhotos()`'s caller sets their `textContent` from a template string mixing static wording with a live
`fmtBytes()` byte count and a `sale ? 'ซื้อขาย' : 'โครงการ'` branch - a composite string can never exactly match a
dictionary key once the number is filled in (the same limitation `renderPager()` already worked around), so it was
made `currentLang`-aware directly instead, picking its own English or Thai template string rather than going through
`I18N_EN` at all. The printed
handover/Action Plan PDFs (`#printArea`) are explicitly excluded from `translatePage()` and always print in Thai
regardless of the on-screen language, since the document must keep matching `docs/handover-template.docx` exactly (see
"Printing"). The two `"แผนดำเนินการ (Action Plan)"` labels found during this work (a nav tooltip and a page title) had
their redundant English half removed, since a real language toggle makes a permanently-bilingual label just show the
same name twice depending on which language is active.

## Data model (short)
`pm_projects` (`jobType` sale | project; items[] link to `pm_warehouse` (goods, `kind:'good'`) or `pm_serviceWarehouse` (services, `kind:'service'`, `svcId` instead of
`whId` - see "Service warehouse" below); plan[] for projects; `docNo`, `contractNo`, `poNo`; project installments: `installmentTotal`, `installmentNo` (last delivered,
printed as "3/4"), `deliveries[]` written by the "ส่งงาน" dialog; the โครงการ list's own "งวดงาน" column/filter reads `currentInstallmentStage()` - the next undelivered
installment, or the last one once everything is in - not `installmentNo` directly; `closedAt`/`closedBy`, ซื้อขาย only - see "ปิดงาน" below), `pm_customers`, `pm_companies`,
`pm_warehouse` (quantity, serials[], history[] capped 500), `pm_serviceWarehouse` (same shape minus quantity/serials/history - services aren't stocked),
`pm_counters` (SO/PJ + yyyymmdd -> n; the admin session raises them via `syncDocCounters()`), `pm_catalogs` + `pm_catalogChunks`, `pm_files` (attachments, base64, <=650 KB
each, 8 per project - a `role:'closing'` one is the ปิดงาน signed document instead, exactly one per job, not one of the 8), `pm_photos` (handover photos, base64 <=900 KB
each - see "Handover photos" below), `pm_users` (`status` approved|pending|rejected; no status = approved),
`pm_pendingRoles` (invites), `pm_auditLog`/`pm_errorLog` (immutable), `pm_appointments` (ปฏิทิน's own นัดหมาย records - see
"ปฏิทิน (Calendar)" below; no soft delete, a real `.delete()`). Soft delete = `deletedAt`; the Trash tab (admin) restores / purges.

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
  `p.photoCounts.equipment`/`.install > 0`. `#projectsColumnsBtn` opens `#projectColumnsModal`, backed by `PROJECT_COLUMNS` / `projectColumnPrefs`
  (localStorage `pm-sale-project-columns`).
- **ซื้อขาย** (`#salesTable`): only 2 sub-columns ("รูปภาพอุปกรณ์" / "รูปภาพงานติดตั้ง" - a sale has no plan, so no first column). Backed by its own
  `SALES_COLUMNS` / `salesColumnPrefs` (localStorage `pm-sale-sales-columns`), opened by `#salesColumnsBtn`.
- Both column-picker triggers live the same way now (moved off a toolbar text button, to match): the rightmost `<th>` of their own table header,
  a small `⚙` icon button (`#projectsColumnsBtn` / `#salesColumnsBtn`) rather than a labelled button in the filter-bar - โครงการ's used to be the
  odd one out with a "คอลัมน์" text button in the filter-bar, moved here so both lists behave identically.
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

## Item status: live warehouse lock ("เลือกแล้ว")
Flipping a **goods** line's status between "รอดำเนินการ" and "เลือกแล้ว" (the option used to read "ดำเนินการแล้ว" - renamed since the act of
picking it now genuinely reserves the stock, not just marks work done) hits `pm_warehouse` immediately when editing a job that has already been
saved at least once (`editingProjectId` set) - not deferred to "บันทึกรายการ" like everything else on the form, so two people editing different jobs
at once can't both grab the same units. A brand-new, never-saved job still waits for its first save (there's no id/docNo yet for the warehouse's own
history entry to point at), and a **service** line is untouched either way (no `whId`, nothing to lock) - `setItemStatus()` only routes into
`lockOrUnlockItem()` when `editingProjectId && it.kind !== 'service' && it.whId`.

`lockOrUnlockItem(i, to)` re-renders the row **before** opening its own `confirmAction()` (not the end-of-form one) - this snaps the `<select>` back
to its real, unchanged value for as long as the dialog is up, so cancelling needs no separate revert step. On confirm, one transaction (a) applies the
effect to the warehouse via `warehouseEffectPatch()` - the same per-item math `commitProject()` uses, extracted so there is exactly one place that
turns an effect into a warehouse write - and (b) overwrites the project doc's own `items[]` with a **full fresh snapshot** from
`buildItemsFromEditing()` (not a single-field patch), so a row that's brand new to this editing session (just added, never saved) is captured too, and
nothing between one live toggle and the next can go stale. `editingOrigItems` is updated to match afterward, so the whole-form save's own
`stockEffects()` diff sees the row as already applied and never touches it a second time - saving the rest of the form after a live toggle shows no
stock-effects confirm at all. Deleting a **locked** (`status:'done'`) goods row (`removeItemRow()`) goes through the same live give-back-then-write
path before splicing it out, for the same reason. A failed transaction (not enough stock, a serial already gone) reverts the row's status locally and
toasts the error; nothing was written.

## ซื้อขาย: ปิดงาน
`closeJobButton(p)` - ซื้อขาย row-actions only, never on โครงการ - reads "ปิดงาน" until `p.closedAt` is set (then "ปิดงานแล้ว", permanently disabled) and
is otherwise disabled with an explanatory `title` until the job has at least one saved photo (`p.photoCounts.equipment`/`.install > 0`). Clicking it
opens `#closeJobModal`: an editable date (`#closeJobDate`, defaults to today, backdatable - a job can be closed for a date in the past) and a required
single-file upload, the signed handover document. That file is its own `pm_files` row with `role:'closing'` rather than one of the general 8 "ไฟล์แนบ" -
`loadProjectFiles()` filters `role === 'closing'` out of that list/count entirely, and there is always at most one per job (re-closing deletes the
previous one first, since `pm_files` rows can't be updated in place - `allow update: if false`). Saving writes that file plus `closedAt`/`closedBy` on
the project doc; no new Firestore rules were needed for either write (`pm_files` create has no `hasOnly()` on keys, and the `pm_projects` update rule
has no field restriction). `projectStatus()`/`statusLabelFor()` treat a closed sale as `'ended'` unconditionally (regardless of its item lines' own
done/pending state) with the label overridden to "ปิดงานแล้ว" instead of the normal "ดำเนินการแล้ว" for that status - this is what actually shows the
closed state in the ซื้อขาย list's own "สถานะ" column, not a separate badge element. Once closed, "ลบ" is disabled too (with the same explanatory
`title`) so a closed sale can never be soft-deleted - `deleteEntity()` itself also refuses (`type === 'projects' && x.closedAt`), matching the button's
own disabled state, in case delete is ever triggered another way. A disabled `.icon-btn` (this button while ineligible, "ลบ" once closed, or any other
row-action button disabled elsewhere) now actually looks disabled - `.icon-btn:disabled` (greyed text/background, `cursor:not-allowed`) was missing
entirely before this, so a disabled row-action button looked completely identical to a clickable one.

## โครงการ/ซื้อขาย lists: click-a-row to view, edit-in-place
Clicking anywhere on a job row (`tr.job-row`, everywhere except inside its own `.row-actions` - guarded by `event.target.closest('.row-actions')`
in the row's own `onclick`, since the action buttons that remain must still work on their own) opens `#projectModal` in a new **read-only "view"
mode** (`openProjectView(id, kind)` -> `openProjectForm()` then `setProjectViewMode(true)`) instead of jumping straight to the editable form - the
same fields the edit form shows, just disabled. This replaced three of the row's own buttons (รูปภาพ/แก้ไข/พิมพ์ PDF), which now live inside the
modal itself, top-right next to the title (`#prjViewActions`), so a row only keeps the buttons that don't fit that pattern: ซื้อขาย keeps
`closeJobButton(p)` (ปิดงาน) + ลบ; โครงการ keeps แผนงาน, ส่งงาน (if it has installments) + ลบ.

`setProjectViewMode(on)` toggles a single `<fieldset id="prjFormFieldset">` (wrapping everything in `#projectForm` except the footer's
ยกเลิก/บันทึกรายการ) disabled or not - this disables every input/select/button inside in one shot (item-row selects, +เพิ่มสินค้า/+เพิ่มบริการ, the
file-attach button, per-row remove buttons) with no separate per-field wiring, rather than a CSS-only look that would still let clicks through.
It also shows/hides `#prjViewActions`, hides/shows the "บันทึกรายการ" submit button, and swaps "ยกเลิก" for "ปิด" and the title between
"รายละเอียด..." and "แก้ไข.../เพิ่ม...". Clicking **แก้ไข** inside the view (`#prjViewEditBtn`) just calls `setProjectViewMode(false)` on the *same*
already-open modal - editing happens in place, so there's never a second modal stacked on top of the first. Clicking **รูปภาพ**
(`#prjViewPhotosBtn`) closes this modal and calls `openPhotosPage(id, {fromView:true})`; **พิมพ์ PDF** (`#prjViewPrintBtn`) calls `printProject()`
directly without closing anything. The `{fromView:true}` flag (`photosBackToView`) is what makes the photo page's own "← กลับ" button reopen the
same read-only view modal instead of dropping back onto the bare list - without it, going รายการ -> รูปภาพ -> กลับ used to land on the plain
ซื้อขาย/โครงการ list, forcing the row to be clicked all over again to get back to where you were. The other two callers of `openPhotosPage()`
(a brand-new sale's save routing straight there, and Action Plan's "รูปภาพ →") pass no `opts`, so "กลับ" still behaves exactly as before for them
- only a รูปภาพ click that came from inside the view modal gets this shortcut back into it. `openProjectForm()` itself always resets to `setProjectViewMode(false)` before opening, so every OTHER existing entry
point into the same modal (the dashboard's job click, Action Plan's own "แก้ไข", the warranty page's/serial page's/company page's links into a
project) is untouched and still opens straight into the normal editable form - only a row click on the ซื้อขาย/โครงการ list itself goes through
`openProjectView()` first. `setProjectViewMode()` recomputes the title from scratch on every call (`on ? 'รายละเอียด'+jobWord : (p?'แก้ไข':'เพิ่ม')+jobWord`)
rather than only setting it inside `if(on)` - the first version only ever set the "รายละเอียด..." title and never put "แก้ไข..." back once `#prjViewEditBtn`
switched view mode back off, since nothing else re-ran `openProjectForm()`'s own title line on that path. No test had asserted the title text after that
specific transition, so it shipped once before being caught.

## โกดังบริการ: click-a-row to view, edit-in-place
Same pattern as the ซื้อขาย/โครงการ lists above, applied to `#serviceWarehouseModal`: clicking a row (`onclick` on the `<tr>`, guarded by
`event.target.closest('.row-actions')` the same way) opens the existing add/edit modal in a read-only view first (`openServiceWarehouseView(id)` ->
`openServiceWarehouseForm()` then `setServiceViewMode(true)`), with a single **แก้ไข** button (`#svcViewEditBtn`, next to the title - there's no
รูปภาพ/พิมพ์ PDF equivalent here) switching the same modal into the normal editable form in place. `setServiceViewMode(on)` disables
`<fieldset id="svcFormFieldset">` (wrapping the whole form-grid, including the addable-select "+" buttons for ซัพพลายเออร์/ประเภทงาน), hides the
"บันทึก" button, and swaps "ยกเลิก"/"ปิด" and the title the same way the project modal does - recomputing the title on every call rather than only
under `if(on)`, having already caught that mistake once on the project modal above. The row's own separate "แก้ไข" button was removed (`ลบ` is all
that's left in `.row-actions`) since the view modal now provides one - โกดังบริการ has no serials/quantity/history the way โกดังสินค้า's own
`openSerialModal()` shows, so reusing the just-built view-mode pattern (disable the existing form) made more sense here than adding a second,
service-specific read-only viewer. โกดังสินค้า's row-level "แก้ไข" (`openWarehouseForm()` called directly off the row) was later dropped too, for
the same reason: its row click already opens `#serialModal`, which has always had its own `#serialEditBtn` - `.row-actions` there now holds only
"ลบ" (admin), matching โกดังบริการ.

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

The items table (`.ho-items`, goods and services both) prints smaller than the rest of the document - 12pt main text / 10pt sub-text (the `.sub`
parenthetical line under a name), down from the document-wide 14pt/12pt that `.ho-t td, .ho-t th` still sets for every other table (section 1's
"ข้อมูลทั่วไป" info table included) - the items rows were the tightest-packed part of the page and the user asked specifically to shrink only
those. `.ho-items` cells are centered by default but `td:nth-child(2)` (รหัสสินค้า/ยี่ห้อ) and `td:nth-child(3)` (รายละเอียด) are left-aligned instead,
since a code and a free-text description read better ragged-left than centered; the remaining columns (#, รหัสอุปกรณ์/serial, จำนวน) stay centered.
Section 4's checklist gained a fourth line, "เอกสารแสดงรูปภาพของรายการอุปกรณ์ (ถ้ามี)", inserted right after "คู่มือการใช้งานอุปกรณ์ของโครงการ (ถ้ามี)"
and before "เอกสารแสดงรายละเอียดของงานติดตั้ง (ถ้ามี)" - the handover photos feature above already produces a per-project photo set, so the printed
checklist should offer to check it off alongside the other attachments.

## Loading gate: watchdog
`#loadingOverlay` ("กำลังโหลดข้อมูล...") only clears once `checkAllLoaded()` sees all six of `projects`/`customers`/`companies`/`warehouse`/
`serviceWarehouse`/`users` report their first `onSnapshot` back - but every tab already renders progressively off whatever has arrived so far
(`onAnyUpdate()` re-renders on every single one of those snapshots, not just the last). If a connection to just one of the six stalls or drops
(flaky network, a backgrounded/throttled tab, one bad listener), the app underneath was already fully usable while this plain block element -
it isn't a fixed/blocking overlay, just sits inline above the tab panels in `.content` - kept showing forever, which read as the page being stuck
loading even though everything below it worked. `attachRealtimeListeners()` now also arms an 8s `loadingWatchdog` timeout that force-clears the
overlay (and logs which key(s) never reported, via `console.warn`) if `checkAllLoaded()` hasn't already done it naturally; `checkAllLoaded()` and
`detachListeners()` (called on every fresh sign-in and on sign-out) both clear that timer so it never fires after a normal load or leaks into the
next session.

## Sample data
Rows tagged `sample: true` / names starting `[ตัวอย่าง]` are test data (generators in `tests/fixtures/`). `#deleteSampleDataBtn` on the (admin-only) Trash page
hard-deletes every `sample: true` doc across `SAMPLE_DATA_COLS` (`pm_companies`, `pm_customers`, `pm_warehouse`, `pm_projects`, `pm_pendingRoles`, `pm_photos`) in
one go, whether that row is currently live or already sitting in the Trash - it queries each collection directly (`where('sample','==',true)`), not through the
Trash's own `deletedAt` listing, so a soft-deleted sample row is caught too. `pm_photos` has no Trash concept of its own but is swept the same way, so a sample
project's own handover photos (see `#projectsAddSampleBtn` below) never outlive it as orphaned rows. No rules change was needed: admin already has unconditional
delete on all six of those collections. Real, non-sample rows are matched by the same tag and are never touched. Audit-log rows written while seeding still
cannot be deleted (rules) - this button doesn't try to.

`#warehouseAddSampleBtn` on the โกดังสินค้า page (admin-only, same visibility toggle pattern as `#catalogUploadBtn`) is a matching one-click **add**: a fixed
`SAMPLE_WAREHOUSE_SET` of 5 real-looking items (3 CCTV, 2 Switch; every field filled in, including a full set of unique serials sized to each item's own
quantity), tagged `sample: true` and named `[ตัวอย่าง] ...` so it's picked up by `#deleteSampleDataBtn` above like any other sample row, and just as
deletable one at a time through the page's own normal "ลบ" -> Trash flow. Guards against creating the set twice (checks `data.warehouse` for any of its
five `part` codes first) since, unlike the bulk generators in `tests/fixtures/`, this one is meant to be clicked from the live production site by an
admin, not just seeded once for a test run. Written directly with `history: []` and `sample: true` as extra keys beyond `pm_warehouse`'s non-admin
`hasOnly()` create rule - safe only because the button itself is admin-only, since `pmIsAdmin()` bypasses that key restriction entirely.

`#projectsAddSampleBtn` on the โครงการ page (same admin-only pattern) is the same idea for โครงการ specifically: 5 real-looking projects
(`PROJECT_SAMPLE_DEFS`), each with every field filled in, one linked-looking (but unlinked - `whId:''`, so it never touches real warehouse stock)
equipment line already `status:'done'`, a 5-step Action Plan (`PROJECT_SAMPLE_PLAN_STEPS`) with every step `done:true`, and installments one short of
the total (`installmentNo = installmentTotal - 1`, `deliveries[]` filled to match) so the โครงการ list's own "งวดงาน" column reads "รอส่งงวดที่ N" for
the LAST installment - ready to hand over via "ส่งงาน". Each project also gets two real `pm_photos` rows (one per set, tagged `equipBrand`/`equipName`/
`equipSerial` from its own item line) so its "รูปภาพ" page has something real to open and print, not just a ticked checkbox with nothing behind it -
`photoCounts` is set to match. Reuses the first existing company for the letterhead if there is one, else makes a throwaway sample one; its own sample
customer is always created fresh. Everything (customer, company if made, 5 projects, 10 photos) is `sample: true`, so `#deleteSampleDataBtn` cleans all
of it up together. Guards against duplicating the set the same way `#warehouseAddSampleBtn` does (checks project names first).
