# # src/api/execution/executor.py
# # The single place that performs HTTP (Playwright / requests / mock) 
# # by calling any of the API Clients (api, requests.Session) from the conftest file 
# # and records to Allure + your trace via ApiRecorder.
# src/api/execution/executor.py
# Enhanced version with console logging and colors

from __future__ import annotations

import json
import os
import re
import sys
import threading
import time
import random
from contextlib import contextmanager
from typing import Any, Dict, List, Optional, Tuple, Union, Callable
from urllib.parse import urlparse, parse_qsl, urlencode, urlunparse

from .router import select_mode, ApiClientMode, mock_call

# Optional typing helper so imports don't explode if Playwright isn't installed
try:
    from playwright.sync_api import APIRequestContext as PWContext  # noqa: F401
except Exception:  # pragma: no cover
    PWContext = object  # type: ignore


# ---------- Console colors ----------

class ConsoleColors:
    def __init__(self):
        self.use_colors = (
            hasattr(sys.stdout, "isatty")
            and sys.stdout.isatty()
            and os.getenv("TERM") != "dumb"
            and os.getenv("NO_COLOR") is None
        )

    def _c(self, code: str, text: str) -> str:
        return f"\033[{code}m{text}\033[0m" if self.use_colors else text

    def green(self, t):   return self._c("92", t)
    def red(self, t):     return self._c("91", t)
    def yellow(self, t):  return self._c("93", t)
    def blue(self, t):    return self._c("94", t)
    def cyan(self, t):    return self._c("96", t)
    def magenta(self, t): return self._c("95", t)
    def bold(self, t):    return self._c("1", t)
    def dim(self, t):     return self._c("2", t)


# ---------- Enhanced data redaction ----------

