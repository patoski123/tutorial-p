import os
from typing import Optional, Dict, Any
from dataclasses import dataclass
from pathlib import Path
import yaml
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

@dataclass
class APIConfig:
    base_url: str
    timeout: int = 30
    retries: int = 3
    verify_ssl: bool = True

@dataclass
class UIConfig:
    headless: bool = False
    browser: str = "chromium"
    slow_mo: int = 0
    viewport_width: int = 1920
    viewport_height: int = 1080

@dataclass
class MobileConfig:
    platform: str = "Android"
    device_name: str = "Pixel 6"
    app_package: Optional[str] = None
    app_activity: Optional[str] = None

@dataclass
class PerformanceConfig:
    users: int = 10
    spawn_rate: int = 2
    run_time: str = "5m"

class Config:
    """Central configuration management"""

    def __init__(self, env: str = None):
        self.env = env or os.getenv('TEST_ENV', 'local')
        self.project_root = Path(__file__).parent.parent
        self._load_config()

    def _load_config(self):
        """Load configuration from files and environment"""
        config_file = self.project_root / 'data' / f'{self.env}_config.yaml'

        if config_file.exists():
            with open(config_file, 'r') as f:
                file_config = yaml.safe_load(f) or {}
        else:
            file_config = {}

        # API Configuration
        self.api = APIConfig(
            base_url=os.getenv('API_BASE_URL', file_config.get('api', {}).get('base_url', 'https://api.example.com')),
            timeout=int(os.getenv('API_TIMEOUT', file_config.get('api', {}).get('timeout', 30))),
            retries=int(os.getenv('API_RETRIES', file_config.get('api', {}).get('retries', 3))),
            verify_ssl=os.getenv('API_VERIFY_SSL', 'true').lower() == 'true'
        )

        # UI Configuration
        self.ui = UIConfig(
            headless=os.getenv('UI_HEADLESS', 'false').lower() == 'true',
            browser=os.getenv('UI_BROWSER', file_config.get('ui', {}).get('browser', 'chromium')),
            slow_mo=int(os.getenv('UI_SLOW_MO', file_config.get('ui', {}).get('slow_mo', 0))),
            viewport_width=int(os.getenv('UI_VIEWPORT_WIDTH', '1920')),
            viewport_height=int(os.getenv('UI_VIEWPORT_HEIGHT', '1080'))
        )

        # Mobile Configuration
        self.mobile = MobileConfig(
            platform=os.getenv('MOBILE_PLATFORM', 'Android'),
            device_name=os.getenv('MOBILE_DEVICE', 'Pixel 6'),
            app_package=os.getenv('MOBILE_APP_PACKAGE'),
            app_activity=os.getenv('MOBILE_APP_ACTIVITY')
        )

        # Performance Configuration
        self.performance = PerformanceConfig(
            users=int(os.getenv('PERF_USERS', '10')),
            spawn_rate=int(os.getenv('PERF_SPAWN_RATE', '2')),
            run_time=os.getenv('PERF_RUN_TIME', '5m')
        )

        # Test Credentials
        self.test_user = {
            'username': os.getenv('TEST_USERNAME', 'testuser@example.com'),
            'password': os.getenv('TEST_PASSWORD', 'testpassword'),
            'api_key': os.getenv('TEST_API_KEY', '')
        }

        # Database Configuration
        self.database = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'port': int(os.getenv('DB_PORT', '5432')),
            'name': os.getenv('DB_NAME', 'testdb'),
            'username': os.getenv('DB_USERNAME', 'testuser'),
            'password': os.getenv('DB_PASSWORD', 'testpass')
        }

# Global config instance
config = Config()