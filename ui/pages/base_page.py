from playwright.sync_api import Page, expect
from typing import Optional
import structlog
from utils.config import config

logger = structlog.get_logger(__name__)

class BasePage:
    """Base page class with common UI functionality"""

    def __init__(self, page: Page):
        self.page = page
        self.timeout = 30000  # 30 seconds default timeout

    def navigate_to(self, url: str, wait_for_load: bool = True):
        """Navigate to URL"""
        logger.info("Navigating to URL", url=url)
        self.page.goto(url)

        if wait_for_load:
            self.wait_for_page_load()

    def wait_for_page_load(self, state: str = "networkidle"):
        """Wait for page to load completely"""
        logger.info("Waiting for page load", state=state)
        self.page.wait_for_load_state(state)

    def click(self, selector: str, timeout: int = None):
        """Click element with logging"""
        timeout = timeout or self.timeout
        logger.info("Clicking element", selector=selector)
        self.page.click(selector, timeout=timeout)

    def fill(self, selector: str, value: str, timeout: int = None):
        """Fill input field with logging"""
        timeout = timeout or self.timeout
        logger.info("Filling field", selector=selector, value="***" if "password" in selector.lower() else value)
        self.page.fill(selector, value, timeout=timeout)

    def get_text(self, selector: str, timeout: int = None) -> str:
        """Get text content of element"""
        timeout = timeout or self.timeout
        logger.info("Getting text", selector=selector)
        return self.page.locator(selector).text_content(timeout=timeout)

    def is_visible(self, selector: str, timeout: int = 5000) -> bool:
        """Check if element is visible"""
        try:
            return self.page.locator(selector).is_visible(timeout=timeout)
        except:
            return False

    def wait_for_element(self, selector: str, state: str = "visible", timeout: int = None):
        """Wait for element to reach specified state"""
        timeout = timeout or self.timeout
        logger.info("Waiting for element", selector=selector, state=state)
        self.page.wait_for_selector(selector, state=state, timeout=timeout)

    def take_screenshot(self, name: str, full_page: bool = False):
        """Take screenshot"""
        screenshot_path = f"screenshots/ui/{name}.png"
        logger.info("Taking screenshot", path=screenshot_path)
        self.page.screenshot(path=screenshot_path, full_page=full_page)
        return screenshot_path

    def get_current_url(self) -> str:
        """Get current page URL"""
        return self.page.url

    def get_title(self) -> str:
        """Get page title"""
        return self.page.title()

    def scroll_to_element(self, selector: str):
        """Scroll element into view"""
        logger.info("Scrolling to element", selector=selector)
        self.page.locator(selector).scroll_into_view_if_needed()

    def hover(self, selector: str, timeout: int = None):
        """Hover over element"""
        timeout = timeout or self.timeout
        logger.info("Hovering element", selector=selector)
        self.page.hover(selector, timeout=timeout)

    def select_option(self, selector: str, value: str, timeout: int = None):
        """Select option from dropdown"""
        timeout = timeout or self.timeout
        logger.info("Selecting option", selector=selector, value=value)
        self.page.select_option(selector, value, timeout=timeout)

    def assert_text_present(self, text: str):
        """Assert text is present on page"""
        logger.info("Asserting text present", text=text)
        expect(self.page.locator(f"text={text}")).to_be_visible()

    def assert_element_visible(self, selector: str):
        """Assert element is visible"""
        logger.info("Asserting element visible", selector=selector)
        expect(self.page.locator(selector)).to_be_visible()

    def assert_url_contains(self, url_part: str):
        """Assert URL contains specified part"""
        logger.info("Asserting URL contains", url_part=url_part)
        expect(self.page).to_have_url_pattern(f"*{url_part}*")