class DataRedactor:
    """Redacts sensitive values in headers, JSON bodies, and URL query params with size limits."""

    # Always redact these headers, regardless of values
    ALWAYS_REDACT_HEADERS = {
        "authorization",
        "proxy-authorization",
        "x-api-key",
        "api-key",
        "x-auth-token",
        "x-session-id",
        "cookie",
        "set-cookie",
        "x-forwarded-authorization",
        "x-real-authorization",
    }

    # Field names that are sensitive (exact match after normalization)
    DEFAULT_SENSITIVE_FIELDS = {
        "password", "passwd", "pwd",
        "secret", "token", "key", "api_key", "private_key",
        "credential", "pin", "ssn", "social_security",
        "credit_card", "creditcard", "cc_number", "cvv",
        "access_token", "refresh_token", "id_token",
        "session_id", "client_secret", "webhook_secret",
    }

    # Enhanced value patterns for better detection (UUID removed from defaults)
    SENSITIVE_VALUE_PATTERNS = [
        r"^[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+$",  # JWT (xxx.yyy.zzz)
        r"^Bearer\s+[A-Za-z0-9\-._~+/]+=*$",                  # Bearer token
        r"^Basic\s+[A-Za-z0-9+/]+=*$",                        # Basic auth
        r"^[A-Za-z0-9+/]{32,}={0,2}$",                        # Long base64-ish
        r"^\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}$",          # Credit card
        r"^\d{3}-\d{2}-\d{4}$",                               # US SSN
        r"^sk-[a-zA-Z0-9]{32,}$",                             # OpenAI-style API keys
    ]
    
    # Optional UUID pattern (opt-in only)
    UUID_PATTERN = r"^[a-fA-F0-9]{8}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{12}$"

    def __init__(
        self, 
        sensitive_fields: Optional[set] = None, 
        redaction_text: str = "***REDACTED***",
        max_body_size: int = 51200,  # 50KB default
        include_uuid_pattern: bool = False  # Opt-in for UUID redaction
    ):
        self.sensitive_fields = sensitive_fields or self.DEFAULT_SENSITIVE_FIELDS
        self.redaction_text = redaction_text
        self.max_body_size = max_body_size
        
        # Build patterns list - UUID is opt-in
        patterns = self.SENSITIVE_VALUE_PATTERNS.copy()
        if include_uuid_pattern:
            patterns.append(self.UUID_PATTERN)
        
        self.value_patterns = [re.compile(p) for p in patterns]

    # ---- helpers ----

    def _normalize(self, s: str) -> str:
        return s.lower().replace("-", "_").replace(" ", "_")

    def _is_sensitive_field(self, field_name: str) -> bool:
        return self._normalize(field_name) in self.sensitive_fields

    def _is_sensitive_header(self, header_name: str) -> bool:
        return self._normalize(header_name) in self.ALWAYS_REDACT_HEADERS

    def _is_sensitive_value(self, value: str) -> bool:
        if not isinstance(value, str) or len(value) < 8:
            return False
        return any(p.match(value) for p in self.value_patterns)

    def _truncate_if_large(self, data: Any) -> Any:
        """Truncate large bodies (JSON, strings, or bytes) to prevent performance issues"""
        if not data:
            return data
        
        # Handle different data types
        if isinstance(data, (str, bytes)):
            # Raw string or bytes response
            content_size = len(data)
            if content_size > self.max_body_size:
                safe_size = max(1024, self.max_body_size // 2)
                if isinstance(data, bytes):
                    truncated_content = data[:safe_size].decode('utf-8', errors='replace')
                    data_type = "bytes"
                else:
                    truncated_content = data[:safe_size]
                    data_type = "string"
                
                return {
                    "_redactor_truncated": True,
                    "_original_size": content_size,
                    "_data_type": data_type,
                    "_showing_first_chars": safe_size,
                    "_truncated_content": truncated_content,
                    "_note": f"Large {data_type} response ({content_size} chars/bytes). Showing first {safe_size}."
                }
            return data
        
        # JSON-serializable data
        try:
            json_str = json.dumps(data)
            if len(json_str) > self.max_body_size:
                safe_size = max(1024, self.max_body_size // 2)
                truncated_str = json_str[:safe_size]
                
                return {
                    "_redactor_truncated": True,
                    "_original_size_bytes": len(json_str),
                    "_showing_first_bytes": safe_size,
                    "_truncated_content": truncated_str,
                    "_note": f"Large JSON response ({len(json_str)} bytes). Showing first {safe_size} bytes."
                }
        except (TypeError, ValueError):
            # Not JSON serializable, leave as-is
            pass
        
        return data

    # ---- URL query redaction ----

    def redact_url(self, url: str) -> str:
        """Redact sensitive query parameters in URLs"""
        try:
            p = urlparse(url)
            if not p.query:
                return url
            q: List[Tuple[str, str]] = []
            for k, v in parse_qsl(p.query, keep_blank_values=True):
                if self._is_sensitive_field(k) or self._is_sensitive_value(v):
                    q.append((k, self.redaction_text))
                else:
                    q.append((k, v))
            return urlunparse(p._replace(query=urlencode(q, doseq=True)))
        except Exception:
            return url

    # ---- JSON/headers redaction ----

    def redact_dict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        if not isinstance(data, dict):
            return data
        out: Dict[str, Any] = {}
        for k, v in data.items():
            if self._is_sensitive_field(k):
                out[k] = self.redaction_text
            elif isinstance(v, dict):
                out[k] = self.redact_dict(v)
            elif isinstance(v, list):
                out[k] = self.redact_list(v)
            elif isinstance(v, str) and self._is_sensitive_value(v):
                out[k] = self.redaction_text
            else:
                out[k] = v
        return out

    def redact_list(self, data: List[Any]) -> List[Any]:
        if not isinstance(data, list):
            return data
        out: List[Any] = []
        for item in data:
            if isinstance(item, dict):
                out.append(self.redact_dict(item))
            elif isinstance(item, list):
                out.append(self.redact_list(item))
            elif isinstance(item, str) and self._is_sensitive_value(item):
                out.append(self.redaction_text)
            else:
                out.append(item)
        return out

    def redact_headers(self, headers: Optional[Dict[str, str]]) -> Optional[Dict[str, str]]:
        if not headers:
            return headers
        out: Dict[str, str] = {}
        for k, v in headers.items():
            if self._is_sensitive_header(k) or self._is_sensitive_field(k):
                out[k] = self.redaction_text
            elif isinstance(v, str) and self._is_sensitive_value(v):
                out[k] = self.redaction_text
            else:
                out[k] = v
        return out

    def redact_json(self, data: Union[Dict, List, Any]) -> Union[Dict, List, Any]:
        """Main redaction method with size limits"""
        # First truncate if too large, then redact
        truncated_data = self._truncate_if_large(data)
        
        if isinstance(truncated_data, dict):
            return self.redact_dict(truncated_data)
        if isinstance(truncated_data, list):
            return self.redact_list(truncated_data)
        return truncated_data


# ---------- Enhanced retry utilities ----------

class RetryHelpers:
    """Enhanced retry utilities with exponential backoff and comprehensive error handling"""
    
    # Comprehensive list of retryable HTTP status codes
    DEFAULT_RETRYABLE_STATUSES = [
        0,    # Transport/connection errors (synthetic status)
        408,  # Request Timeout
        429,  # Too Many Requests
        500,  # Internal Server Error
        501,  # Not Implemented
        502,  # Bad Gateway
        503,  # Service Unavailable
        504,  # Gateway Timeout
        505,  # HTTP Version Not Supported
        507,  # Insufficient Storage
        508,  # Loop Detected
        509,  # Bandwidth Limit Exceeded
        510,  # Not Extended
        511,  # Network Authentication Required
    ]
    
    @staticmethod
    def retry_api_call(
        api_call: Callable[[], Tuple[int, Dict[str, Any]]],
        max_attempts: int = 5,
        delay: float = 1.0,
        retry_on_statuses: Optional[List[int]] = None,
        timeout: Optional[float] = None,
        description: str = "API call"
    ) -> Tuple[int, Dict[str, Any]]:
        """
        Basic retry with linear backoff and exception handling
        """
        if retry_on_statuses is None:
            retry_on_statuses = RetryHelpers.DEFAULT_RETRYABLE_STATUSES
        
        start_time = time.time()
        
        for attempt in range(1, max_attempts + 1):
            # Check timeout
            if timeout and (time.time() - start_time) > timeout:
                print(f"❌ {description} timed out after {timeout}s")
                return 408, {"error": "Request timeout", "elapsed_time": time.time() - start_time}
            
            try:
                status, data = api_call()
            except Exception as e:
                # Convert exceptions to synthetic HTTP responses
                status = 0  # Special status for exceptions
                data = {
                    "error": "Connection/transport error",
                    "exception_type": type(e).__name__,
                    "exception_message": str(e),
                    "attempt": attempt
                }
                print(f"🔌 {description} attempt {attempt} failed with {type(e).__name__}: {e}")
                
                # Treat exceptions as retryable
                if attempt == max_attempts:
                    print(f"❌ {description} failed after {max_attempts} attempts (final error: {type(e).__name__})")
                    return status, data
                
                print(f"🔄 Retrying {description} in {delay}s...")
                time.sleep(delay)
                continue
            
            # Success or non-retryable status
            if status not in retry_on_statuses:
                if attempt > 1:
                    print(f"✅ {description} succeeded on attempt {attempt}")
                return status, data
            
            # Last attempt - return the failure
            if attempt == max_attempts:
                print(f"❌ {description} failed after {max_attempts} attempts")
                return status, data
            
            # Wait and retry
            print(f"🔄 {description} attempt {attempt} failed (status: {status}). Retrying in {delay}s...")
            time.sleep(delay)
        
        return status, data
    
    @staticmethod
    def retry_api_call_with_backoff(
        api_call: Callable[[], Tuple[int, Dict[str, Any]]],
        max_attempts: int = 5,
        initial_delay: float = 1.0,
        max_delay: float = 30.0,
        backoff_factor: float = 2.0,
        jitter: bool = True,
        retry_on_statuses: Optional[List[int]] = None,
        timeout: Optional[float] = None,
        description: str = "API call"
    ) -> Tuple[int, Dict[str, Any]]:
        """
        Enhanced retry with exponential backoff and jitter
        """
        if retry_on_statuses is None:
            retry_on_statuses = RetryHelpers.DEFAULT_RETRYABLE_STATUSES
        
        start_time = time.time()
        delay = initial_delay
        
        for attempt in range(1, max_attempts + 1):
            # Check timeout
            if timeout and (time.time() - start_time) > timeout:
                elapsed = time.time() - start_time
                print(f"❌ {description} timed out after {elapsed:.1f}s")
                return 408, {"error": "Request timeout", "elapsed_time": elapsed}
            
            try:
                status, data = api_call()
            except Exception as e:
                # Convert exceptions to synthetic HTTP responses
                status = 0  # Special status for exceptions
                data = {
                    "error": "Connection/transport error",
                    "exception_type": type(e).__name__,
                    "exception_message": str(e),
                    "attempt": attempt
                }
                print(f"🔌 {description} attempt {attempt} failed with {type(e).__name__}: {e}")
    
                # Treat exceptions as retryable
                if attempt == max_attempts:
                    elapsed = time.time() - start_time
                    print(f"❌ {description} failed after {max_attempts} attempts (final error: {type(e).__name__})")
                    return status, data
    
                print(f"🔄 Retrying {description} in {actual_delay:.1f}s...")
                time.sleep(actual_delay)
    
                # Exponential backoff for next iteration
                delay = min(delay * backoff_factor, max_delay)
                continue           

            # Success or non-retryable status
            if status not in retry_on_statuses:
                if attempt > 1:
                    elapsed = time.time() - start_time
                    print(f"✅ {description} succeeded on attempt {attempt} after {elapsed:.1f}s")
                return status, data
            
            # Last attempt - return the failure
            if attempt == max_attempts:
                elapsed = time.time() - start_time
                print(f"❌ {description} failed after {max_attempts} attempts in {elapsed:.1f}s")
                return status, data
            
            # Calculate next delay with exponential backoff and optional jitter
            actual_delay = delay
            if jitter:
                # Add ±25% random jitter to prevent thundering herd
                jitter_range = delay * 0.25
                actual_delay = delay + random.uniform(-jitter_range, jitter_range)
                actual_delay = max(0.1, actual_delay)  # Minimum 100ms
            
            print(f"🔄 {description} attempt {attempt} failed (status: {status}). Retrying in {actual_delay:.1f}s...")
            time.sleep(actual_delay)
            
            # Exponential backoff for next iteration
            delay = min(delay * backoff_factor, max_delay)
        
        return status, data


# ---------- Enhanced ApiExecutor ----------

class ApiExecutor:
    """
    Enhanced executor with comprehensive retry, redaction, and monitoring capabilities.
    Routes requests to Playwright request context, python-requests, or mock,
    prints colored logs (optional), redacts sensitive data, and records via a
    provided recorder.
    """

    def __init__(self, *, pw_api, rq_session, settings, recorder):
        self.pw_api = pw_api
        self.rq = rq_session
        self.settings = settings
        self.recorder = recorder

        self.debug = getattr(settings, "debug_api", False) or os.getenv("DEBUG_API", "").lower() == "true"
        self.colors = ConsoleColors()
        self.last_response: Optional[Dict[str, Any]] = None

        # Thread-local storage for parallel execution safety
        self._local = threading.local()
        
        # Enhanced redaction with configurable size limits
        redact_enabled = getattr(settings, "redact_sensitive_data", True) or os.getenv("REDACT_SENSITIVE_DATA", "true").lower() == "true"
        max_body_size = getattr(settings, "max_log_body_size", 51200)  # 50KB default
        include_uuid = (getattr(settings, "redact_uuid_values", False) or os.getenv("REDACT_UUIDS", "false").lower() == "true")
        self.redactor = DataRedactor(max_body_size=max_body_size, include_uuid_pattern=include_uuid,) if redact_enabled else None

    # ---- recording toggles ----

    @property
    def skip_recording(self) -> bool:
        return getattr(self._local, "skip_recording", False)

    @skip_recording.setter
    def skip_recording(self, value: bool) -> None:
        self._local.skip_recording = value

    @contextmanager
    def silent_recording(self):
        """Thread-safe context manager for temporarily disabling recording"""
        prev = self.skip_recording
        self.skip_recording = True
        try:
            yield
        finally:
            self.skip_recording = prev

    # ---- helpers ----

    def _redact_if_enabled(self, data: Any) -> Any:
        return self.redactor.redact_json(data) if (self.redactor and data is not None) else data

    def _method_allows_body(self, method: str) -> bool:
        return method.upper() in {"POST", "PUT", "PATCH", "DELETE"}

    def _extract_response_headers(self, resp_obj: Any, mode: ApiClientMode) -> Dict[str, str]:
        """Extract actual response headers based on the client type"""
        try:
            if mode == ApiClientMode.PLAYWRIGHT:
                return dict(resp_obj.headers or {})
            elif mode == ApiClientMode.REQUESTS:
                return dict(resp_obj.headers or {})
            else:  # MOCK
                return {"Content-Type": "application/json", "X-Mock-Response": "true"}
        except Exception:
            return {"Content-Type": "application/json"}

    def _ensure_leading_slash(self, path: str) -> str:
        """Ensure path has leading slash for proper URL joining"""
        return path if path.startswith('/') else f'/{path}'

    def _get_mode_name(self, mode) -> str:
        """Get clean mode name for logging"""
        if hasattr(mode, 'name'):
            return mode.name
        return str(mode).replace('ApiClientMode.', '')

    def _has_content_type(self, headers: Dict[str, str]) -> bool:
        """Case-insensitive check for Content-Type header"""
        return any(key.lower() == 'content-type' for key in headers.keys())

    # ---- main call ----

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

        # Assemble headers: keep minimal defaults; only set Content-Type if we do send a body
        headers: Dict[str, str] = {"Accept": "application/json"}
        if req_headers:
            headers.update(req_headers)
        send_body = self._method_allows_body(method) and (req_json is not None)
        if send_body and not self._has_content_type(headers):
            headers["Content-Type"] = "application/json"

        base = self.settings.api_base_url.rstrip("/")
        safe_path = self._ensure_leading_slash(path)
        full_url = f"{base}{safe_path}"
        safe_url = self.redactor.redact_url(full_url) if self.redactor else full_url

        if not self.skip_recording:
            self._log_request(step, method, safe_url, headers, req_json, mode, send_body)
           
        # Execute with proper exception handling and response header capture
        real_resp_headers: Dict[str, str] = {}
        status = 0
        data: Dict[str, Any] = {}
        
        try:
            if mode == ApiClientMode.PLAYWRIGHT:
                if not self.pw_api:
                    raise RuntimeError("Playwright API client not available")
                resp = self.pw_api.fetch(
                    safe_path,
                    method=method.upper(),
                    headers=headers,
                    data=json.dumps(req_json) if send_body else None,
                )
                status = resp.status
                real_resp_headers = self._extract_response_headers(resp, mode)
                ct = (real_resp_headers.get("content-type") or "").lower()
                if "application/json" in ct:
                    try:
                        data = resp.json()
                    except Exception:
                        data = {}
                else:
                    # capture small text responses (won’t blow up logs)
                    try:
                        txt = resp.text()
                        max_size = self.redactor.max_body_size if self.redactor else 51200
                        if isinstance(txt, str) and len(txt) <= max_size:
                            data = txt
                    except Exception:
                        pass

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
                    headers=headers,
                    json=req_json if send_body else None,
                    timeout=30,
                )
                status = r.status_code
                real_resp_headers = self._extract_response_headers(r, mode)
                ct = (real_resp_headers.get("content-type") or "").lower()
                if "application/json" in ct:
                    try:
                        data = r.json()
                    except Exception:
                        data = {}
                else:
                    try:
                        txt = r.text
                        max_size = self.redactor.max_body_size if self.redactor else 51200
                        if isinstance(txt, str) and len(txt) <= max_size:
                            data = txt
                    except Exception:
                        pass

            else:  # MOCK
                status, data = mock_call(method, safe_path, req_json, self.settings)
                real_resp_headers = resp_headers or self._extract_response_headers(None, mode)

        except Exception as e:
            # Capture transport/connection errors as synthetic failures
            status = 0  # Special status for exceptions
            data = {
                "error": "Transport/connection error",
                "exception_type": type(e).__name__,
                "exception_message": str(e),
                "url": full_url,
                "method": method.upper()
            }
            real_resp_headers = {"Content-Type": "application/json"}
            print(f"🔌 Transport error for {method.upper()} {safe_url}: {type(e).__name__}: {e}")

        # Enhanced last response tracking
        self.last_response = {
            "status": status,
            "headers": real_resp_headers,
            "body": data,
            "url": full_url,
            "mode": self._get_mode_name(mode),
            "method": method.upper(),
            "timestamp": time.time(),
            "step": step,
        }

        if self.debug and not self.skip_recording:
            self._log_response(status, data, mode, safe_url, real_resp_headers)

        if not self.skip_recording:
            safe_req_headers = self.redactor.redact_headers(headers) if self.redactor else headers
            safe_req_json = self._redact_if_enabled(req_json)
            safe_resp_headers = self.redactor.redact_headers(real_resp_headers) if self.redactor else real_resp_headers
            safe_resp_json = self._redact_if_enabled(data)

            self.recorder.record(
                step=step,
                method=method.upper(),
                url=safe_url,
                status=status,
                req_headers=safe_req_headers,
                req_json=safe_req_json,
                resp_headers=safe_resp_headers,
                resp_json=safe_resp_json,
            )

        return status, data

    # ---- enhanced logging ----

    def _log_request(self, step, method, url, headers, body, mode, send_body):    
        mode_name = self._get_mode_name(mode)
        print(f"\n{self.colors.cyan('🚀 API REQUEST')} {self.colors.dim(f'[{mode_name}]')}")
        print(f"   {self.colors.bold('Step:')} {step}")
        print(f"   {self.colors.bold('Method:')} {self.colors.yellow(method.upper())}")
        print(f"   {self.colors.bold('URL:')} {self.colors.blue(url)}")

        if headers:
            print(f"   {self.colors.bold('Headers:')}")
            safe_headers = self.redactor.redact_headers(headers) if self.redactor else headers
            print(self.colors.dim(json.dumps(safe_headers, indent=6)))

        if body is not None and send_body:
            print(f"   {self.colors.bold('Body:')}")
            safe_body = self._redact_if_enabled(body)
            print(self.colors.green(json.dumps(safe_body, indent=6)))

    def _log_response(self, status, data, mode, url, headers):
        mode_name = self._get_mode_name(mode)
        status_color = self.colors.green if status < 400 else self.colors.red
        print(f"\n{self.colors.magenta('📥 API RESPONSE')} {self.colors.dim(f'[{mode_name}]')}")
        print(f"   {self.colors.bold('URL:')} {self.colors.blue(url)}")
        print(f"   {self.colors.bold('Status:')} {status_color(str(status))}")
        
        if headers:
            print(f"   {self.colors.bold('Response Headers:')}")
            safe_headers = self.redactor.redact_headers(headers) if self.redactor else headers
            print(self.colors.dim(json.dumps(safe_headers, indent=6)))
        
        if data is not None:
            print(f"   {self.colors.bold('Body:')}")
            safe = self._redact_if_enabled(data)
            print(status_color(json.dumps(safe, indent=6)))
        print(self.colors.dim("=" * 60))

    def log_last_response_on_failure(self):
        """Enhanced failure logging with more context"""
        if not self.last_response:
            return
        resp = self.last_response
        safe_url = self.redactor.redact_url(resp['url']) if self.redactor else resp['url']

        print(f"\n{self.colors.red('💥 TEST FAILURE - LAST API RESPONSE 💥')}")
        print(f"   {self.colors.bold('Step:')} {self.colors.red(resp.get('step', 'UNKNOWN'))}")
        print(f"   {self.colors.bold('Method:')} {self.colors.red(resp.get('method', 'UNKNOWN'))}")
        print(f"   {self.colors.bold('URL:')} {self.colors.blue(safe_url)}")
        print(f"   {self.colors.bold('Status:')} {self.colors.red(str(resp['status']))}")
        print(f"   {self.colors.bold('Mode:')} {self.colors.dim(resp.get('mode', 'UNKNOWN'))}")

        if resp.get("headers"):
            print(f"   {self.colors.bold('Response Headers:')}")
            safe_headers = self.redactor.redact_headers(resp["headers"]) if self.redactor else resp["headers"]
            print(self.colors.red(json.dumps(safe_headers, indent=6)))

        if resp.get("body") is not None:
            print(f"   {self.colors.bold('Response Body:')}")
            safe = self._redact_if_enabled(resp["body"])
            print(self.colors.red(json.dumps(safe, indent=6)))
        print(self.colors.red("=" * 60))


    
    def record_final_retry_attempt(
        self,
        step: str,
        method: str,
        path: str,
        req_json: Optional[Dict] = None,
        req_headers: Optional[Dict] = None,
        ):
        """Record the final attempt from a retry using cached last_response data."""
        if not self.last_response:
            return

        safe_path = self._ensure_leading_slash(path)
        base = self.settings.api_base_url.rstrip("/")
        full_url = f"{base}{safe_path}"
        safe_url = self.redactor.redact_url(full_url) if self.redactor else full_url

        safe_req_headers = (
            self.redactor.redact_headers(req_headers) if (self.redactor and req_headers) else req_headers
        )
        safe_req_json = self._redact_if_enabled(req_json)
        safe_resp_headers = (
            self.redactor.redact_headers(self.last_response["headers"]) if self.redactor else self.last_response["headers"]
        )
        safe_resp_json = self._redact_if_enabled(self.last_response["body"])

        self.recorder.record(
            step=step,
            method=method.upper(),
            url=safe_url,
            status=self.last_response["status"],
            req_headers=safe_req_headers,
            req_json=safe_req_json,
            resp_headers=safe_resp_headers,
            resp_json=safe_resp_json,
        )



def make_api_executor(*, pw_api, rq_session, settings, recorder) -> ApiExecutor:
    """Factory for DI/tests."""
    return ApiExecutor(pw_api=pw_api, rq_session=rq_session, settings=settings, recorder=recorder)


# from __future__ import annotations
# import json
# import sys
# import os
# from typing import Any, Dict, Tuple, Optional

# from .router import select_mode, ApiClientMode, mock_call

# # type hints are optional to keep deps light
# try:
#     from playwright.sync_api import APIRequestContext as PWContext  # noqa: F401
# except Exception:
#     PWContext = object  # fallback so type hints don't explode

# class ConsoleColors:
#     def __init__(self):
#         # Auto-detect color support
#         self.use_colors = (
#             hasattr(sys.stdout, 'isatty') and sys.stdout.isatty() and
#             os.getenv('TERM') != 'dumb' and
#             os.getenv('NO_COLOR') is None
#         )
    
#     def green(self, text): 
#         return f"\033[92m{text}\033[0m" if self.use_colors else text
    
#     def red(self, text): 
#         return f"\033[91m{text}\033[0m" if self.use_colors else text
    
#     def yellow(self, text): 
#         return f"\033[93m{text}\033[0m" if self.use_colors else text
    
#     def blue(self, text): 
#         return f"\033[94m{text}\033[0m" if self.use_colors else text
    
#     def cyan(self, text): 
#         return f"\033[96m{text}\033[0m" if self.use_colors else text
    
#     def magenta(self, text): 
#         return f"\033[95m{text}\033[0m" if self.use_colors else text
    
#     def bold(self, text): 
#         return f"\033[1m{text}\033[0m" if self.use_colors else text
    
#     def dim(self, text): 
#         return f"\033[2m{text}\033[0m" if self.use_colors else text

# class ApiExecutor:
#     """
#     Callable executor that routes requests to Playwright, requests, or mocks,
#     and records each call via ApiRecorder.
#     """
#     def __init__(self, *, pw_api, rq_session, settings, recorder):
#         self.pw_api = pw_api          
#         self.rq = rq_session          
#         self.settings = settings
#         self.recorder = recorder
#         self.debug = getattr(settings, 'debug_api', False) or os.getenv('DEBUG_API', '').lower() == 'true'
#         self.colors = ConsoleColors()
        
#         # Store last response for failure reporting
#         self.last_response = None
        
#         # Control recording for retry scenarios
#         self.skip_recording = False

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
        
#         full_url = f"{self.settings.api_base_url}{path}"

#         # Always log request (colored) unless explicitly disabled
#         if not self.skip_recording:
#             self._log_request(step, method, full_url, req_headers, req_json, mode)

#         # ... existing API call logic ...
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
#                 try:
#                     import requests
#                 except Exception as e:
#                     raise RuntimeError("requests mode selected but 'requests' is not installed") from e
#                 raise RuntimeError("requests mode selected but no requests.Session provided")
#             r = self.rq.request(
#                 method=method.upper(),
#                 url=full_url,
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

#         # Always store for potential failure reporting
#         self.last_response = {
#             "status": status,
#             "headers": resp_headers,
#             "body": data,
#             "url": full_url,
#             "mode": mode
#         }

#         # Log response if debugging and not skipping
#         if self.debug and not self.skip_recording:
#             self._log_response(status, data, mode, full_url)

#         # Record to Allure + trace only if not skipping
#         if not self.skip_recording:
#             self.recorder.record(
#                 step=step,
#                 method=method.upper(),
#                 url=full_url,
#                 status=status,
#                 req_headers=req_headers,
#                 req_json=req_json,
#                 resp_headers=resp_headers,
#                 resp_json=data,
#             )
#         return status, data

#     def _log_request(self, step, method, url, headers, body, mode):
#         """Enhancement #2 & #3: Always log request with colors"""
#         print(f"\n{self.colors.cyan('🚀 API REQUEST')} {self.colors.dim(f'[{mode.upper()}]')}")
#         print(f"   {self.colors.bold('Step:')} {step}")
#         print(f"   {self.colors.bold('Method:')} {self.colors.yellow(method.upper())}")
#         print(f"   {self.colors.bold('URL:')} {self.colors.blue(url)}")
        
#         if headers:
#             print(f"   {self.colors.bold('Headers:')}")
#             headers_str = json.dumps(headers, indent=6)
#             print(f"{self.colors.dim(headers_str)}")
        
#         if body:
#             print(f"   {self.colors.bold('Body:')}")
#             body_str = json.dumps(body, indent=6)
#             print(f"{self.colors.green(body_str)}")

#     def _log_response(self, status, data, mode, url):
#         """Enhancement #3: Log response when DEBUG_API=true"""
#         status_color = self.colors.green if status < 400 else self.colors.red
#         print(f"\n{self.colors.magenta('📥 API RESPONSE')} {self.colors.dim(f'[{mode.upper()}]')}")
#         print(f"   {self.colors.bold('URL:')} {self.colors.blue(url)}")
#         print(f"   {self.colors.bold('Status:')} {status_color(str(status))}")
        
#         if data:
#             print(f"   {self.colors.bold('Body:')}")
#             data_str = json.dumps(data, indent=6)
#             print(f"{status_color(data_str)}")
        
#         print(f"{self.colors.dim('=' * 60)}")

#     def log_last_response_on_failure(self):
#         """Enhancement #2: Call this on test failure to log response"""
#         if not self.last_response:
#             return
            
#         resp = self.last_response
#         status_color = self.colors.red  # Always red for failures
        
#         print(f"\n{self.colors.red('💥 TEST FAILURE - LAST API RESPONSE 💥 ')}")
#         print(f"   {self.colors.bold('URL:')} {self.colors.blue(resp['url'])}")
#         print(f"   {self.colors.bold('Status:')} {status_color(str(resp['status']))}")
#         print(f"   {self.colors.bold('Mode:')} {self.colors.dim(resp['mode'].upper())}")
        
#         if resp['body']:
#             print(f"   {self.colors.bold('Response Body:')}")
#             body_str = json.dumps(resp['body'], indent=6)
#             print(f"{status_color(body_str)}")
        
#         print(f"{self.colors.red('=' * 60)}")


# def make_api_executor(*, pw_api, rq_session, settings, recorder) -> ApiExecutor:
#     """Factory for the executor (nice for tests and DI)."""
#     return ApiExecutor(pw_api=pw_api, rq_session=rq_session, settings=settings, recorder=recorder)