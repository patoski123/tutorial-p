import pathlib
import sys
import pkgutil
import importlib
import importlib.util
import shutil
import os, inspect
from typing import Optional, Dict, Any
from pathlib import Path
import pytest
import requests
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
import json, base64
from pathlib import Path
from typing import Generator, Dict, Any
import pytest
from playwright.sync_api import (
    Playwright,
    Browser,
    BrowserType,
    BrowserContext,
    Page,
    APIRequestContext,
)
from pytest import FixtureRequest
# Appium imports can be optional if not always installed
try:
    from appium import webdriver as appium_driver
    from appium.options.android import UiAutomator2Options
    from appium.options.ios import XCUITestOptions
except Exception:
    appium_driver = None
    UiAutomator2Options = None
    XCUITestOptions = None

from config.settings import Settings
from utils.logger import get_logger
from utils.api.api_reporting import ApiRecorder
from src.api.execution.executor import make_api_executor
from src.api.clients.auth_api import AuthAPI
logger = get_logger(__name__)

ROOT = pathlib.Path(__file__).parent.resolve()
SRC = ROOT / "src"
STEPS_DIR = ROOT / "step_definitions"

# ensure root and src on sys.path once
for p in (ROOT, SRC):
    p_str = str(p)
    if p_str not in sys.path:
        sys.path.insert(0, p_str)

def _discover_step_modules():
    mods = []
    if STEPS_DIR.is_dir():
        for py in STEPS_DIR.rglob("*_steps.py"):
            mod = ".".join(py.relative_to(ROOT).with_suffix("").parts)  # e.g. step_definitions.api.auth_api_steps
            mods.append(mod)
    # optional: print for debug
    for m in sorted(set(mods)):
        print(f"[bdd] registering step plugin: {m}")
    return sorted(set(mods))

pytest_plugins = _discover_step_modules()

# --- CLI options ---
def pytest_addoption(parser):
    parser.addoption("--env", action="store", default="dev", help="Environment to run tests")
    parser.addoption("--browser-path", action="store", default=None, help="Absolute path to a custom browser executable")
    parser.addoption("--mobile-platform", action="store", default="android", choices=["android", "ios"], help="Mobile platform")
    parser.addoption("--user-role", action="store", default="user", help="Test user role (e.g. user, admin)")

# --- Settings / environment ---
@pytest.fixture(scope="session")
def settings(request) -> Settings:
    """Load settings from .env files based on --env option."""
    env = request.config.getoption("--env")
    os.environ["TEST_ENV"] = env
    return Settings(environment=env)

# --- Playwright browser/context/page ---
# --- centralised Custom launcher that supports --browser-path but DOES NOT conflict with plugin fixtures ---
@pytest.fixture(scope="session")
def browser_context_args(settings) -> Dict[str, Any]:
    """Browser context configuration."""
    args: Dict[str, Any] = {
        "viewport": {"width": 1920, "height": 1080},
        "ignore_https_errors": True,
        "base_url": settings.base_url,
    }
    if getattr(settings, "record_video", False):
        args.update({
            "record_video_dir": "reports/videos/",
            "record_video_size": {"width": 1920, "height": 1080},
        })
    return args

@pytest.fixture(scope="session")
 # BrowserType from pytest-playwright 
