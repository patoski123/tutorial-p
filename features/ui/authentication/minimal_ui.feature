Feature: Minimal UI smoke

  @smoke @patrickUiTest
  Scenario: Visit the home page of App
    When I open the playwright home page
    Then the page title should contain "Playqwwwright"


