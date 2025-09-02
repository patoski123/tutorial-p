from typing import Dict, Any
from config.settings import Settings


class ParallelConfig:
    """Parallel execution configuration per environment"""

    ENVIRONMENT_WORKERS = {
        "dev": 2,  # Slow execution for debugging
        "test": 4,  # Balanced execution
        "staging": 6,  # Fast pre-deployment testing
        "preprod": 8,  # High throughput validation
        "prod": 10  # Maximum safe concurrency
    }

    TEST_TYPE_WORKERS = {
        "ui": 4,  # UI tests - moderate parallelization
        "api": 8,  # API tests - high parallelization
        "mobile": 2,  # Mobile tests - limited by devices
        "mixed": 4,  # Mixed tests - balanced approach
        "performance": 1  # Performance tests - single worker
    }

    @staticmethod
    def get_optimal_workers(environment: str, test_type: str = None) -> int:
        """Get optimal worker count based on environment and test type"""
        env_workers = ParallelConfig.ENVIRONMENT_WORKERS.get(environment, 4)

        if test_type:
            type_workers = ParallelConfig.TEST_TYPE_WORKERS.get(test_type, 4)
            return min(env_workers, type_workers)

        return env_workers

    @staticmethod
    def get_parallel_args(environment: str, test_type: str = None) -> Dict[str, Any]:
        """Get pytest-xdist arguments for parallel execution"""
        workers = ParallelConfig.get_optimal_workers(environment, test_type)

        return {
            "numprocesses": workers,
            "dist": "worksteal",  # Load balancing
            "tx": [f"--env={environment}"]  # Pass environment to workers
        }