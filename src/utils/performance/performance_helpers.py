import time
import statistics
from typing import List, Dict, Any, Callable
import structlog

logger = structlog.get_logger(__name__)

class PerformanceMetrics:
    """Utility class for performance measurements"""

    def __init__(self):
        self.response_times = []
        self.error_count = 0
        self.success_count = 0

    def measure_response_time(self, func: Callable, *args, **kwargs) -> tuple:
        """Measure function execution time"""
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            end_time = time.time()
            response_time = end_time - start_time

            self.response_times.append(response_time)
            self.success_count += 1

            logger.info("Performance measurement",
                        function=func.__name__,
                        response_time=response_time,
                        success=True)

            return result, response_time

        except Exception as e:
            end_time = time.time()
            response_time = end_time - start_time

            self.error_count += 1
            logger.error("Performance measurement failed",
                         function=func.__name__,
                         response_time=response_time,
                         error=str(e))

            raise e

    def get_statistics(self) -> Dict[str, Any]:
        """Get performance statistics"""
        if not self.response_times:
            return {"error": "No measurements recorded"}

        return {
            "total_requests": len(self.response_times),
            "successful_requests": self.success_count,
            "failed_requests": self.error_count,
            "success_rate": (self.success_count / (self.success_count + self.error_count)) * 100,
            "avg_response_time": statistics.mean(self.response_times),
            "min_response_time": min(self.response_times),
            "max_response_time": max(self.response_times),
            "median_response_time": statistics.median(self.response_times),
            "p95_response_time": self._percentile(self.response_times, 95),
            "p99_response_time": self._percentile(self.response_times, 99)
        }

    def _percentile(self, data: List[float], percentile: float) -> float:
        """Calculate percentile"""
        sorted_data = sorted(data)
        index = (percentile / 100) * (len(sorted_data) - 1)

        if index.is_integer():
            return sorted_data[int(index)]
        else:
            lower_index = int(index)
            upper_index = lower_index + 1
            weight = index - lower_index
            return sorted_data[lower_index] * (1 - weight) + sorted_data[upper_index] * weight

def benchmark_api_endpoint(api_client, endpoint: str, method: str = "GET",
                           iterations: int = 100, **kwargs) -> Dict[str, Any]:
    """Benchmark API endpoint performance"""
    metrics = PerformanceMetrics()

    logger.info("Starting API benchmark", endpoint=endpoint, iterations=iterations)

    for i in range(iterations):
        try:
            if method.upper() == "GET":
                metrics.measure_response_time(api_client.get, endpoint, **kwargs)
            elif method.upper() == "POST":
                metrics.measure_response_time(api_client.post, endpoint, **kwargs)
            elif method.upper() == "PUT":
                metrics.measure_response_time(api_client.put, endpoint, **kwargs)
            elif method.upper() == "DELETE":
                metrics.measure_response_time(api_client.delete, endpoint, **kwargs)

        except Exception as e:
            logger.warning("Benchmark iteration failed", iteration=i, error=str(e))
            continue

    results = metrics.get_statistics()
    logger.info("API benchmark completed", results=results)
    return results