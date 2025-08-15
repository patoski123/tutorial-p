import pytest
from pytest_bdd import scenarios

# Load all scenarios from feature files
def pytest_configure(config):
    """Configure BDD tests"""
    # Load API scenarios
    scenarios('../features/api/', strict_gherkin=False)

    # Load UI scenarios
    scenarios('../features/ui/', strict_gherkin=False)

    # Load integration scenarios
    scenarios('../features/integration/', strict_gherkin=False)

# Additional BDD-specific configuration
def pytest_bdd_step_error(request, feature, scenario, step, step_func, step_func_args, exception):
    """Handle BDD step errors"""
    print(f"Step failed: {step}")
    print(f"Exception: {exception}")

def pytest_bdd_before_scenario(request, feature, scenario):
    """Before each scenario"""
    print(f"Starting scenario: {scenario.name}")

def pytest_bdd_after_scenario(request, feature, scenario):
    """After each scenario"""
    print(f"Completed scenario: {scenario.name}")