# 2) Custom launcher that won’t collide with plugin fixtures
def custom_browser(browser_type: BrowserType, request: FixtureRequest) -> Generator[Browser, None, None]:
    headed = bool(request.config.getoption("--headed"))
    slowmo_opt = request.config.getoption("--slowmo")
    slowmo = int(slowmo_opt) if slowmo_opt else 0
    channel = request.config.getoption("--browser-channel")
    custom_executable = request.config.getoption("--browser-path")

    if channel and custom_executable:
        raise RuntimeError("Use either --browser-channel OR --browser-path, not both.")

    # Chromium-only guard
    if (channel or custom_executable) and browser_type.name != "chromium":
        which = "--browser-path" if custom_executable else "--browser-channel"
        raise RuntimeError(f"{which} is only supported with --browser=chromium.")

    launch_kwargs: Dict[str, Any] = {
        "headless": not headed,
        "slow_mo": slowmo,
    }

    # Pick one: path > channel > bundled
    if custom_executable:
        if not os.path.exists(custom_executable):
            raise FileNotFoundError(f"Custom browser executable not found: {custom_executable}")
        launch_kwargs["executable_path"] = custom_executable
        print(f"[browser] Using custom executable: {custom_executable}")
    elif channel:
        launch_kwargs["channel"] = channel
        print(f"[browser] Using channel: {channel}")

    browser = browser_type.launch(**launch_kwargs)
    try:
        yield browser
    finally:
        browser.close()

@pytest.fixture(scope="session")
def ui_context(custom_browser: Browser,browser_context_args: Dict[str, Any],) -> Generator[BrowserContext, None, None]:
    ctx = custom_browser.new_context(**browser_context_args)
    try:
        yield ctx
    finally:
        ctx.close()

@pytest.fixture
def ui_page(ui_context: BrowserContext) -> Generator[Page, None, None]:
    page = ui_context.new_page()
    try:
        yield page
    finally:
        page.close()

@pytest.fixture
def ui_api_client(playwright: Playwright, ui_context: BrowserContext, settings) -> Generator[APIRequestContext, None, None]:
    """API client that shares auth with the UI context (for E2E)."""
    storage = ui_context.storage_state()
    ctx = playwright.request.new_context(
        base_url=settings.api_base_url,
        storage_state=storage,
        extra_http_headers={"Content-Type": "application/json", "Accept": "application/json"},
        ignore_https_errors=True,
        timeout=settings.timeout * 1000,
    )
    try:
        yield ctx
    finally:
        ctx.dispose()

@pytest.fixture
def pw_api(playwright: Playwright, settings) -> Generator[APIRequestContext, None, None]:
    """Standalone Playwright API client (no browser required)."""
    ctx = playwright.request.new_context(
        base_url=settings.api_base_url,
        extra_http_headers={"Content-Type": "application/json", "Accept": "application/json"},
        ignore_https_errors=True,
        timeout=settings.timeout * 1000,
    )
    try:
        yield ctx
    finally:
        ctx.dispose()

# # --- Playwright browser/context/page ---
# def browser(playwright, browser_type, request):
#     headed = request.config.getoption("--headed")
#     slowmo = int(request.config.getoption("--slowmo") or 0)
#     exe = request.config.getoption("--browser-path")

#     launch_kwargs = {"headless": not headed, "slow_mo": slowmo}
#     if exe:
#         launch_kwargs["executable_path"] = exe  # custom Chrome/Chromium

#     b = browser_type.launch(**launch_kwargs)
#     yield b
#     b.close()

# @pytest.fixture(scope="session")
# def browser_context_args(settings):
#     """Only context-supported keys here (no slow_mo)."""
#     args = {
#         "viewport": {"width": 1920, "height": 1080},
#         "ignore_https_errors": True,
#         "base_url": settings.base_url,
#     }
#     # Optional video recording
#     if getattr(settings, "record_video", False):
#         args["record_video_dir"] = "reports/videos/"
#         args["record_video_size"] = {"width": 1920, "height": 1080}
#     return args

# @pytest.fixture(scope="session")
# def browser_context(browser: Browser, browser_context_args) -> BrowserContext:
#     ctx = browser.new_context(**browser_context_args)
#     yield ctx
#     ctx.close()

# @pytest.fixture
# def page(browser_context: BrowserContext):
#     p = browser_context.new_page()
#     yield p
#     p.close()

