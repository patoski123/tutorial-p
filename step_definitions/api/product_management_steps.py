from pytest_bdd import given, when, then, parsers
from playwright.sync_api import APIRequestContext
from utils.logger import get_logger
# scenarios('../../features/api/product_management/product_management_api.feature')

logger = get_logger(__name__)

# Context to store API responses
api_context = {}


# Given Steps
@given("I am an authenticated admin")
def setup_api_auth(api_client: APIRequestContext):
    # Login to get token
    response = api_client.post("/auth/login", data={
        "username": "testuser",
        "password": "testpass"
    })
    assert response.status == 200
    token = response.json()["token"]
    api_context["auth_token"] = token

@given("I see the product in the catalogue")
def setup_api_auth(api_client: APIRequestContext):
    # Login to get token
    response = api_client.post("/auth/login", data={
        "username": "testuser",
        "password": "testpass"
    })
    assert response.status == 200
    token = response.json()["token"]
    api_context["auth_token"] = token    


@given(parsers.parse('I create a product named "{user_id}"'))
def ensure_user_exists(api_client: APIRequestContext, user_id: str):
    headers = {"Authorization": f"Bearer {api_context['auth_token']}"}
    response = api_client.get(f"/users/{user_id}", headers=headers)
    if response.status == 404:
        # Create user if doesn't exist
        user_data = {"id": user_id, "name": "John Doe", "email": "john@example.com"}
        api_client.post("/users", data=user_data, headers=headers)

