# Test Automation Framework

A comprehensive, scalable test automation framework supporting API, UI, Mobile, and Performance testing.

## Quick Start

### Installation
```bash

# 1. Clone the repository
git clone https://github.com/your-org/test-automation-framework.git
cd test-automation-framework

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Install Playwright browsers
playwright install

# 5. Set up environment variables
cp .env.example .env
# Edit .env with your configuration

# 6. Verify installation
pytest --version
playwright --version

# Development environment
pytest --env=dev -m smoke

# Staging environment  
pytest --env=staging -m regression

# Production environment (smoke tests only)
pytest --env=prod -m "smoke and prod_safe"

# Run UI tests in Chrome
pytest -m ui --browser=chromium

# Run UI tests in multiple browsers
pytest -m ui --browser=chromium --browser=firefox --browser=webkit

# Run UI tests with video recording
pytest -m ui --env=dev --record-video

# Run all API tests
pytest -m api

# Run API tests with authentication
pytest -m api --env=staging

# Run API tests in parallel
pytest -m api -n 8

# Run Android tests
pytest -m mobile --mobile-platform=android

# Run iOS tests  
pytest -m mobile --mobile-platform=ios

# Run mobile tests with specific device
pytest -m mobile --device="iPhone 14"


# Run complete end-to-end scenarios
pytest -m mixed --env=staging

# Run mixed tests in parallel
pytest -m mixed -n 4


# Run performance tests
cd src/performance
locust -f locustfile.py --host=https://example.com

# Run with specific parameters
locust -f locustfile.py --users=100 --spawn-rate=10 --run-time=300s

# Auto-detect optimal workers
pytest -n auto

# Specific number of workers
pytest -n 8

# Environment-aware parallel execution
pytest --env=dev -n 2      # Dev: 2 workers
pytest --env=staging -n 6  # Staging: 6 workers  
pytest --env=prod -n 10    # Prod: 10 workers

# Load balancing distribution
pytest -n 8 --dist=worksteal

# Test scope distribution
pytest -n 4 --dist=loadscope

# Monitor resources during execution
pytest -n 8 --monitor-resources

# Multi-user scenarios with user pool
pytest -n 10 --users=50 -m multi_user

# Concurrent user operations
pytest -n 8 -m "concurrent_users"

# HTML report
pytest --html=reports/report.html --self-contained-html

# Allure report
pytest --alluredir=allure-results
allure serve allure-results

# JSON report
pytest --json-report --json-report-file=reports/report.json

# Open HTML report
open reports/report.html

# Serve Allure report
allure serve allure-results

# Generate static Allure report
allure generate allure-results --clean -o allure-report

# Build Docker image
docker build -t test-automation .

# Run tests in container
docker run --rm -v $(pwd)/reports:/app/reports test-automation

# Run with environment
docker run --rm -e TEST_ENV=staging test-automation

# Run all environments
docker-compose up

# Run specific environment
docker-compose up test-staging

# Run performance tests
docker-compose up performance-tests

# Smoke tests (critical functionality)
pytest -m smoke

# Regression tests (full test suite)
pytest -m regression

# Integration tests (system integration)
pytest -m integration

# Performance tests (load/stress testing)
pytest -m performance

# Environment-specific tests
pytest -m "smoke and prod_safe"  # Production-safe smoke tests
pytest -m "regression and not destructive"  # Safe regression tests



# Run with visible browser
pytest --headless=false --slowmo=1000

# Single test with debugging
pytest tests/test_login.py::test_valid_login -v -s

# Debug with breakpoints
pytest --pdb


# Install development dependencies
pip install -r requirements-dev.txt

# Run pre-commit hooks
pre-commit install

# Run tests before committing
pytest -m smoke

# Run tests in different environments
pytest --env=dev                    # Development environment
pytest --env=test                   # Test environment  
pytest --env=staging                # Staging environment
pytest --env=preprod                # Pre-production environment
pytest --env=prod                   # Production environment

# Environment with specific test types
pytest --env=staging -m smoke       # Smoke tests in staging
pytest --env=preprod -m "not destructive"  # Safe tests in preprod
pytest --env=prod -m prod_safe      # Only production-safe tests

# Environment with user roles
pytest --env=dev --user-role=admin  # Run as admin user
pytest --env=staging --user-role=user   # Run as regular user

# Environment with browser settings
pytest --env=dev --browser=chromium --headless=false    # Dev with UI
pytest --env=prod --browser=chromium --headless=true    # Prod headless

# Parallel execution per environment
pytest --env=dev -n 2               # 2 workers in dev
pytest --env=staging -n 4           # 4 workers in staging  
pytest --env=preprod -n 8           # 8 workers in preprod


# Development - Full test suite with UI
pytest --env=dev --headless=false -m "smoke or regression"

# Test Environment - Integration tests  
pytest --env=test -m integration -n 4

# Staging - Pre-deployment validation
pytest --env=staging -m "smoke and not destructive" -n 6

# Pre-Production - Final validation
pytest --env=preprod -m "prod_safe" -n 8 --headless

# Production - Smoke tests only
pytest --env=prod -m "prod_safe and smoke" -n 10 --headless

# Docker multi-environment execution
docker-compose -f docker-compose.multi-env.yml up test-dev test-staging


# Basic parallel execution
pytest -n 4                    # Run with 4 parallel workers
pytest -n auto                 # Auto-detect CPU cores
pytest -n logical              # Use logical CPU count

# Environment-specific parallel execution  
pytest --env=dev -n 2          # Dev: 2 workers (slower for debugging)
pytest --env=staging -n 6      # Staging: 6 workers (faster execution)
pytest --env=prod -n 10        # Prod: 10 workers (maximum throughput)

# Parallel by test type
pytest -m ui -n 4              # 4 parallel UI tests
pytest -m api -n 8             # 8 parallel API tests (faster)
pytest -m mobile -n 2          # 2 parallel mobile tests (resource intensive)

# Advanced parallel options
pytest -n 4 --dist=worksteal   # Work stealing for load balancing
pytest -n 4 --dist=each        # Run each test on all workers
pytest -n 4 --dist=loadscope   # Distribute by test scope


pytest -m authentication -s -vv --alluredir=reports/allure-results
allure serve reports/allure-results
allure generate -c reports/allure-results -o reports/allure-report
open reports/allure-report/index.html   # macOS

pytest -m authentication --clean-alluredir
allure serve reports/allure-results

allure generate reports/allure-results -o reports/allure-report --clean

git clone <your-repo-url>
cd python_playwright

# 2) venv + deps
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -U pip
pip install -r requirements.txt

# 3) Playwright browsers (if you run UI or PNG snapshots)
python -m playwright install --with-deps chromium

# 4) env files
cp .env.example .env.dev           # edit values as needed
# If you want .env to auto-load, either:
#   cp .env.dev .env
# or run pytest with --env=dev (we already default to dev in Settings)

# 5) smoke run (authentication feature, with Allure results)
pytest -m authentication --clean-alluredir --alluredir=reports/allure-results

# 6) view reports
allure serve reports/allure-results     # requires Allure CLI
# Unified API trace (HTML):
open reports/api-report.html

# Stop any running allure servers
pkill -f allure

# Clean regenerate the report
allure generate reports/allure-results --clean -o reports/allure-report

# Serve the fresh report
allure serve reports/allure-results

System Chrome:
pytest -m authentication --browser=chromium --browser-channel=chrome

Specific binary:
pytest -m authentication --browser=chromium --browser-path="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

pip install --upgrade pytest-bdd gherkin-official

# Disable redaction
REDACT_SENSITIVE_DATA=false pytest

# settings.redact_uuid_values = True, or

# env var: REDACT_UUIDS=true.