from playwright.sync_api import Page
from abc import ABC, abstractmethod
from src.utils.logger import get_logger


logger = get_logger(__name__)

class BasePage(ABC):
    def __init__(self, page: Page):
        self.page = page
        self.logger = logger

    @abstractmethod
    def navigate(self):
        """Navigate to the page"""
        pass

    def wait_for_page_load(self, timeout: int = 30000):
        """Wait for page to load"""
        self.page.wait_for_load_state("networkidle", timeout=timeout)

    def take_screenshot(self, name: str):
        """Take screenshot"""
        self.page.screenshot(path=f"reports/screenshots/{name}.png")

    def scroll_to_element(self, selector: str):
        """Scroll element into view"""
        self.page.locator(selector).scroll_into_view_if_needed()

    def wait_for_element(self, selector: str, timeout: int = 10000):
        """Wait for element to be visible"""
        return self.page.wait_for_selector(selector, timeout=timeout)