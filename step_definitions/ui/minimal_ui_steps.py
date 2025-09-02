from typing import Any, Dict
import pytest
from pytest_bdd import when, then, parsers

@pytest.fixture
def ctx() -> Dict[str, Any]:
    return {}

@when("I open the playwright home page")
def open_home_headed(ui_page, ctx):
    ui_page.goto("/")         # uses base_url from your browser_context_args
    ctx["playwrightTitle"] = ui_page.title()
    print(f"🔍 Stored title: '{ctx['playwrightTitle']}'")  # Debug

@then(parsers.parse('the page title should contain "{pageTitle}"'))
def title_contains_expected(ctx, pageTitle: str):
    # Debug: Check what's in ctx
    print(f"🔍 ctx contents: {ctx}")
    print(f"🔍 Expected pageTitle: '{pageTitle}'")
    print(f"🔍 Actual title from ctx: '{ctx.get('playwrightTitle', 'NOT_FOUND')}'")
    
    # Get the actual title from context
    actual_title = ctx.get("playwrightTitle")
    
    # Assert with proper error message
    assert actual_title is not None, f"No title found in context. Available keys: {list(ctx.keys())}"
    assert pageTitle in actual_title, f"Expected '{pageTitle}' to be in page title '{actual_title}'"

    assert pageTitle.lower() in ctx["playwrightTitle"].lower()
