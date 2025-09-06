import json
import csv
from pathlib import Path
from typing import Dict, Any, List
import time
from functools import wraps
from dataclasses import dataclass, field

@dataclass
class TestContext:
    data: Dict[str, Any] = field(default_factory=dict)
    def set(self, key: str, value: Any): self.data[key] = value
    def get(self, key: str, default: Any = None): return self.data.get(key, default)
    def clear(self): self.data.clear()

# # to go in conftest.py file
# import pytest
# from src.utils.helpers.context import TestContext

# @pytest.fixture
# def ctx() -> TestContext:
#     return TestContext()    

# usage in step definition
# def have_username(ctx: TestContext, username: str):
#     ctx.set("username", username)


def retry(times: int = 3, delay: float = 1.0):
    """Retry decorator"""

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(times):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == times - 1:
                        raise e
                    time.sleep(delay)
            return None

        return wrapper

    return decorator


def load_test_data(file_path: str) -> Dict[str, Any]:
    """Load test data from JSON file"""
    data_file = Path(file_path)
    if data_file.exists():
        with open(data_file, 'r') as f:
            return json.load(f)
    return {}


def save_test_data(data: Dict[str, Any], file_path: str):
    """Save test data to JSON file"""
    data_file = Path(file_path)
    data_file.parent.mkdir(parents=True, exist_ok=True)
    with open(data_file, 'w') as f:
        json.dump(data, f, indent=2, default=str)


def read_csv_data(file_path: str) -> List[Dict[str, str]]:
    """Read data from CSV file"""
    data = []
    with open(file_path, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            data.append(row)
    return data


def wait_for_condition(condition_func, timeout: int = 30, poll_interval: float = 0.5):
    """Wait for a condition to be true"""
    end_time = time.time() + timeout
    while time.time() < end_time:
        if condition_func():
            return True
        time.sleep(poll_interval)
    return False


# class TestContext:
#     """Shared test context for storing data between steps"""
#     _instance = None
#     _data = {}

#     def __new__(cls):
#         if cls._instance is None:
#             cls._instance = super(TestContext, cls).__new__(cls)
#         return cls._instance

#     def set(self, key: str, value: Any):
#         """Set value in context"""
#         self._data[key] = value

#     def get(self, key: str, default: Any = None):
#         """Get value from context"""
#         return self._data.get(key, default)

#     def clear(self):
#         """Clear all context data"""
#         self._data.clear()


def take_screenshot_on_failure(page, test_name: str):
    """Take screenshot when test fails"""
    screenshot_dir = Path("reports/screenshots")
    screenshot_dir.mkdir(parents=True, exist_ok=True)
    timestamp = int(time.time())
    screenshot_path = screenshot_dir / f"{test_name}_{timestamp}.png"
    page.screenshot(path=str(screenshot_path))
    return str(screenshot_path)