"""
Playwright end-to-end tests for the public search flow and the dashboard.

These tests drive a real browser against the running frontend and backend:
  1. Navbar renders and routes between pages
  2. Searching by keyword or section code shows result cards
  3. Quick-example chips trigger a search
  4. A query with no matches shows the empty state
  5. The dashboard renders, and shows live API status once signed in

/search and /dashboard are public; admin diagnostics require an analyst
token, so the live-status checks sign in through the /login page first.

Prerequisites:
  - Backend:  uvicorn backend.main:app --port 8000
  - Frontend: (cd frontend && npm run build && npm run start)   # port 3000
  - Browsers: pip install pytest-playwright && python -m playwright install chromium

Run:
  pytest tests/e2e -v                 # headless
  pytest tests/e2e -v --headed        # watch the browser
See tests/e2e/conftest.py for the environment variables the suite reads.
"""

import os
import re

import pytest
from playwright.sync_api import Page, expect

FRONTEND_URL = os.getenv("E2E_BASE_URL", "http://localhost:3000").rstrip("/")
TIMEOUT = 10_000  # ms
SEARCH_PLACEHOLDER = "Search by keyword, IPC code, or BNS code"
RESULT_COUNT = re.compile(r"^\d+ results? for")


def _result_count(page: Page):
    return page.get_by_text(RESULT_COUNT)


# ── Navbar ───────────────────────────────────────────────────────────────────

class TestNavbar:
    def test_navbar_visible_on_search_page(self, page: Page):
        page.goto(f"{FRONTEND_URL}/search", timeout=TIMEOUT)
        expect(page.locator("nav")).to_be_visible()

    def test_logo_links_to_home(self, page: Page):
        page.goto(f"{FRONTEND_URL}/search", timeout=TIMEOUT)
        logo = page.locator("nav").get_by_role("link", name="NyayaSetu")
        expect(logo).to_be_visible()
        expect(logo).to_have_attribute("href", "/")

    def test_search_nav_link_active_on_search_page(self, page: Page):
        page.goto(f"{FRONTEND_URL}/search", timeout=TIMEOUT)
        search_link = page.locator("nav").get_by_role("link", name="Search")
        expect(search_link).to_have_attribute("aria-current", "page")
        expect(search_link).to_have_class(re.compile(r"\bbg-amber-500\b"))

    def test_dashboard_nav_link_navigates(self, page: Page):
        page.goto(f"{FRONTEND_URL}/search", timeout=TIMEOUT)
        page.locator("nav").get_by_role("link", name="Dashboard").click()
        expect(page).to_have_url(f"{FRONTEND_URL}/dashboard", timeout=TIMEOUT)


# ── Search page ──────────────────────────────────────────────────────────────

class TestSearchPage:
    def test_search_page_loads(self, page: Page):
        page.goto(f"{FRONTEND_URL}/search", timeout=TIMEOUT)
        expect(page).to_have_title(re.compile(r"IPC|BNS|NyayaSetu"))
        expect(page.get_by_role("heading", name="IPC ↔ BNS Legal Search")).to_be_visible()

    def test_search_input_visible(self, page: Page):
        page.goto(f"{FRONTEND_URL}/search", timeout=TIMEOUT)
        expect(page.get_by_placeholder(SEARCH_PLACEHOLDER)).to_be_visible()

    def test_search_button_visible(self, page: Page):
        page.goto(f"{FRONTEND_URL}/search", timeout=TIMEOUT)
        expect(page.get_by_role("button", name="Search", exact=True)).to_be_visible()

    def test_search_button_disabled_when_empty(self, page: Page):
        page.goto(f"{FRONTEND_URL}/search", timeout=TIMEOUT)
        expect(page.get_by_role("button", name="Search", exact=True)).to_be_disabled()

    def test_search_button_enabled_after_typing(self, page: Page):
        page.goto(f"{FRONTEND_URL}/search", timeout=TIMEOUT)
        page.get_by_placeholder(SEARCH_PLACEHOLDER).fill("murder")
        expect(page.get_by_role("button", name="Search", exact=True)).to_be_enabled()

    def test_example_chips_visible_before_search(self, page: Page):
        page.goto(f"{FRONTEND_URL}/search", timeout=TIMEOUT)
        expect(page.get_by_role("button", name="IPC-302", exact=True)).to_be_visible()
        expect(page.get_by_role("button", name="murder", exact=True)).to_be_visible()

    def test_example_chip_triggers_search(self, page: Page):
        page.goto(f"{FRONTEND_URL}/search", timeout=TIMEOUT)
        page.get_by_role("button", name="IPC-302", exact=True).click()
        expect(_result_count(page)).to_be_visible(timeout=TIMEOUT)


# ── Search results ───────────────────────────────────────────────────────────

