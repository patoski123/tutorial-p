# # src/api/execution/executor.py
# # The single place that performs HTTP (Playwright / requests / mock) 
# # by calling any of the API Clients (api, requests.Session) from the conftest file 
# # and records to Allure + your trace via ApiRecorder.

# from __future__ import annotations
# import json
# from typing import Any, Dict, Tuple, Optional
# import os

# from .router import select_mode, ApiClientMode, mock_call

# # type hints are optional to keep deps light
# try:
#     from playwright.sync_api import APIRequestContext as PWContext 
# except Exception:
#     PWContext = object  # fallback so type hints don't explode

# class ApiExecutor:
#     """
#     Callable executor that routes requests to Playwright, requests, or mocks,
#     and records each call via ApiRecorder.
#     """
#     def __init__(self, *, pw_api, rq_session, settings, recorder):
#         self.pw_api = pw_api          # Playwright APIRequestContext (or None)
#         self.rq = rq_session          # requests.Session (or None)
#         self.settings = settings
#         self.recorder = recorder
#         # To console out the request and response body in the console use the below script.
#         # DEBUG_API=true pytest tests/
#         self.debug = getattr(settings, 'debug_api', False) or os.getenv('DEBUG_API', '').lower() == 'true'


#     def __call__(
#         self,
#         *,
#         ctx: Dict[str, Any],
#         step: str,
#         method: str,
#         path: str,
#         req_json: Optional[Dict[str, Any]] = None,
#         req_headers: Optional[Dict[str, str]] = None,
#         resp_headers: Optional[Dict[str, str]] = None,
#     ) -> Tuple[int, Dict[str, Any]]:
#         mode = select_mode(ctx)
#         req_headers = req_headers or {"Accept": "application/json", "Content-Type": "application/json"}
#         resp_headers = resp_headers or {"Content-Type": "application/json"}

#         if self.debug:
#             self._log_request(step, method, path, req_headers, req_json, mode)

#         if mode == ApiClientMode.PLAYWRIGHT:
#             if not self.pw_api:
#                 raise RuntimeError("Playwright API client not available")
#             resp = self.pw_api.fetch(
#                 path,
#                 method=method.upper(),
#                 headers=req_headers,
#                 data=json.dumps(req_json) if req_json else None,
#             )
#             status = resp.status
#             data = {}
#             ct = (resp.headers.get("content-type") or "").lower()
#             if "application/json" in ct:
#                 data = resp.json()

#         elif mode == ApiClientMode.REQUESTS:
#             if not self.rq:
#                 # lazy import if user didn’t install requests
#                 try:
#                     import requests  # noqa: F401
#                 except Exception as e:
#                     raise RuntimeError("requests mode selected but 'requests' is not installed") from e
#                 raise RuntimeError("requests mode selected but no requests.Session provided")
#             r = self.rq.request(
#                 method=method.upper(),
#                 url=f"{self.settings.api_base_url}{path}",
#                 headers=req_headers,
#                 json=req_json,
#                 timeout=30,
#             )
#             status = r.status_code
#             data = {}
#             ct = (r.headers.get("content-type") or "").lower()
#             if ct.startswith("application/json") or "application/json" in ct:
#                 try:
#                     data = r.json()
#                 except Exception:
#                     data = {}

#         else:  # MOCK
#             status, data = mock_call(method, path, req_json, self.settings)

#         if self.debug:
#             self._log_response(status, data, mode)

#         # one call: Allure + trace
#         self.recorder.record(
#             step=step,
#             method=method.upper(),
#             url=f"{self.settings.api_base_url}{path}",
#             status=status,
#             req_headers=req_headers,
#             req_json=req_json,
#             resp_headers=resp_headers,
#             resp_json=data,
#         )
#         return status, data

#     def _log_request(self, step, method, path, headers, body, mode):
#         full_url = f"{self.settings.api_base_url}{path}"
#         print(f"\n🚀 API REQUEST [{mode.upper()}]")
#         print(f"   Step: {step}")
#         print(f"   Method: {method.upper()}")
#         print(f"   Base URL: {self.settings.api_base_url}")
#         print(f"   Path: {path}")
#         print(f"   Full URL: {full_url}")
#         if headers:
#             print(f"   Headers: {json.dumps(headers, indent=8)}")
#         if body:
#             print(f"   Body: {json.dumps(body, indent=8)}")

#     def _log_response(self, status, data, mode):
#         print(f"\n📥 API RESPONSE [{mode.upper()}]")
#         print(f"   Status: {status}")
#         print(f"   Body: {json.dumps(data, indent=8)}")
#         print("=" * 60)

# def make_api_executor(*, pw_api, rq_session, settings, recorder) -> ApiExecutor:
#     """Factory for the executor (nice for tests and DI)."""
#     return ApiExecutor(pw_api=pw_api, rq_session=rq_session, settings=settings, recorder=recorder)

# src/api/execution/executor.py
# Enhanced version with console logging and colors

from __future__ import annotations
import json
import sys
import os
from typing import Any, Dict, Tuple, Optional

from .router import select_mode, ApiClientMode, mock_call

# type hints are optional to keep deps light
try:
    from playwright.sync_api import APIRequestContext as PWContext  # noqa: F401
