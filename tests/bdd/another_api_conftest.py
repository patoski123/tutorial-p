import pytest
from api.user_api import UserAPI
from api.product_api import ProductAPI

@pytest.fixture
def user_api(authenticated_api_client):
    """User API client"""
    return UserAPI()

@pytest.fixture
def product_api(authenticated_api_client):
    """Product API client"""
    return ProductAPI()

@pytest.fixture
def sample_user_data():
    """Sample user data for API tests"""
    return {
        "username": "testuser123",
        "email": "testuser123@example.com",
        "first_name": "Test",
        "last_name": "User",
        "password": "SecurePass123!"
    }

### tests/api/test_auth_api.py
```python
import pytest
from api.auth_api import AuthAPI
import structlog

logger = structlog.get_logger(__name__)

class TestAuthAPI:
    """Authentication API test suite"""

    @pytest.mark.smoke
    @pytest.mark.api
    def test_successful_login(self, api_client, test_config):
        """Test successful user login"""
        success, response_data = api_client.login(
            test_config.test_user['username'],
            test_config.test_user['password']
        )

        assert success, "Login should be successful"
        assert 'access_token' in response_data, "Response should contain access token"
        assert 'refresh_token' in response_data, "Response should contain refresh token"
        assert response_data['access_token'], "Access token should not be empty"

    @pytest.mark.api
    def test_invalid_credentials(self, api_client):
        """Test login with invalid credentials"""
        success, response_data = api_client.login(
            "invalid@example.com",
            "wrongpassword"
        )

        assert not success, "Login should fail with invalid credentials"
        assert 'error' in response_data or 'message' in response_data, "Response should contain error message"

    @pytest.mark.api
    def test_empty_credentials(self, api_client):
        """Test login with empty credentials"""
        success, response_data = api_client.login("", "")

        assert not success, "Login should fail with empty credentials"

    @pytest.mark.api
    def test_logout(self, authenticated_api_client):
        """Test user logout"""
        success = authenticated_api_client.logout()
        assert success, "Logout should be successful"

    @pytest.mark.api
    def test_get_user_profile(self, authenticated_api_client):
        """Test getting user profile"""
        success, profile_data = authenticated_api_client.get_user_profile()

        assert success, "Getting user profile should be successful"
        assert 'username' in profile_data or 'email' in profile_data, "Profile should contain user identifier"

    @pytest.mark.api
    def test_api_response_time(self, api_client, test_config):
        """Test API response time is acceptable"""
        response = api_client.session.post(
            f"{api_client.base_url}/auth/login",
            json={
                "username": test_config.test_user['username'],
                "password": test_config.test_user['password']
            }
        )

        # Assert response time is under 2 seconds
        api_client.assert_response_time(response, 2.0)

### tests/api/test_user_api.py
```python
import pytest
from faker import Faker
import structlog

fake = Faker()
logger = structlog.get_logger(__name__)

