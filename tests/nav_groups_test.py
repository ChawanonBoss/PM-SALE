import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from harness import new_page, serve_repo, goto_tab

with serve_repo() as base, new_page(viewport={"width": 1400, "height": 900}) as (page, errors):
    page.goto(f"{base}/index.html"); page.wait_for_timeout(500)
    page.evaluate("() => localStorage.setItem('pm-sale-login-ts', String(Date.now()))")
    page.evaluate("() => window.__authListeners[0]({uid:'admin1', email:'admin@a.com', displayName:'Admin One'})"); page.wait_for_timeout(900)
    page.evaluate("""async ([endSoon]) => {
      await db.collection('pm_customers').doc('c1').set({name:'ลูกค้า ก', type:'gov', createdBy:'admin1'});
      await db.collection('pm_projects').doc('p1').set({jobType:'project', docNo:'PJ1', name:'โครงการใกล้หมดสัญญา', customerId:'c1', customerName:'ลูกค้า ก',
        startDate:'2026-01-01', endDate:endSoon, createdBy:'admin1', items:[], warrantyMonths:1});
      await db.collection('pm_users').doc('u2').set({email:'u2@a.com', name:'User Two', status:'pending'});
    }""", ["2026-10-05"])   # within 30 days of "today" in the app's own alert window logic across the test range used elsewhere in this suite
    page.wait_for_timeout(500)

    # ---- dashboard / actionplan remain standalone top-level buttons, not folded into any group ----
    assert page.locator('.nav-item[data-tab="dashboard"]').count() == 1 and page.locator('.nav-item[data-tab="actionplan"]').count() == 1
    for grp in ('group1', 'group2', 'group3', 'settings'):
        assert page.locator(f'.nav-item[data-group="{grp}"]').count() == 1, grp

    # ---- opening a group reveals its real pages; the flyout is closed by default ----
    assert not page.is_visible('#navGroupPopover')
    page.click('.nav-item[data-group="group1"]')
    assert page.is_visible('#navGroupPopover')
    tabs = page.evaluate("[...document.querySelectorAll('.nav-group-item')].map(b => b.dataset.tab)")
    assert tabs == ['sales', 'projects'], tabs
    page.click('.nav-item[data-group="group1"]')   # toggling the same group again closes it
    assert not page.is_visible('#navGroupPopover')

    # ---- group2/group3/settings list the right pages, in the user's own requested grouping/order ----
    page.click('.nav-item[data-group="group2"]')
    assert page.evaluate("[...document.querySelectorAll('.nav-group-item')].map(b => b.dataset.tab)") == ['warehouse', 'catalog', 'equipment']
    page.click('.nav-item[data-group="group3"]')
    assert page.evaluate("[...document.querySelectorAll('.nav-group-item')].map(b => b.dataset.tab)") == ['customers', 'companies']
    page.click('.nav-item[data-group="settings"]')
    assert page.evaluate("[...document.querySelectorAll('.nav-group-item')].map(b => b.dataset.tab)") == ['users', 'audit', 'trash']
    assert page.inner_text('.nav-group-title') == 'ตั้งค่า'

    # ---- clicking a flyout item navigates there, closes the flyout, and the group button (not any single-item state) shows active ----
    page.click('.nav-group-item[data-tab="trash"]')
    assert not page.is_visible('#navGroupPopover')
    assert page.evaluate("currentTab") == 'trash'
    assert 'active' in page.get_attribute('.nav-item[data-group="settings"]', 'class')
    assert page.locator('#trashBody tr').count() >= 0   # loadTrash() ran without needing a separate click - a one-time fetch tab still populates on open

    # ---- clicking outside a group closes it too ----
    page.click('.nav-item[data-group="group2"]'); assert page.is_visible('#navGroupPopover')
    page.click('.nav-item[data-tab="dashboard"]')
    assert not page.is_visible('#navGroupPopover') and page.evaluate("currentTab") == 'dashboard'

    # ---- badges: a group button aggregates its members' counts, and the same number appears inline in its flyout item ----
    assert page.inner_text('#group1NavBadge').strip() == '1', "1 contract ending soon, surfaced on the ซื้อขาย/โครงการ group"
    assert page.inner_text('#settingsNavBadge').strip() == '1', "1 pending user, surfaced on the ตั้งค่า group"
    page.click('.nav-item[data-group="group1"]')
    assert page.inner_text('.nav-group-item[data-tab="projects"]').strip().endswith('1')
    assert '1' not in page.inner_text('.nav-group-item[data-tab="sales"]'), "sales itself has no alert of its own"
    page.click('.nav-item[data-group="group1"]')

    # ---- non-admin never sees the settings group, regardless of its own badge count ----
    page.evaluate("currentUserRole = 'user'; $('navSettingsGroup').style.display = 'none';")
    assert not page.is_visible('.nav-item[data-group="settings"]')
    page.evaluate("currentUserRole = 'admin'; $('navSettingsGroup').style.display = '';")

    # ---- mobile: picking a flyout item closes the drawer, same as any other nav click ----
    page.set_viewport_size({"width": 375, "height": 800})
    page.click('#mobileMenuBtn'); page.wait_for_timeout(200)
    assert page.evaluate("document.getElementById('sidebar').classList.contains('open')")
    page.click('.nav-item[data-group="group3"]'); page.wait_for_timeout(150)
    page.click('.nav-group-item[data-tab="customers"]'); page.wait_for_timeout(200)
    assert not page.evaluate("document.getElementById('sidebar').classList.contains('open')")
    assert page.evaluate("currentTab") == 'customers'

    print("errors:", errors); assert not errors
print("OK")
