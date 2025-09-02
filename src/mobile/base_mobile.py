from appium.webdriver.common.appiumby import AppiumBy
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.remote.webelement import WebElement
from typing import List, Optional
from utils.logger import get_logger

logger = get_logger(__name__)


class BaseMobile:
    def __init__(self, driver):
        self.driver = driver
        self.wait = WebDriverWait(driver, 10)

    def find_element(self, locator: tuple) -> WebElement:
        """Find single element"""
        return self.wait.until(EC.presence_of_element_located(locator))

    def find_elements(self, locator: tuple) -> List[WebElement]:
        """Find multiple elements"""
        self.wait.until(EC.presence_of_element_located(locator))
        return self.driver.find_elements(*locator)

    def click_element(self, locator: tuple):
        """Click element"""
        element = self.wait.until(EC.element_to_be_clickable(locator))
        element.click()

    def enter_text(self, locator: tuple, text: str):
        """Enter text in element"""
        element = self.find_element(locator)
        element.clear()
        element.send_keys(text)

    def get_text(self, locator: tuple) -> str:
        """Get element text"""
        element = self.find_element(locator)
        return element.text

    def is_element_displayed(self, locator: tuple) -> bool:
        """Check if element is displayed"""
        try:
            element = self.find_element(locator)
            return element.is_displayed()
        except:
            return False

    def wait_for_element(self, locator: tuple, timeout: int = 10):
        """Wait for element to be present"""
        wait = WebDriverWait(self.driver, timeout)
        return wait.until(EC.presence_of_element_located(locator))

    def wait_for_element_clickable(self, locator: tuple, timeout: int = 10):
        """Wait for element to be clickable"""
        wait = WebDriverWait(self.driver, timeout)
        return wait.until(EC.element_to_be_clickable(locator))

    def scroll_to_element(self, locator: tuple):
        """Scroll to element"""
        element = self.find_element(locator)
        self.driver.execute_script("mobile: scroll", {"direction": "down", "element": element})

    def swipe_left(self):
        """Swipe left"""
        size = self.driver.get_window_size()
        start_x = size["width"] * 0.8
        start_y = size["height"] * 0.5
        end_x = size["width"] * 0.2
        end_y = size["height"] * 0.5
        self.driver.swipe(start_x, start_y, end_x, end_y, 1000)

    def swipe_right(self):
        """Swipe right"""
        size = self.driver.get_window_size()
        start_x = size["width"] * 0.2
        start_y = size["height"] * 0.5
        end_x = size["width"] * 0.8
        end_y = size["height"] * 0.5
        self.driver.swipe(start_x, start_y, end_x, end_y, 1000)

    def swipe_up(self):
        """Swipe up"""
        size = self.driver.get_window_size()
        start_x = size["width"] * 0.5
        start_y = size["height"] * 0.8
        end_x = size["width"] * 0.5
        end_y = size["height"] * 0.2
        self.driver.swipe(start_x, start_y, end_x, end_y, 1000)

    def swipe_down(self):
        """Swipe down"""
        size = self.driver.get_window_size()
        start_x = size["width"] * 0.5
        start_y = size["height"] * 0.2
        end_x = size["width"] * 0.5
        end_y = size["height"] * 0.8
        self.driver.swipe(start_x, start_y, end_x, end_y, 1000)

    def take_screenshot(self, filename: str):
        """Take screenshot"""
        self.driver.save_screenshot(f"reports/screenshots/{filename}.png")