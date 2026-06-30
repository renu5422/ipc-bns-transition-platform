"""
Playwright E2E tests — Search flow.

Week 5 of Learning Plan: Playwright setup, locators, assertions, synchronization.

These tests simulate real user journeys through the frontend:
  1. Search for a keyword and see results
  2. Quick-example chips trigger a search
  3. Empty search shows validation (no crash)
  4. No-result query shows the empty-state message
  5. Dashboard loads and shows live API status

Prerequisites:
  - Backend running:  uvicorn backend.main:app --reload  (port 8000)
  - Frontend running: npm run dev  (port 3000)
  - Install Playwright: pip install playwright && playwright install chromium

Run:
  pytest tests/e2e/test_search_flow.py -v --headed   # with browser
  pytest tests/e2e/test_search_flow.py -v            # headless
"""

import pytest
from playwright.sync_api import Page, expect


FRONTEND_URL = "http://localhost:3000"
TIMEOUT = 10_000  # 10 s


# ── Fixtures ────────────────────────────────────────────────────────────────

@pytest.fixture(scope="session")
def browser_context_args(browser_context_args):
    """Use a larger viewport so all UI elements are visible."""
    return {**browser_context_args, "viewport": {"width": 1280, "height": 800}}


# ── Navbar tests ─────────────────────────────────────────────────────────────

class TestNavbar:
    def test_navbar_visible_on_search_page(self, page: Page):
        page.goto(f"{FRONTEND_URL}/search", timeout=TIMEOUT)
        expect(page.locator("nav")).to_be_visible()

    def test_logo_links_to_home(self, page: Page):
        page.goto(f"{FRONTEND_URL}/search", timeout=TIMEOUT)
        logo = page.get_by_text("IPC-BNS")
        expect(logo).to_be_visible()

    def test_search_nav_link_active_on_search_page(self, page: Page):
        page.goto(f"{FRONTEND_URL}/search", timeout=TIMEOUT)
        search_link = page.get_by_role("link", name="Search")
        # Active link has amber background
        expect(search_link).to_have_class(lambda cls: "bg-amber-500" in cls)

    def test_dashboard_nav_link_navigates(self, page: Page):
        page.goto(f"{FRONTEND_URL}/search", timeout=TIMEOUT)
        page.get_by_role("link", name="Dashboard").click()
        expect(page).to_have_url(f"{FRONTEND_URL}/dashboard", timeout=TIMEOUT)


# ── Search page tests ─────────────────────────────────────────────────────────

class TestSearchPage:
    def test_search_page_loads(self, page: Page):
        page.goto(f"{FRONTEND_URL}/search", timeout=TIMEOUT)
        expect(page).to_have_title(lambda t: "IPC" in t or "BNS" in t or "Search" in t)

    def test_search_input_visible(self, page: Page):
        page.goto(f"{FRONTEND_URL}/search", timeout=TIMEOUT)
        search_input = page.get_by_placeholder("Search by keyword, IPC code, or BNS code")
        expect(search_input).to_be_visible()

    def test_search_button_visible(self, page: Page):
        page.goto(f"{FRONTEND_URL}/search", timeout=TIMEOUT)
        expect(page.get_by_role("button", name="Search")).to_be_visible()

    def test_search_button_disabled_when_empty(self, page: Page):
        page.goto(f"{FRONTEND_URL}/search", timeout=TIMEOUT)
        btn = page.get_by_role("button", name="Search")
        expect(btn).to_be_disabled()

    def test_search_button_enabled_after_typing(self, page: Page):
        page.goto(f"{FRONTEND_URL}/search", timeout=TIMEOUT)
        page.get_by_placeholder("Search by keyword, IPC code, or BNS code").fill("murder")
        btn = page.get_by_role("button", name="Search")
        expect(btn).to_be_enabled()

    def test_example_chips_visible_before_search(self, page: Page):
        page.goto(f"{FRONTEND_URL}/search", timeout=TIMEOUT)
        expect(page.get_by_text("IPC-302")).to_be_visible()
        expect(page.get_by_text("murder")).to_be_visible()

    def test_example_chip_triggers_search(self, page: Page):
        page.goto(f"{FRONTEND_URL}/search", timeout=TIMEOUT)
        page.get_by_role("button", name="IPC-302").click()
        # Results section should appear
        expect(page.get_by_text("result")).to_be_visible(timeout=TIMEOUT)


# ── Search results tests ────────────────────────────────────────────────────