# @pytest.fixture
# def ui_api_client(playwright: Playwright, browser_context: BrowserContext, settings):
#     """Playwright API client that shares auth/cookies with the UI context (E2E)."""
#     storage = browser_context.storage_state()  # dict
#     api_ctx = playwright.request.new_context(
#         base_url=settings.api_base_url,
#         storage_state=storage,
#         extra_http_headers={"Content-Type": "application/json", "Accept": "application/json"},
#         ignore_https_errors=True,
#         timeout=settings.timeout * 1000
#     )
#     yield api_ctx
#     api_ctx.dispose()

# @pytest.fixture
# def pw_api(playwright: Playwright, settings):
#     """Standalone Playwright API client (no browser required)."""
#     ctx = playwright.request.new_context(
#         base_url=settings.api_base_url,
#         extra_http_headers={"Content-Type": "application/json", "Accept": "application/json"},
#         ignore_https_errors=True,
#         timeout=settings.timeout * 1000,
#     )
#     try:
#         yield ctx
#     finally:
#         ctx.dispose()

@pytest.fixture
def rq(settings):
    """ If you also want requests for API and not playwright for API Testing"""
    s = requests.Session()
    s.headers.update({"Accept": "application/json", "Content-Type": "application/json"})
    s.base_url = settings.api_base_url  # just a hint; build URLs as f"{s.base_url}/path"
    try:
        yield s
    finally:
        s.close()

# --- Useful env fixtures ---
@pytest.fixture(scope="session")
def test_user(settings, request):
    role = request.config.getoption("--user-role")
    return settings.get_test_user(role)

@pytest.fixture(scope="session")
def skip_if_prod(settings):
    if settings.is_production_like():
        pytest.skip("Destructive test skipped in production environment")

# --- Robust failure screenshot hook ---
def _get_available_fixtures(request) -> list:
    """Extract all available fixture names from the request."""
    try:
        if hasattr(request, 'fixturenames'):
            return list(request.fixturenames)
        elif hasattr(request, '_fixturemanager'):
            return list(request._fixturemanager._arg2fixturedefs.keys())
        else:
            return []
    except Exception as e:
        logger.debug(f"Could not retrieve fixture names: {e}")
        return []

def _filter_page_fixtures(available_fixtures: list) -> list:
    """
    Filter fixtures that are likely to be Playwright page objects.
    
    Prioritizes common patterns and returns them in order of preference.
    """
    page_patterns = [
        'ui_page',      # Most common custom pattern
        'page',         # Standard playwright fixture
        'mobile_page',  # Mobile testing
        'browser_page', # Alternative naming
        'test_page',    # Another common pattern
    ]
    
    # First, check for exact matches in order of preference
    candidates = []
    for pattern in page_patterns:
        if pattern in available_fixtures:
            candidates.append(pattern)
    
    # Then add any other fixtures containing 'page'
    for fixture in available_fixtures:
        if 'page' in fixture.lower() and fixture not in candidates:
            candidates.append(fixture)
    
    return candidates

def _attempt_screenshot_from_fixture(request, fixture_name: str) -> Optional[bytes]:
    """
    Attempt to capture screenshot from a specific fixture.
    
    Returns:
        bytes: Screenshot data or None if failed
    """
    try:
        # Get the fixture value
        page_object = request.getfixturevalue(fixture_name)
        
        # Validate it's a Playwright page
        if not _is_playwright_page(page_object):
            return None
        
        # Check page state
        if not _is_page_capturable(page_object):
            return None
        
        # Capture screenshot
        return page_object.screenshot(
            full_page=True,
            type="png",
            animations="disabled"  # Prevent flaky screenshots
        )
        
    except Exception as e:
        logger.debug(f"Screenshot attempt failed for fixture '{fixture_name}': {e}")
        return None

def _is_playwright_page(obj) -> bool:
    """Check if object is a Playwright Page with screenshot capabilities."""
    required_methods = ['screenshot', 'is_closed', 'url', 'title']
    return all(hasattr(obj, method) for method in required_methods)


