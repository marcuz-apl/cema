from playwright.sync_api import Page, expect

def test_home_loads(page: Page):
    page.goto("http://localhost:4070")
    expect(page.locator("h1")).to_contain_text("CEMA")
