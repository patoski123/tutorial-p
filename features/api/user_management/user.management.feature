@api @smoke
Feature: User Management API
  As a developer
  I want to manage users via API
  So that I can perform CRUD operations

  Background:
    Given I have a valid API authentication token

  @positive
  Scenario: Create new user
    When I create a user with the following details:
      | name     | email           | role  |
      | John Doe | john@example.com| admin |
    Then the user should be created successfully
    And the response should contain user ID
    And the user details should match the request

  @positive
  Scenario: Get user by ID
    Given a user exists with ID "123"
    When I request user details for ID "123"
    Then I should receive user details
    And the response should contain:
      | field | value |
      | id    | 123   |
      | name  | John Doe |

  @negative
  Scenario: Get non-existent user
    When I request user details for ID "999999"
    Then I should receive 404 not found error
    And the error message should be "User not found"