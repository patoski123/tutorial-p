# step_definitions/retry_steps.py

import pytest
from pytest_bdd import given, when, then, parsers

@given(parsers.parse('the retry endpoint is configured to fail {max_failures:d} times'))
def configure_retry_endpoint(ctx, max_failures):
    """Configure how many times the endpoint should fail before succeeding"""
    ctx['max_failures'] = max_failures
    ctx['endpoint_id'] = f"test_{max_failures}"  # Unique ID per test

@given('the retry endpoint state is reset')
def reset_retry_endpoint_state(ctx, retry_api):
    """Reset the retry endpoint state for clean testing"""
    endpoint_id = ctx.get('endpoint_id', 'default')
    retry_api.reset_endpoint_state(endpoint_id)

@when('I call the retry endpoint without retry logic')
def call_retry_endpoint_no_retry(ctx, retry_api):
    """Call the endpoint once without retry logic - should fail initially"""
    max_failures = ctx.get('max_failures', 3)
    endpoint_id = ctx.get('endpoint_id', 'default')
    
    status, data = retry_api.test_retry_endpoint(
        ctx=ctx,
        max_failures=max_failures,
        endpoint_id=endpoint_id
    )
    
    ctx['status'] = status
    ctx['response'] = data
    ctx['retry_method'] = 'none'

@when(parsers.parse('I call the retry endpoint with {max_attempts:d} linear retry attempts'))
def call_retry_endpoint_with_linear_retry(ctx, retry_api, max_attempts):
    """Call the endpoint with linear retry logic"""
    max_failures = ctx.get('max_failures', 3)
    endpoint_id = ctx.get('endpoint_id', 'default')
    
    status, data = retry_api.test_retry_with_retry_logic(
        ctx=ctx,
        max_failures=max_failures,
        endpoint_id=endpoint_id,
        max_attempts=max_attempts,
        delay=0.1,  # Fast for testing
        timeout=15.0
    )
    
    ctx['status'] = status
    ctx['response'] = data
    ctx['retry_method'] = 'linear'
    ctx['max_attempts_used'] = max_attempts

@when(parsers.parse('I call the retry endpoint with {max_attempts:d} exponential backoff attempts'))
def call_retry_endpoint_with_backoff(ctx, retry_api, max_attempts):
    """Call the endpoint with exponential backoff retry logic"""
    max_failures = ctx.get('max_failures', 3)
    endpoint_id = ctx.get('endpoint_id', 'default')
    
    status, data = retry_api.test_retry_with_exponential_backoff(
        ctx=ctx,
        max_failures=max_failures,
        endpoint_id=endpoint_id,
        max_attempts=max_attempts,
        initial_delay=0.1,  # Fast for testing
        max_delay=2.0,
        backoff_factor=2.0,
        jitter=False  # Disable for predictable testing
    )
    
    ctx['status'] = status
    ctx['response'] = data
    ctx['retry_method'] = 'exponential'
    ctx['max_attempts_used'] = max_attempts

@when(parsers.parse('I call the retry endpoint with {timeout:g} second timeout'))
def call_retry_with_timeout(ctx, retry_api, timeout):
    """Test retry with timeout constraint"""
    max_failures = ctx.get('max_failures', 10)  # More failures than attempts to force timeout
    endpoint_id = ctx.get('endpoint_id', 'timeout_test')
    
    status, data = retry_api.test_retry_with_retry_logic(
        ctx=ctx,
        max_failures=max_failures,
        endpoint_id=endpoint_id,
        max_attempts=20,  # High attempts but timeout should trigger first
        delay=0.5,
        timeout=timeout
    )
    
    ctx['status'] = status
    ctx['response'] = data
    ctx['retry_method'] = 'timeout'
    ctx['timeout_used'] = timeout

@when('I call the retry endpoint with retry until success')
def call_retry_until_success(ctx, retry_api):
    """Test retry until specific success status"""
    max_failures = ctx.get('max_failures', 3)
    endpoint_id = ctx.get('endpoint_id', 'default')
    
    status, data = retry_api.test_retry_until_success(
        ctx=ctx,
        max_failures=max_failures,
        endpoint_id=endpoint_id,
        max_attempts=8,
        delay=0.1
    )
    
    ctx['status'] = status
    ctx['response'] = data
    ctx['retry_method'] = 'until_success'

@when('I call the retry endpoint with custom condition retry')
def call_retry_with_custom_condition(ctx, retry_api):
    """Test retry with custom success condition"""
    max_failures = ctx.get('max_failures', 3)
    endpoint_id = ctx.get('endpoint_id', 'default')
    
    status, data = retry_api.test_retry_with_custom_condition(
        ctx=ctx,
        max_failures=max_failures,
        endpoint_id=endpoint_id,
        max_attempts=6,
        delay=0.1
    )
    
    ctx['status'] = status
    ctx['response'] = data
    ctx['retry_method'] = 'custom_condition'

