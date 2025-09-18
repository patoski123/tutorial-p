# step_definitions/api/auth_api_steps.py
import pytest
from pytest_bdd import given, when, then, parsers
import logging
from typing import Any, Dict
from src.api.wrappers.auth_api import AuthAPI
# Add logging to see if steps are being registered
logger = logging.getLogger(__name__)

# Optional: Allure attachments if allure is installed
try:
    import allure
except Exception:
    allure = None  # degrade gracefully

# Domain-specific fixture - keeps auth logic with auth steps
# @pytest.fixture
# def auth_api(api_executor):
#     """Auth API client for authentication-related operations."""
#     return AuthAPI(api_executor, base_path="/auth")

# Shared per-scenario context
@pytest.fixture
def ctx() -> Dict[str, Any]:
    return {}

# ---------- Background ----------
# @given("the API is available")
# def api_is_available():
#     # Mock: assume service is up (no network calls)
#     pass

@given(parsers.parse("I use the {client} API client"))
def choose_api_client(ctx, client):
    client = client.strip().lower()
    assert client in {"mock", "requests", "playwright"}
    ctx["api_client"] = client

@given("I have valid test credentials")
def have_valid_test_credentials(ctx, settings):
    # pull dev creds from .env via Settings
    ctx["username"] = settings.test_username
    ctx["password"] = settings.test_password

# ---------- Scenario steps ----------
@given(parsers.parse('I have a valid username "{username}"'))
def have_username(ctx, username: str):
    ctx["username"] = username

@given(parsers.parse('I have a valid password "{password}"'))
def have_password(ctx, password: str):
    ctx["password"] = password

@when("I send a login request")
# def send_login_request(ctx, auth_api, api): 
def send_login_request(ctx, api_executor): 
    # status, data = auth_api.login(ctx, ctx["username"], ctx["password"])
    # ctx["resp_status"], ctx["resp_json"], ctx["token"] = status, data, 
    # ctx["resp_status"], ctx["resp_json"], ctx["token"] = status, data, 
    # data.get("access_token")

    auth_api = AuthAPI(api_executor)
    status, data = auth_api.login(ctx, ctx["username"], ctx["password"])
    ctx["resp_status"], ctx["resp_json"] = status, data,
    if isinstance(data, dict):
        ctx["token"] = data.get("access_token") if isinstance(data, dict) else None
    if status != 200:
        print(f"Login failed with status {status}: {data}")

@then("I have a valid API authentication token")
def have_valid_api_token(ctx):
    assert ctx.get("resp_status") == 200, f"Unexpected status: {ctx.get('resp_status')}"
    token = (ctx.get("resp_json") or {}).get("access_token")
    assert token and isinstance(token, str) and token.strip(), f"No token in response: {ctx.get('resp_json')}"

@then(parsers.parse("the response status should be {expected_status:d}"))
def assert_response_status(ctx, expected_status, api_executor):
    actual_status = ctx.get("resp_status")
    assert actual_status == expected_status, f"Expected {expected_status} but got {actual_status}"

# If you have E2E scenarios that need shared browser state, add alternative steps:
@when("I send a login request with shared browser state")
def send_login_request_shared(ctx, auth_api, api_shared, page):
    """
    For E2E scenarios where you've done UI login first and need API calls with shared state.
    """
    # Create API client with shared state AFTER any UI interactions
    shared_api = api_shared()
    status, data = auth_api.login(ctx, ctx["username"], ctx["password"], api_client=shared_api)
    ctx["resp_status"], ctx["resp_json"], ctx["token"] = status, data, data.get("access_token")

@when('I get list instance with retry')
def get_list_instance_with_retry(ctx, api_executor):
    auth_api = AuthAPI(api_executor)
    endpoint = ctx['endpoint']  # Get endpoint from previous step
    status, data = auth_api.get_list_instance_with_retry(
        ctx, "testuser", "testpass", endpoint, max_attempts=5
    )
    ctx['status'] = status
    ctx['response'] = data