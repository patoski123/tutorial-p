import pytest
from pytest_bdd import scenarios

# Load integration feature scenarios
scenarios('../../features/integration/')

@pytest.mark.integration
class TestIntegrationFeatures:
    """Test class to group integration BDD tests"""
    pass