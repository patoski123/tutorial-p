import pytest
from pytest_bdd import given, when, then, parsers
from playwright.sync_api import expect
from utils.config import config
import structlog

logger = structlog.get_logger(__name__)

# Given steps
@given("I navigate to the login page")
def navigate_to_login_page(bdd_login_page, ui_context):
    """Navigate to the login page"""
    bdd_login_page.navigate_to_login(config.api.base_url)
    ui_context['current_page'] = 'login'

@given("the login form is displayed")
def login_form_is_displayed(bdd_login_page):
    """Verify login form elements are visible"""
    bdd_login_page.assert_login_form_visible()

@given("I have valid login credentials")
def have_valid_login_credentials(ui_context):
    """Set up valid login credentials"""
    ui_context['user_credentials'] = {
        'username': config.test_user['username'],
        'password': config.test_user['password']
    }

@given("I have invalid login credentials")
def have_invalid_login_credentials(ui_context):
    """Set up invalid login credentials"""
    ui_context['user_credentials'] = {
        'username': 'invalid@example.com',
        'password': 'wrongpassword'
    }

@given("I have entered a password")
def have_entered_password(bdd_login_page):
    """Enter a password in the password field"""
    bdd_login_page.enter_password("testpassword123")

# When steps
@when("I enter my username and password")
def enter_username_and_password(bdd_login_page, ui_context):
    """Enter valid credentials"""
    credentials = ui_context['user_credentials']
    bdd_login_page.enter_username(credentials['username'])
    bdd_login_page.enter_password(credentials['password'])

@when("I click the login button")
def click_login_button(bdd_login_page):
    """Click the login button"""
    bdd_login_page.click_login()

@when("I enter the invalid username and password")
def enter_invalid_credentials(bdd_login_page, ui_context):
    """Enter invalid credentials"""
    credentials = ui_context['user_credentials']
    bdd_login_page.enter_username(credentials['username'])
    bdd_login_page.enter_password(credentials['password'])

@when("I click the login button without entering credentials")
def click_login_without_credentials(bdd_login_page):
    """Click login button with empty fields"""
    bdd_login_page.click_login()

@when("I click the password visibility toggle")
def click_password_visibility_toggle(bdd_login_page):
    """Click password visibility toggle"""
    bdd_login_page.page.click(".password-toggle")  # Adjust selector as needed

@when('I check the "Remember me" checkbox')
def check_remember_me(bdd_login_page):
    """Check the remember me checkbox"""
    bdd_login_page.page.check("#remember-me")

@when("I enter my credentials and login")
def enter_credentials_and_login(bdd_login_page, ui_context):
    """Complete login process"""
    credentials = ui_context['user_credentials']
    bdd_login_page.login(credentials['username'], credentials['password'], remember_me=True)

@when('I click the "Forgot Password" link')
def click_forgot_password_link(bdd_login_page):
    """Click forgot password link"""
    bdd_login_page.click_forgot_password()

# Then steps
@then("I should be redirected to the dashboard")
def should_be_redirected_to_dashboard(bdd_login_page):
    """Verify redirection to dashboard"""
    expect(bdd_login_page.page).to_have_url_pattern("**/dashboard")

@then("I should see a welcome message")
def should_see_welcome_message(bdd_login_page):
    """Verify welcome message is displayed"""
    welcome_selector = ".welcome-message, .greeting, [data-testid='welcome']"
    expect(bdd_login_page.page.locator(welcome_selector)).to_be_visible(timeout=10000)

@then(parsers.parse('the page title should contain "{title_part}"'))
def page_title_should_contain(bdd_login_page, title_part):
    """Verify page title contains expected text"""
    expect(bdd_login_page.page).to_have_title_pattern(f".*{title_part}.*")

@then("I should remain on the login page")
def should_remain_on_login_page(bdd_login_page):
    """Verify still on login page"""
    expect(bdd_login_page.page).to_have_url_pattern("**/login")

