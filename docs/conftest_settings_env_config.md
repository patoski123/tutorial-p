# conftest, settings, and environment config

This document explains how environment selection and runtime configuration work in the test framework. It covers:

- `conftest.py` (pytest fixtures & CLI)
- `config/settings.py` (`Settings` loader)
- `.env` (local & CI overrides)
- `environment.json` (per-environment values)

---

## Overview

At startup, pytest reads **`conftest.py`**, which:

1. Parses CLI flags (e.g. `--env=dev`, `--headed`).
2. Instantiates **`Settings(environment=ENV)`**.
3. Builds core fixtures:
   - Playwright **browser / context / page**.
   - **API client factory** (`api_client_factory`) + conveniences (`api`, `api_shared`).
   - **ApiRecorder** and **ApiExecutor** for API call routing & reporting.
4. Handles **parallel runs** (xdist): per-worker JSON traces → combined HTML/JSON report.

`Settings` merges values from **`environment.json`** (per environment) and **environment variables** (including `.env`). Jenkins passes `--env` and writes a minimal `.env` so the test run is reproducible.

---

## `conftest.py` responsibilities

### CLI flags (examples)

| Flag | Purpose |
|---|---|
| `--env=dev` | Pick environment; forwarded into `Settings(environment=...)` |
| `--headed` | Run browser headed (UI/E2E) |
| `--browser-path=/path/to/chrome` | Use a custom Chromium/Chrome |
| `--mobile-platform=android|ios` | Enable Appium path (if installed) |

### Core fixtures (what you’ll use most)

- `settings` → a singleton `Settings` object (see below).
- `browser` / `context` / `page`  
  - `context` is **function-scoped** by default for clean isolation.  
  - `shared_context` is **session-scoped** (optional) when you need persistence within a worker.
- `api_client_factory(shared=False|True, …)`  
  - Creates Playwright API clients on demand.  
  - `shared=True` captures the current browser `storage_state()` and (optionally) an `Authorization` token from `sessionStorage/localStorage` after UI login (E2E flow).
- `api` / `api_shared`  
  - Convenience wrappers over the factory for pure API and UI→API cases.
- `api_recorder` / `api_executor`  
  - **Executor** routes the HTTP call (Playwright API or `requests`) and records it via the **recorder**.
  - **Recorder** adds one entry per call to the trace and attaches JSON/PNG to Allure per `ALLURE_API_ATTACH`.

### Reporting (single & parallel runs)

- Each worker writes **per-worker JSON**: `reports/workers/<worker>.json`.
- The controller (or single run) merges those into:
  - `reports/api-report.json`
  - `reports/api-report.html`  
- Allure results go to `reports/allure-results/`.

---

## `config/settings.py` (the `Settings` loader)

## Where values come from and precedence
- First setting loads CLI (--env, --username etc.)

- Secondly it loads the environment variables ( .env, .env.dev, .env.preprod)

- Lastly it loads the environment.json defaults for the selected environment

- Rule of thumb: CLI > .env > environment.json.


`Settings` centralizes configuration. Typical fields:

```python
class Settings:
    environment: str           # 'dev', 'staging', 'prod', ...
    api_base_url: str
    timeout: int               # seconds
    test_username: str
    test_password: str
    test_data: dict | None     # optional pools (users, seeds)
    UI:
    android_device_name: str | None
    android_app_path: str | None
    ios_device_name: str | None
    ios_app_path: str | None


