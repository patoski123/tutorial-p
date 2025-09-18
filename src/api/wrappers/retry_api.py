# src/api/retry_api.py - Enhanced API wrapper for retry testing with comprehensive functionality

from typing import Tuple, Dict, Any, Optional, List
from src.utils.api.api_helpers import APIHelpers


class RetryTestAPI:
    """Enhanced API wrapper for testing retry functionality with comprehensive options"""
    
    def __init__(self, api_executor):
        self.api_executor = api_executor
    
    def test_retry_endpoint(
        self, 
        ctx: dict, 
        max_failures: int = 3,
        endpoint_id: str = "default"
    ) -> Tuple[int, Dict[str, Any]]:
        """
        Test the retry endpoint without retry logic (will fail initially)
        """
        return self.api_executor(
            ctx=ctx,
            step="Retry Test: call endpoint",
            method="POST",
            path="/api/retry-test",
            req_json={
                "max_failures": max_failures,
                "endpoint_id": endpoint_id
            }
        )
    
    def test_retry_with_retry_logic(
        self, 
        ctx: dict, 
        max_failures: int = 3,
        endpoint_id: str = "default",
        max_attempts: int = 5,
        delay: float = 0.5,
        timeout: Optional[float] = 30.0,
        retry_on_statuses: Optional[List[int]] = None
    ) -> Tuple[int, Dict[str, Any]]:
        """
        Test the retry endpoint WITH linear retry logic and clean recording
        
        Args:
            ctx: Test context
            max_failures: Number of failures the mock endpoint should return before succeeding
            endpoint_id: Unique identifier for this test endpoint
            max_attempts: Maximum number of retry attempts
            delay: Fixed delay between attempts in seconds
            timeout: Total timeout for all attempts
            retry_on_statuses: Custom list of status codes to retry on
        """
        def api_call_silent():
            # Use thread-safe context manager for silent recording
            with self.api_executor.silent_recording():
                return self.api_executor(
                    ctx=ctx,
                    step=f"Retry Test: attempt call (endpoint_id: {endpoint_id})",
                    method="POST", 
                    path="/api/retry-test",
                    req_json={
                        "max_failures": max_failures,
                        "endpoint_id": endpoint_id
                    }
                )
        
        # Use enhanced retry with comprehensive status codes by default
        if retry_on_statuses is None:
            retry_on_statuses = [503]  # Keep simple for mock testing
        
        # Do retry with silent attempts
        status, data = APIHelpers.retry_api_call(
            api_call=api_call_silent,
            max_attempts=max_attempts,
            delay=delay,
            timeout=timeout,
            retry_on_statuses=retry_on_statuses,
            description=f"Retry test endpoint (id: {endpoint_id})"
        )
        
        # Record only the final result using enhanced recording method
        self.api_executor.record_final_retry_attempt(
            step="Retry Test: final result",
            method="POST",
            path="/api/retry-test",
            req_json={
                "max_failures": max_failures,
                "endpoint_id": endpoint_id
            },
            req_headers={"Accept": "application/json", "Content-Type": "application/json"}
        )
        
        return status, data

    def test_retry_with_exponential_backoff(
        self,
        ctx: dict,
        max_failures: int = 3,
        endpoint_id: str = "default",
        max_attempts: int = 5,
        initial_delay: float = 0.5,
        max_delay: float = 10.0,
        backoff_factor: float = 2.0,
        jitter: bool = True,
        timeout: Optional[float] = 30.0,
        retry_on_statuses: Optional[List[int]] = None
    ) -> Tuple[int, Dict[str, Any]]:
        """
        Test the retry endpoint WITH exponential backoff retry logic
        
        Args:
            ctx: Test context
            max_failures: Number of failures the mock endpoint should return before succeeding
            endpoint_id: Unique identifier for this test endpoint
            max_attempts: Maximum number of retry attempts
            initial_delay: Initial delay in seconds
            max_delay: Maximum delay between attempts
            backoff_factor: Multiplier for exponential backoff
            jitter: Whether to add random jitter to delays
            timeout: Total timeout for all attempts
            retry_on_statuses: Custom list of status codes to retry on
        """
        def api_call_silent():
            with self.api_executor.silent_recording():
                return self.api_executor(
                    ctx=ctx,
                    step=f"Retry Test: backoff attempt (endpoint_id: {endpoint_id})",
                    method="POST",
                    path="/api/retry-test",
                    req_json={
                        "max_failures": max_failures,
                        "endpoint_id": endpoint_id
                    }
                )
        
        if retry_on_statuses is None:
            retry_on_statuses = [503]  # Keep simple for mock testing
        
        # Use exponential backoff retry
        status, data = APIHelpers.retry_api_call_with_backoff(
            api_call=api_call_silent,
            max_attempts=max_attempts,
            initial_delay=initial_delay,
            max_delay=max_delay,
            backoff_factor=backoff_factor,
            jitter=jitter,
            timeout=timeout,
            retry_on_statuses=retry_on_statuses,
            description=f"Retry test with backoff (id: {endpoint_id})"
        )
        
        # Record final result
        self.api_executor.record_final_retry_attempt(
            step="Retry Test: backoff final result",
            method="POST",
            path="/api/retry-test",
            req_json={
                "max_failures": max_failures,
                "endpoint_id": endpoint_id
            },
            req_headers={"Accept": "application/json", "Content-Type": "application/json"}
        )
        
        return status, data

    def test_retry_until_success(
        self,
        ctx: dict,
        max_failures: int = 3,
        endpoint_id: str = "default",
        max_attempts: int = 5,
        delay: float = 1.0
    ) -> Tuple[int, Dict[str, Any]]:
        """
        Test retry until specific success status (200) is returned
        """
        def api_call_silent():
            with self.api_executor.silent_recording():
                return self.api_executor(
                    ctx=ctx,
                    step=f"Retry Test: until success (endpoint_id: {endpoint_id})",
                    method="POST",
                    path="/api/retry-test",
                    req_json={
                        "max_failures": max_failures,
                        "endpoint_id": endpoint_id
                    }
                )
        
        status, data = APIHelpers.retry_until_status(
            api_call=api_call_silent,
            expected_status=200,
            max_attempts=max_attempts,
            delay=delay,
            description=f"Retry until success (id: {endpoint_id})"
        )
        
        # Record final result
        self.api_executor.record_final_retry_attempt(
            step="Retry Test: until success final result",
            method="POST",
            path="/api/retry-test",
            req_json={
                "max_failures": max_failures,
                "endpoint_id": endpoint_id
            },
            req_headers={"Accept": "application/json", "Content-Type": "application/json"}
        )
        
        return status, data

    def test_retry_with_custom_condition(
        self,
        ctx: dict,
        max_failures: int = 3,
        endpoint_id: str = "default",
        max_attempts: int = 5,
        delay: float = 1.0
    ) -> Tuple[int, Dict[str, Any]]:
        """
        Test retry with custom success condition
        """
        def api_call_silent():
            with self.api_executor.silent_recording():
                return self.api_executor(
                    ctx=ctx,
                    step=f"Retry Test: custom condition (endpoint_id: {endpoint_id})",
                    method="POST",
                    path="/api/retry-test",
                    req_json={
                        "max_failures": max_failures,
                        "endpoint_id": endpoint_id
                    }
                )
        
        def success_condition(status: int, data: Dict[str, Any]) -> bool:
            """Custom condition: success when status is 200 AND response contains 'Successful'"""
            return status == 200 and isinstance(data, dict) and data.get("status") == "Successful"
        
        status, data = APIHelpers.retry_until_condition(
            api_call=api_call_silent,
            condition=success_condition,
            max_attempts=max_attempts,
            delay=delay,
            description=f"Retry with custom condition (id: {endpoint_id})"
        )
        
        # Record final result
        self.api_executor.record_final_retry_attempt(
            step="Retry Test: custom condition final result",
            method="POST",
            path="/api/retry-test",
            req_json={
                "max_failures": max_failures,
                "endpoint_id": endpoint_id
            },
            req_headers={"Accept": "application/json", "Content-Type": "application/json"}
        )
        
        return status, data

    def test_comprehensive_retry_scenarios(
        self,
        ctx: dict,
        scenario: str = "linear"
    ) -> Tuple[int, Dict[str, Any]]:
        """
        Test comprehensive retry scenarios for demonstration
        
        Args:
            ctx: Test context
            scenario: Type of retry scenario ('linear', 'exponential', 'until_success', 'custom_condition')
        """
        endpoint_id = f"comprehensive_{scenario}"
        
        if scenario == "linear":
            return self.test_retry_with_retry_logic(
                ctx=ctx,
                max_failures=2,
                endpoint_id=endpoint_id,
                max_attempts=4,
                delay=0.5,
                timeout=15.0
            )
        elif scenario == "exponential":
            return self.test_retry_with_exponential_backoff(
                ctx=ctx,
                max_failures=3,
                endpoint_id=endpoint_id,
                max_attempts=5,
                initial_delay=0.5,
                max_delay=8.0,
                backoff_factor=2.0,
                jitter=True,
                timeout=20.0
            )
        elif scenario == "until_success":
            return self.test_retry_until_success(
                ctx=ctx,
                max_failures=2,
                endpoint_id=endpoint_id,
                max_attempts=5,
                delay=1.0
            )
        elif scenario == "custom_condition":
            return self.test_retry_with_custom_condition(
                ctx=ctx,
                max_failures=2,
                endpoint_id=endpoint_id,
                max_attempts=4,
                delay=0.8
            )
        else:
            raise ValueError(f"Unknown scenario: {scenario}. Use 'linear', 'exponential', 'until_success', or 'custom_condition'")

    def reset_endpoint_state(self, endpoint_id: str) -> None:
        """
        Reset the state for a specific endpoint (useful for testing)
        This is a convenience method that calls the router's reset function
        """
        try:
            # Import here to avoid circular imports
            from src.api.execution.router import reset_retry_attempts
            reset_retry_attempts()
            print(f"✅ Reset state for endpoint ID: {endpoint_id}")
        except ImportError:
            print(f"⚠️ Could not reset state for endpoint ID: {endpoint_id} - reset function not available")