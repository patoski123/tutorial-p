Feature: Minimal Product API

  Background:
    Given the API is available

  @smoke @api
  Scenario: Create a product via API (mock)
    When I create a product named "Widget 1" via the API
    Then the API should return the product with name "Widget 1"