def _is_page_capturable(page) -> bool:
    """Check if page is in a state where screenshot can be taken."""
    try:
        if page.is_closed():
            logger.debug("Page is closed")
            return False
        
        if not page.context.browser.is_connected():
            logger.debug("Browser is disconnected")
            return False
        
        # Additional check: ensure page has loaded content
        try:
            page.url  # This will throw if page is in invalid state
            return True
        except:
            logger.debug("Page is in invalid state")
            return False
            
    except Exception as e:
        logger.debug(f"Page state check failed: {e}")
        return False

def _try_capture_page_screenshot(request) -> Optional[bytes]:
    """
    Dynamically discover and capture screenshot from any available Playwright page fixture.
    """
    available_fixtures = _get_available_fixtures(request)
    page_candidates = _filter_page_fixtures(available_fixtures)
    
    for fixture_name in page_candidates:
        screenshot_bytes = _attempt_screenshot_from_fixture(request, fixture_name)
        if screenshot_bytes:
            logger.debug(f"Screenshot captured using fixture: {fixture_name}")
            return screenshot_bytes
    
    logger.warning("No valid Playwright page fixture found for screenshot capture")
    return None

# --- Mobile fallback screenshot helper ---
def _try_capture_mobile_screenshot(request) -> Optional[bytes]:
    """Capture screenshot from mobile-specific fixtures."""
    available_fixtures = _get_available_fixtures(request)
    
    # Find mobile fixtures by pattern matching
    mobile_candidates = [
        fixture for fixture in available_fixtures 
        if any(pattern in fixture.lower() for pattern in ['mobile', 'device'])
    ]
    
    for fixture_name in mobile_candidates:
        screenshot_bytes = _attempt_screenshot_from_fixture(request, fixture_name)
        if screenshot_bytes:
            logger.debug(f"Mobile screenshot captured using: {fixture_name}")
            return screenshot_bytes
    
    return None
        

@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()

    if report.when != "call" or not report.failed:
        return

    # UI/Mobile screenshot: UI first, then mobile
    png = _try_capture_page_screenshot(item._request) or _try_capture_mobile_screenshot(item._request)
    if png:
        # pytest-html (if enabled)
        try:
            import pytest_html
            if hasattr(report, "extra"):
                report.extra.append(pytest_html.extras.png(png, mime_type="image/png"))
        except Exception:
            pass
        # Allure
        try:
            import allure
            allure.attach(png, name="failure-screenshot", attachment_type=allure.attachment_type.PNG)
        except Exception:
            pass

    # Re-attach last API JSON (handy if asserts happen after the call)
    try:
        last = getattr(item, "_api_last", None)
        if last:
            import allure
            if last.get("req_json") is not None:
                allure.attach(
                    json.dumps(last["req_json"], indent=2),
                    name="api-last-request.json",
                    attachment_type=allure.attachment_type.JSON,
                )
            if last.get("resp_json") is not None:
                allure.attach(
                    json.dumps(last["resp_json"], indent=2),
                    name="api-last-response.json",
                    attachment_type=allure.attachment_type.JSON,
                )
    except Exception:
        pass

# def pytest_runtest_makereport(item, call):
#     # Execute all other hooks to obtain the report object
#     outcome = yield
#     report = outcome.get_result()

#     # Only care about test phase failures
#     if report.when == "call" and report.failed:
#         screenshot = _try_capture_page_screenshot(item._request)
#         if screenshot:
#             # Attach to pytest-html / allure if present
#             try:
#                 import pytest_html
#                 if hasattr(report, "extra"):
#                     report.extra.append(pytest_html.extras.png(screenshot, mime_type="image/png"))
#             except Exception:
#                 pass
#             try:
#                 import allure
#                 allure.attach(screenshot, name="failure-screenshot", attachment_type=allure.attachment_type.PNG)
#             except Exception:
#                 pass

