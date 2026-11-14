"""
Fixtures and guards for the Playwright end-to-end suite.

The E2E suite needs a running backend and frontend, plus the Playwright
browser binaries. When those are missing (e.g. a plain ``pytest tests/`` run
on a developer machine) the suite is skipped instead of erroring, so it never
breaks the unit/integration suite. Set ``E2E_REQUIRED=1`` (as CI does) to turn
an unreachable frontend into a hard failure instead of a skip.

Environment:
  E2E_BASE_URL   frontend origin   (default http://localhost:3000)
  E2E_API_URL    backend origin    (default http://localhost:8000)
  E2E_USERNAME / E2E_PASSWORD      analyst account used by signed-in tests
                                   (fall back to AUTH_USERNAME / AUTH_PASSWORD)
  E2E_REQUIRED   "1" -> fail instead of skip when servers are down
"""

import importlib.util
import os
import urllib.error
import urllib.request

import pytest

# Without Playwright installed the test modules cannot even be imported.
if importlib.util.find_spec("playwright") is None:
    collect_ignore_glob = ["test_*.py"]

FRONTEND_URL = os.getenv("E2E_BASE_URL", "http://localhost:3000").rstrip("/")
API_URL = os.getenv("E2E_API_URL", "http://localhost:8000").rstrip("/")


def _reachable(url: str) -> bool:
    try:
        with urllib.request.urlopen(url, timeout=3):
            return True
    except (urllib.error.URLError, OSError):
        return False


@pytest.fixture(scope="session", autouse=True)
def _require_servers():
    missing = [u for u in (FRONTEND_URL, f"{API_URL}/health") if not _reachable(u)]
    if missing:
        msg = f"E2E servers not reachable: {', '.join(missing)}"
        if os.getenv("E2E_REQUIRED") == "1":
            pytest.fail(msg)
        pytest.skip(msg)


@pytest.fixture(scope="session")
def frontend_url() -> str:
    return FRONTEND_URL


@pytest.fixture(scope="session")
def analyst_credentials() -> tuple[str, str]:
    username = os.getenv("E2E_USERNAME") or os.getenv("AUTH_USERNAME")
    password = os.getenv("E2E_PASSWORD") or os.getenv("AUTH_PASSWORD")
    if not username or not password:
        pytest.skip("Set E2E_USERNAME/E2E_PASSWORD to run signed-in E2E tests")
    return username, password


@pytest.fixture(scope="session")
def browser_context_args(browser_context_args):
    """Desktop viewport so navbar labels (hidden below `sm`) are rendered."""
    return {**browser_context_args, "viewport": {"width": 1280, "height": 800}}
