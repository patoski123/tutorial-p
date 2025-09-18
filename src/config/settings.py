

# class Settings(BaseSettings):
#     # ----- Core env selection -----
#     environment: str = Field(default_factory=lambda: os.getenv("TEST_ENV", "dev"))

#     # ----- URLs ----- 
#     # Explicitly map environment variable names to avoid confusion
#     base_url: str = Field(default="https://example.com", alias="BASE_URL")
#     api_base_url: str = Field(default="https://api.example.com", alias="API_BASE_URL")

#     # ----- Database -----
#     database_url: str = Field(default="", alias="DATABASE_URL")

#     # ----- Test Configuration -----
#     timeout: int = Field(default=30, alias="API_TIMEOUT")
#     retries: int = Field(default=3, alias="TEST_RETRIES")
#     parallel_workers: int = Field(default=2, alias="PARALLEL_WORKERS")
#     browser_slowmo: int = Field(default=500, alias="UI_SLOW_MO")
#     record_video: bool = Field(default=False, alias="RECORD_VIDEO")
#     run_smoke_only: bool = Field(default=False, alias="RUN_SMOKE_ONLY")

#     # ----- Mobile & Performance -----
#     mobile_config: Dict[str, str] = Field(default_factory=dict)
#     performance_config: Dict[str, Any] = Field(default_factory=dict)

#     # ----- Credentials -----
#     test_username: str = Field(default="testuser", alias="TEST_USERNAME")
#     test_password: str = Field(default="testpass", alias="TEST_PASSWORD")

#     # ----- Environment-specific test data -----
#     test_data: Dict[str, Any] = Field(default_factory=dict)

#     # Pydantic Settings Configuration
#     model_config = SettingsConfigDict(
#         env_file=None,  # We handle .env loading ourselves
#         env_file_encoding="utf-8",
#         case_sensitive=False,
#         extra="ignore",
#         env_prefix="",  # No prefix for env vars
#     )

#     def __init__(self, **values):
#         # Determine target environment
#         desired_env = values.get("environment") or os.getenv("TEST_ENV", "dev")
    
#         # Set TEST_ENV so it's available for other components
#         os.environ["TEST_ENV"] = desired_env
    
#         # Project root = parent of this config/ directory  
#         root = Path(__file__).resolve().parent.parent.parent
#         base_env = root / ".env"
#         env_specific = root / f".env.{desired_env}"

#         # Load .env files with proper precedence
#         if base_env.exists():
#             load_dotenv(base_env, override=False)
        
#         if env_specific.exists():
#             load_dotenv(env_specific, override=False)
#         super().__init__(**values)

#     @model_validator(mode="after") 
#     def _load_additional_config(self) -> "Settings":
#         """Load additional configuration after Pydantic has processed env vars."""
#         self._load_environment_config()
#         self._load_test_data()
#         self._validate_environment()
#         return self

#     def _load_environment_config(self) -> None:
#         """Load non-secret per-env config from environments.json"""
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
        
#         # Only override fields that weren't set from environment variables
#         for key, value in env_config.items():
#             if hasattr(self, key):
#                 # Check if this field was set from env var or is still default
#                 current_value = getattr(self, key)
#                 field_info = self.__class__.model_fields.get(key)  # Use class, not instance
                
#                 # If current value is the default and we have a config override, use it
#                 if field_info and current_value == field_info.default:
#                     setattr(self, key, value)

#     def _load_test_data(self) -> None:
#         """Load test data specific to the environment."""
#         test_data_file = Path(__file__).parent / f"test_data/{self.environment}_data.json"
#         if test_data_file.exists():
#             with open(test_data_file) as f:
#                 self.test_data = json.load(f)

#     def _validate_environment(self) -> None:
#         """Validate required settings are present."""
#         required = ["base_url", "api_base_url"]
#         missing = [name for name in required if not getattr(self, name, None)]
#         if missing:
#             raise ValueError(
#                 f"Missing required settings for environment '{self.environment}': {missing}"
#             )

#     # --------- Public helpers ---------
#     def get_test_user(self, role: str = "user") -> Dict[str, str]:
#         """Get test user credentials by role."""
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
#         """Get test product data."""
#         return self.test_data.get("products", [])

