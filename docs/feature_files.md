<!-- Write steps for the feature file -->
<!-- Add a featurefile in well named folders -->

### BDD feature discovery

This repository auto-registers every valid `.feature` under `features/` via
`tests/test__load_all_features.py`. It parses each file to ensure it has a
`Feature:` line and at least one `Scenario:`/`Scenario Outline:` and then calls
`pytest_bdd.scenarios(...)` to generate pytest tests.

- Filter to a subfolder or a single file by exporting `FEATURE`:

```bash
FEATURE=api/authentication pytest -n auto --env=dev
FEATURE=api/authentication/login.feature pytest -n auto --env=dev

#  features/api/orders/orders.feature

Feature: Orders API
  Scenario: List orders
    When I list my orders
    Then I see at least one order

<!-- step definitions -->
<!-- if it is a reuseable step then place it in the the shared folder -->
step_definitions/shared/common_api_steps.py

step_definitions/api/orders_api_steps.py

import pytest
from pytest_bdd import given, when, then, parsers
from src.api.wrappers.orders_api import OrdersAPI
from src.api.schemas.order_schema import Order

@pytest.fixture
def orders_api(api_executor):
    return OrdersAPI(api_executor)

@pytest.fixture
def ctx(): return {}

<!-- for the binding to work properly the 'def' value and step def both have to be unique if not pytest-bdd will always override the second -->
<!-- "I list my orders  and def list_orders"  -->
@when("I list my orders")
def list_orders(ctx, orders_api):
    status, data = orders_api.list(ctx)
    ctx["resp_status"], ctx["resp_json"] = status, data

@then("I see at least one order")
def assert_orders(ctx):
    assert ctx["resp_status"] == 200
    # validate each item if your API responds with a list
    for item in ctx["resp_json"].get("items", []):
        Order.model_validate(item)