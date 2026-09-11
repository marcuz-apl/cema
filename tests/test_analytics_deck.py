"""Playwright E2E for the Analytics deck (needs the app serving on :4071)."""
import json
import re
import urllib.request

import pytest
from playwright.sync_api import sync_playwright

BASE = "http://localhost:4071"
TABS = ["overview", "time", "energy", "regions"]


def _catalog_size():
    with urllib.request.urlopen(f"{BASE}/api/v1/earthquakes?min_mag=0") as r:
        return json.load(r)["count"]


@pytest.fixture(scope="module")
def page():
    try:
        urllib.request.urlopen(BASE, timeout=3)
    except OSError:
        pytest.skip("CEMA app not serving on :4071")
    with sync_playwright() as p:
        browser = p.chromium.launch()
        pg = browser.new_page()
        pg.goto(BASE, wait_until="networkidle")
        yield pg
        browser.close()


def _open_deck(page):
    open_already = page.evaluate(
        "document.getElementById('analytics-modal').classList.contains('open')"
    )
    if not open_already:
        page.click("#btn-analytics")
        page.wait_for_selector("#analytics-modal.open")


def test_deck_opens_with_archive_catalog(page):
    _open_deck(page)
    page.wait_for_function(
        "document.getElementById('analytics-arch-count').textContent.match(/k/)", timeout=15000
    )
    expected = f"{_catalog_size() / 1000:.1f}k"
    assert page.inner_text("#analytics-arch-count") == expected


def test_kpis_are_real_not_placeholder(page):
    _open_deck(page)
    assert page.inner_text("#analytics-total-quakes") == f"{_catalog_size():,}"
    assert page.inner_text("#analytics-24h-kpi") != "—"
    assert "—" not in page.inner_text("#analytics-avg-depth-kpi")
    assert re.fullmatch(r"\d{4}-\d{2}-\d{2} — \d{4}-\d{2}-\d{2}", page.inner_text("#analytics-date-range"))
    assert page.inner_text("#analytics-max-mag-kpi").startswith("M")


def test_all_tabs_render_panes_and_charts(page):
    _open_deck(page)
    containers = {
        "overview": "#analytics-mag-chart .chart-bar-row",
        "time": "#analytics-monthly-chart svg",
        "energy": "#analytics-energy-curve svg",
        "regions": "#analytics-top-regions-list .region-row-ext",
    }
    for tab, selector in containers.items():
        page.click(f'.analytics-tab-btn[data-tab="{tab}"]')
        assert page.is_visible(f"#tab-analytics-{tab}")
        rows = page.query_selector_all(selector)
        assert rows, f"{tab}: no chart nodes under {selector}"
        # each pane keeps its chart populated with counts, not em-dashes
        if tab == "overview":
            assert "—" not in page.inner_text("#analytics-health-summary")
        if tab == "energy":
            assert page.inner_text("#analytics-energy-joules").endswith("PJ")
            assert page.inner_text("#analytics-energy-tnt").endswith("Mt")


def test_scope_toggle_switches_dataset(page):
    _open_deck(page)
    page.click("#btn-scope-view")
    page.wait_for_function("document.getElementById('btn-scope-view').classList.contains('active')")
    filtered = page.inner_text("#analytics-view-count")
    assert filtered not in ("—", "")
    assert page.inner_text("#analytics-total-quakes").replace(",", "") != "0"
    page.click("#btn-scope-archive")


def test_monthly_window_slider_pans(page):
    _open_deck(page)
    page.click('.analytics-tab-btn[data-tab="time"]')
    slider = page.query_selector("#timeline-window-range")
    if slider.get_attribute("disabled") is not None:
        pytest.skip("catalog shorter than window — slider disabled")
    before = page.inner_text("#timeline-slider-label")
    slider.fill("0")
    slider.dispatch_event("input")
    page.wait_for_function(
        f"document.getElementById('timeline-slider-label').textContent !== {json.dumps(before)}"
    )
    slider.fill("100")
    slider.dispatch_event("input")


def test_exports_fire_without_errors(page):
    _open_deck(page)
    page.wait_for_function("typeof window.html2canvas !== 'undefined'", timeout=15000)
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    with page.expect_download(timeout=20000) as dl:
        page.click("#btn-export-analytics-png")
    assert dl.value.suggested_filename.startswith("CEMA_Seismic_Bulletin_")
    assert not errors


def test_no_uncaught_page_errors(page):
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    _open_deck(page)
    for tab in TABS:
        page.click(f'.analytics-tab-btn[data-tab="{tab}"]')
    page.click("#analytics-modal-close")
    assert not errors


