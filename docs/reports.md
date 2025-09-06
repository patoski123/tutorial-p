# Reports

## Requirements
- Allure plugin is needed for local runs to serve reports
- Allure is included in the requirement.txt file

## Install

```bash
# Allure mode via ALLURE_API_ATTACH: json (default) | png | both | none.

# Final API report: reports/api-report.html.

# Combined JSON: reports/api-report.json.
---

```markdown
# API Reference & Extension Guide

This page explains the core building blocks and how to add a new API wrapper.

## Executor (do not call directly)

`src/api/execution/executor.py` exposes a factory:

```python
def make_api_executor(*, pw_api, rq_session, settings, recorder) -> ApiExecutor
The ApiExecutor is a callable:

status, data = executor(
    ctx=ctx,
    step="Login",
    method="POST",
    path="/auth/login",
    req_json={"username": "...", "password": "..."},
    req_headers={"Accept":"application/json"},
)


# It:

# picks the client (Playwright/requests/mock) via the router,

# sends the HTTP call,

# records the call via ApiRecorder.record(...),

# returns (status, resp_json).
