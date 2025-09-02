import psutil
import time
import threading
from typing import Dict, List
import json


class ParallelExecutionMonitor:
    """Monitor system resources during parallel test execution"""

    def __init__(self):
        self.monitoring = False
        self.stats = []
        self.monitor_thread = None

    def start_monitoring(self, interval: float = 1.0):
        """Start resource monitoring"""
        self.monitoring = True
        self.monitor_thread = threading.Thread(
            target=self._monitor_resources,
            args=(interval,)
        )
        self.monitor_thread.start()

    def stop_monitoring(self):
        """Stop resource monitoring"""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join()

    def _monitor_resources(self, interval: float):
        """Monitor system resources"""
        while self.monitoring:
            stat = {
                "timestamp": time.time(),
                "cpu_percent": psutil.cpu_percent(interval=None),
                "memory_percent": psutil.virtual_memory().percent,
                "disk_io": psutil.disk_io_counters()._asdict(),
                "network_io": psutil.net_io_counters()._asdict(),
                "process_count": len(psutil.pids())
            }
            self.stats.append(stat)
            time.sleep(interval)

    def get_summary(self) -> Dict[str, Any]:
        """Get monitoring summary"""
        if not self.stats:
            return {}

        cpu_values = [s["cpu_percent"] for s in self.stats]
        memory_values = [s["memory_percent"] for s in self.stats]

        return {
            "duration_seconds": len(self.stats),
            "cpu_usage": {
                "avg": sum(cpu_values) / len(cpu_values),
                "max": max(cpu_values),
                "min": min(cpu_values)
            },
            "memory_usage": {
                "avg": sum(memory_values) / len(memory_values),
                "max": max(memory_values),
                "min": min(memory_values)
            },
            "peak_process_count": max(s["process_count"] for s in self.stats)
        }

    def save_stats(self, filename: str):
        """Save monitoring stats to file"""
        with open(filename, 'w') as f:
            json.dump({
                "stats": self.stats,
                "summary": self.get_summary()
            }, f, indent=2)


# Pytest plugin for monitoring
@pytest.fixture(scope="session", autouse=True)
def resource_monitor(request):
    """Monitor resources during test session"""
    if request.config.getoption("--monitor-resources", default=False):
        monitor = ParallelExecutionMonitor()
        monitor.start_monitoring()

        yield monitor

        monitor.stop_monitoring()
        summary = monitor.get_summary()

        print(f"\n=== Resource Usage Summary ===")
        print(f"Average CPU: {summary.get('cpu_usage', {}).get('avg', 0):.1f}%")
        print(f"Average Memory: {summary.get('memory_usage', {}).get('avg', 0):.1f}%")
        print(f"Peak Processes: {summary.get('peak_process_count', 0)}")

        # Save detailed stats
        monitor.save_stats("reports/resource_usage.json")
    else:
        yield None