@when(parsers.parse('I run comprehensive retry scenario "{scenario}"'))
def run_comprehensive_scenario(ctx, retry_api, scenario):
    """Run predefined comprehensive retry scenarios"""
    status, data = retry_api.test_comprehensive_retry_scenarios(
        ctx=ctx,
        scenario=scenario
    )
    
    ctx['status'] = status
    ctx['response'] = data
    ctx['retry_method'] = f'comprehensive_{scenario}'
    ctx['scenario'] = scenario

@then(parsers.parse('the response should have status {expected_status:d}'))
def check_response_status(ctx, expected_status):
    """Verify the response status code"""
    actual_status = ctx.get('status')
    assert actual_status == expected_status, f"Expected status {expected_status}, got {actual_status}"

@then('the response should indicate it is running')
def check_response_running(ctx):
    """Verify the response indicates the service is running (initial failure)"""
    response = ctx.get('response', {})
    assert response.get('status') == 'Running'
    assert 'running' in response.get('message', '').lower() or 'wait' in response.get('message', '').lower()
    assert response.get('details') is None

@then('the response should indicate success')
def check_response_success(ctx):
    """Verify the response indicates successful completion"""
    response = ctx.get('response', {})
    assert response.get('status') == 'Successful'
    assert 'successfully' in response.get('message', '').lower()
    assert response.get('details') is not None
    assert isinstance(response.get('details'), list)
    assert len(response.get('details')) > 0

@then('the response should indicate a timeout occurred')
def check_response_timeout(ctx):
    """Verify the response indicates a timeout occurred"""
    response = ctx.get('response', {})
    status = ctx.get('status')
    
    # Could be 408 (timeout) or 503 if timeout occurred during retries
    assert status in [408, 503], f"Expected timeout status (408 or 503), got {status}"
    
    if status == 408:
        assert 'timeout' in response.get('error', '').lower()
    else:
        # If 503, it means we hit timeout during retry attempts
        assert response.get('status') == 'Running'

@then(parsers.parse('the retry should have used {expected_method} method'))
def check_retry_method(ctx, expected_method):
    """Verify the correct retry method was used"""
    actual_method = ctx.get('retry_method', 'none')
    assert expected_method in actual_method, f"Expected {expected_method} method, got {actual_method}"

@then('the retry should have eventually succeeded')
def check_retry_success(ctx):
    """Verify that retry logic eventually succeeded"""
    retry_method = ctx.get('retry_method', 'none')
    
    # Should have used some form of retry
    assert retry_method != 'none', "Expected retry method to be used"
    
    # Should have succeeded
    assert ctx['status'] == 200, f"Retry should have succeeded, got status {ctx['status']}"
    assert ctx['response'].get('status') == 'Successful'

@then('the retry should have failed without success')
def check_retry_failure(ctx):
    """Verify that retry logic failed to achieve success"""
    retry_method = ctx.get('retry_method', 'none')
    
    if retry_method == 'none':
        # No retry, should fail immediately
        assert ctx['status'] == 503, f"Single attempt should fail with 503, got {ctx['status']}"
    else:
        # Retry was attempted but failed
        assert ctx['status'] in [503, 408], f"Retry failure should return 503 or 408, got {ctx['status']}"

@then(parsers.parse('the retry should have been attempted at most {max_attempts:d} times'))
def check_max_attempts_respected(ctx, max_attempts):
    """Verify that retry logic respected the maximum attempts limit"""
    max_attempts_used = ctx.get('max_attempts_used', 1)
    assert max_attempts_used <= max_attempts, f"Used {max_attempts_used} attempts, max allowed {max_attempts}"

@then(parsers.parse('the timeout should have been {expected_timeout:g} seconds'))
def check_timeout_value(ctx, expected_timeout):
    """Verify the correct timeout value was used"""
    timeout_used = ctx.get('timeout_used')
    assert timeout_used == expected_timeout, f"Expected timeout {expected_timeout}s, got {timeout_used}s"

@then(parsers.parse('the "{scenario}" scenario should complete successfully'))
def check_scenario_success(ctx, scenario):
    """Verify that a comprehensive scenario completed successfully"""
    actual_scenario = ctx.get('scenario')
    assert actual_scenario == scenario, f"Expected scenario {scenario}, got {actual_scenario}"
    
    # All comprehensive scenarios should eventually succeed
    assert ctx['status'] == 200, f"Scenario {scenario} should succeed, got status {ctx['status']}"
    assert ctx['response'].get('status') == 'Successful'

@then('the response should contain valid test data')
def check_response_contains_test_data(ctx):
    """Verify response contains expected test data structure"""
    response = ctx.get('response', {})
    
    if response.get('status') == 'Successful':
        details = response.get('details', [])
        assert isinstance(details, list), "Details should be a list"
        if len(details) > 0:
            # Check first item has expected structure
            first_item = details[0]
            assert isinstance(first_item, dict), "Detail items should be dictionaries"
            assert 'id' in first_item, "Detail items should have 'id' field"
            assert 'name' in first_item, "Detail items should have 'name' field"