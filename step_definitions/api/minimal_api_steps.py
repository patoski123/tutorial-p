from typing import Any, Dict
import pytest
from pytest_bdd import given, when, then, parsers
from src.api.clients.product_management_api import ProductManagementAPI

@pytest.fixture
def ctx() -> Dict[str, Any]:
    return {}

@given("the API is available")
def api_available():
    # Just a placeholder for now
    pass

@when(parsers.parse('I create a product named "{name}" via the API'))
def create_product(name: str, settings, pw_api, api_recorder, ctx):
    client = ProductManagementAPI(
        settings.api_base_url,
        api=pw_api,         # provided; we’ll still run in mock mode for now
        mock=True,          # flip to False when you have a real endpoint
        recorder=api_recorder,
    )
    status, data = client.create_product(name)
    ctx["status"] = status
    ctx["product"] = data

@then(parsers.parse('the API should return the product with name "{name}"'))
def api_returns_product(ctx, name: str):
    assert ctx["status"] == 201
    assert ctx["product"]["name"] == name
