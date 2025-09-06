import pathlib
import sys
import os, inspect
from pathlib import Path
import requests
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
import json, base64
from pathlib import Path
from typing import Generator, Dict, Any, Optional, Callable, List, Set
import pytest
from playwright.sync_api import (Playwright, BrowserType, Browser, BrowserContext, Page, APIRequestContext)

# Appium imports can be optional if not always installed
try:
    from appium import webdriver as appium_driver
    from appium.options.android import UiAutomator2Options
    from appium.options.ios import XCUITestOptions
except Exception:
    appium_driver = None
    UiAutomator2Options = None
    XCUITestOptions = None

from src.config.settings import Settings
from src.utils.logger import get_logger
from src.utils.api.api_reporting import ApiRecorder
from src.api.execution.executor import make_api_executor
logger = get_logger(__name__)

ROOT = pathlib.Path(__file__).parent.resolve()
SRC = ROOT / "src"
STEPS_DIR = ROOT / "step_definitions"

# Only add ROOT to sys.path - forces explicit src.utils imports
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

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
    parser.addoption("--api-worker-html", action="store_true", default=False, help="Also write per-worker HTML under reports/workers/")
    parser.addoption("--api-clean-workers", action="store_true", default=False, help="Delete reports/workers/* after combining")

# --- Settings / environment ---
@pytest.fixture(scope="session")
def settings(request) -> Settings:
    """Load settings from .env files based on --env option."""
    env = request.config.getoption("--env")
    os.environ["TEST_ENV"] = env
    return Settings(environment=env)

# -------------------------
# Browser / Context / Page
# -------------------------

@pytest.fixture(scope="session")
def browser(browser_type: BrowserType, request: pytest.FixtureRequest) -> Generator[Browser, None, None]:
    headed = bool(request.config.getoption("--headed"))
    slowmo_opt = request.config.getoption("--slowmo")
    slowmo = int(slowmo_opt) if slowmo_opt else 0

    launch_kwargs: Dict[str, Any] = {
        "headless": not headed,
        "slow_mo": slowmo,
    }
    print(f"[browser] Using Playwright {browser_type.name} (headless={not headed}, slow_mo={slowmo}ms)")
    b = browser_type.launch(**launch_kwargs)
    try:
        yield b
    finally:
        b.close()

@pytest.fixture
def context(browser: Browser, browser_context_args: Dict[str, Any]) -> Generator[BrowserContext, None, None]:
    """
    Default: function-scoped for test isolation and parallel safety.
    One fresh context per test, but we reuse the same Browser (fast).
    """
    ctx = browser.new_context(**browser_context_args)
    try:
        yield ctx
    finally:
        ctx.close()

@pytest.fixture(scope="session")
def shared_context(browser: Browser, browser_context_args: Dict[str, Any]) -> Generator[BrowserContext, None, None]:
    """
    Optional: session-scoped context for speed or state persistence across tests in the SAME worker.
    Use with care when running in parallel; prefer isolated 'context' unless you truly need persistence.
    """
    ctx = browser.new_context(**browser_context_args)
    try:
        yield ctx
    finally:
        ctx.close()

@pytest.fixture
def page(context: BrowserContext) -> Generator[Page, None, None]:
    p = context.new_page()
    try:
        yield p
    finally:
        p.close()

@pytest.fixture
def shared_page(shared_context: BrowserContext) -> Generator[Page, None, None]:
    """
    Page tied to the shared_context; cookies/localStorage persist across tests in a worker.
    Still one page per test to avoid tab interference.
    """
    p = shared_context.new_page()
    try:
        yield p
    finally:
        p.close()

# -------------------------
# Token helpers
# -------------------------

def _bearer_from_local_storage(storage_state: Dict[str, Any], token_keys: Optional[Set[str]] = None) -> Optional[str]:
    token_keys = token_keys or {"access_token", "id_token", "jwt", "authToken"}
    for origin in storage_state.get("origins", []):
        for item in origin.get("localStorage", []):
            if item.get("name") in token_keys:
                return item.get("value")
    return None

