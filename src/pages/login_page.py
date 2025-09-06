from playwright.sync_api import Page, expect
from src.pages.base_page import BasePage

class LoginPage(BasePage):
    def __init__(self, page: Page):
        super().__init__(page)
        self.username_input = "#username"
        self.password_input = "#password"
        self.login_button = "button[type='submit']"
        self.error_message = ".error-message"

    def navigate(self):
        """Navigate to login page"""
        self.page.goto("/login")
        self.wait_for_page_load()

    def enter_username(self, username: str):
        """Enter username"""
        self.page.fill(self.username_input, username)

    def enter_password(self, password: str):
        """Enter password"""
        self.page.fill(self.password_input, password)

    def enter_credentials(self, username: str, password: str):
        """Enter both username and password"""
        self.enter_username(username)
        self.enter_password(password)

    def click_login(self):
        """Click login button"""
        self.page.click(self.login_button)

    def get_error_message(self) -> str:
        """Get error message text"""
        return self.page.locator(self.error_message).text_content()

    def is_error_message_visible(self) -> bool:
        """Check if error message is visible"""
        return self.page.locator(self.error_message).is_visible()

    def login(self, username: str, password: str):
        """Complete login flow"""
        self.enter_credentials(username, password)
        self.click_login()