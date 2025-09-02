# step_definitions/api/auth_api_steps.py
import pytest
from pytest_bdd import given, when, then, parsers
import logging

# Add logging to see if steps are being registered
logger = logging.getLogger(__name__)

# step_definitions/api/auth_api_steps.py
from typing import Any, Dict
from uuid import uuid4
import json



# Optional: Allure attachments if allure is installed
try:
    import allure
except Exception:
    allure = None  # degrade gracefully

# Shared per-scenario context
@pytest.fixture
def ctx() -> Dict[str, Any]:
    return {}

# ---------- Background ----------
@given("the API is available")
def api_is_available():
    # Mock: assume service is up (no network calls)
    pass

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
def send_login_request(ctx, auth_api):
    status, data = auth_api.login(ctx, ctx["username"], ctx["password"])
    ctx["resp_status"], ctx["resp_json"], ctx["token"] = status, data, data.get("access_token")

    
# @when("I send a login requestsss")
# def send_login_request(ctx, settings, api_recorder):
#     headers = {"Content-Type": "application/json", "Accept": "application/json"}
#     body = {"username": ctx.get("username"), "password": ctx.get("password")}

#     ok = (body["username"] == settings.test_username and body["password"] == settings.test_password)
#     if ok:
#         status = 200
#         response_json = {"access_token": f"mock-{uuid4()}", "token_type": "Bearer", "expires_in": 3600}
#     else:
#         status = 401
#         response_json = {"detail": "Invalid credentials"}

#     # stash for the Then
#     ctx["resp_status"] = status
#     ctx["resp_json"] = response_json
#     ctx["token"] = response_json.get("access_token")

#     # 🔹 one call does both: Allure attachments + trace HTML/JSON
#     api_recorder.record(
#         step="I send a login request",
#         method="POST",
#         url=f"{settings.api_base_url}/auth/login",
#         status=status,
#         req_headers=headers,
#         req_json=body,
#         resp_headers={"Content-Type": "application/json"},
#         resp_json=response_json,
#     )

@when("I send a login request to keep if you want it in the cucumber report")
def send_login_request(ctx, settings):
    """
    Pure mock of a JSON login:
    - Content-Type: application/json
    - Body: {"username": "...", "password": "..."}
    """
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    body = {
        "username": ctx.get("username"),
        "password": ctx.get("password"),
    }

    # (Optional) show what we'd "send" in Allure
    if allure:
        allure.attach(
            json.dumps({"headers": headers, "json": body}, indent=2),
            name="mock-login-request",
            attachment_type=getattr(allure.attachment_type, "JSON", None) or "application/json",
        )

    # Mocked verification against .env creds
    ok = (
        body["username"] == settings.test_username
        and body["password"] == settings.test_password
    )

    if ok:
        token = f"mock-{uuid4()}"
        status = 200
        response_json = {"access_token": token, "token_type": "Bearer", "expires_in": 3600}
    else:
        status = 401
        response_json = {"detail": "Invalid credentials"}

    # Save "response" in ctx for assertions
    ctx["resp_status"] = status
    ctx["resp_json"] = response_json
    ctx["token"] = response_json.get("access_token")

    if allure:
        allure.attach(
            json.dumps({"status": status, "json": response_json}, indent=2),
            name="mock-login-response",
            attachment_type=getattr(allure.attachment_type, "JSON", None) or "application/json",
        )

@then("I have a valid API authentication token")
def have_valid_api_token(ctx):
    assert ctx.get("resp_status") == 200, f"Unexpected status: {ctx.get('resp_status')}"
    token = (ctx.get("resp_json") or {}).get("access_token")
    assert token and isinstance(token, str) and token.strip(), f"No token in response: {ctx.get('resp_json')}"

