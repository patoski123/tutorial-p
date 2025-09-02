Feature: User Authentication API
  As a system user
  I want to authenticate via API
  So that I can access protected resources

  Background:
    Given the API is available
    And I have valid test credentials

  @smoke @api @authentication
  Scenario: Successful login with a valid credentials Simon
    Given I have a valid username "testuser@example.com"
    And I have a valid password "testpassword"
    When I send a login request
    Then I have a valid API authentication token
  
  @smoke @api @authentication
  Scenario: Successful login with another valid credential Pete
    Given I have a valid username "testuser@example.com"
    And I have a valid password "testpassword"
    When I send a login request
    Then I have a valid API authentication token
  