#     def get_api_key(self, service: str) -> str:
#         """Get API key for a service."""
#         return self.test_data.get("api_keys", {}).get(service, "")

#     def is_production_like(self) -> bool:
#         """Check if environment is production-like."""
#         return self.environment in {"prod", "production", "preprod"}

#     def should_run_smoke_only(self) -> bool:
#         """Check if only smoke tests should run."""
#         return bool(self.run_smoke_only)



# Debug configuration loading
# To use please start test sript as below
# DEBUG_CONFIG=true pytest tests/

# # settings.py
# from __future__ import annotations
# import json
# import os
# import warnings
# from functools import lru_cache
# from pathlib import Path
# from typing import Any, Dict, List

# from dotenv import load_dotenv
# from pydantic import Field, AliasChoices, model_validator
# from pydantic_settings import BaseSettings, SettingsConfigDict
# from pydantic_core import PydanticUndefined


# # ---------- Project root discovery ----------
# def find_project_root() -> Path:
#     current = Path(__file__).resolve()
#     markers = {"pytest.ini", ".git", "pyproject.toml", "setup.py", "requirements.txt"}
#     for parent in current.parents:
#         if any((parent / m).exists() for m in markers):
#             return parent
#     return current.parent.parent


# class ConfigurationError(Exception):
#     pass


# # ---------- Helper ----------
# def should_override_field_value(field_name: str, current_value: Any, model_fields: Dict[str, Any]) -> bool:
#     field_info = model_fields.get(field_name)
#     env_names = {field_name.upper()}
#     va = getattr(field_info, "validation_alias", None)
#     choices = getattr(va, "choices", None) if va else None
#     if choices:
#         env_names.update(str(c) for c in choices)

#     if any(name in os.environ for name in env_names):
#         return False

#     if isinstance(current_value, str):
#         return not current_value.strip()

#     default = getattr(field_info, "default", PydanticUndefined)
#     return default is not PydanticUndefined and current_value == default


# # ---------- Settings ----------
# class Settings(BaseSettings):
#     environment: str = Field(
#         default_factory=lambda: os.getenv("TEST_ENV", "dev"),
#         validation_alias=AliasChoices("TEST_ENV"),
#     )

#     base_url: str = Field("", validation_alias=AliasChoices("BASE_URL"))
#     api_base_url: str = Field("", validation_alias=AliasChoices("API_BASE_URL"))
#     database_url: str = Field("", validation_alias=AliasChoices("DATABASE_URL"))

#     timeout: int = Field(30, ge=1, le=300, validation_alias=AliasChoices("API_TIMEOUT"))
#     retries: int = Field(3, ge=0, le=10, validation_alias=AliasChoices("TEST_RETRIES"))
#     browser_slowmo: int = Field(500, ge=0, le=5000, validation_alias=AliasChoices("UI_SLOW_MO"))
#     record_video: bool = Field(False, validation_alias=AliasChoices("RECORD_VIDEO"))
#     run_smoke_only: bool = Field(False, validation_alias=AliasChoices("RUN_SMOKE_ONLY"))

#     mobile_config: Dict[str, str] = Field(default_factory=dict)
#     performance_config: Dict[str, Any] = Field(default_factory=dict)

#     test_username: str = Field("", validation_alias=AliasChoices("TEST_USERNAME"))
#     test_password: str = Field("", validation_alias=AliasChoices("TEST_PASSWORD"))

#     test_data: Dict[str, Any] = Field(default_factory=dict)

#     config_sources: Dict[str, str] = Field(default_factory=dict, exclude=True)
#     loaded_files: List[str] = Field(default_factory=list, exclude=True)

#     model_config = SettingsConfigDict(
#         env_file=None,
#         env_file_encoding="utf-8",
#         case_sensitive=False,
#         extra="ignore",
#         env_prefix="",
#     )

#     def __init__(self, **values):
#         desired_env = values.get("environment") or os.getenv("TEST_ENV", "dev")
#         os.environ["TEST_ENV"] = desired_env

#         try:
#             root = find_project_root()
#         except Exception as e:
#             warnings.warn(f"Could not find project root: {e}")
#             root = Path(__file__).resolve().parent.parent

