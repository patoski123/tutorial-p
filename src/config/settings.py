from pydantic import BaseSettings, Field
import json
import os
from pathlib import Path
from typing import Dict, Any, List


class Settings(BaseSettings):
    # Environment
    environment: str = "dev"

    # URLs
    base_url: str = Field(default="https://example.com")
    api_base_url: str = Field(default="https://api.example.com")

    # Database
    database_url: str = Field(default="")

    # Test Configuration
    timeout: int = Field(default=30)
    retries: int = Field(default=3)
    parallel_workers: int = Field(default=2)
    browser_slowmo: int = Field(default=500)
    record_video: bool = Field(default=False)
    run_smoke_only: bool = Field(default=False)

    # Mobile Configuration
    mobile_config: Dict[str, str] = Field(default_factory=dict)

    # Performance Configuration
    performance_config: Dict[str, Any] = Field(default_factory=dict)

    # Credentials
    test_username: str = Field(default="testuser")
    test_password: str = Field(default="testpass")

    # Environment-specific test data
    test_data: Dict[str, Any] = Field(default_factory=dict)

    def __init__(self, environment: str = None):
        super().__init__()

        # Get environment from parameter, env var, or default
        self.environment = (
                environment or
                os.getenv("TEST_ENV", "dev")
        )

        self.load_environment_config()
        self.load_test_data()
        self.validate_environment()

    def load_environment_config(self):
        """Load environment-specific configuration"""
        config_file = Path(__file__).parent / "environments.json"

        if config_file.exists():
            with open(config_file) as f:
                configs = json.load(f)

                if self.environment in configs:
                    env_config = configs[self.environment]

                    # Update all settings from environment config
                    for key, value in env_config.items():
                        if hasattr(self, key):
                            setattr(self, key, value)
                else:
                    available_envs = list(configs.keys())
                    raise ValueError(
                        f"Environment '{self.environment}' not found. "
                        f"Available environments: {available_envs}"
                    )

    def load_test_data(self):
        """Load environment-specific test data"""
        test_data_file = Path(__file__).parent / f"test_data/{self.environment}_data.json"

        if test_data_file.exists():
            with open(test_data_file) as f:
                self.test_data = json.load(f)

    def validate_environment(self):
        """Validate required settings for environment"""
        required_settings = ["base_url", "api_base_url"]

        missing = [setting for setting in required_settings
                   if not getattr(self, setting, None)]

        if missing:
            raise ValueError(
                f"Missing required settings for environment '{self.environment}': {missing}"
            )

    def get_test_user(self, role: str = "user") -> Dict[str, str]:
        """Get test user by role"""
        users = self.test_data.get("users", [])
        for user in users:
            if user.get("role") == role:
                return user

        # Fallback to default user
        return {
            "username": self.test_username,
            "password": self.test_password,
            "role": role
        }

    def get_test_products(self) -> List[Dict[str, Any]]:
        """Get test products for environment"""
        return self.test_data.get("products", [])

    def get_api_key(self, service: str) -> str:
        """Get API key for external service"""
        return self.test_data.get("api_keys", {}).get(service, "")

    def is_production_like(self) -> bool:
        """Check if environment is production-like"""
        return self.environment in ["prod", "production", "preprod"]

    def should_run_smoke_only(self) -> bool:
        """Check if only smoke tests should run"""
        return getattr(self, "run_smoke_only", False)

    class Config:
        env_file = ".env"
        case_sensitive = False