from playwright.sync_api import Page, expect

def test_home(page: Page):
    page.goto("http://localhost:4070")
    expect(page.locator("h1")).to_contain_text("CEMA")

def test_telemetry_visible(page: Page):
    page.goto("http://localhost:4070")
    expect(page.locator(".telemetry")).to_be_visible()

def test_filter_bar(page: Page):
    page.goto("http://localhost:4070")
    expect(page.locator(".filter")).to_be_visible()

def test_map_initialized(page: Page):
    page.goto("http://localhost:4070")
    expect(page.locator("#map")).to_be_visible()