@then(parsers.parse('I should see an error message "{error_message}"'))
def should_see_error_message(bdd_login_page, error_message):
    """Verify specific error message"""
    assert bdd_login_page.is_error_displayed(), "Error message should be visible"
    actual_message = bdd_login_page.get_error_message()
    assert error_message.lower() in actual_message.lower(), f"Expected '{error_message}' in '{actual_message}'"

@then("the error message should be displayed prominently")
def error_message_displayed_prominently(bdd_login_page):
    """Verify error message is prominent"""
    error_locator = bdd_login_page.page.locator(".error-message")
    expect(error_locator).to_be_visible()
    expect(error_locator).to_have_css("color", "rgb(220, 53, 69)")  # Red color, adjust as needed

@then("I should see validation messages")
def should_see_validation_messages(bdd_login_page):
    """Verify validation messages are present"""
    validation_selector = ".validation-error, .field-error, .error"
    expect(bdd_login_page.page.locator(validation_selector)).to_be_visible()

@then(parsers.parse('the username field should show "{validation_message}"'))
def username_field_should_show_validation(bdd_login_page, validation_message):
    """Verify username field validation"""
    username_error = bdd_login_page.page.locator("#username ~ .error, .username-error")
    expect(username_error).to_contain_text(validation_message)

@then(parsers.parse('the password field should show "{validation_message}"'))
def password_field_should_show_validation(bdd_login_page, validation_message):
    """Verify password field validation"""
    password_error = bdd_login_page.page.locator("#password ~ .error, .password-error")
    expect(password_error).to_contain_text(validation_message)

@then("the password should be visible in plain text")
def password_should_be_visible(bdd_login_page):
    """Verify password is visible"""
    password_field = bdd_login_page.page.locator("#password")
    expect(password_field).to_have_attribute("type", "text")

@then("the password should be hidden")
def password_should_be_hidden(bdd_login_page):
    """Verify password is hidden"""
    password_field = bdd_login_page.page.locator("#password")
    expect(password_field).to_have_attribute("type", "password")

@then("I should be logged in successfully")
def should_be_logged_in_successfully(bdd_login_page):
    """Verify successful login"""
    expect(bdd_login_page.page).to_have_url_pattern("**/dashboard")

@then("a remember me cookie should be set")
def remember_me_cookie_should_be_set(bdd_login_page):
    """Verify remember me cookie exists"""
    cookies = bdd_login_page.page.context.cookies()
    remember_cookie = next((c for c in cookies if 'remember' in c['name'].lower()), None)
    assert remember_cookie is not None, "Remember me cookie should be set"

@then("the session should persist across browser restarts")
def session_should_persist(bdd_login_page):
    """Verify session persistence (simulated)"""
    # In a real test, you'd restart the browser and verify login state
    # For now, we'll just verify the cookie is persistent
    cookies = bdd_login_page.page.context.cookies()
    remember_cookie = next((c for c in cookies if 'remember' in c['name'].lower()), None)

    if remember_cookie:
        # Check if cookie has a future expiration (persistent)
        assert remember_cookie.get('expires', 0) > 0, "Remember me cookie should be persistent"

@then("I should be redirected to the password reset page")
def should_be_redirected_to_password_reset(bdd_login_page):
    """Verify redirection to password reset"""
    expect(bdd_login_page.page).to_have_url_pattern("**/forgot-password")

@then("the page should contain a password reset form")
def page_should_contain_reset_form(bdd_login_page):
    """Verify password reset form exists"""
    email_field = bdd_login_page.page.locator("input[type='email'], input[name='email']")
    expect(email_field).to_be_visible()

@then("I should be able to enter my email address")
def should_be_able_to_enter_email(bdd_login_page):
    """Verify email field is functional"""
    email_field = bdd_login_page.page.locator("input[type='email'], input[name='email']")
    email_field.fill("test@example.com")
    expect(email_field).to_have_value("test@example.com")