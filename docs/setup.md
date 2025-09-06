# Setup

## Requirements
- Python 3.10+ (3.13 supported)
- pip, venv
- (UI/E2E) Playwright browsers
- (CI) Jenkins with Allure plugin (optional)

## Install

```bash
python3 -m venv .venv
. .venv/bin/activate
bash scripts/setup-git_hooks.sh
pip install -U pip wheel
pip install -r requirements.txt
python -m playwright install

# All tests
pytest -n auto --dist=worksteal --env=dev -ra

# Only API
pytest -n auto -m api --env=dev -ra

# Only UI
pytest -m ui --env=dev --headed -ra

# E2E (UI+API)
pytest -m e2e --env=dev -ra