class TestSearchResults:
    def _search(self, page: Page, query: str):
        page.goto(f"{FRONTEND_URL}/search", timeout=TIMEOUT)
        page.get_by_placeholder(SEARCH_PLACEHOLDER).fill(query)
        page.get_by_role("button", name="Search", exact=True).click()

    def test_murder_search_returns_results(self, page: Page):
        self._search(page, "murder")
        expect(_result_count(page)).to_be_visible(timeout=TIMEOUT)

    def test_ipc_code_card_shows_section_codes(self, page: Page):
        self._search(page, "IPC-302")
        expect(page.get_by_text("IPC-302", exact=True).first).to_be_visible(timeout=TIMEOUT)
        expect(page.get_by_text("BNS-101", exact=True).first).to_be_visible(timeout=TIMEOUT)

    def test_result_card_shows_chapter(self, page: Page):
        self._search(page, "murder")
        expect(
            page.get_by_text("Offences Against Human Body", exact=True).first
        ).to_be_visible(timeout=TIMEOUT)

    def test_result_card_shows_confidence_badge(self, page: Page):
        self._search(page, "IPC-302")
        # An exact section-code match scores high enough for the HIGH badge.
        expect(page.get_by_text("High confidence").first).to_be_visible(timeout=TIMEOUT)

    def test_no_result_shows_empty_state(self, page: Page):
        self._search(page, "xyznonexistentsection99999")
        expect(page.get_by_text("No results found")).to_be_visible(timeout=TIMEOUT)

    def test_no_result_shows_query_in_message(self, page: Page):
        self._search(page, "xyznonexistentsection99999")
        expect(
            page.locator("strong", has_text="xyznonexistentsection99999")
        ).to_be_visible(timeout=TIMEOUT)

    def test_example_chips_hidden_after_search(self, page: Page):
        self._search(page, "murder")
        expect(_result_count(page)).to_be_visible(timeout=TIMEOUT)
        expect(page.get_by_role("button", name="IPC-302", exact=True)).to_have_count(0)

    def test_search_is_deterministic(self, page: Page):
        """Same query run twice must show the same ordered result cards."""
        self._search(page, "murder")
        expect(_result_count(page)).to_be_visible(timeout=TIMEOUT)
        cards_1 = page.locator(".font-mono").all_text_contents()

        self._search(page, "murder")
        expect(_result_count(page)).to_be_visible(timeout=TIMEOUT)
        cards_2 = page.locator(".font-mono").all_text_contents()

        assert cards_1, "No result cards rendered"
        assert cards_1 == cards_2, "Search results are not deterministic!"


# ── Dashboard ────────────────────────────────────────────────────────────────

@pytest.fixture
def signed_in_page(page: Page, analyst_credentials) -> Page:
    """Sign in through the real /login form; the JWT lands in localStorage."""
    username, password = analyst_credentials
    page.goto(f"{FRONTEND_URL}/login", timeout=TIMEOUT)
    page.get_by_label("Username").fill(username)
    page.get_by_label("Password").fill(password)
    page.get_by_role("button", name="Sign in", exact=True).click()
    expect(page).to_have_url(f"{FRONTEND_URL}/", timeout=TIMEOUT)
    return page


class TestDashboard:
    def test_dashboard_page_loads(self, page: Page):
        page.goto(f"{FRONTEND_URL}/dashboard", timeout=TIMEOUT)
        expect(page.get_by_role("heading", name="Project Dashboard")).to_be_visible(
            timeout=TIMEOUT
        )

    def test_dashboard_shows_stat_cards(self, page: Page):
        page.goto(f"{FRONTEND_URL}/dashboard", timeout=TIMEOUT)
        expect(page.get_by_text("API Status", exact=True)).to_be_visible(timeout=TIMEOUT)
        expect(page.get_by_text("Mapping Records", exact=True)).to_be_visible(timeout=TIMEOUT)

    def test_dashboard_shows_module_tracker(self, page: Page):
        page.goto(f"{FRONTEND_URL}/dashboard", timeout=TIMEOUT)
        expect(page.get_by_text("Backend Modules")).to_be_visible(timeout=TIMEOUT)
        expect(page.get_by_text("Retrieval Engine", exact=True)).to_be_visible(timeout=TIMEOUT)

    def test_dashboard_shows_api_endpoints(self, page: Page):
        page.goto(f"{FRONTEND_URL}/dashboard", timeout=TIMEOUT)
        expect(page.get_by_text("API Endpoints")).to_be_visible(timeout=TIMEOUT)
        expect(page.get_by_text("/search", exact=True)).to_be_visible(timeout=TIMEOUT)
        expect(page.get_by_text("/mapping", exact=True)).to_be_visible(timeout=TIMEOUT)

    def test_signed_in_dashboard_shows_live_api_status(self, signed_in_page: Page):
        page = signed_in_page
        page.goto(f"{FRONTEND_URL}/dashboard", timeout=TIMEOUT)
        expect(page.get_by_text("Last updated:")).to_be_visible(timeout=TIMEOUT)
        expect(page.get_by_text("ok", exact=True)).to_be_visible()
        expect(page.get_by_text("Could not connect to the backend")).to_have_count(0)

    def test_signed_in_dashboard_refresh_button_works(self, signed_in_page: Page):
        page = signed_in_page
        page.goto(f"{FRONTEND_URL}/dashboard", timeout=TIMEOUT)
        expect(page.get_by_text("Last updated:")).to_be_visible(timeout=TIMEOUT)
        with page.expect_response(lambda r: r.url.endswith("/health") and r.ok):
            page.get_by_role("button", name="⟳ Refresh").click()
        expect(page.get_by_text("Last updated:")).to_be_visible(timeout=TIMEOUT)
