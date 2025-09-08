#  utils/api/api_reporting.py

from __future__ import annotations
from typing import Any, Dict, Optional
import base64, os, html, json
from string import Template

try:
    import allure
except Exception:
    allure = None

_HTML_TPL = Template("""\
<html><head><meta charset="utf-8">
<style>
  body{font-family:-apple-system,Segoe UI,Roboto,system-ui,sans-serif;background:#0b0f14;color:#e6e6e6;margin:0}
  .card{margin:0;padding:24px}
  h1{font-size:16px;margin:0 0 8px;color:#cbd5e1}
  pre{background:#0f1622;border:1px solid #24324a;border-radius:10px;padding:12px;margin:0;white-space:pre-wrap}
</style></head>
<body><div class="card">
  <h1>$title</h1>
  <pre>$payload</pre>
</div></body></html>
""")

def _safe_json_text(obj: Any) -> str:
    """Best-effort pretty JSON (falls back to repr for non-serializable)."""
    try:
        return json.dumps(obj or {}, indent=2, ensure_ascii=False)
    except TypeError:
        return json.dumps({"_repr": repr(obj)}, indent=2, ensure_ascii=False)

class ApiRecorder:
    """
    Capture a single API call into (a) your trace store via `add_trace`, and
    (b) Allure attachments (JSON/PNG) based on  `make_png` or `ALLURE_API_ATTACH` : json | png | both | none.

    - Lazily creates a Playwright BrowserContext to render JSON → PNG when enabled.
    - Gracefully no-ops PNG generation if no browser is available.
    - Call `close()` to dispose of the context at the end of the session.
    """

    def __init__(self, add_trace, browser, make_png: bool = True):
        self._add_trace = add_trace
        self._browser = browser
        self._ctx = None

        # Attachment mode for Allure (default: json)
        self._attach_mode = (os.getenv("ALLURE_API_ATTACH", "json") or "json").lower()
        if self._attach_mode not in {"json", "png", "both", "none"}:
            self._attach_mode = "json"

        self._make_png = bool(make_png or self._attach_mode in {"png", "both"})

    def _ensure_ctx(self):
        if self._ctx is None and self._make_png:
            # If no browser (API-only runs), skip PNG rendering gracefully
            if not self._browser:
                self._make_png = False
                return
            try:
                self._ctx = self._browser.new_context(viewport={"width": 1000, "height": 10})
            except Exception:
                # Browser may be closed or unavailable in some teardown windows
                self._make_png = False
                self._ctx = None

    def _json_to_png(self, payload: Dict[str, Any], title: str) -> Optional[bytes]:
        if not self._make_png:
            return None
        self._ensure_ctx()
        if self._ctx is None:
            return None
        page = self._ctx.new_page()
        try:
            payload_str = _safe_json_text(payload)
            html_doc = _HTML_TPL.substitute(title=title, payload=html.escape(payload_str))
            page.set_content(html_doc)  # waits for 'load' by default
            return page.screenshot(full_page=True)
        except Exception:
            # Don't fail the test for a reporting glitch
            return None
        finally:
            try:
                page.close()
            except Exception:
                pass

    def record(
        self,
        *,
        step: str,
        method: str,
        url: str,
        status: Optional[int],
        req_headers: Optional[Dict[str, Any]] = None,
        req_json: Optional[Dict[str, Any]] = None,
        resp_headers: Optional[Dict[str, Any]] = None,
        resp_json: Optional[Dict[str, Any]] = None,
    ) -> None:
        # Enhancement #1: Include URL context in attachments
        
        # Create enhanced request context with URL
        req_context = {
            "method": method.upper(),
            "url": url,
            "headers": req_headers or {},
            "body": req_json or {}
        }
        
        # Create enhanced response context with URL  
        resp_context = {
            "url": url,
            "status": status,
            "headers": resp_headers or {},
            "body": resp_json or {}
        }

        # Generate PNGs only if enabled (now with URL context)
        req_png_b = self._json_to_png(req_context, f"Request: {method.upper()} {url}") if self._make_png else None
        resp_png_b = self._json_to_png(resp_context, f"Response: {status} {url}") if self._make_png else None

        # 1) Feed your unified trace (strings for PNGs; headers/json forwarded as dicts)
        self._add_trace(
            step=step,
            method=method,
            url=url,
            status=status,
            req_json=req_json,
            resp_json=resp_json,
            req_png_b64=(base64.b64encode(req_png_b).decode("ascii") if req_png_b else None),
            resp_png_b64=(base64.b64encode(resp_png_b).decode("ascii") if resp_png_b else None),
        )

        # 2) Enhanced Allure attachments with URL context
        if allure and self._attach_mode != "none":
            if self._attach_mode in {"json", "both"}:
                # Enhancement #1: Attach request context (includes URL)
                if req_json is not None or req_headers:
                    allure.attach(
                        _safe_json_text(req_context), 
                        f"{step} - request.json", 
                        allure.attachment_type.JSON
                    )
                
                # Enhancement #1: Attach response context (includes URL)
                if resp_json is not None or status:
                    allure.attach(
                        _safe_json_text(resp_context), 
                        f"{step} - response.json", 
                        allure.attachment_type.JSON
                    )

            if self._attach_mode in {"png", "both"}:
                # Only attach if we actually rendered them
                if req_png_b:
                    allure.attach(req_png_b, f"{step} - request.png", allure.attachment_type.PNG)
                if resp_png_b:
                    allure.attach(resp_png_b, f"{step} - response.png", allure.attachment_type.PNG)

    def close(self):
        if self._ctx:
            try:
                self._ctx.close()
            except Exception:
                pass
            self._ctx = None