# --- Optional: BDD lifecycle logging (safe, minimal signatures) ---
def pytest_bdd_before_scenario(request, feature, scenario):
    logger.info(f"Starting scenario: {scenario.name}")

def pytest_bdd_after_scenario(request, feature, scenario):
    logger.info(f"Completed scenario: {scenario.name}")

# --- Appium (optional) ---
@pytest.fixture(scope="session")
def mobile_driver(request, settings):
    """Only set up if Appium and options are installed and wanted."""
    if appium_driver is None:
        pytest.skip("Appium not available in this environment")

    platform = request.config.getoption("--mobile-platform")
    if platform == "android":
        if UiAutomator2Options is None:
            pytest.skip("Android Appium options not available")
        options = UiAutomator2Options()
        options.platform_name = "Android"
        options.automation_name = "UiAutomator2"
        options.device_name = getattr(settings, "android_device_name", "emulator-5554")
        options.app = settings.android_app_path
        options.app_package = settings.android_app_package
        options.app_activity = settings.android_app_activity
    else:
        if XCUITestOptions is None:
            pytest.skip("iOS Appium options not available")
        options = XCUITestOptions()
        options.platform_name = "iOS"
        options.automation_name = "XCUITest"
        options.device_name = settings.ios_device_name
        options.app = settings.ios_app_path
        options.bundle_id = settings.ios_bundle_id

    driver = appium_driver.Remote(settings.appium_server_url, options=options)
    yield driver
    driver.quit()

# --- API Trace logger (HTML/JSON report, optional PDF) ---

@dataclass
class ApiTrace:
    feature: str
    scenario: str
    step: str
    method: str
    url: str
    status: int | None
    request_headers_b64: str | None
    request_json: dict | None
    response_headers_b64: str | None
    response_json: dict | None
    # NEW: embed PNGs (base64)
    request_png_b64: Optional[str] = None
    response_png_b64: Optional[str] = None
    # at: str  # ISO 8601 UTC
    at: str = ""

def _b64_json(d: dict | None) -> str | None:
    if d is None:
        return None
    return base64.b64encode(
        json.dumps(d, indent=2).encode("utf-8")
    ).decode("ascii")

def _b64(d: dict | None) -> str | None:
    if not d:
        return None
    return base64.b64encode(json.dumps(d, indent=2).encode("utf-8")).decode("ascii")

