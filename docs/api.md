# API Test Architecture

This repo uses a simple, composable flow:

Feature/Step ──▶ Wrapper (AuthAPI, UserAPI, …)
└──▶ ApiExecutor (routes + records)
└──▶ Client (Playwright API / requests / mock)
└──▶ ApiRecorder (Allure + HTML/JSON trace)


## Components

- **Wrappers (`src/api/wrappers/*_api.py`)**
  - One Python class per API domain (e.g., `AuthAPI`, `UserAPI`).
  - Each method maps to a business operation (`login`, `get_user`, `update_profile`, …).
  - They call the **executor** with the right `step`, `method`, `path`, and payload.

- **Executor (`src/api/execution/executor.py`)**
  - A thin router that sends requests via **Playwright API** or **requests**, based on mode.
  - Serializes JSON safely, captures real response headers/body, and calls **ApiRecorder**.

- **Router (`src/api/execution/router.py`)**
  - Chooses the client mode (`PLAYWRIGHT`, `REQUESTS`, `MOCK`) from a `ctx` or settings.

- **Schemas (`src/api/schemas/*.py`)**
  - Optional response validation (pydantic/dataclasses) and shape helpers.

- **Reporting (`utils/api/api_reporting.py` + `conftest.py`)**
  - `ApiRecorder.record()` adds one entry to the trace (and Allure).
  - Per-worker JSON is written at teardown, combined into a single HTML/JSON in `pytest_sessionfinish`.
  - Final report: `reports/api-report.html` and `reports/api-report.json`.

## Test flow (high-level)

1. **Given** / **When** / **Then** steps (pytest-bdd) populate a `ctx` dict (user, tokens, inputs).
2. Step calls a **wrapper** method (e.g., `AuthAPI.login(ctx, user, pass)`).
3. Wrapper calls the **executor** with `step="Login"`, `method="POST"`, `path="/auth/login"`, `req_json=...`.
4. Executor sends the request via the selected client, gets `status`, `resp_json`, and calls **recorder**.
5. Assertions happen in the step (status, schema, business checks).
6. Reports are written on teardown (one combined HTML per full run).
