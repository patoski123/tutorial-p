import pytest
import os
from datetime import datetime
from playwright.sync_api import sync_playwright
from api.auth_api import AuthAPI
from utils.config import config
from utils.logger import setup_logging
import structlog

# Setup logging for tests
logger = setup_logging()

def pytest_configure(config_obj):
    """Configure pytest"""
    # Create necessary directories
    os.makedirs("reports/html", exist_ok=True)
    os.makedirs("reports/json", exist_ok=True)
    os.makedirs("reports/allure", exist_ok=True)
    os.makedirs("screenshots/ui", exist_ok=True)
    os.makedirs("screenshots/mobile", exist_ok=True)
    os.makedirs("logs", exist_ok=True)

def pytest_collection_modifyitems(config_obj, items):
    """Modify test collection"""
    # Auto-add markers based on test path
    for item in items:
        if "api" in str(item.fspath):
            item.add_marker(pytest.mark.api)
        elif "ui" in str(item.fspath):
            item.add_marker(pytest.mark.ui)
        elif "mobile" in str(item.fspath):
            item.add_marker(pytest.mark.mobile)
        elif "performance" in str(item.fspath):
            item.add_marker(pytest.mark.performance)

# Session-scoped fixtures
@pytest.fixture(scope="session")
def test_config():
    """Provide test configuration"""
    return config

@pytest.fixture(scope="session")
def playwright():
    """Playwright instance"""
    with sync_playwright() as p:
        yield p

@pytest.fixture(scope="session")
def browser(playwright, test_config):
    """Browser instance"""
    browser = playwright.chromium.launch(
        headless=test_config.ui.headless,
        slow_mo=test_config.ui.slow_mo,
        args=["--no-sandbox", "--disable-dev-shm-usage"] if test_config.ui.headless else []
    )
    yield browser
    browser.close()

@pytest.fixture(scope="session")
def api_client():
    """API client instance"""
    return AuthAPI()

# Function-scoped fixtures
@pytest.fixture
def page(browser, test_config):
    """New page for each test"""
    context = browser.new_context(
        viewport={
            "width": test_config.ui.viewport_width,
            "height": test_config.ui.viewport_height
        }
    )
    page = context.new_page()
    yield page
    page.close()
    context.close()

@pytest.fixture
def authenticated_api_client(api_client, test_config):
    """Authenticated API client"""
    success, _ = api_client.login(
        test_config.test_user['username'],
        test_config.test_user['password']
    )

    if not success:
        pytest.skip("Unable to authenticate API client")

    yield api_client

    # Cleanup
    api_client.logout()

# Utility fixtures
@pytest.fixture
def screenshot_on_failure(request, page):
    """Auto-screenshot on test failure"""
    yield

    if hasattr(request.node, 'rep_call') and request.node.rep_call.failed:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        screenshot_name = f"failed_{request.node.name}_{timestamp}"

        try:
            page.screenshot(path=f"screenshots/ui/{screenshot_name}.png")
            logger.info("Failure screenshot taken", path=screenshot_name)
        except Exception as e:
            logger.error("Failed to take screenshot", error=str(e))

@pytest.fixture
def test_data():
    """Provide test data"""
    return {
        'valid_user': {
            'username': 'testuser@example.com',
            'password': 'validpassword123',
            'first_name': 'Test',
            'last_name': 'User'
        },
        'invalid_user': {
            'username': 'invalid@example.com',
            'password': 'wrongpassword'
        }
    }

# Hooks for reporting
@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Hook to capture test results"""
    outcome = yield
    rep = outcome.get_result()
    setattr(item, "rep_" + rep.when, rep)

    # Log test results
    if rep.when == "call":
        logger.info("Test completed",
                    test_name=item.name,
                    outcome=rep.outcome,
                    duration=rep.duration)