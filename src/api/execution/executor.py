# src/api/execution/executor.py
# The single place that performs HTTP (Playwright / requests / mock) 
# and records to Allure + your trace via ApiRecorder.

from __future__ import annotations
import json
from typing import Any, Dict, Tuple, Optional

from .router import select_mode, ApiClientMode, mock_call

# type hints are optional to keep deps light
try:
    from playwright.sync_api import APIRequestContext as PWContext  # noqa: F401
except Exception:
    PWContext = object  # fallback so type hints don't explode

class ApiExecutor:
    """
    Callable executor that routes requests to Playwright, requests, or mocks,
    and records each call via ApiRecorder.
    """
    def __init__(self, *, pw_api, rq_session, settings, recorder):
        self.pw_api = pw_api          # Playwright APIRequestContext (or None)
        self.rq = rq_session          # requests.Session (or None)
        self.settings = settings
        self.recorder = recorder

    def __call__(
        self,
        *,
        ctx: Dict[str, Any],
        step: str,
        method: str,
        path: str,
        req_json: Optional[Dict[str, Any]] = None,
        req_headers: Optional[Dict[str, str]] = None,
        resp_headers: Optional[Dict[str, str]] = None,
    ) -> Tuple[int, Dict[str, Any]]:
        mode = select_mode(ctx)
        req_headers = req_headers or {"Accept": "application/json", "Content-Type": "application/json"}
        resp_headers = resp_headers or {"Content-Type": "application/json"}

        if mode == ApiClientMode.PLAYWRIGHT:
            if not self.pw_api:
                raise RuntimeError("Playwright API client not available")
            resp = self.pw_api.fetch(
                path,
                method=method.upper(),
                headers=req_headers,
                data=json.dumps(req_json) if req_json else None,
            )
            status = resp.status
            data = {}
            ct = (resp.headers.get("content-type") or "").lower()
            if "application/json" in ct:
                data = resp.json()

        elif mode == ApiClientMode.REQUESTS:
            if not self.rq:
                # lazy import if user didn’t install requests
                try:
                    import requests  # noqa: F401
                except Exception as e:
                    raise RuntimeError("requests mode selected but 'requests' is not installed") from e
                raise RuntimeError("requests mode selected but no requests.Session provided")
            r = self.rq.request(
                method=method.upper(),
                url=f"{self.settings.api_base_url}{path}",
                headers=req_headers,
                json=req_json,
                timeout=30,
            )
            status = r.status_code
            data = {}
            ct = (r.headers.get("content-type") or "").lower()
            if ct.startswith("application/json") or "application/json" in ct:
                try:
                    data = r.json()
                except Exception:
                    data = {}

        else:  # MOCK
            status, data = mock_call(method, path, req_json, self.settings)

        # one call: Allure + trace
        self.recorder.record(
            step=step,
            method=method.upper(),
            url=f"{self.settings.api_base_url}{path}",
            status=status,
            req_headers=req_headers,
            req_json=req_json,
            resp_headers=resp_headers,
            resp_json=data,
        )
        return status, data


def make_api_executor(*, pw_api, rq_session, settings, recorder) -> ApiExecutor:
    """Factory for the executor (nice for tests and DI)."""
    return ApiExecutor(pw_api=pw_api, rq_session=rq_session, settings=settings, recorder=recorder)
