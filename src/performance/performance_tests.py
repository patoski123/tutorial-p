import subprocess
import time
from pathlib import Path
from src.config.settings import Settings
from src.utils.logger import get_logger

logger = get_logger(__name__)


class PerformanceTestRunner:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.results_dir = Path("reports/performance")
        self.results_dir.mkdir(parents=True, exist_ok=True)

    def run_web_performance_test(self):
        """Run web application performance test"""
        cmd = [
            "locust",
            "-f", "performance/locustfile.py",
            "--host", self.settings.base_url,
            "--users", str(self.settings.performance_users),
            "--spawn-rate", str(self.settings.performance_spawn_rate),
            "--run-time", self.settings.performance_run_time,
            "--html", str(self.results_dir / "web_performance_report.html"),
            "--csv", str(self.results_dir / "web_performance"),
            "--headless"
        ]

        logger.info(f"Starting web performance test with {self.settings.performance_users} users")
        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode == 0:
            logger.info("Web performance test completed successfully")
        else:
            logger.error(f"Web performance test failed: {result.stderr}")

        return result.returncode == 0

    def run_api_performance_test(self):
        """Run API performance test"""
        cmd = [
            "locust",
            "-f", "performance/locustfile.py",
            "APIUser",
            "--host", self.settings.api_base_url,
            "--users", str(self.settings.performance_users),
            "--spawn-rate", str(self.settings.performance_spawn_rate),
            "--run-time", self.settings.performance_run_time,
            "--html", str(self.results_dir / "api_performance_report.html"),
            "--csv", str(self.results_dir / "api_performance"),
            "--headless"
        ]

        logger.info(f"Starting API performance test")
        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode == 0:
            logger.info("API performance test completed successfully")
        else:
            logger.error(f"API performance test failed: {result.stderr}")

        return result.returncode == 0

    def analyze_results(self):
        """Analyze performance test results"""
        web_stats_file = self.results_dir / "web_performance_stats.csv"
        api_stats_file = self.results_dir / "api_performance_stats.csv"

        results = {}

        if web_stats_file.exists():
            results["web"] = self._parse_stats_file(web_stats_file)

        if api_stats_file.exists():
            results["api"] = self._parse_stats_file(api_stats_file)

        return results

    def _parse_stats_file(self, stats_file: Path):
        """Parse Locust stats CSV file"""
        import pandas as pd

        df = pd.read_csv(stats_file)
        summary = {
            "total_requests": df["Request Count"].sum(),
            "failure_count": df["Failure Count"].sum(),
            "average_response_time": df["Average Response Time"].mean(),
            "min_response_time": df["Min Response Time"].min(),
            "max_response_time": df["Max Response Time"].max(),
            "requests_per_second": df["Requests/s"].mean()
        }

        return summary