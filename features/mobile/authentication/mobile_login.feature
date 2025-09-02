@mobile @smoke
Feature: App Navigation
  As a mobile user
  I want to navigate through the app
  So that I can access different features

  Background:
    Given I have launched the mobile app

  @positive
  Scenario: Navigate to profile screen
    When I tap on the profile icon
    Then I should see the profile screen
    And the profile information should be displayed

  @positive
  Scenario: Search functionality
    Given I am on the home screen
    When I tap on the search icon
    And I enter "test product" in the search field
    And I tap the search button
    Then I should see search results
    And the results should contain "test product"