except Exception:
    PWContext = object  # fallback so type hints don't explode

class ConsoleColors:
    def __init__(self):
        # Auto-detect color support
        self.use_colors = (
            hasattr(sys.stdout, 'isatty') and sys.stdout.isatty() and
            os.getenv('TERM') != 'dumb' and
            os.getenv('NO_COLOR') is None
        )
    
    def green(self, text): 
        return f"\033[92m{text}\033[0m" if self.use_colors else text
    
    def red(self, text): 
        return f"\033[91m{text}\033[0m" if self.use_colors else text
    
    def yellow(self, text): 
        return f"\033[93m{text}\033[0m" if self.use_colors else text
    
    def blue(self, text): 
        return f"\033[94m{text}\033[0m" if self.use_colors else text
    
    def cyan(self, text): 
        return f"\033[96m{text}\033[0m" if self.use_colors else text
    
    def magenta(self, text): 
        return f"\033[95m{text}\033[0m" if self.use_colors else text
    
    def bold(self, text): 
        return f"\033[1m{text}\033[0m" if self.use_colors else text
    
    def dim(self, text): 
        return f"\033[2m{text}\033[0m" if self.use_colors else text

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
        self.debug = getattr(settings, 'debug_api', False) or os.getenv('DEBUG_API', '').lower() == 'true'
        self.colors = ConsoleColors()
        
        # Store last response for failure reporting
        self.last_response = None

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
        
        full_url = f"{self.settings.api_base_url}{path}"

        # Enhancement #2 & #3: Always log request (colored)
        self._log_request(step, method, full_url, req_headers, req_json, mode)

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
                try:
                    import requests  # noqa: F401
                except Exception as e:
                    raise RuntimeError("requests mode selected but 'requests' is not installed") from e
                raise RuntimeError("requests mode selected but no requests.Session provided")
            r = self.rq.request(
                method=method.upper(),
                url=full_url,
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

        # Store for potential failure reporting
        self.last_response = {
            "status": status,
            "headers": resp_headers,
            "body": data,
            "url": full_url,
            "mode": mode
        }

        # Enhancement #3: If DEBUG_API=true, always log response
        if self.debug:
            self._log_response(status, data, mode, full_url)

        # Record to Allure + trace
        self.recorder.record(
            step=step,
            method=method.upper(),
            url=full_url,
            status=status,
            req_headers=req_headers,
            req_json=req_json,
            resp_headers=resp_headers,
            resp_json=data,
        )
        return status, data

    def _log_request(self, step, method, url, headers, body, mode):
        """Enhancement #2 & #3: Always log request with colors"""
        print(f"\n{self.colors.cyan('🚀 API REQUEST')} {self.colors.dim(f'[{mode.upper()}]')}")
        print(f"   {self.colors.bold('Step:')} {step}")
        print(f"   {self.colors.bold('Method:')} {self.colors.yellow(method.upper())}")
        print(f"   {self.colors.bold('URL:')} {self.colors.blue(url)}")
        
        if headers:
            print(f"   {self.colors.bold('Headers:')}")
            headers_str = json.dumps(headers, indent=6)
            print(f"{self.colors.dim(headers_str)}")
        
        if body:
            print(f"   {self.colors.bold('Body:')}")
            body_str = json.dumps(body, indent=6)
            print(f"{self.colors.green(body_str)}")

    def _log_response(self, status, data, mode, url):
        """Enhancement #3: Log response when DEBUG_API=true"""
        status_color = self.colors.green if status < 400 else self.colors.red
        print(f"\n{self.colors.magenta('📥 API RESPONSE')} {self.colors.dim(f'[{mode.upper()}]')}")
        print(f"   {self.colors.bold('URL:')} {self.colors.blue(url)}")
        print(f"   {self.colors.bold('Status:')} {status_color(str(status))}")
        
        if data:
            print(f"   {self.colors.bold('Body:')}")
            data_str = json.dumps(data, indent=6)
            print(f"{status_color(data_str)}")
        
        print(f"{self.colors.dim('=' * 60)}")

    def log_last_response_on_failure(self):
        """Enhancement #2: Call this on test failure to log response"""
        if not self.last_response:
            return
            
        resp = self.last_response
        status_color = self.colors.red  # Always red for failures
        
        print(f"\n{self.colors.red('💥 TEST FAILURE - LAST API RESPONSE 💥 ')}")
        print(f"   {self.colors.bold('URL:')} {self.colors.blue(resp['url'])}")
        print(f"   {self.colors.bold('Status:')} {status_color(str(resp['status']))}")
        print(f"   {self.colors.bold('Mode:')} {self.colors.dim(resp['mode'].upper())}")
        
        if resp['body']:
            print(f"   {self.colors.bold('Response Body:')}")
            body_str = json.dumps(resp['body'], indent=6)
            print(f"{status_color(body_str)}")
        
        print(f"{self.colors.red('=' * 60)}")


def make_api_executor(*, pw_api, rq_session, settings, recorder) -> ApiExecutor:
    """Factory for the executor (nice for tests and DI)."""
    return ApiExecutor(pw_api=pw_api, rq_session=rq_session, settings=settings, recorder=recorder)