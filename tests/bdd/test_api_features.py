import pytest
from pytest_bdd import scenarios

# Load API feature scenarios
scenarios('../../features/api/')

# This file will automatically discover and run all API feature tests
# The step definitions are imported from step_definitions/api/

# You can add scenario-specific fixtures here if needed
@pytest.mark.api
class TestAPIFeatures:
    """Test class to group API BDD tests"""
    pass