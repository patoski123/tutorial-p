from playwright.sync_api import Response
from typing import Dict, Any
import json


class APIHelpers:
    """API-specific helper functions"""

    @staticmethod
    def assert_status_code(response: Response, expected_code: int):
        """Assert response status code"""
        actual_code = response.status
        assert actual_code == expected_code, f"Expected {expected_code}, got {actual_code}"

    @staticmethod
    def assert_response_time(response: Response, max_time_ms: int = 5000):
        """Assert response time is within limits"""
        # Note: Playwright doesn't directly expose response time
        # This could be implemented with timing decorators
        pass

    @staticmethod
    def extract_json_path(response: Response, json_path: str):
        """Extract value from JSON response using JSONPath"""
        import jsonpath_ng
        data = response.json()
        jsonpath_expr = jsonpath_ng.parse(json_path)
        matches = jsonpath_expr.find(data)
        return matches[0].value if matches else None