class TestUserAPI:
    """User management API test suite"""

    @pytest.mark.api
    def test_create_user(self, user_api, sample_user_data):
        """Test creating a new user"""
        response = user_api.create_user(sample_user_data)
        user_api.assert_status_code(response, 201)

        response_data = response.json()
        assert response_data['username'] == sample_user_data['username']
        assert response_data['email'] == sample_user_data['email']
        assert 'id' in response_data, "Response should contain user ID"

    @pytest.mark.api
    def test_get_user_by_id(self, user_api, sample_user_data):
        """Test retrieving user by ID"""
        # First create a user
        create_response = user_api.create_user(sample_user_data)
        user_api.assert_status_code(create_response, 201)
        user_id = create_response.json()['id']

        # Then retrieve it
        response = user_api.get_user(user_id)
        user_api.assert_status_code(response, 200)

        user_data = response.json()
        assert user_data['id'] == user_id
        assert user_data['username'] == sample_user_data['username']

    @pytest.mark.api
    def test_update_user(self, user_api, sample_user_data):
        """Test updating user information"""
        # Create user first
        create_response = user_api.create_user(sample_user_data)
        user_id = create_response.json()['id']

        # Update user
        updated_data = {
            "first_name": "Updated",
            "last_name": "Name"
        }
        response = user_api.update_user(user_id, updated_data)
        user_api.assert_status_code(response, 200)

        # Verify update
        get_response = user_api.get_user(user_id)
        user_data = get_response.json()
        assert user_data['first_name'] == "Updated"
        assert user_data['last_name'] == "Name"

    @pytest.mark.api
    def test_delete_user(self, user_api, sample_user_data):
        """Test deleting a user"""
        # Create user first
        create_response = user_api.create_user(sample_user_data)
        user_id = create_response.json()['id']

        # Delete user
        response = user_api.delete_user(user_id)
        user_api.assert_status_code(response, 204)

        # Verify deletion
        get_response = user_api.get_user(user_id)
        user_api.assert_status_code(get_response, 404)

    @pytest.mark.api
    @pytest.mark.parametrize("invalid_email", [
        "invalid-email",
        "@example.com",
        "test@",
        "test..test@example.com"
    ])
    def test_create_user_invalid_email(self, user_api, sample_user_data, invalid_email):
        """Test creating user with invalid email formats"""
        sample_user_data['email'] = invalid_email

        response = user_api.create_user(sample_user_data)
        user_api.assert_status_code(response, 400)

    @pytest.mark.api
    def test_get_all_users(self, user_api):
        """Test retrieving all users with pagination"""
        response = user_api.get_users(page=1, limit=10)
        user_api.assert_status_code(response, 200)

        data = response.json()
        assert 'users' in data or 'data' in data, "Response should contain users list"
        assert 'total' in data or 'count' in data, "Response should contain total count"

### api/user_api.py
```python
from api.base_api import BaseAPI
from typing import Dict, Optional
import structlog

logger = structlog.get_logger(__name__)

class UserAPI(BaseAPI):
    """User management API client"""

    def create_user(self, user_data: Dict) -> requests.Response:
        """Create a new user"""
        return self.post("/users", json=user_data)

    def get_user(self, user_id: int) -> requests.Response:
        """Get user by ID"""
        return self.get(f"/users/{user_id}")

    def get_users(self, page: int = 1, limit: int = 10, search: str = None) -> requests.Response:
        """Get list of users with pagination"""
        params = {"page": page, "limit": limit}
        if search:
            params["search"] = search
        return self.get("/users", params=params)

    def update_user(self, user_id: int, update_data: Dict) -> requests.Response:
        """Update user information"""
        return self.put(f"/users/{user_id}", json=update_data)

    def delete_user(self, user_id: int) -> requests.Response:
        """Delete user"""
        return self.delete(f"/users/{user_id}")

    def search_users(self, query: str) -> requests.Response:
        """Search users by query"""
        return self.get("/users/search", params={"q": query})

### api/product_api.py
```python
from api.base_api import BaseAPI
from typing import Dict, List, Optional
import structlog

logger = structlog.get_logger(__name__)

class ProductAPI(BaseAPI):
    """Product management API client"""

    def create_product(self, product_data: Dict) -> requests.Response:
        """Create a new product"""
        return self.post("/products", json=product_data)

    def get_product(self, product_id: int) -> requests.Response:
        """Get product by ID"""
        return self.get(f"/products/{product_id}")

    def get_products(self, category: str = None, page: int = 1, limit: int = 10) -> requests.Response:
        """Get list of products"""
        params = {"page": page, "limit": limit}
        if category:
            params["category"] = category
        return self.get("/products", params=params)

    def update_product(self, product_id: int, update_data: Dict) -> requests.Response:
        """Update product information"""
        return self.put(f"/products/{product_id}", json=update_data)

    def delete_product(self, product_id: int) -> requests.Response:
        """Delete product"""
        return self.delete(f"/products/{product_id}")

    def get_product_categories(self) -> requests.Response:
        """Get all product categories"""
        return self.get("/products/categories")

