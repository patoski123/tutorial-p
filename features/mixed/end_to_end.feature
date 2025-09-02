@mixed @regression
Feature: End-to-End User Journey
  As a user
  I want to complete a full user journey
  So that I can verify the entire system works together

  @e2e
  Scenario: Complete user registration and profile update
    # UI: Register new user
    Given I am on the registration page
    When I fill in the registration form with valid details
    And I submit the registration form
    Then I should see registration success message

    # API: Verify user was created
    When I query the API for the newly created user
    Then the user should exist in the system
    And the user status should be "active"

    # UI: Login and update profile
    Given I navigate to the login page
    When I login with the new user credentials
    Then I should be on the dashboard

    When I navigate to profile page
    And I update my profile information
    And I save the changes
    Then I should see profile updated message

    # API: Verify profile was updated
    When I query the API for the user profile
    Then the profile should reflect the updated information