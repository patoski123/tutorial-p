from pytest_bdd import given, when, then, parsers
from appium.webdriver.common.appiumby import AppiumBy
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from src.utils.logger import get_logger

logger = get_logger(__name__)

# Given Steps
@given("I have launched the mobile app")
def app_launched(mobile_driver):
    # App should be launched automatically by fixture
    # Wait for app to load
    WebDriverWait(mobile_driver, 10).until(
        EC.presence_of_element_located((AppiumBy.ID, "com.example.app:id/main_layout"))
    )

@given("I am on the app home screen")
def navigate_to_home_screen(mobile_driver):
    home_button = mobile_driver.find_element(AppiumBy.ID, "com.example.app:id/home_tab")
    home_button.click()

# When Steps
@when("I tap on the profile icons")
def tap_profile_icon(mobile_driver):
    profile_icon = mobile_driver.find_element(AppiumBy.ID, "com.example.app:id/profile_icon")
    profile_icon.click()

@when("I tap on the search icons")
def tap_search_icon(mobile_driver):
    search_icon = mobile_driver.find_element(AppiumBy.ID, "com.example.app:id/search_icon")
    search_icon.click()

@when(parsers.parse('I enter "{text}" in the search fields'))
def enter_search_text(mobile_driver, text: str):
    search_field = mobile_driver.find_element(AppiumBy.ID, "com.example.app:id/search_input")
    search_field.clear()
    search_field.send_keys(text)

@when("I tap search button")
def tap_search_button(mobile_driver):
    search_button = mobile_driver.find_element(AppiumBy.ID, "com.example.app:id/search_button")
    search_button.click()

# Then Steps
@then("I should see the profile screens")
def verify_profile_screen(mobile_driver):
    profile_screen = WebDriverWait(mobile_driver, 10).until(
        EC.presence_of_element_located((AppiumBy.ID, "com.example.app:id/profile_screen"))
    )
    assert profile_screen.is_displayed()

@then("the profile informations should be displayed")
def verify_profile_information(mobile_driver):
    profile_name = mobile_driver.find_element(AppiumBy.ID, "com.example.app:id/profile_name")
    assert profile_name.is_displayed()
    assert profile_name.text != ""

@then("I should see search result")
def verify_search_results(mobile_driver):
    results_list = WebDriverWait(mobile_driver, 10).until(
        EC.presence_of_element_located((AppiumBy.ID, "com.example.app:id/search_results"))
    )
    assert results_list.is_displayed()

@then(parsers.parse('the result should contain "{expected_text}"'))
def verify_search_results_contain_text(mobile_driver, expected_text: str):
    results = mobile_driver.find_elements(AppiumBy.CLASS_NAME, "android.widget.TextView")
    result_texts = [result.text for result in results]
    assert any(expected_text in text for text in result_texts)