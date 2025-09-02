from pytest_bdd import given, when, then, parsers
from playwright.sync_api import Page, expect
from pages.login_page import LoginPage
from pages.dashboard_page import DashboardPage
from utils.logger import get_logger

logger = get_logger(__name__)

# Given Steps
@given("I am on the login page")
def navigate_to_login_page(page: Page):
    login_page = LoginPage(page)
    login_page.navigate()

@given("I am on the registration page")
def navigate_to_registration_page(page: Page):
    page.goto("/register")

# When Steps
@when(parsers.parse('I enter username "{username}" and password "{password}"'))
def enter_credentials(page: Page, username: str, password: str):
    login_page = LoginPage(page)
    login_page.enter_credentials(username, password)

@when("I click the login button")
def click_login_button(page: Page):
    login_page = LoginPage(page)
    login_page.click_login()

@when("I fill in the registration form with valid details")
def fill_registration_form(page: Page):
    page.fill("#username", "newuser")
    page.fill("#email", "newuser@example.com")
    page.fill("#password", "password123")
    page.fill("#confirmPassword", "password123")

@when("I submit the registration form")
def submit_registration_form(page: Page):
    page.click("button[type='submit']")

# Then Steps
@then("I should be redirected to the dashboard")
def verify_dashboard_redirect(page: Page):
    expect(page).to_have_url("/dashboard")

@then(parsers.parse('I should see welcome message "{message}"'))
def verify_welcome_message(page: Page, message: str):
    expect(page.locator(f"text={message}")).to_be_visible()

@then(parsers.parse('I should see error message "{error_message}"'))
def verify_error_message(page: Page, error_message: str):
    expect(page.locator(f"text={error_message}")).to_be_visible()

@then("I should remain on the login page")
def verify_still_on_login_page(page: Page):
    expect(page).to_have_url("/login")

@then("I should see registration success message")
def verify_registration_success(page: Page):
    expect(page.locator("text=Registration successful")).to_be_visible()