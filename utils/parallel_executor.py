import pytest
import subprocess
from pathlib import Path
from typing import List, Dict, Any
from config.parallel_config import ParallelConfig


class ParallelTestExecutor:
    """Advanced parallel test execution manager"""

    def __init__(self, environment: str):
        self.environment = environment
        self.config = ParallelConfig()

    def run_ui_tests_parallel(self, workers: int = None):
        """Run UI tests with optimal parallelization"""
        workers = workers or self.config.get_optimal_workers(self.environment, "ui")

        cmd = [
            "pytest",
            "--env", self.environment,
            "-m", "ui",
            "-n", str(workers),
            "--dist", "worksteal",
            "--headless"
        ]

        return subprocess.run(cmd, capture_output=True, text=True)

    def run_api_tests_parallel(self, workers: int = None):
        """Run API tests with high parallelization"""
        workers = workers or self.config.get_optimal_workers(self.environment, "api")

        cmd = [
            "pytest",
            "--env", self.environment,
            "-m", "api",
            "-n", str(workers),
            "--dist", "worksteal"
        ]

        return subprocess.run(cmd, capture_output=True, text=True)

    def run_mixed_tests_parallel(self, workers: int = None):
        """Run mixed UI/API tests with balanced parallelization"""
        workers = workers or self.config.get_optimal_workers(self.environment, "mixed")

        cmd = [
            "pytest",
            "--env", self.environment,
            "-m", "mixed",
            "-n", str(workers),
            "--dist", "loadscope"  # Better for mixed tests
        ]

        return subprocess.run(cmd, capture_output=True, text=True)

    def run_all_parallel(self):
        """Run all test types in parallel simultaneously"""
        import concurrent.futures

        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            ui_future = executor.submit(self.run_ui_tests_parallel)
            api_future = executor.submit(self.run_api_tests_parallel)
            mixed_future = executor.submit(self.run_mixed_tests_parallel)

            results = {
                "ui": ui_future.result(),
                "api": api_future.result(),
                "mixed": mixed_future.result()
            }

        return results


# Usage example
if __name__ == "__main__":
    executor = ParallelTestExecutor("staging")
    results = executor.run_all_parallel()

    for test_type, result in results.items():
        print(f"{test_type.upper()} Tests: {'PASSED' if result.returncode == 0 else 'FAILED'}")