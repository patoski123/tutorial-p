import pytest
from pytest_bdd import scenarios

# Load UI feature scenarios
scenarios('../../features/ui/')

@pytest.mark.ui
class TestUIFeatures:
    """Test class to group UI BDD tests"""
    pass