#         base_env = root / ".env"
#         env_specific = root / f".env.{desired_env}"

#         if os.getenv("DEBUG_CONFIG", "").lower() in ("1", "true", "yes"):
#             print(f"[CONFIG] Loading environment: {desired_env}")
#             print(f"[CONFIG] Base .env: {base_env} ({'found' if base_env.exists() else 'missing'})")
#             print(f"[CONFIG] Env-specific: {env_specific} ({'found' if env_specific.exists() else 'missing'})")

#         loaded_files: List[str] = []
#         if base_env.exists():
#             load_dotenv(base_env, override=False)
#             loaded_files.append(str(base_env))
#         if env_specific.exists():
#             load_dotenv(env_specific, override=False)
#             loaded_files.append(str(env_specific))

#         super().__init__(**values)
#         self.loaded_files = loaded_files

#     @model_validator(mode="after")
#     def _post_init(self) -> "Settings":
#         self._load_environment_config_json()
#         self._load_test_data_json()
#         self._validate_required_fields()
#         self._validate_security()
#         return self

#     def _load_environment_config_json(self) -> None:
#         config_file = Path(__file__).parent / "environments.json"
#         if not config_file.exists():
#             return

#         with open(config_file, encoding="utf-8") as f:
#             configs = json.load(f)

#         env = self.environment
#         if env not in configs:
#             raise ConfigurationError(
#                 f"Environment '{env}' not found in environments.json. "
#                 f"Available: {list(configs.keys())}"
#             )

#         env_config: Dict[str, Any] = configs[env]
#         for key, value in env_config.items():
#             if hasattr(self, key):
#                 current_value = getattr(self, key)
#                 if should_override_field_value(key, current_value, self.__class__.model_fields):
#                     setattr(self, key, value)
#                     self.config_sources[key] = f"environments.json[{env}]"

#     def _load_test_data_json(self) -> None:
#         test_data_file = Path(__file__).parent / f"test_data/{self.environment}_data.json"
#         if not test_data_file.exists():
#             return

#         try:
#             with open(test_data_file, encoding="utf-8") as f:
#                 self.test_data = json.load(f)
#                 self.config_sources["test_data"] = str(test_data_file)
#         except (json.JSONDecodeError, OSError) as e:
#             warnings.warn(f"Failed to load test data from {test_data_file}: {e}")

#     def _validate_required_fields(self) -> None:
#         required_fields = {
#             "base_url": "Base URL for the application",
#             "api_base_url": "API base URL",
#             "test_username": "Test username for authentication",
#             "test_password": "Test password for authentication",
#         }

#         missing: List[str] = []
#         for field_name, description in required_fields.items():
#             value = getattr(self, field_name, None)
#             if not value or (isinstance(value, str) and not value.strip()):
#                 missing.append(f"{field_name} ({description})")

#         if missing:
#             files_checked = ", ".join(self.loaded_files) if self.loaded_files else "no .env files found"
#             raise ConfigurationError(
#                 f"Missing required settings for environment '{self.environment}':\n"
#                 f"- " + "\n- ".join(missing) + "\n\n"
#                 f"Files checked: {files_checked}\n"
#                 f"Set these via environment variables or .env files."
#             )

#     def _validate_security(self) -> None:
#         if self.is_production_like():
#             if self.test_password in {"testpass", "password", "123456", "admin"}:
#                 raise ConfigurationError(
#                     f"Production environment '{self.environment}' cannot use common test passwords"
#                 )
#             if self.timeout > 120:
#                 warnings.warn(f"Long timeout ({self.timeout}s) in production environment")

#     # --- Public helpers ---
#     def get_test_user(self, role: str = "user") -> Dict[str, str]:
#         for user in self.test_data.get("users", []):
#             if user.get("role") == role:
#                 return user
#         return {"username": self.test_username, "password": self.test_password, "role": role}

#     def get_test_products(self) -> List[Dict[str, Any]]:
#         return self.test_data.get("products", [])

#     def get_api_key(self, service: str) -> str:
#         return self.test_data.get("api_keys", {}).get(service, "")

#     def is_production_like(self) -> bool:
#         return self.environment.lower() in {"prod", "production", "preprod", "staging"}

