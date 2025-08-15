Feature: User Authentication API
  As a system user
  I want to authenticate via API
  So that I can access protected resources

  Background:
    Given the API is available
    And I have valid test credentials

  @smoke @api @authentication
  Scenario: Successful login with valid credentials
    Given I have a valid username "testuser@example.com"
    And I have a valid password "testpassword"
    When I send a login request
    Then the response status should be 200
    And the response should contain an access token
    And the response should contain a refresh token
    And the access token should be valid

  @api @authentication
  Scenario: Login fails with invalid credentials
    Given I have an invalid username "invalid@example.com"
    And I have an invalid password "wrongpassword"
    When I send a login request
    Then the response status should be 401
    And the response should contain an error message
    And no access token should be provided

  @api @authentication
  Scenario Outline: Login validation with missing credentials
    Given I have username "<username>"
    And I have password "<password>"
    When I send a login request
    Then the response status should be 400
    And the response should contain a validation error

    Examples:
      | username              | password    |
      |                       | validpass   |
      | testuser@example.com  |             |
      |                       |             |

  @api @authentication
  Scenario: Token refresh functionality
    Given I am authenticated with valid credentials
    And I have a valid refresh token
    When I send a token refresh request
    Then the response status should be 200
    And I should receive a new access token
    And the new access token should be different from the old one

  @api @authentication
  Scenario: Access protected resource with valid token
    Given I am authenticated with valid credentials
    When I request my user profile
    Then the response status should be 200
    And the response should contain my user information
    And the user information should include username and email