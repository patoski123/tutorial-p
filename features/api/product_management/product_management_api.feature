Feature: API Product Test
  This will contain all API Product tests

   Background:
    Given I am an authenticated admin

  Scenario: Create a product
    When I create a product named "Widget"
    Then I see the product in the catalogue