def _bearer_from_page_storage(page: Page, token_keys: Optional[Set[str]] = None) -> Optional[str]:
    """
    Try sessionStorage first (common for SPAs), then fallback to localStorage.
    Requires the page to be on the correct origin (post-login).
    """
    token_keys = token_keys or {"access_token", "id_token", "jwt", "authToken"}
    for key in token_keys:
        token = page.evaluate(f"sessionStorage.getItem('{key}')")
        if token:
            return token
    for key in token_keys:
        token = page.evaluate(f"localStorage.getItem('{key}')")
        if token:
            return token
    return None

def _merge_dict(a: Dict[str, str], b: Optional[Dict[str, str]]) -> Dict[str, str]:
    return {**a, **(b or {})}

# -------------------------
# One factory to rule them all
# -------------------------

@pytest.fixture
def api_client_factory(
    playwright: Playwright,
    context: BrowserContext,      # default source for shared state (function-scoped)
    settings,                      # settings fixture (api_base_url, timeout, etc.)
) -> Generator[Callable[..., APIRequestContext], None, None]:
    """
    Create API clients on demand.

    Usage:
      # Pure API:
      api = api_client_factory(shared=False)

      # Share current UI state (cookies + optional Authorization from storage):
      api = api_client_factory(shared=True)                    # uses default 'context'
      api = api_client_factory(shared=True, source_context=shared_context)  # use shared_context

      # If token lives in sessionStorage, pass a post-login page:
      api = api_client_factory(shared=True, from_page=page)

      # Per-client overrides:
      api = api_client_factory(shared=True,
                               extra_headers={"X-Env": "dev"},
                               base_url="https://alt-api.example.com",
                               timeout_ms=30_000)
    """
    created: List[APIRequestContext] = []

    def factory(
        *,
        shared: bool = False,
        source_context: Optional[BrowserContext] = None,
        from_page: Optional[Page] = None,
        base_url: Optional[str] = None,
        timeout_ms: Optional[int] = None,
        extra_headers: Optional[Dict[str, str]] = None,
        token_keys: Optional[Set[str]] = None,
        ignore_https_errors: bool = True,
    ) -> APIRequestContext:
        base = base_url or settings.api_base_url
        to = timeout_ms if timeout_ms is not None else settings.timeout * 1000

        # Keep default headers minimal. Do NOT set Content-Type globally.
        headers: Dict[str, str] = {"Accept": "application/json"}

        storage_state: Optional[Dict[str, Any]] = None
        if shared:
            src_ctx = source_context or context   # default: function-scoped context
            storage_state = src_ctx.storage_state()  # cookies + localStorage (NOT sessionStorage)

            # Try to add Authorization if we can discover a token.
            token = None
            if from_page is not None:
                token = _bearer_from_page_storage(from_page, token_keys)
            if not token:
                token = _bearer_from_local_storage(storage_state, token_keys)
            if token:
                headers["Authorization"] = f"Bearer {token}"

        api_ctx = playwright.request.new_context(
            base_url=base,
            storage_state=storage_state,                 # shares cookies if domains align
            extra_http_headers=_merge_dict(headers, extra_headers),
            ignore_https_errors=ignore_https_errors,
            timeout=to,
        )
        created.append(api_ctx)
        return api_ctx

    try:
        yield factory
    finally:
        for c in created:
            c.dispose()

# -------------------------
# Convenience fixtures
# -------------------------

@pytest.fixture
def api(api_client_factory) -> APIRequestContext:
    """
    Pure API client (no browser state).
    """
    return api_client_factory(shared=False)

@pytest.fixture
def api_shared(api_client_factory) -> Callable[..., APIRequestContext]:
    """
    Returns a callable so the test can create a shared-state API client at the right moment
    (e.g., AFTER UI login). You can pass 'from_page=page' to read sessionStorage tokens.
    """
    return lambda **kwargs: api_client_factory(shared=True, **kwargs)


@pytest.fixture
def rq(settings):
    """ If you also want requests for API and not playwright for API Testing"""
    s = requests.Session()
    s.headers.update({"Accept": "application/json"})
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
            decoded = base64.b64decode(b64).decode("utf-8")
        except Exception:
            return ""
        try:
            return json.dumps(json.loads(decoded), indent=2, ensure_ascii=False)
        except Exception:
            return decoded


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
def api_trace_store(request):
    data: list[ApiTrace] = []
    yield data

    worker = os.getenv("PYTEST_XDIST_WORKER") or "main"
    workers_dir = Path("reports") / "workers"
    workers_dir.mkdir(parents=True, exist_ok=True)

    # Always write per-worker JSON (intermediate for aggregator)
    (workers_dir / f"{worker}.json").write_text(
        json.dumps([asdict(t) for t in data], indent=2), encoding="utf-8"
    )

    # Optional: per-worker HTML for debugging
    if request.config.getoption("--api-worker-html"):
        html = _render_html(data)  # list[ApiTrace]
        (workers_dir / f"{worker}.html").write_text(html, encoding="utf-8")

