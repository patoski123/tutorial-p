from playwright.sync_api import Page
from typing import Dict
from utils.logger import get_logger

logger = get_logger(__name__)


class UIHelpers:
    """UI-specific helper functions"""

    def __init__(self, page: Page):
        self.page = page

    def fill_form(self, field_data: Dict[str, str]):
        """Fill multiple form fields"""
        for selector, value in field_data.items():
            self.page.fill(selector, value)
            logger.debug(f"Filled field {selector} with value")

    def wait_for_url_contains(self, url_fragment: str, timeout: int = 30000):
        """Wait for URL to contain specific fragment"""
        self.page.wait_for_url(f"**/*{url_fragment}*", timeout=timeout)

    def take_screenshot_with_timestamp(self, name: str):
        """Take screenshot with timestamp"""
        import time
        timestamp = int(time.time())
        screenshot_path = f"reports/screenshots/{name}_{timestamp}.png"
        self.page.screenshot(path=screenshot_path)
        return screenshot_path

    def scroll_and_click(self, selector: str):
        """Scroll element into view and click"""
        element = self.page.locator(selector)
        element.scroll_into_view_if_needed()
        element.click()