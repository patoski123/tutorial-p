@ui @smoke
Feature: User Login
  As a user
  I want to login to the application
  So that I can access my account

  Background:
    Given I am on the login page

  @positive
  Scenario: Successful login with valid credentials
    When I enter username "testuser" and password "testpass"
    And I click the login button
    Then I should be redirected to the dashboard
    And I should see welcome message "Welcome testuser"

  @negative
  Scenario: Failed login with invalid credentials
    When I enter username "invalid" and password "invalid"
    And I click the login button
    Then I should see error message "Invalid credentials"
    And I should remain on the login page

  @negative
  Scenario Outline: Login validation messages
    When I enter username "<username>" and password "<password>"
    And I click the login button
    Then I should see error message "<error_message>"

    Examples:
      | username | password | error_message |
      |          | testpass | Username is required |
      | testuser |          | Password is required |
      |          |          | Username and password are required |