def _render_html(traces: list[ApiTrace]) -> str:
    import base64, json

    def esc(s: str | None) -> str:
        s = s or ""
        return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    def decode_headers(b64: str | None) -> str:
        if not b64:
            return ""
        try:
            raw = base64.b64decode(b64).decode("utf-8")
            return json.dumps(json.loads(raw), indent=2)
        except Exception:
            # fallback to raw text if it wasn't JSON
            return raw

    def json_pre(obj) -> str:
        return esc(json.dumps(obj or {}, indent=2))

    def img_tag(b64: str | None, alt: str) -> str:
        if not b64:
            return ""
        return f'<img class="jsonshot" alt="{esc(alt)}" src="data:image/png;base64,{b64}"/>'

    rows = []
    for i, t in enumerate(traces, 1):
        req_headers_text = decode_headers(t.request_headers_b64)
        resp_headers_text = decode_headers(t.response_headers_b64)

        # Request block: prefer PNG, fallback to JSON text
        if t.request_png_b64:
            req_block = f'''
              <details open><summary>Request JSON</summary>
                <div class="imgwrap">{img_tag(t.request_png_b64, "Request JSON")}</div>
              </details>
            '''
        else:
            req_block = f'''
              <details open><summary>Request JSON</summary>
                <pre>{json_pre(t.request_json)}</pre>
              </details>
            '''

        # Response block: prefer PNG, fallback to JSON text
        if t.response_png_b64:
            resp_block = f'''
              <details open><summary>Response JSON</summary>
                <div class="imgwrap">{img_tag(t.response_png_b64, "Response JSON")}</div>
              </details>
            '''
        else:
            resp_block = f'''
              <details open><summary>Response JSON</summary>
                <pre>{json_pre(t.response_json)}</pre>
              </details>
            '''

        rows.append(f"""
        <section class="card">
          <div class="meta">
            <span class="idx">#{i}</span>
            <span class="feat">{esc(t.feature)}</span>
            <span class="scen">{esc(t.scenario)}</span>
            <span class="ts">{esc(t.at)}</span>
          </div>
          <div class="req">
            <div class="line"><span class="method">{esc(t.method)}</span>
              <code>{esc(t.url)}</code>
              → <span class="status">{t.status if t.status is not None else "-"}</span>
            </div>
            <details><summary>Request headers</summary><pre>{esc(req_headers_text)}</pre></details>
            {req_block}
          </div>
          <div class="resp">
            <details><summary>Response headers</summary><pre>{esc(resp_headers_text)}</pre></details>
            {resp_block}
          </div>
        </section>
        """)

    css = """
    body{font-family:ui-sans-serif,system-ui,-apple-system,Segoe UI,Roboto,Ubuntu,Cantarell,Noto Sans,sans-serif;background:#0b0f14;color:#e6e6e6;margin:0;padding:2rem}
    h1{margin:0 0 1rem;font-size:1.4rem}
    .summary{opacity:.8;margin-bottom:1rem}
    .card{background:#121826;border:1px solid #24324a;border-radius:12px;padding:1rem;margin:0 0 1rem;box-shadow:0 1px 10px rgba(0,0,0,.2)}
    .meta{display:flex;gap:.75rem;flex-wrap:wrap;margin-bottom:.5rem;font-size:.85rem;opacity:.85}
    .idx{background:#24324a;padding:.2rem .5rem;border-radius:8px}
    .feat,.scen,.ts{background:#0f1622;padding:.2rem .5rem;border-radius:8px}
    .line{margin:.25rem 0 .5rem}
    .method{display:inline-block;background:#2a6ad9;padding:.15rem .45rem;border-radius:6px;margin-right:.5rem;font-weight:600}
    .status{display:inline-block;background:#214a2e;padding:.15rem .45rem;border-radius:6px;margin-left:.5rem}
    pre{background:#0f1622;border:1px solid #24324a;border-radius:10px;padding:.75rem;overflow:auto;max-height:320px}
    code{background:#0f1622;border:1px solid #24324a;border-radius:6px;padding:.1rem .3rem}
    details>summary{cursor:pointer;opacity:.9}
    .imgwrap{background:#0f1622;border:1px solid #24324a;border-radius:10px;padding:.5rem;overflow:auto}
    .imgwrap img{display:block;max-width:100%}
    """
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><title>API Report</title>
<meta name="viewport" content="width=device-width,initial-scale=1">
<style>{css}</style></head>
<body>
<h1>API Report</h1>
<div class="summary">Total entries: {len(traces)}</div>
{''.join(rows) if rows else "<p>No API calls captured.</p>"}
</body></html>"""

@pytest.fixture(scope="session")
def api_trace_store():
    """Session-scoped store per worker. Writes per-worker files to avoid clobbering."""
    data: list[ApiTrace] = []
    yield data  # tests run here

    # session teardown → write artifacts (per worker)
    worker = os.getenv("PYTEST_XDIST_WORKER") or "main"   # e.g. gw0, gw1 …
    out = Path("reports")
    out.mkdir(parents=True, exist_ok=True)

    # JSON
    with open(out / f"api-report-{worker}.json", "w", encoding="utf-8") as f:
        json.dump([asdict(t) for t in data], f, indent=2)

    # HTML
    html = _render_html(data)
    (out / f"api-report-{worker}.html").write_text(html, encoding="utf-8")

@pytest.fixture
def api_trace_add(api_trace_store, request):
    feature_name = getattr(getattr(request.node, "parent", None), "name", "") or ""
    scenario_name = getattr(request.node, "name", "") or ""
    def _add(
        *, step: str, method: str, url: str, status: int | None,
        req_headers: dict | None = None, req_json: dict | None = None,
        resp_headers: dict | None = None, resp_json: dict | None = None,
        # NEW:
        req_png_b64: str | None = None, resp_png_b64: str | None = None,
        at: str | None = None,
    ):
        api_trace_store.append(ApiTrace(
            feature=feature_name,
            scenario=scenario_name,
            step=step,
            method=method,
            url=url,
            status=status,
            request_headers_b64=_b64_json(req_headers),
            response_headers_b64=_b64_json(resp_headers),
            request_json=req_json,
            response_json=resp_json,
            request_png_b64=req_png_b64,
            response_png_b64=resp_png_b64,
            at=at or datetime.now(timezone.utc).isoformat(timespec="seconds"),
        ))
    return _add


@pytest.fixture
def api_recorder(api_trace_add, browser):
    DEBUG = os.getenv("API_REC_DEBUG", "").lower() in ("1", "true", "yes")
    # usage: API_REC_DEBUG=1 pytest -m authentication -s
    if DEBUG:
        print("[dbg] ApiRecorder module:", ApiRecorder.__module__)
        print("[dbg] ApiRecorder file:", inspect.getsourcefile(ApiRecorder))
        print("[dbg] has record/close:", hasattr(ApiRecorder, "record"), hasattr(ApiRecorder, "close"))
    r = ApiRecorder(api_trace_add, browser, make_png=True)
    try:
        yield r
    finally:
        r.close()


@pytest.fixture
def api_executor(pw_api, rq, settings, api_recorder):
    return make_api_executor(pw_api=pw_api, rq_session=rq, settings=settings, recorder=api_recorder)

@pytest.fixture
def auth_api(api_executor):
    return AuthAPI(api_executor, base_path="/auth")

# --- Post-session aggregator: merge per-worker API traces into one JSON/HTML ---

def _is_worker(config) -> bool:
    return hasattr(config, "workerinput")

def _gather_worker_reports(root: Path) -> list[dict]:
    files = sorted(root.glob("api-report-*.json"))  # e.g. api-report-gw0.json, api-report-main.json
    merged: list[dict] = []
    for fp in files:
        try:
            data = json.loads(fp.read_text(encoding="utf-8"))
            if isinstance(data, list):
                merged.extend(data)
        except Exception as e:
            print(f"[api-report] skip {fp}: {e}")
    return merged

def _dedupe(items: list[dict]) -> list[dict]:
    seen = set()
    out: list[dict] = []
    for obj in items:
        key = (
            obj.get("feature", ""),
            obj.get("scenario", ""),
            obj.get("step", ""),
            obj.get("method", ""),
            obj.get("url", ""),
            obj.get("status"),
            obj.get("at", ""),
        )
        if key in seen:
            continue
        seen.add(key)
        out.append(obj)
    return out

def pytest_sessionfinish(session, exitstatus):
    """Run once on the controller after all workers finish; create combined report."""
    config = session.config
    if _is_worker(config):
        return  # workers do nothing

    reports_dir = Path("reports")
    merged = _gather_worker_reports(reports_dir)
    if not merged:
        return

    merged = _dedupe(merged)
    merged.sort(key=lambda x: (x.get("feature", ""), x.get("scenario", ""), x.get("at", "")))

    # Write combined JSON
    (reports_dir / "api-report.json").write_text(json.dumps(merged, indent=2), encoding="utf-8")

    # Write combined HTML using your existing renderer
    try:
        html = _render_html(merged)  # uses the same function you already have
        (reports_dir / "api-report.html").write_text(html, encoding="utf-8")
        print("[api-report] wrote reports/api-report.json and reports/api-report.html")
    except Exception as e:
        print(f"[api-report] couldn't render HTML: {e}")