def test_regions_renders_top_10(page):
    _open_deck(page)
    page.click('.analytics-tab-btn[data-tab="regions"]')
    rows = page.query_selector_all("#analytics-top-regions-list .region-row-ext")
    assert len(rows) == 10
    assert "Top 10" in page.inner_text(".card-regions-left")


def test_all_tabs_fit_single_page_without_scroll(page):
    page.set_viewport_size({"width": 1440, "height": 900})
    _open_deck(page)
    for tab in TABS:
        page.click(f'.analytics-tab-btn[data-tab="{tab}"]')
        page.wait_for_timeout(250)
        overflow = page.evaluate("""() => {
            const body = document.querySelector('.analytics-modal-body');
            return body.scrollHeight - body.clientHeight;
        }""")
        assert overflow <= 2, f"{tab} overflows by {overflow}px (should be <= 2px for zero-scroll 1-page fit)"


def test_all_tabs_export_single_page_pdf(page):
    _open_deck(page)
    for tab in TABS:
        page.click(f'.analytics-tab-btn[data-tab="{tab}"]')
        page.wait_for_timeout(250)
        pdf = page.pdf(format="A4", landscape=True, print_background=True)
        pages = len(re.findall(rb"/Type\s*/Page[^s]", pdf))
        assert pages == 1, f"{tab} generated {pages} PDF pages (expected exactly 1)"


def test_energy_tab_cards_equal_height(page):
    page.set_viewport_size({"width": 1440, "height": 900})
    _open_deck(page)
    page.click('.analytics-tab-btn[data-tab="energy"]')
    page.wait_for_timeout(300)
    diff = page.evaluate("""() => {
        const left = document.querySelector('.card-energy-main');
        const right = document.querySelector('.energy-side-col');
        return Math.abs(left.getBoundingClientRect().height - right.getBoundingClientRect().height);
    }""")
    assert diff <= 1, f"Energy tab left card and right side heights differ by {diff}px (expected equal)"


def test_data_table_export_geojson(page):
    page.goto('http://localhost:4071', wait_until='networkidle')
    page.click('#btn-table')
    page.wait_for_selector('#table-modal.open')
    assert page.is_visible('#btn-export-geojson')
    page.click('#table-modal-close')


def test_all_tabs_have_identical_height(page):
    page.set_viewport_size({'width': 1440, 'height': 900})
    _open_deck(page)
    pane_heights = []
    panel_heights = []
    for tab in TABS:
        page.click(f'.analytics-tab-btn[data-tab="{tab}"]')
        page.wait_for_timeout(200)
        h = page.evaluate(f'''() => {{
            const pane = document.getElementById('tab-analytics-{tab}');
            const panel = document.getElementById('analytics-modal-panel');
            return {{ pane: pane.clientHeight, panel: panel.clientHeight }};
        }}''')
        pane_heights.append(h['pane'])
        panel_heights.append(h['panel'])
    assert max(pane_heights) - min(pane_heights) == 0, f"Pane heights differ: {pane_heights}"
    assert max(panel_heights) - min(panel_heights) == 0, f"Panel heights differ: {panel_heights}"


def test_png_export_filename_bears_tab_and_datetime(page):
    _open_deck(page)
    page.click('.analytics-tab-btn[data-tab="regions"]')
    page.wait_for_timeout(250)
    with page.expect_download() as dl:
        page.click('#btn-export-analytics-png')
    filename = dl.value.suggested_filename
    assert 'Regions' in filename
    assert re.search(r'\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2}\.png$', filename)


def test_data_table_scope_toggle_and_exports(page):
    page.goto("http://localhost:4071", wait_until="networkidle")
    page.click("#btn-table")
    page.wait_for_selector("#table-modal.open")
    assert page.is_visible("#btn-table-scope-1000")
    assert page.is_visible("#btn-table-scope-all")

    # Verify initial Latest 1000
    assert "active" in page.query_selector("#btn-table-scope-1000").get_attribute("class")

    # Toggle to All Time
    page.click("#btn-table-scope-all")
    tot = _catalog_size()
    tot_fmt = f"{tot:,}"
    page.wait_for_function(f"document.getElementById('table-count').textContent.includes('{tot_fmt}') || document.getElementById('table-count').textContent.includes('{tot}')")
    assert "active" in page.query_selector("#btn-table-scope-all").get_attribute("class")

    # Export CSV All Time
    with page.expect_download() as dl_csv:
        page.click("#btn-export-csv")
    assert "all_time" in dl_csv.value.suggested_filename

    # Export GeoJSON All Time
    with page.expect_download() as dl_geo:
        page.click("#btn-export-geojson")
    assert "all_time" in dl_geo.value.suggested_filename

    page.click("#table-modal-close")
