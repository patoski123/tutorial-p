from playwright.sync_api import Response
import jsonschema
from typing import Dict, Any


class ResponseValidator:
    """Advanced API response validation"""

    def __init__(self, response: Response):
        self.response = response
        self.data = response.json() if self._is_json_response() else None

    def _is_json_response(self) -> bool:
        """Check if response is JSON"""
        content_type = self.response.headers.get("content-type", "")
        return "application/json" in content_type

    def assert_status_code(self, expected_code: int):
        """Assert response status code"""
        assert self.response.status == expected_code

    def assert_json_schema(self, schema: Dict[str, Any]):
        """Validate JSON response against schema"""
        if not self.data:
            raise ValueError("Response is not JSON")

        jsonschema.validate(instance=self.data, schema=schema)

    def assert_response_headers(self, expected_headers: Dict[str, str]):
        """Assert response headers"""
        for header, value in expected_headers.items():
            actual_value = self.response.headers.get(header)
            assert actual_value == value, f"Header {header}: expected {value}, got {actual_value}"

    def assert_json_contains(self, expected_data: Dict[str, Any]):
        """Assert JSON response contains expected data"""
        if not self.data:
            raise ValueError("Response is not JSON")

        for key, expected_value in expected_data.items():
            assert key in self.data, f"Key {key} not found in response"
            assert self.data[key] == expected_value, f"Key {key}: expected {expected_value}, got {self.data[key]}"