#     def should_run_smoke_only(self) -> bool:
#         return bool(self.run_smoke_only or self.is_production_like())

#     def get_config_summary(self) -> Dict[str, Any]:
#         return {
#             "environment": self.environment,
#             "loaded_files": self.loaded_files,
#             "config_sources": self.config_sources,
#             "base_url": self.base_url,
#             "api_base_url": self.api_base_url,
#             "timeout": self.timeout,
#             "parallel_workers": self.parallel_workers,
#             "has_test_data": bool(self.test_data),
#         }


# @lru_cache(maxsize=1)
# def get_settings() -> Settings:
#     return Settings()


# settings.py
from __future__ import annotations
import json
import os
import warnings
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List

from dotenv import load_dotenv
from pydantic import Field, AliasChoices, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic_core import PydanticUndefined


# ---------- Project root discovery ----------
def find_project_root() -> Path:
    current = Path(__file__).resolve()
    markers = {"pytest.ini", ".git", "pyproject.toml", "setup.py", "requirements.txt"}
    for parent in current.parents:
        if any((parent / m).exists() for m in markers):
            return parent
    return current.parent.parent


class ConfigurationError(Exception):
    pass


# ---------- Helper ----------
def should_override_field_value(field_name: str, current_value: Any, model_fields: Dict[str, Any]) -> bool:
    field_info = model_fields.get(field_name)
    env_names = {field_name.upper()}
    va = getattr(field_info, "validation_alias", None)
    choices = getattr(va, "choices", None) if va else None
    if choices:
        env_names.update(str(c) for c in choices)

    if any(name in os.environ for name in env_names):
        return False

    if isinstance(current_value, str):
        return not current_value.strip()

    default = getattr(field_info, "default", PydanticUndefined)
    return default is not PydanticUndefined and current_value == default


