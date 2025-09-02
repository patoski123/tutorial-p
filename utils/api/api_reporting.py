# utils/api/api_reporting.py
from __future__ import annotations
from typing import Any, Dict, Optional
import base64 
from string import Template
import html, json

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

def _b64_bytes(b: Optional[bytes]) -> Optional[str]:
    return base64.b64encode(b).decode("ascii") if b else None

class ApiRecorder:
    """Logs API calls to your HTML/JSON trace and Allure."""

    def __init__(self, add_trace, browser, make_png: bool = True):
        self._add_trace = add_trace
        self._browser = browser
        self._ctx = None
        self._make_png = make_png

    def _ensure_ctx(self):
        if self._ctx is None and self._make_png:
            self._ctx = self._browser.new_context(viewport={"width": 1000, "height": 10})

    def _json_to_png(self, payload: Dict[str, Any], title: str) -> Optional[bytes]:
        if not self._make_png:
            return None
        self._ensure_ctx()
        page = self._ctx.new_page()
        payload_str = json.dumps(payload or {}, indent=2, ensure_ascii=False)
        html_doc = _HTML_TPL.substitute(title=title, payload=html.escape(payload_str))
        page.set_content(html_doc)
        png = page.screenshot(full_page=True)
        page.close()
        return png

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
        # Render PNGs once so both Allure and the unified report can use them
        # req_png = self._json_to_png(req_json or {}, "Request JSON") if self._make_png else None
        # resp_png = self._json_to_png(resp_json or {}, "Response JSON") if self._make_png else None

        req_png_b = self._json_to_png(req_json or {}, "Request JSON") if self._make_png else None
        resp_png_b = self._json_to_png(resp_json or {}, "Response JSON") if self._make_png else None


        # 1) Feed your standalone trace (NOW includes PNGs)
        self._add_trace(
            step=step,
            method=method,
            url=url,
            status=status,
            req_headers=req_headers,
            req_json=req_json,
            resp_headers=resp_headers,
            resp_json=resp_json,
            req_png_b64=(base64.b64encode(req_png_b).decode("ascii") if req_png_b else None),
            resp_png_b64=(base64.b64encode(resp_png_b).decode("ascii") if resp_png_b else None),
        
            # if you want screenshot in cucumber report
            # req_png_b64=_b64_bytes(req_png),
            # resp_png_b64=_b64_bytes(resp_png),
        )

        # 2) Allure attachments
        if allure:
            if req_json is not None:
                allure.attach(json.dumps(req_json, indent=2), f"{step} - request.json", allure.attachment_type.JSON)
            if resp_json is not None:
                allure.attach(json.dumps(resp_json, indent=2), f"{step} - response.json", allure.attachment_type.JSON)
            # if you want screenshot in the cucumber report
            # if req_png:
            #     allure.attach(req_png, f"{step} - request.png", allure.attachment_type.PNG)
            # if resp_png:
            #     allure.attach(resp_png, f"{step} - response.png", allure.attachment_type.PNG)

    def close(self):
        if self._ctx:
            self._ctx.close()
            self._ctx = None
