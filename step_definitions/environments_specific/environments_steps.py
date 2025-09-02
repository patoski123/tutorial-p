from pytest_bdd import given, when, then, parsers
import pytest
from config.settings import Settings


@given("I am in the development environment")
def verify_dev_environment(environment_settings: Settings):
    if environment_settings.environment != "dev":
        pytest.skip("This test only runs in development environment")


@given("I am in the production environment")
def verify_prod_environment(environment_settings: Settings):
    if environment_settings.environment != "prod":
        pytest.skip("This test only runs in production environment")


@given("I have admin privileges")
def verify_admin_privileges(environment_settings: Settings, test_user):
    if test_user.get("role") != "admin":
        pytest.skip("This test requires admin privileges")


@when("I call the API to delete all test users")
def delete_all_test_users(api_client, environment_settings, skip_if_prod):
    # This will be skipped automatically in prod due to skip_if_prod fixture
    response = api_client.delete("/api/test-data/users")
    assert response.status == 200


@when("I reset the database")
def reset_database(environment_settings, skip_if_prod):
    # Only allowed in dev environment
    if not environment_settings.environment == "dev":
        pytest.fail("Database reset only allowed in dev environment")

    # Database reset logic here
    pass


@when("I check the application health endpoint")
def check_health_endpoint(api_client):
    response = api_client.get("/health")
    assert response.status == 200


@then("the system should report as healthy")
def verify_system_health(api_client):
    response = api_client.get("/health")
    health_data = response.json()
    assert health_data.get("status") == "healthy"