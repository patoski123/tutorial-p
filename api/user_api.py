Feature: User Management API
As an administrator
I want to manage users via API
So that I can maintain the user base

Background:
Given the API is available
And I am authenticated as an administrator

@api @user_management @crud
Scenario: Create a new user
Given I have valid user data:
| field      | value                 |
| username   | newuser123           |
| email      | newuser@example.com  |
| first_name | John                 |
| last_name  | Doe                  |
| password   | SecurePass123!       |
When I create a new user
Then the response status should be 201
And the response should contain the created user ID
And the user should be retrievable by ID
And the password should not be returned in the response

@api @user_management @crud
Scenario: Retrieve user by ID
Given I have created a user with ID "12345"
When I request user details for ID "12345"
    Then the response status should be 200
And the response should contain user details
And the user ID should match "12345"

@api @user_management @crud
Scenario: Update user information
Given I have created a user
And I have updated user data:
| field      | value        |
| first_name | UpdatedName  |
| last_name  | UpdatedLast  |
When I update the user information
Then the response status should be 200
And the user should have updated information
And the username should remain unchanged

@api @user_management @crud
Scenario: Delete a user
Given I have created a user
When I delete the user
Then the response status should be 204
And the user should no longer exist
And requesting the user should return 404

@api @user_management @validation
Scenario Outline: User creation with invalid data
Given I have invalid user data:
| field      | value      |
| username   | <username> |
| email      | <email>    |
| first_name | <fname>    |
| last_name  | <lname>    |
When I attempt to create a user
Then the response status should be 400
And the response should contain validation errors

Examples:
| username | email           | fname | lname | description           |
|          | valid@test.com  | John  | Doe   | Missing username      |
| testuser | invalid-email   | John  | Doe   | Invalid email format  |
| testuser | valid@test.com  |       | Doe   | Missing first name    |
| a        | valid@test.com  | John  | Doe   | Username too short    |

@api @user_management @pagination
Scenario: List users with pagination
    Given I have created 15 users
    When I request users with page 1 and limit 5
    Then the response status should be 200
    And the response should contain 5 users
    And the response should include pagination metadata
    And the total count should be at least 15

@api @user_management @search
Scenario: Search users by criteria
Given I have created users with various data
When I search for users with email containing "example.com"
Then the response status should be 200
And all returned users should have emails containing "example.com"
And the results should be properly formatted