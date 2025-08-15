Feature: End-to-End User Journey
  As a new user
  I want to complete the full user journey
  So that I can effectively use the application

  @integration @e2e @critical
  Scenario: Complete user onboarding journey
    Given the application is available
    When I create a new user account via API
    And I verify the user was created successfully
    And I login to the web interface with the new credentials
    Then I should access the dashboard successfully
    And I should see my user profile information
    When I update my profile information via the UI
    And I verify the changes via API
    Then the API should reflect the updated information
    And the UI should display the updated information

  @integration @e2e
  Scenario: User lifecycle management
    Given I am an administrator
    When I create a new user via API
    And the user logs in via UI
    And the user performs various actions
    And I deactivate the user via API
    Then the user should not be able to login via UI
    And API requests should be rejected for the deactivated user
    When I reactivate the user via API
    Then the user should be able to login again
    And all functionality should be restored