import pytest
import threading
from queue import Queue
from typing import Dict, Any


# Thread-safe test data management
class ThreadSafeTestContext:
    """Thread-safe context for parallel test execution"""

    def __init__(self):
        self._data = {}
        self._lock = threading.Lock()

    def set(self, key: str, value: Any, worker_id: str = None):
        with self._lock:
            if worker_id:
                key = f"{worker_id}_{key}"
            self._data[key] = value

    def get(self, key: str, worker_id: str = None, default: Any = None):
        with self._lock:
            if worker_id:
                key = f"{worker_id}_{key}"
            return self._data.get(key, default)


# Global thread-safe context
test_context = ThreadSafeTestContext()


@pytest.fixture(scope="session")
def worker_id(request):
    """Get unique worker ID for parallel execution"""
    return getattr(request.config, "workerinput", {}).get("workerid", "master")


@pytest.fixture(scope="session")
def isolated_browser_context(playwright, browser_context_args, worker_id):
    """Create isolated browser context per worker"""
    browser = playwright.chromium.launch(headless=True)

    # Add worker ID to context for isolation
    context_args = {
        **browser_context_args,
        "storage_state": None,  # Ensure fresh state per worker
        "user_agent": f"TestRunner-Worker-{worker_id}"
    }

    context = browser.new_context(**context_args)
    yield context
    context.close()
    browser.close()


@pytest.fixture
def isolated_page(isolated_browser_context, worker_id):
    """Create isolated page per worker"""
    page = isolated_browser_context.new_page()
    # Add worker identification for debugging
    page.add_init_script(f"window.testWorker = '{worker_id}';")
    yield page
    page.close()


@pytest.fixture
def isolated_api_client(playwright, isolated_browser_context, settings, worker_id):
    """Create isolated API client per worker"""
    api_context = playwright.request.new_context(
        base_url=settings.api_base_url,
        extra_http_headers={
            "X-Test-Worker": worker_id,
            "Content-Type": "application/json"
        }
    )
    yield api_context
    api_context.dispose()


# Parallel-safe user management
@pytest.fixture
def test_user_pool(settings, worker_id):
    """Manage pool of test users for parallel execution"""
    users = settings.test_data.get("users", [])

    # Assign users to workers to avoid conflicts
    if users:
        worker_index = hash(worker_id) % len(users)
        return users[worker_index]

    # Fallback to default user with worker suffix
    return {
        "username": f"{settings.test_username}_{worker_id}",
        "password": settings.test_password,
        "role": "user"
    }