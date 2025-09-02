import time
import psutil
from typing import Dict, List, Any


class MetricsCollector:
    """Collect performance metrics during test execution"""

    def __init__(self):
        self.metrics = []
        self.start_time = None

    def start_collection(self):
        """Start metrics collection"""
        self.start_time = time.time()
        self.collect_baseline_metrics()

    def collect_baseline_metrics(self):
        """Collect baseline system metrics"""
        baseline = {
            "timestamp": time.time(),
            "type": "baseline",
            "cpu_percent": psutil.cpu_percent(),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_usage": psutil.disk_usage('/').percent,
            "network_io": psutil.net_io_counters()._asdict()
        }
        self.metrics.append(baseline)

    def record_response_time(self, operation: str, response_time_ms: float):
        """Record response time for specific operation"""
        metric = {
            "timestamp": time.time(),
            "type": "response_time",
            "operation": operation,
            "response_time_ms": response_time_ms,
            "elapsed_time": time.time() - self.start_time if self.start_time else 0
        }
        self.metrics.append(metric)

    def get_performance_summary(self) -> Dict[str, Any]:
        """Generate performance summary"""
        response_times = [m for m in self.metrics if m["type"] == "response_time"]

        if not response_times:
            return {"message": "No response time data collected"}

        times = [rt["response_time_ms"] for rt in response_times]

        return {
            "total_operations": len(response_times),
            "avg_response_time": sum(times) / len(times),
            "min_response_time": min(times),
            "max_response_time": max(times),
            "total_execution_time": response_times[-1]["elapsed_time"] if response_times else 0
        }