@pytest.fixture(autouse=True)
def debug_fixtures(api_trace_add, api_recorder):
    print(f"[DEBUG] In debug_fixtures:")
    print(f"  api_trace_add: {type(api_trace_add)} = {api_trace_add}")
    print(f"  api_recorder: {type(api_recorder)}")
    print(f"  api_recorder._add_trace: {api_recorder._add_trace}")
    yield


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
    print(f"\n[DEBUG] Creating api_recorder:")
    print(f"  api_trace_add: {api_trace_add}")
    print(f"  api_trace_add type: {type(api_trace_add)}")
    print(f"  browser: {browser}")
    
    if api_trace_add is None:
        raise ValueError("CRITICAL: api_trace_add is None - fixture dependency failed!")
    
    DEBUG = os.getenv("API_REC_DEBUG", "").lower() in ("1", "true", "yes")
    if DEBUG:
        print("[dbg] ApiRecorder module:", ApiRecorder.__module__)
        print("[dbg] ApiRecorder file:", inspect.getsourcefile(ApiRecorder))
        print("[dbg] has record/close:", hasattr(ApiRecorder, "record"), hasattr(ApiRecorder, "close"))
    
    r = ApiRecorder(api_trace_add, browser, make_png=True)
    print(f"[DEBUG] Created ApiRecorder, _add_trace: {r._add_trace}")
    
    try:
        yield r
    finally:
        r.close()

@pytest.fixture
def api_executor(api, rq, settings, api_recorder):
    """
    Core API execution engine that can route between different clients.
    Uses the 'api' fixture (pure API client) as the default Playwright client.
    """
    return make_api_executor(pw_api=api, rq_session=rq, settings=settings, recorder=api_recorder)

# --- Post-session aggregator: merge per-worker API traces into one JSON/HTML ---
# --- aggregator helpers ---
def _is_worker(config) -> bool:
    return hasattr(config, "workerinput")  # True on xdist workers, False on controller/single run

def _gather_worker_reports(root: Path) -> list[dict]:
    workers = root / "workers"
    files = sorted(workers.glob("*.json"))
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

def _rehydrate(obj: dict) -> ApiTrace:
    return ApiTrace(
        feature=obj.get("feature", "Unknown Feature"),
        scenario=obj.get("scenario", "Unknown Scenario"),
        step=obj.get("step", ""),
        method=obj.get("method", ""),
        url=obj.get("url", ""),
        status=obj.get("status"),
        request_headers_b64=obj.get("request_headers_b64"),
        request_json=obj.get("request_json"),
        response_headers_b64=obj.get("response_headers_b64"),
        response_json=obj.get("response_json"),
        request_png_b64=obj.get("request_png_b64"),
        response_png_b64=obj.get("response_png_b64"),
        at=obj.get("at", ""),
    )

# --- run once on controller to write the single combined report ---
def pytest_sessionfinish(session, exitstatus):
    config = session.config
    if _is_worker(config):
        return  # workers only write their own JSON

    reports_dir = Path("reports")
    merged = _gather_worker_reports(reports_dir)
    if not merged:
        return

    merged = _dedupe(merged)
    merged.sort(key=lambda x: (x.get("feature", ""), x.get("scenario", ""), x.get("at", "")))

    # Combined JSON
    (reports_dir / "api-report.json").write_text(json.dumps(merged, indent=2), encoding="utf-8")

    # Combined HTML (renderer expects ApiTrace objects)
    traces = [_rehydrate(x) for x in merged]
    html = _render_html(traces)
    (reports_dir / "api-report.html").write_text(html, encoding="utf-8")
    print("[api-report] wrote reports/api-report.json and reports/api-report.html")

    # cleanup of per-worker intermediates
    if config.getoption("--api-clean-workers"):
        workers_dir = reports_dir / "workers"
        for fp in workers_dir.glob("*"):
            try:
                fp.unlink()
            except Exception:
                pass
