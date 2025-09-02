Feature: Minimal E2E sample

  @smoke @e2e
  Scenario: Login via API and open the home page
    When I login via the API using valid credentials
    And I open the home page
    Then I should have a token and see the page title

