import pytest
from pytest_bdd import given, when, then, parsers
from src.api.wrappers.auth_api import AuthAPI
from src.api.wrappers.user_api import UserAPI
from src.pages.login_page import LoginPage
import structlog

logger = structlog.get_logger(__name__)

# Shared fixtures for BDD tests
@pytest.fixture
def api_context():
    """Context for API-related data during BDD scenarios"""
    return {
        'response': None,
        'created_users': [],
        'auth_data': {},
        'test_data': {}
    }

@pytest.fixture
def ui_context():
    """Context for UI-related data during BDD scenarios"""
    return {
        'current_page': None,
        'test_data': {},
        'user_credentials': {}
    }

@pytest.fixture
def bdd_auth_api():
    """AuthAPI instance for BDD tests"""
    return AuthAPI()

@pytest.fixture
def bdd_user_api():
    """UserAPI instance for BDD tests"""
    return UserAPI()

@pytest.fixture
def bdd_login_page(page):
    """Login page instance for BDD tests"""
    return LoginPage(page)

# Cleanup fixture
@pytest.fixture(autouse=True)
def cleanup_created_users(api_context, bdd_user_api):
    """Automatically cleanup users created during BDD tests"""
    yield

    # Cleanup any users created during the test
    for user_id in api_context.get('created_users', []):
        try:
            bdd_user_api.delete_user(user_id)
            logger.info("Cleaned up user", user_id=user_id)
        except Exception as e:
            logger.warning("Failed to cleanup user", user_id=user_id, error=str(e))