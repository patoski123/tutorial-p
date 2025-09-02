# src/pages/dashboard_page.py
from pages.base_page import BasePage  # or relative, but this is fine if SRC on sys.path

class DashboardPage(BasePage):
    def __init__(self, page):
        super().__init__(page)
        # locators, etc.