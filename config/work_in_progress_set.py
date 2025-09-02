# from __future__ import annotations

# import json
# import os
# from pathlib import Path
# from typing import Any, Dict, List

# from pydantic import Field, model_validator
# from pydantic_settings import BaseSettings, SettingsConfigDict


# class Settings(BaseSettings):
#     # ----- Core env selection -----
#     # default comes from TEST_ENV if set, else "dev"
#     environment: str = Field(default_factory=lambda: os.getenv("TEST_ENV", "dev"))

#     # ----- URLs -----
#     base_url: str = Field(default="https://example.com")
#     api_base_url: str = Field(default="https://api.example.com")

#     # ----- Database -----
#     database_url: str = Field(default="")

#     # ----- Test Configuration -----
#     timeout: int = Field(default=30)
#     retries: int = Field(default=3)
#     parallel_workers: int = Field(default=2)
#     browser_slowmo: int = Field(default=500)
#     record_video: bool = Field(default=False)
#     run_smoke_only: bool = Field(default=False)

#     # ----- Mobile & Performance -----
#     mobile_config: Dict[str, str] = Field(default_factory=dict)
#     performance_config: Dict[str, Any] = Field(default_factory=dict)

#     # ----- Credentials -----
#     test_username: str = Field(default="testuser")
#     test_password: str = Field(default="testpass")

#     # ----- Environment-specific test data -----
#     test_data: Dict[str, Any] = Field(default_factory=dict)

#     # pydantic-settings v2 config
#     model_config = SettingsConfigDict(
#         env_file=".env",
#         env_file_encoding="utf-8",
#         case_sensitive=False,
#         extra="ignore",
#     )

#     # --- v2 way to run post-init logic (instead of overriding __init__) ---
#     @model_validator(mode="after")
#     def _load_env_overrides_and_data(self) -> "Settings":
#         # 1) Merge environment-specific config from environments.json
#         self._load_environment_config()
#         # 2) Load environment-specific test data file
#         self._load_test_data()
#         # 3) Validate required fields
#         self._validate_environment()
#         return self

#     # --------- Helpers (unchanged logic, just made "private") ---------
#     def _load_environment_config(self) -> None:
#         """Load environment-specific configuration from environments.json"""
#         config_file = Path(__file__).parent / "environments.json"
#         if not config_file.exists():
#             return

#         with open(config_file) as f:
#             configs = json.load(f)

#         env = self.environment
#         if env not in configs:
#             available_envs = list(configs.keys())
#             raise ValueError(
#                 f"Environment '{env}' not found. Available environments: {available_envs}"
#             )

#         env_config: Dict[str, Any] = configs[env]
#         # Assign only known fields
#         for key, value in env_config.items():
#             if hasattr(self, key):
#                 setattr(self, key, value)

#     def _load_test_data(self) -> None:
#         """Load environment-specific test data"""
#         test_data_file = Path(__file__).parent / f"test_data/{self.environment}_data.json"
#         if test_data_file.exists():
#             with open(test_data_file) as f:
#                 self.test_data = json.load(f)

#     def _validate_environment(self) -> None:
#         """Validate required settings for environment"""
#         required = ["base_url", "api_base_url"]
#         missing = [name for name in required if not getattr(self, name, None)]
#         if missing:
#             raise ValueError(
#                 f"Missing required settings for environment '{self.environment}': {missing}"
#             )

#     # --------- Public helpers (unchanged API) ---------
#     def get_test_user(self, role: str = "user") -> Dict[str, str]:
#         users = self.test_data.get("users", [])
#         for user in users:
#             if user.get("role") == role:
#                 return user
#         return {
#             "username": self.test_username,
#             "password": self.test_password,
#             "role": role,
#         }

#     def get_test_products(self) -> List[Dict[str, Any]]:
#         return self.test_data.get("products", [])

#     def get_api_key(self, service: str) -> str:
#         return self.test_data.get("api_keys", {}).get(service, "")

#     def is_production_like(self) -> bool:
#         return self.environment in {"prod", "production", "preprod"}

#     def should_run_smoke_only(self) -> bool:
#         return bool(self.run_smoke_only)