### ui/pages/login_page.py
```python
from ui.pages.base_page import BasePage
from playwright.sync_api import expect
import structlog

logger = structlog.get_logger(__name__)

class LoginPage(BasePage):
    """Login page object"""

    def __init__(self, page):
        super().__init__(page)

        # Locators
        self.username_field = "#username"
        self.password_field = "#password"
        self.login_button = "#login-button"
        self.error_message = ".error-message"
        self.forgot_password_link = ".forgot-password"
        self.remember_me_checkbox = "#remember-me"

    def navigate_to_login(self, base_url: str):
        """Navigate to login page"""
        login_url = f"{base_url.rstrip('/')}/login"
        self.navigate_to(login_url)

    def enter_username(self, username: str):
        """Enter username"""
        self.fill(self.username_field, username)

    def enter_password(self, password: str):
        """Enter password"""
        self.fill(self.password_field, password)

    def click_login(self):
        """Click login button"""
        self.click(self.login_button)

    def login(self, username: str, password: str, remember_me: bool = False):
        """Complete login process"""
        logger.info("Performing login", username=username)

        self.enter_username(username)
        self.enter_password(password)

        if remember_me:
            self.click(self.remember_me_checkbox)

        self.click_login()

    def get_error_message(self) -> str:
        """Get error message text"""
        return self.get_text(self.error_message)

    def is_error_displayed(self) -> bool:
        """Check if error message is displayed"""
        return self.is_visible(self.error_message)

    def click_forgot_password(self):
        """Click forgot password link"""
        self.click(self.forgot_password_link)

    def assert_login_form_visible(self):
        """Assert login form elements are visible"""
        self.assert_element_visible(self.username_field)
        self.assert_element_visible(self.password_field)
        self.assert_element_visible(self.login_button)

    def assert_error_message(self, expected_message: str):
        """Assert specific error message is displayed"""
        self.assert_element_visible(self.error_message)
        actual_message = self.get_error_message()
        assert expected_message in actual_message, f"Expected '{expected_message}' in '{actual_message}'"

### tests/ui/conftest.py
```python
import pytest
from ui.pages.login_page import LoginPage
from ui.pages.dashboard_page import DashboardPage

@pytest.fixture
def login_page(page):
    """Login page object"""
    return LoginPage(page)

@pytest.fixture
def dashboard_page(page):
    """Dashboard page object"""
    return DashboardPage(page)

@pytest.fixture
def authenticated_ui_session(page, login_page, test_config):
    """UI session with authenticated user"""
    login_page.navigate_to_login(test_config.api.base_url)
    login_page.login(
        test_config.test_user['username'],
        test_config.test_user['password']
    )

    # Wait for successful login (adjust selector based on your app)
    page.wait_for_selector(".dashboard", timeout=10000)

    yield page

    # Logout if needed
    if page.locator(".logout-button").is_visible():
        page.click(".logout-button")