class TestSearchResults:
    def _search(self, page: Page, query: str):
        page.goto(f"{FRONTEND_URL}/search", timeout=TIMEOUT)
        page.get_by_placeholder("Search by keyword, IPC code, or BNS code").fill(query)
        page.get_by_role("button", name="Search").click()

    def test_murder_search_returns_results(self, page: Page):
        self._search(page, "murder")
        # Result count line e.g. "1 result for "murder""
        expect(page.get_by_text("result")).to_be_visible(timeout=TIMEOUT)

    def test_ipc_code_card_shows_section_codes(self, page: Page):
        self._search(page, "IPC-302")
        expect(page.get_by_text("IPC-302")).to_be_visible(timeout=TIMEOUT)
        expect(page.get_by_text("BNS-101")).to_be_visible(timeout=TIMEOUT)

    def test_result_card_shows_chapter(self, page: Page):
        self._search(page, "murder")
        expect(page.get_by_text("Offences Against Human Body")).to_be_visible(timeout=TIMEOUT)

    def test_result_card_shows_confidence_badge(self, page: Page):
        self._search(page, "IPC-302")
        # High confidence badge should appear for exact section code match
        expect(page.get_by_text("High confidence")).to_be_visible(timeout=TIMEOUT)

    def test_no_result_shows_empty_state(self, page: Page):
        self._search(page, "xyznonexistentsection99999")
        expect(page.get_by_text("No results found")).to_be_visible(timeout=TIMEOUT)

    def test_no_result_shows_query_in_message(self, page: Page):
        self._search(page, "xyznonexistentsection99999")
        expect(
            page.get_by_text("xyznonexistentsection99999", exact=False)
        ).to_be_visible(timeout=TIMEOUT)

    def test_example_chips_hidden_after_search(self, page: Page):
        self._search(page, "murder")
        page.wait_for_selector("text=result", timeout=TIMEOUT)
        # Chips should be gone after a query is set
        expect(page.get_by_role("button", name="IPC-302")).not_to_be_visible()

    def test_search_is_deterministic(self, page: Page):
        """Same query run twice must show the same top result."""
        self._search(page, "murder")
        page.wait_for_selector("text=result", timeout=TIMEOUT)
        cards_1 = page.locator(".font-mono").all_text_contents()

        self._search(page, "murder")
        page.wait_for_selector("text=result", timeout=TIMEOUT)
        cards_2 = page.locator(".font-mono").all_text_contents()

        assert cards_1 == cards_2, "Search results are not deterministic!"


# ── Dashboard tests ──────────────────────────────────────────────────────────

class TestDashboard:
    def test_dashboard_page_loads(self, page: Page):
        page.goto(f"{FRONTEND_URL}/dashboard", timeout=TIMEOUT)
        expect(page.get_by_text("Project Dashboard")).to_be_visible(timeout=TIMEOUT)

    def test_dashboard_shows_api_status(self, page: Page):
        page.goto(f"{FRONTEND_URL}/dashboard", timeout=TIMEOUT)
        expect(page.get_by_text("API Status")).to_be_visible(timeout=TIMEOUT)

    def test_dashboard_shows_mapping_records(self, page: Page):
        page.goto(f"{FRONTEND_URL}/dashboard", timeout=TIMEOUT)
        expect(page.get_by_text("Mapping Records")).to_be_visible(timeout=TIMEOUT)

    def test_dashboard_shows_module_tracker(self, page: Page):
        page.goto(f"{FRONTEND_URL}/dashboard", timeout=TIMEOUT)
        expect(page.get_by_text("Backend Modules")).to_be_visible(timeout=TIMEOUT)
        expect(page.get_by_text("Retrieval Engine")).to_be_visible(timeout=TIMEOUT)

    def test_dashboard_refresh_button_works(self, page: Page):
        page.goto(f"{FRONTEND_URL}/dashboard", timeout=TIMEOUT)
        refresh_btn = page.get_by_role("button", name="⟳ Refresh")
        expect(refresh_btn).to_be_visible()
        refresh_btn.click()
        # After refresh, "Last updated" time should be visible
        expect(page.get_by_text("Last updated:")).to_be_visible(timeout=TIMEOUT)

    def test_dashboard_shows_api_endpoints(self, page: Page):
        page.goto(f"{FRONTEND_URL}/dashboard", timeout=TIMEOUT)
        expect(page.get_by_text("API Endpoints")).to_be_visible(timeout=TIMEOUT)
        expect(page.get_by_text("/search")).to_be_visible(timeout=TIMEOUT)
        expect(page.get_by_text("/mapping")).to_be_visible(timeout=TIMEOUT)
