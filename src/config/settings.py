# from pydantic import BaseSettings, Field
# import json
# import os
# from pathlib import Path
# from typing import Dict, Any, List


# class Settings(BaseSettings):
#     # Environment
#     environment: str = "dev"

#     # URLs
#     base_url: str = Field(default="https://example.com")
#     api_base_url: str = Field(default="https://api.example.com")

#     # Database
#     database_url: str = Field(default="")

#     # Test Configuration
#     timeout: int = Field(default=30)
#     retries: int = Field(default=3)
#     parallel_workers: int = Field(default=2)
#     browser_slowmo: int = Field(default=500)
#     record_video: bool = Field(default=False)
#     run_smoke_only: bool = Field(default=False)

#     # Mobile Configuration
#     mobile_config: Dict[str, str] = Field(default_factory=dict)

#     # Performance Configuration
#     performance_config: Dict[str, Any] = Field(default_factory=dict)

#     # Credentials
#     test_username: str = Field(default="testuser")
#     test_password: str = Field(default="testpass")

#     # Environment-specific test data
#     test_data: Dict[str, Any] = Field(default_factory=dict)

#     def __init__(self, environment: str = None):
#         super().__init__()

#         # Get environment from parameter, env var, or default
#         self.environment = (
#                 environment or
#                 os.getenv("TEST_ENV", "dev")
#         )

#         self.load_environment_config()
#         self.load_test_data()
#         self.validate_environment()

#     def load_environment_config(self):
#         """Load environment-specific configuration"""
#         config_file = Path(__file__).parent / "environments.json"

#         if config_file.exists():
#             with open(config_file) as f:
#                 configs = json.load(f)

#                 if self.environment in configs:
#                     env_config = configs[self.environment]

#                     # Update all settings from environment config
#                     for key, value in env_config.items():
#                         if hasattr(self, key):
#                             setattr(self, key, value)
#                 else:
#                     available_envs = list(configs.keys())
#                     raise ValueError(
#                         f"Environment '{self.environment}' not found. "
#                         f"Available environments: {available_envs}"
#                     )

#     def load_test_data(self):
#         """Load environment-specific test data"""
#         test_data_file = Path(__file__).parent / f"test_data/{self.environment}_data.json"

#         if test_data_file.exists():
#             with open(test_data_file) as f:
#                 self.test_data = json.load(f)

#     def validate_environment(self):
#         """Validate required settings for environment"""
#         required_settings = ["base_url", "api_base_url"]

#         missing = [setting for setting in required_settings
#                    if not getattr(self, setting, None)]

#         if missing:
#             raise ValueError(
#                 f"Missing required settings for environment '{self.environment}': {missing}"
#             )

#     def get_test_user(self, role: str = "user") -> Dict[str, str]:
#         """Get test user by role"""
#         users = self.test_data.get("users", [])
#         for user in users:
#             if user.get("role") == role:
#                 return user

#         # Fallback to default user
#         return {
#             "username": self.test_username,
#             "password": self.test_password,
#             "role": role
#         }

#     def get_test_products(self) -> List[Dict[str, Any]]:
#         """Get test products for environment"""
#         return self.test_data.get("products", [])

#     def get_api_key(self, service: str) -> str:
#         """Get API key for external service"""
#         return self.test_data.get("api_keys", {}).get(service, "")

#     def is_production_like(self) -> bool:
#         """Check if environment is production-like"""
#         return self.environment in ["prod", "production", "preprod"]

#     def should_run_smoke_only(self) -> bool:
#         """Check if only smoke tests should run"""
#         return getattr(self, "run_smoke_only", False)

#     class Config:
#         env_file = ".env"
#         case_sensitive = False


from __future__ import annotations
import json
import os
from pathlib import Path
from typing import Any, Dict, List

