Feature: User Login Interface
  As a user
  I want to log in through the web interface
  So that I can access the application

  Background:
    Given I navigate to the login page
    And the login form is displayed

  @smoke @ui @login
  Scenario: Successful login with valid credentials
    Given I have valid login credentials
    When I enter my username and password
    And I click the login button
    Then I should be redirected to the dashboard
    And I should see a welcome message
    And the page title should contain "Dashboard"

  @ui @login
  Scenario: Login fails with invalid credentials
    Given I have invalid login credentials
    When I enter the invalid username and password
    And I click the login button
    Then I should remain on the login page
    And I should see an error message "Invalid credentials"
    And the error message should be displayed prominently

  @ui @login @validation
  Scenario: Form validation for empty fields
    When I click the login button without entering credentials
    Then I should see validation messages
    And the username field should show "Username is required"
    And the password field should show "Password is required"
    And I should remain on the login page

  @ui @login
  Scenario: Password visibility toggle
    Given I have entered a password
    When I click the password visibility toggle
    Then the password should be visible in plain text
    When I click the password visibility toggle again
    Then the password should be hidden

  @ui @login
  Scenario: Remember me functionality
    Given I have valid login credentials
    When I check the "Remember me" checkbox
    And I enter my credentials and login
    Then I should be logged in successfully
    And a remember me cookie should be set
    And the session should persist across browser restarts

  @ui @login
  Scenario: Forgot password link
    When I click the "Forgot Password" link
    Then I should be redirected to the password reset page
    And the page should contain a password reset form
    And I should be able to enter my email address