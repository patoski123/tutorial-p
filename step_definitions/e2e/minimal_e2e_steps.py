from typing import Any, Dict
import pytest
from pytest_bdd import when, then
# assuming you already have src/api/clients/auth_api.py with .login(...)->(status, data)
from src.api.clients.auth_api import AuthAPI

@pytest.fixture
def ctx() -> Dict[str, Any]:
    return {}

@when("I login via the API using valid credentials")
def login_via_api(settings, ui_api_client, api_recorder, ctx):
    auth = AuthAPI(
        base_url=settings.api_base_url,
        api=ui_api_client,   # shares storage with the UI browser context
        mock=True,           # set False when wired to a real endpoint
        recorder=api_recorder,
    )
    status, data = auth.login(None, settings.test_username, settings.test_password)
    ctx["status"] = status
    ctx["token"] = data.get("access_token")

@when("I open the home page")
def open_home(ui_page, ctx):
    ui_page.goto("/")
    ctx["title"] = ui_page.title()

@then("I should have a token and see the page title")
def token_and_title(ctx):
    assert ctx["status"] == 200
    assert ctx["token"], "Expected a token from the API login"
    assert ctx["title"], "Expected a page title after navigating"

