# features/retry_functionality.feature
@retry_functionality
Feature: API Retry Functionality
  As a test automation engineer
  I want to test comprehensive API retry mechanisms
  So that I can ensure robust handling of temporary service failures

  Background:
    Given the retry endpoint state is reset

  Scenario: Single call fails when service is not ready
    Given the retry endpoint is configured to fail 3 times
    When I call the retry endpoint without retry logic
    Then the response should have status 503
    And the response should indicate it is running
    And the retry should have used none method

  Scenario: Linear retry succeeds after multiple attempts
    Given the retry endpoint is configured to fail 3 times
    When I call the retry endpoint with 5 linear retry attempts
    Then the response should have status 200
    And the response should indicate success
    And the retry should have eventually succeeded
    And the retry should have used linear method
    And the response should contain valid test data

  Scenario: Exponential backoff retry succeeds
    Given the retry endpoint is configured to fail 4 times
    When I call the retry endpoint with 6 exponential backoff attempts
    Then the response should have status 200
    And the response should indicate success
    And the retry should have eventually succeeded
    And the retry should have used exponential method

  Scenario: Linear retry fails with insufficient attempts
    Given the retry endpoint is configured to fail 5 times
    When I call the retry endpoint with 3 linear retry attempts
    Then the response should have status 503
    And the response should indicate it is running
    And the retry should have failed without success
    And the retry should have been attempted at most 3 times

  Scenario: Retry with timeout constraint
    Given the retry endpoint is configured to fail 10 times
    When I call the retry endpoint with 2.0 second timeout
    Then the response should indicate a timeout occurred
    And the timeout should have been 2.0 seconds
    And the retry should have used timeout method

  Scenario: Retry until success strategy
    Given the retry endpoint is configured to fail 2 times
    When I call the retry endpoint with retry until success
    Then the response should have status 200
    And the response should indicate success
    And the retry should have eventually succeeded
    And the retry should have used until_success method

  Scenario: Custom condition retry
    Given the retry endpoint is configured to fail 3 times
    When I call the retry endpoint with custom condition retry
    Then the response should have status 200
    And the response should indicate success
    And the retry should have eventually succeeded
    And the retry should have used custom_condition method

  Scenario Outline: Different failure counts with linear retry
    Given the retry endpoint is configured to fail <failures> times
    When I call the retry endpoint with <attempts> linear retry attempts
    Then the response should have status <expected_status>
    And the retry should have been attempted at most <attempts> times

    Examples:
      | failures | attempts | expected_status |
      | 1        | 3        | 200            |
      | 2        | 4        | 200            |
      | 3        | 5        | 200            |
      | 5        | 3        | 503            |
      | 7        | 4        | 503            |

  Scenario Outline: Comprehensive retry scenarios
    When I run comprehensive retry scenario "<scenario>"
    Then the "<scenario>" scenario should complete successfully
    And the response should indicate success
    And the response should contain valid test data

    Examples:
      | scenario        |
      | linear          |
      | exponential     |
      | until_success   |
      | custom_condition|

  Scenario: Compare retry strategies performance
    Given the retry endpoint is configured to fail 3 times
    When I call the retry endpoint with 5 linear retry attempts
    Then the retry should have eventually succeeded
    And the retry should have used linear method

    Given the retry endpoint state is reset
    And the retry endpoint is configured to fail 3 times
    When I call the retry endpoint with 5 exponential backoff attempts
    Then the retry should have eventually succeeded
    And the retry should have used exponential method

  Scenario: Edge case - zero failures (immediate success)
    Given the retry endpoint is configured to fail 0 times
    When I call the retry endpoint with 3 linear retry attempts
    Then the response should have status 200
    And the response should indicate success
    And the retry should have eventually succeeded

  Scenario: Edge case - single failure
    Given the retry endpoint is configured to fail 1 times
    When I call the retry endpoint without retry logic
    Then the response should have status 503
    And the response should indicate it is running

    Given the retry endpoint state is reset
    And the retry endpoint is configured to fail 1 times
    When I call the retry endpoint with 2 linear retry attempts
    Then the response should have status 200
    And the response should indicate success