from dotenv import load_dotenv
from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # ----- Core env selection -----
    environment: str = Field(default_factory=lambda: os.getenv("TEST_ENV", "dev"))

    # ----- URLs ----- 
    # Explicitly map environment variable names to avoid confusion
    base_url: str = Field(default="https://example.com", alias="BASE_URL")
    api_base_url: str = Field(default="https://api.example.com", alias="API_BASE_URL")

    # ----- Database -----
    database_url: str = Field(default="", alias="DATABASE_URL")

    # ----- Test Configuration -----
    timeout: int = Field(default=30, alias="API_TIMEOUT")
    retries: int = Field(default=3, alias="TEST_RETRIES")
    parallel_workers: int = Field(default=2, alias="PARALLEL_WORKERS")
    browser_slowmo: int = Field(default=500, alias="UI_SLOW_MO")
    record_video: bool = Field(default=False, alias="RECORD_VIDEO")
    run_smoke_only: bool = Field(default=False, alias="RUN_SMOKE_ONLY")

    # ----- Mobile & Performance -----
    mobile_config: Dict[str, str] = Field(default_factory=dict)
    performance_config: Dict[str, Any] = Field(default_factory=dict)

    # ----- Credentials -----
    test_username: str = Field(default="testuser", alias="TEST_USERNAME")
    test_password: str = Field(default="testpass", alias="TEST_PASSWORD")

    # ----- Environment-specific test data -----
    test_data: Dict[str, Any] = Field(default_factory=dict)

    # Pydantic Settings Configuration
    model_config = SettingsConfigDict(
        env_file=None,  # We handle .env loading ourselves
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        env_prefix="",  # No prefix for env vars
    )

    def __init__(self, **values):
        # Determine target environment
        desired_env = values.get("environment") or os.getenv("TEST_ENV", "dev")
    
        # Set TEST_ENV so it's available for other components
        os.environ["TEST_ENV"] = desired_env
    
        # Project root = parent of this config/ directory  
        root = Path(__file__).resolve().parent.parent.parent
        base_env = root / ".env"
        env_specific = root / f".env.{desired_env}"

        # NOW you can print the debug info:
        print(f"Settings file location: {Path(__file__).resolve()}")
        print(f"Calculated root: {root}")
        print(f"Looking for .env at: {base_env}")
        print(f"Looking for env-specific at: {env_specific}")

        # Load .env files with proper precedence
        if base_env.exists():
            load_dotenv(base_env, override=False)
        
        if env_specific.exists():
            load_dotenv(env_specific, override=False)

        # Now let Pydantic BaseSettings do its magic
        super().__init__(**values)

    # def __init__(self, **values):
    #     """
    #     Load environment files in the correct precedence order:
    #     1. .env (base defaults)
    #     2. .env.{environment} (environment-specific overrides)  
    #     3. OS environment variables (highest priority - never overridden)
    #     """

    #     # Add debug logging to your Settings.__init__ method:
    #     print(f"Settings file location: {Path(__file__).resolve()}")
    #     print(f"Calculated root: {root}")
    #     print(f"Looking for .env at: {base_env}")
    #     print(f"Looking for env-specific at: {env_specific}")
    #     # Determine target environment
    #     desired_env = values.get("environment") or os.getenv("TEST_ENV", "dev")
        
    #     # Set TEST_ENV so it's available for other components
    #     os.environ["TEST_ENV"] = desired_env
        
    #     # Project root = parent of this config/ directory  
    #     root = Path(__file__).resolve().parent.parent
    #     base_env = root / ".env"
    #     env_specific = root / f".env.{desired_env}"

    #     # Load .env files with proper precedence
    #     # 1. Load base .env first (lowest priority)
    #     if base_env.exists():
    #         load_dotenv(base_env, override=False)  # Don't override existing env vars
            
    #     # 2. Load environment-specific .env (medium priority) 
    #     if env_specific.exists():
    #         load_dotenv(env_specific, override=False)  # Don't override existing env vars

    #     # 3. OS environment variables have highest priority (already in os.environ)
        
    #     # Now let Pydantic BaseSettings do its magic
    #     # It will read from os.environ using the env="FIELD_NAME" mappings
    #     super().__init__(**values)

    @model_validator(mode="after") 
    def _load_additional_config(self) -> "Settings":
        """Load additional configuration after Pydantic has processed env vars."""
        self._load_environment_config()
        self._load_test_data()
        self._validate_environment()
        return self

    def _load_environment_config(self) -> None:
        """Load non-secret per-env config from environments.json"""
        config_file = Path(__file__).parent / "environments.json"
        if not config_file.exists():
            return
            
        with open(config_file) as f:
            configs = json.load(f)

        env = self.environment
        if env not in configs:
            available_envs = list(configs.keys())
            raise ValueError(
                f"Environment '{env}' not found. Available environments: {available_envs}"
            )

        env_config: Dict[str, Any] = configs[env]
        
        # Only override fields that weren't set from environment variables
        for key, value in env_config.items():
            if hasattr(self, key):
                # Check if this field was set from env var or is still default
                current_value = getattr(self, key)
                field_info = self.__class__.model_fields.get(key)  # Use class, not instance
                
                # If current value is the default and we have a config override, use it
                if field_info and current_value == field_info.default:
                    setattr(self, key, value)

    def _load_test_data(self) -> None:
        """Load test data specific to the environment."""
        test_data_file = Path(__file__).parent / f"test_data/{self.environment}_data.json"
        if test_data_file.exists():
            with open(test_data_file) as f:
                self.test_data = json.load(f)

    def _validate_environment(self) -> None:
        """Validate required settings are present."""
        required = ["base_url", "api_base_url"]
        missing = [name for name in required if not getattr(self, name, None)]
        if missing:
            raise ValueError(
                f"Missing required settings for environment '{self.environment}': {missing}"
            )

    # --------- Public helpers ---------
    def get_test_user(self, role: str = "user") -> Dict[str, str]:
        """Get test user credentials by role."""
        users = self.test_data.get("users", [])
        for user in users:
            if user.get("role") == role:
                return user
        return {
            "username": self.test_username,
            "password": self.test_password, 
            "role": role,
        }

    def get_test_products(self) -> List[Dict[str, Any]]:
        """Get test product data."""
        return self.test_data.get("products", [])

    def get_api_key(self, service: str) -> str:
        """Get API key for a service."""
        return self.test_data.get("api_keys", {}).get(service, "")

    def is_production_like(self) -> bool:
        """Check if environment is production-like."""
        return self.environment in {"prod", "production", "preprod"}

    def should_run_smoke_only(self) -> bool:
        """Check if only smoke tests should run."""
        return bool(self.run_smoke_only)
    