# ---------- Settings ----------
class Settings(BaseSettings):
    environment: str = Field(
        default_factory=lambda: os.getenv("TEST_ENV", "dev"),
        validation_alias=AliasChoices("TEST_ENV"),
    )

    base_url: str = Field("", validation_alias=AliasChoices("BASE_URL"))
    api_base_url: str = Field("", validation_alias=AliasChoices("API_BASE_URL"))
    database_url: str = Field("", validation_alias=AliasChoices("DATABASE_URL"))

    timeout: int = Field(30, ge=1, le=300, validation_alias=AliasChoices("API_TIMEOUT"))
    retries: int = Field(3, ge=0, le=10, validation_alias=AliasChoices("TEST_RETRIES"))
    browser_slowmo: int = Field(500, ge=0, le=5000, validation_alias=AliasChoices("UI_SLOW_MO"))
    record_video: bool = Field(False, validation_alias=AliasChoices("RECORD_VIDEO"))
    run_smoke_only: bool = Field(False, validation_alias=AliasChoices("RUN_SMOKE_ONLY"))

    mobile_config: Dict[str, str] = Field(default_factory=dict)
    performance_config: Dict[str, Any] = Field(default_factory=dict)

    test_username: str = Field("", validation_alias=AliasChoices("TEST_USERNAME"))
    test_password: str = Field("", validation_alias=AliasChoices("TEST_PASSWORD"))

    test_data: Dict[str, Any] = Field(default_factory=dict)

    # Enhanced API executor configuration
    debug_api: bool = Field(False, validation_alias=AliasChoices("DEBUG_API"))
    redact_sensitive_data: bool = Field(True, validation_alias=AliasChoices("REDACT_SENSITIVE_DATA"))
    redact_uuid_values: bool = Field(False, validation_alias=AliasChoices("REDACT_UUIDS"))
    max_log_body_size: int = Field(51200, ge=1024, le=1048576, validation_alias=AliasChoices("MAX_LOG_BODY_SIZE"))  # 50KB default, 1KB-1MB range

    # Retry configuration for mock endpoints
    login_retry_attempts: int = Field(3, ge=1, le=10, validation_alias=AliasChoices("LOGIN_RETRY_ATTEMPTS"))
    data_fetch_wait_time: float = Field(3.0, ge=0.1, le=30.0, validation_alias=AliasChoices("DATA_FETCH_WAIT_TIME"))
    report_generation_wait_time: float = Field(5.0, ge=0.1, le=60.0, validation_alias=AliasChoices("REPORT_WAIT_TIME"))
    analysis_wait_time: float = Field(4.0, ge=0.1, le=30.0, validation_alias=AliasChoices("ANALYSIS_WAIT_TIME"))

    # Parallel execution configuration (computed property)
    @property
    def parallel_workers(self) -> int:
        """Get parallel worker count from environment or compute based on CPU cores"""
        env_workers = os.getenv("PYTEST_XDIST_WORKER_COUNT")
        if env_workers:
            try:
                return int(env_workers)
            except ValueError:
                pass
        
        # Auto-detect from pytest-xdist if running
        if os.getenv("PYTEST_XDIST_WORKER"):
            return os.cpu_count() or 1
        
        return 1

    config_sources: Dict[str, str] = Field(default_factory=dict, exclude=True)
    loaded_files: List[str] = Field(default_factory=list, exclude=True)

    model_config = SettingsConfigDict(
        env_file=None,
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        env_prefix="",
    )

    def __init__(self, **values):
        desired_env = values.get("environment") or os.getenv("TEST_ENV", "dev")
        os.environ["TEST_ENV"] = desired_env

        try:
            root = find_project_root()
        except Exception as e:
            warnings.warn(f"Could not find project root: {e}")
            root = Path(__file__).resolve().parent.parent

        base_env = root / ".env"
        env_specific = root / f".env.{desired_env}"

        if os.getenv("DEBUG_CONFIG", "").lower() in ("1", "true", "yes"):
            print(f"[CONFIG] Loading environment: {desired_env}")
            print(f"[CONFIG] Base .env: {base_env} ({'found' if base_env.exists() else 'missing'})")
            print(f"[CONFIG] Env-specific: {env_specific} ({'found' if env_specific.exists() else 'missing'})")

        loaded_files: List[str] = []
        if base_env.exists():
            load_dotenv(base_env, override=False)
            loaded_files.append(str(base_env))
        if env_specific.exists():
            load_dotenv(env_specific, override=False)
            loaded_files.append(str(env_specific))

        super().__init__(**values)
        self.loaded_files = loaded_files

    @model_validator(mode="after")
    def _post_init(self) -> "Settings":
        self._load_environment_config_json()
        self._load_test_data_json()
        self._validate_required_fields()
        self._validate_security()
        self._adjust_for_environment()
        return self

    def _load_environment_config_json(self) -> None:
        config_file = Path(__file__).parent / "environments.json"
        if not config_file.exists():
            return

        with open(config_file, encoding="utf-8") as f:
            configs = json.load(f)

        env = self.environment
        if env not in configs:
            raise ConfigurationError(
                f"Environment '{env}' not found in environments.json. "
                f"Available: {list(configs.keys())}"
            )

        env_config: Dict[str, Any] = configs[env]
        for key, value in env_config.items():
            if hasattr(self, key):
                current_value = getattr(self, key)
                if should_override_field_value(key, current_value, self.__class__.model_fields):
                    setattr(self, key, value)
                    self.config_sources[key] = f"environments.json[{env}]"

    def _load_test_data_json(self) -> None:
        test_data_file = Path(__file__).parent / f"test_data/{self.environment}_data.json"
        if not test_data_file.exists():
            return

        try:
            with open(test_data_file, encoding="utf-8") as f:
                self.test_data = json.load(f)
                self.config_sources["test_data"] = str(test_data_file)
        except (json.JSONDecodeError, OSError) as e:
            warnings.warn(f"Failed to load test data from {test_data_file}: {e}")

    def _validate_required_fields(self) -> None:
        required_fields = {
            "base_url": "Base URL for the application",
            "api_base_url": "API base URL",
            "test_username": "Test username for authentication",
            "test_password": "Test password for authentication",
        }

        missing: List[str] = []
        for field_name, description in required_fields.items():
            value = getattr(self, field_name, None)
            if not value or (isinstance(value, str) and not value.strip()):
                missing.append(f"{field_name} ({description})")

        if missing:
            files_checked = ", ".join(self.loaded_files) if self.loaded_files else "no .env files found"
            raise ConfigurationError(
                f"Missing required settings for environment '{self.environment}':\n"
                f"- " + "\n- ".join(missing) + "\n\n"
                f"Files checked: {files_checked}\n"
                f"Set these via environment variables or .env files."
            )

    def _validate_security(self) -> None:
        if self.is_production_like():
            if self.test_password in {"testpass", "password", "123456", "admin"}:
                raise ConfigurationError(
                    f"Production environment '{self.environment}' cannot use common test passwords"
                )
            if self.timeout > 120:
                warnings.warn(f"Long timeout ({self.timeout}s) in production environment")
            
            # Enforce redaction in production
            if not self.redact_sensitive_data:
                warnings.warn(f"Sensitive data redaction is disabled in production environment '{self.environment}'")

    def _adjust_for_environment(self) -> None:
        """Adjust configuration based on environment type"""
        if self.environment.lower() == "dev":
            # Development environment - show more data for debugging
            if self.max_log_body_size < 102400:  # Less than 100KB
                self.max_log_body_size = 102400  # Increase to 100KB for dev
                self.config_sources["max_log_body_size"] = "auto-adjusted for dev"
        
        elif self.is_production_like():
            # Production-like environments - more restrictive
            if self.max_log_body_size > 51200:  # More than 50KB
                self.max_log_body_size = 51200  # Limit to 50KB for prod
                self.config_sources["max_log_body_size"] = "auto-adjusted for production"
            
            # Force redaction in production
            if not self.redact_sensitive_data:
                self.redact_sensitive_data = True
                self.config_sources["redact_sensitive_data"] = "auto-enabled for production"

    # --- Public helpers ---
    def get_test_user(self, role: str = "user") -> Dict[str, str]:
        for user in self.test_data.get("users", []):
            if user.get("role") == role:
                return user
        return {"username": self.test_username, "password": self.test_password, "role": role}

    def get_test_products(self) -> List[Dict[str, Any]]:
        return self.test_data.get("products", [])

    def get_api_key(self, service: str) -> str:
        return self.test_data.get("api_keys", {}).get(service, "")

    def is_production_like(self) -> bool:
        return self.environment.lower() in {"prod", "production", "preprod", "staging"}

    def should_run_smoke_only(self) -> bool:
        return bool(self.run_smoke_only or self.is_production_like())

    def get_redaction_config(self) -> Dict[str, Any]:
        """Get redaction configuration for the API executor"""
        return {
            "enabled": self.redact_sensitive_data,
            "include_uuids": self.redact_uuid_values,
            "max_body_size": self.max_log_body_size
        }

    def get_retry_config(self) -> Dict[str, Any]:
        """Get retry configuration for mock endpoints"""
        return {
            "login_attempts": self.login_retry_attempts,
            "data_fetch_wait": self.data_fetch_wait_time,
            "report_wait": self.report_generation_wait_time,
            "analysis_wait": self.analysis_wait_time
        }

    def validate_urls_accessible(self) -> Dict[str, Any]:
        """Validate that configured URLs are accessible (if enabled)"""
        if not os.getenv("VALIDATE_URLS", "").lower() in ("1", "true", "yes"):
            return {"enabled": False}
        
        results = {"enabled": True, "checks": []}
        
        urls_to_check = [
            ("base_url", self.base_url),
            ("api_base_url", self.api_base_url)
        ]
        
        for name, url in urls_to_check:
            if url:
                try:
                    import requests
                    response = requests.head(url, timeout=5)
                    results["checks"].append({
                        "name": name,
                        "url": url,
                        "status": "accessible" if response.status_code < 500 else "error",
                        "status_code": response.status_code
                    })
                except Exception as e:
                    results["checks"].append({
                        "name": name,
                        "url": url,
                        "status": "unreachable",
                        "error": str(e)
                    })
        
        return results

    def get_config_summary(self) -> Dict[str, Any]:
        return {
            "environment": self.environment,
            "loaded_files": self.loaded_files,
            "config_sources": self.config_sources,
            "base_url": self.base_url,
            "api_base_url": self.api_base_url,
            "timeout": self.timeout,
            "parallel_workers": self.parallel_workers,
            "redaction_enabled": self.redact_sensitive_data,
            "max_log_size": self.max_log_body_size,
            "has_test_data": bool(self.test_data),
        }


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()