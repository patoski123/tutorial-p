from mobile.base_mobile import BaseMobile
from appium.webdriver.common.appiumby import AppiumBy


class HomePage(BaseMobile):
    def __init__(self, driver):
        super().__init__(driver)
        self.search_icon = (AppiumBy.ID, "com.example.app:id/search_icon")
        self.profile_icon = (AppiumBy.ID, "com.example.app:id/profile_icon")
        self.menu_button = (AppiumBy.ID, "com.example.app:id/menu_button")

    def tap_search_icon(self):
        self.click_element(self.search_icon)

    def tap_profile_icon(self):
        self.click_element(self.profile_icon)

    def tap_menu_button(self):
        self.click_element(self.menu_button)


class SearchPage(BaseMobile):
    def __init__(self, driver):
        super().__init__(driver)
        self.search_input = (AppiumBy.ID, "com.example.app:id/search_input")
        self.search_button = (AppiumBy.ID, "com.example.app:id/search_button")
        self.search_results = (AppiumBy.ID, "com.example.app:id/search_results")

    def enter_search_text(self, text: str):
        self.enter_text(self.search_input, text)

    def tap_search_button(self):
        self.click_element(self.search_button)

    def get_search_results(self):
        return self.find_elements(self.search_results)


class ProfilePage(BaseMobile):
    def __init__(self, driver):
        super().__init__(driver)
        self.profile_name = (AppiumBy.ID, "com.example.app:id/profile_name")
        self.profile_email = (AppiumBy.ID, "com.example.app:id/profile_email")
        self.edit_button = (AppiumBy.ID, "com.example.app:id/edit_profile")

    def get_profile_name(self):
        return self.get_text(self.profile_name)

    def get_profile_email(self):
        return self.get_text(self.profile_email)

    def tap_edit_button(self):
        self.click_element(self.edit_button)