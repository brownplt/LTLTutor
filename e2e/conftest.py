import pytest
import os

BASE_URL = os.environ.get("BASE_URL", "http://localhost:5000")


@pytest.fixture(scope="session")
def base_url():
    return BASE_URL


@pytest.fixture()
def logged_in_page(page, base_url):
    """Return a Playwright page that is logged in as an anonymous student."""
    page.goto(f"{base_url}/login")
    page.get_by_role("button", name="Quick Start").click()
    page.wait_for_url(f"{base_url}/")
    return page
