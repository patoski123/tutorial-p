from playwright.sync_api import Page
from typing import Union


class ElementWaits:
    """Advanced element waiting strategies"""

    def __init__(self, page: Page):
        self.page = page

    def wait_for_elements_count(self, selector: str, count: int, timeout: int = 10000):
        """Wait for specific number of elements"""
        self.page.wait_for_function(
            f"document.querySelectorAll('{selector}').length === {count}",
            timeout=timeout
        )

    def wait_for_text_change(self, selector: str, initial_text: str, timeout: int = 10000):
        """Wait for element text to change from initial value"""
        self.page.wait_for_function(
            f"document.querySelector('{selector}').textContent !== '{initial_text}'",
            timeout=timeout
        )

    def wait_for_attribute_value(self, selector: str, attribute: str, value: str, timeout: int = 10000):
        """Wait for element attribute to have specific value"""
        self.page.wait_for_function(
            f"document.querySelector('{selector}').getAttribute('{attribute}') === '{value}'",
            timeout=timeout
        )