### tests/ui/test_login_ui.py
```python
import pytest
from playwright.sync_api import expect
import structlog

logger = structlog.get_logger(__name__)

class TestLoginUI:
    """UI tests for login functionality"""

    @pytest.mark.smoke
    @pytest.mark.ui
    def test_login_page_loads(self, login_page, test_config):
        """Test login page loads correctly"""
        login_page.navigate_to_login(test_config.api.base_url)

        # Assert page title
        expect(login_page.page).to_have_title_pattern(".*[Ll]ogin.*")

        # Assert form elements are visible
        login_page.assert_login_form_visible()

    @pytest.mark.ui
    def test_successful_login(self, login_page, test_config):
        """Test successful login flow"""
        login_page.navigate_to_login(test_config.api.base_url)

        login_page.login(
            test_config.test_user['username'],
            test_config.test_user['password']
        )

        # Assert successful login (adjust based on your app)
        expect(login_page.page).to_have_url_pattern("**/dashboard")

    @pytest.mark.ui
    def test_invalid_login(self, login_page, test_config):
        """Test login with invalid credentials"""
        login_page.navigate_to_login(test_config.api.base_url)

        login_page.login("invalid@example.com", "wrongpassword")

        # Assert error message is displayed
        assert login_page.is_error_displayed(), "Error message should be displayed"
        error_message = login_page.get_error_message()
        assert "invalid" in error_message.lower() or "incorrect" in error_message.lower()

    @pytest.mark.ui
    def test_empty_credentials(self, login_page, test_config):
        """Test login with empty credentials"""
        login_page.navigate_to_login(test_config.api.base_url)

        login_page.click_login()  # Click without entering credentials

        # Assert validation messages or error
        assert login_page.is_error_displayed() or \
               login_page.page.locator(".validation-error").is_visible()

    @pytest.mark.ui
    def test_forgot_password_link(self, login_page, test_config):
        """Test forgot password functionality"""
        login_page.navigate_to_login(test_config.api.base_url)

        login_page.click_forgot_password()

        # Assert navigation to forgot password page
        expect(login_page.page).to_have_url_pattern("**/forgot-password")

    @pytest.mark.ui
    def test_remember_me_functionality(self, login_page, test_config):
        """Test remember me checkbox"""
        login_page.navigate_to_login(test_config.api.base_url)

        login_page.login(
            test_config.test_user['username'],
            test_config.test_user['password'],
            remember_me=True
        )

        # Assert successful login
        expect(login_page.page).to_have_url_pattern("**/dashboard")

        # Check if remember me cookie is set (implementation depends on your app)
        # This is just an example
        cookies = login_page.page.context.cookies()
        remember_me_cookie = next((c for c in cookies if c['name'] == 'remember_me'), None)
        assert remember_me_cookie is not None, "Remember me cookie should be set"

### performance/load_tests/api_load_test.py
```python
from locust import HttpUser, task, between
from utils.config import config
import json
import random

class APILoadTest(HttpUser):
    """Load test for API endpoints"""

    wait_time = between(1, 3)  # Wait 1-3 seconds between requests

    def on_start(self):
        """Setup before starting tests"""
        # Login to get auth token
        response = self.client.post("/auth/login", json={
            "username": config.test_user['username'],
            "password": config.test_user['password']
        })

        if response.status_code == 200:
            token = response.json().get('access_token')
            self.client.headers.update({'Authorization': f'Bearer {token}'})

    @task(3)
    def get_users(self):
        """Load test for getting users"""
        page = random.randint(1, 5)
        self.client.get(f"/users?page={page}&limit=10")

    @task(2)
    def get_products(self):
        """Load test for getting products"""
        self.client.get("/products")

    @task(1)
    def create_user(self):
        """Load test for creating users"""
        user_data = {
            "username": f"loadtest_user_{random.randint(1000, 9999)}",
            "email": f"loadtest_{random.randint(1000, 9999)}@example.com",
            "first_name": "Load",
            "last_name": "Test"
        }

        response = self.client.post("/users", json=user_data)

        # Clean up created user
        if response.status_code == 201:
            user_id = response.json().get('id')
            if user_id:
                self.client.delete(f"/users/{user_id}")

