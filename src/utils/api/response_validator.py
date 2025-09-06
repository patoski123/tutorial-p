from playwright.sync_api import Response
import jsonschema
from typing import Dict, Any, Mapping, Optional

try:
    import allure
except Exception:
    allure = None


class ResponseValidator:
    """Advanced API response validation"""

    def __init__(self, response: Response):
        self.response = response
        self.data = response.json() if self._is_json_response() else None

    def _is_json_response(self) -> bool:
        content_type = self.response.headers.get("content-type", "")
        return "application/json" in content_type

    def assert_status_code(self, expected_code: int):
        assert self.response.status == expected_code

    def assert_json_schema(self, schema: Dict[str, Any]):
        if not self.data:
            raise ValueError("Response is not JSON")
        jsonschema.validate(instance=self.data, schema=schema)

    def assert_response_headers(self, expected_headers: Dict[str, str]):
        for header, value in expected_headers.items():
            actual_value = self.response.headers.get(header)
            assert actual_value == value, f"Header {header}: expected {value}, got {actual_value}"

    def assert_json_contains(self, expected_data: Dict[str, Any]):
        if not self.data:
            raise ValueError("Response is not JSON")
        for key, expected_value in expected_data.items():
            assert key in self.data, f"Key {key} not found in response"
            assert self.data[key] == expected_value, f"Key {key}: expected {expected_value}, got {self.data[key]}"

    # --- Add this: bearer token assertion for real Playwright responses ---
    def assert_bearer_token(self) -> str:
        """Assert OAuth-style bearer token on this response's JSON and return it."""
        if not self.data:
            raise ValueError("Response is not JSON")
        token = self.data.get("access_token")
        token_type = self.data.get("token_type")
        if allure:
            with allure.step("Assert bearer token present"):
                assert token, "missing token"
                assert token_type == "Bearer", f"unexpected token_type: {token_type!r}"
        else:
            assert token, "missing token"
            assert token_type == "Bearer", f"unexpected token_type: {token_type!r}"
        return str(token)


# --- Add this: helper for dict payloads (mock / requests-based flows) ---
def assert_bearer_token_payload(payload: Mapping[str, Any]) -> str:
    """Assert token in a plain dict payload and return it (works with mocks)."""
    token = payload.get("access_token")
    token_type = payload.get("token_type")
    if allure:
        with allure.step("Assert bearer token present"):
            assert token, "missing token"
            assert token_type == "Bearer", f"unexpected token_type: {token_type!r}"
    else:
        assert token, "missing token"
        assert token_type == "Bearer", f"unexpected token_type: {token_type!r}"
    return str(token)


# # step_definitions/api/auth_api_steps.py
# mock flow
# from src.utils.api.response_validator import assert_bearer_token_payload

# @then("I have a valid API_token")
# def have_valid_api_token(ctx):
#     token = assert_bearer_token_payload(ctx["resp_json"])
#     ctx["token"] = token


# from src.utils.api.response_validator import ResponseValidator
# Use it in a real Playwright API call
# # after you get a real Response `resp` from playwright.request
# validator = ResponseValidator(resp)
# token = validator.assert_bearer_token()
# ctx["token"] = token
