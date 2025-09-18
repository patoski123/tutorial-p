# src/api/execution/router.py
# Small helper that decides which client to use 
# and provides simple mocks.

from __future__ import annotations
import os
from typing import Any, Dict, Optional, Tuple
_retry_attempts = {}

class ApiClientMode:
    MOCK = "mock"
    REQUESTS = "requests"
    PLAYWRIGHT = "playwright"

def select_mode(ctx: Dict[str, Any]) -> str:
    """
    Priority: per-scenario ctx['api_client'] > env API_CLIENT > default MOCK.
    Valid values: 'mock' | 'requests' | 'playwright'
    """
    return (ctx.get("api_client") or os.getenv("API_CLIENT") or ApiClientMode.MOCK).lower()

# def mock_call(method: str, path: str, body: Optional[Dict[str, Any]], settings) -> Tuple[int, Dict[str, Any]]:
#     # Example stub: auth
#     if path == "/login" and method.upper() == "POST":
#         ok = (
#             body
#             and body.get("username") == settings.test_username
#             and body.get("password") == settings.test_password
#         )
#         if ok:
#             return 200, {"access_token": "mock-123", "token_type": "Bearer", "expires_in": 3600}
#         return 401, {"detail": "Invalid credentials"}
#     # Default stub
#     return 200, {"ok": True, "path": path, "method": method}

# src/api/execution/router.py - Add this to your existing mock_call function

# Add this global state tracker at the top of your router.py file

def reset_retry_attempts():
    """Reset retry attempts - useful for test cleanup"""
    global _retry_attempts
    _retry_attempts.clear()

def mock_call(method: str, path: str, body: Optional[Dict[str, Any]], settings) -> Tuple[int, Dict[str, Any]]:
    global _retry_attempts
    
    # Your existing login logic here...
    # if path == "/login" and method.upper() == "POST":
    #     ... existing code ...
    
    # NEW: Simple retry endpoint for testing
    if path == "/api/retry-test" and method.upper() == "POST":
        # Get retry configuration from request body or use defaults
        max_failures = body.get("max_failures", 3) if body else 3
        endpoint_id = body.get("endpoint_id", "default") if body else "default"
        
        # Track attempts for this endpoint
        if endpoint_id not in _retry_attempts:
            _retry_attempts[endpoint_id] = 0
        
        _retry_attempts[endpoint_id] += 1
        current_attempt = _retry_attempts[endpoint_id]
        
        # Fail for the first N attempts, then succeed
        if current_attempt <= max_failures:
            return 503, {
                "status": "Running",
                "message": f"Server currently running, wait... (attempt {current_attempt})",
                "details": None,
                "attempt": current_attempt,
                "max_failures": max_failures
            }
        else:
            # Success after max_failures + 1 attempts
            # Reset counter for next test
            _retry_attempts[endpoint_id] = 0
            
            return 200, {
                "status": "Successful", 
                "message": "Details are fetched successfully",
                "details": [
                    {"id": 1, "name": "Test Data 1", "value": "success"},
                    {"id": 2, "name": "Test Data 2", "value": "completed"}
                ],
                "total_attempts": current_attempt
            }
    
    # Your existing default stub
    return 200, {"ok": True, "path": path, "method": method}
