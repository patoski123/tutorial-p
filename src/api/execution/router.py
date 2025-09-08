# src/api/execution/router.py
# Small helper that decides which client to use 
# and provides simple mocks.

from __future__ import annotations
import os
from typing import Any, Dict, Optional, Tuple

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

def mock_call(method: str, path: str, body: Optional[Dict[str, Any]], settings) -> Tuple[int, Dict[str, Any]]:
    # Example stub: auth
    if path == "/login" and method.upper() == "POST":
        ok = (
            body
            and body.get("username") == settings.test_username
            and body.get("password") == settings.test_password
        )
        if ok:
            return 200, {"access_token": "mock-123", "token_type": "Bearer", "expires_in": 3600}
        return 401, {"detail": "Invalid credentials"}
    # Default stub
    return 200, {"ok": True, "path": path, "method": method}