### Jenkinsfile
```groovy
pipeline {
    agent any

parameters {
    choice(
        name: 'TEST_TYPE',
    choices: ['api', 'ui', 'smoke', 'regression', 'performance'],
    description: 'Type of tests to run'
)
choice(
    name: 'ENVIRONMENT',
choices: ['dev', 'staging', 'production'],
description: 'Environment to test against'
)
booleanParam(
    name: 'HEADLESS',
defaultValue: true,
description: 'Run UI tests in headless mode'
)
string(
    name: 'PARALLEL_WORKERS',
defaultValue: '2',
description: 'Number of parallel test workers'
)
}

environment {
    PYTHONPATH = "${WORKSPACE}"
TEST_ENV = "${params.ENVIRONMENT}"
UI_HEADLESS = "${params.HEADLESS}"
PARALLEL_WORKERS = "${params.PARALLEL_WORKERS}"

                   // Credentials from Jenkins credential store
TEST_USERNAME = credentials('test-username')
TEST_PASSWORD = credentials('test-password')
API_BASE_URL = credentials("api-base-url-${params.ENVIRONMENT}")
}

stages {
    stage('Checkout') {
    steps {
    checkout scm
echo "Testing ${params.TEST_TYPE} tests on ${params.ENVIRONMENT} environment"
}
}

stage('Setup Python Environment') {
    steps {
    sh '''
                    python -m venv venv
                    . venv/bin/activate
                    pip install --upgrade pip
                    pip install -r requirements.txt
                '''
}
}

stage('Install Playwright Browsers') {
    when {
    anyOf {
    expression { params.TEST_TYPE == 'ui' }
expression { params.TEST_TYPE == 'smoke' }
expression { params.TEST_TYPE == 'regression' }
}
}
steps {
    sh '''
                    . venv/bin/activate
                    playwright install chromium
                '''
}
}

stage('Lint and Code Quality') {
    parallel {
    stage('Flake8') {
    steps {
    sh '''
                            . venv/bin/activate
                            flake8 . --max-line-length=120 --exclude=venv
                        '''
}
}
stage('Black Format Check') {
    steps {
    sh '''
                            . venv/bin/activate
                            black --check . --exclude=venv
                        '''
}
}
}
}

stage('Run Tests') {
    steps {
    script {
def testCommand = ". venv/bin/activate && "

switch(params.TEST_TYPE) {
    case 'api':
testCommand += "pytest tests/api/ -v -n ${params.PARALLEL_WORKERS} --html=reports/html/api_report.html --json-report --json-report-file=reports/json/api_report.json"
break
case 'ui':
testCommand += "pytest tests/ui/ -v -n ${params.PARALLEL_WORKERS} --html=reports/html/ui_report.html --json-report --json-report-file=reports/json/ui_report.json"
break
case 'smoke':
testCommand += "pytest -m smoke -v -n ${params.PARALLEL_WORKERS} --html=reports/html/smoke_report.html --json-report --json-report-file=reports/json/smoke_report.json"
break
case 'regression':
testCommand += "pytest -m 'not performance' -v -n ${params.PARALLEL_WORKERS} --html=reports/html/regression_report.html --json-report --json-report-file=reports/json/regression_report.json"
break
case 'performance':
testCommand += "pytest tests/performance/ -v --html=reports/html/performance_report.html --json-report --json-report-file=reports/json/performance_report.json"
break
default:
testCommand += "pytest -v -n ${params.PARALLEL_WORKERS} --html=reports/html/full_report.html --json-report --json-report-file=reports/json/full_report.json"
}

sh testCommand
}
}
}

stage('Load Testing') {
    when {
    expression { params.TEST_TYPE == 'performance' }
}
steps {
    sh '''
                    . venv/bin/activate
                    cd performance/load_tests
                    locust -f api_load_test.py --headless -u 10 -r 2 -t 300s --host=${API_BASE_URL} --html ../../reports/performance/load_test_report.html
                '''
}
}

stage('Generate Allure Report') {
    steps {
    sh '''
                    . venv/bin/activate
                    allure generate reports/allure --clean -o reports/allure-report
                '''
}
}
}

post {
    always {
           // Archive test results
archiveArtifacts artifacts: 'reports/**/*', fingerprint: true

                                                         // Publish HTML reports
publishHTML([
    allowMissing: false,
alwaysLinkToLastBuild: true,
keepAll: true,
reportDir: 'reports/html',
reportFiles: '*.html',
reportName: 'Test Report'
])

// Archive screenshots on failure
archiveArtifacts artifacts: 'screenshots/**/*', allowEmptyArchive: true

                                                                   // Archive logs
archiveArtifacts artifacts: 'logs/**/*', allowEmptyArchive: true

                                                            // Clean workspace
cleanWs()
}

failure {
        // Send notification on failure
emailext (
    subject: "Test Execution Failed: ${env.JOB_NAME} - ${env.BUILD_NUMBER}",
body: """
                Test execution failed for ${params.TEST_TYPE} tests on ${params.ENVIRONMENT} environment.
                
                Build URL: ${env.BUILD_URL}
                Console Output: ${env.BUILD_URL}console
                
                Please check the test reports for details.
                """,
to: "${env.CHANGE_AUTHOR_EMAIL ?: 'team@example.com'}"
)
}

success {
    echo "All tests passed successfully!"
}
}
}