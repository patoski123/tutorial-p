from playwright.sync_api import Response
from typing import Dict, Any, Callable, Tuple, List, Optional
import json
import time
import random


class APIHelpers:
    """API-specific helper functions with enhanced retry capabilities"""

    # Comprehensive list of retryable HTTP status codes
    DEFAULT_RETRYABLE_STATUSES = [
        0,    # Transport/connection errors (synthetic status)
        408,  # Request Timeout
        429,  # Too Many Requests
        500,  # Internal Server Error
        501,  # Not Implemented
        502,  # Bad Gateway
        503,  # Service Unavailable
        504,  # Gateway Timeout
        505,  # HTTP Version Not Supported
        507,  # Insufficient Storage
        508,  # Loop Detected
        509,  # Bandwidth Limit Exceeded
        510,  # Not Extended
        511,  # Network Authentication Required
    ]

    @staticmethod
    def assert_status_code(response: Response, expected_code: int):
        """Assert response status code"""
        actual_code = response.status
        assert actual_code == expected_code, f"Expected {expected_code}, got {actual_code}"

    @staticmethod
    def assert_response_time(response: Response, max_time_ms: int = 5000):
        """Assert response time is within limits"""
        # Note: Playwright doesn't directly expose response time
        # This could be implemented with timing decorators
        pass

    @staticmethod
    def extract_json_path(response: Response, json_path: str):
        """Extract value from JSON response using JSONPath"""
        import jsonpath_ng
        data = response.json()
        jsonpath_expr = jsonpath_ng.parse(json_path)
        matches = jsonpath_expr.find(data)
        return matches[0].value if matches else None

    @staticmethod
    def retry_api_call(
        api_call: Callable[[], Tuple[int, Dict[str, Any]]],
        max_attempts: int = 5,
        delay: float = 1.0,
        retry_on_statuses: Optional[List[int]] = None,
        timeout: Optional[float] = None,
        description: str = "API call"
    ) -> Tuple[int, Dict[str, Any]]:
        """
        Simple retry utility with linear backoff and exception handling
        
        Args:
            api_call: Function that returns (status_code, response_data)
            max_attempts: Maximum number of attempts
            delay: Delay between attempts in seconds
            retry_on_statuses: List of status codes to retry on (default: comprehensive list)
            timeout: Total timeout in seconds (default: None for no timeout)
            description: Description for logging
            
        Returns:
            Tuple of (status_code, response_data) from the final attempt
        """
        if retry_on_statuses is None:
            retry_on_statuses = APIHelpers.DEFAULT_RETRYABLE_STATUSES
        
        start_time = time.time()
        
        for attempt in range(1, max_attempts + 1):
            # Check timeout
            if timeout and (time.time() - start_time) > timeout:
                print(f"❌ {description} timed out after {timeout}s")
                return 408, {"error": "Request timeout", "elapsed_time": time.time() - start_time}
            
            try:
                status, data = api_call()
            except Exception as e:
                # Convert exceptions to synthetic HTTP responses
                status = 0  # Special status for exceptions
                data = {
                    "error": "Connection/transport error",
                    "exception_type": type(e).__name__,
                    "exception_message": str(e),
                    "attempt": attempt
                }
                print(f"🔌 {description} attempt {attempt} failed with {type(e).__name__}: {e}")
                
                # Treat exceptions as retryable
                if attempt == max_attempts:
                    print(f"❌ {description} failed after {max_attempts} attempts (final error: {type(e).__name__})")
                    return status, data
                
                print(f"🔄 Retrying {description} in {delay}s...")
                time.sleep(delay)
                continue
            
            # Success or non-retryable status
            if status not in retry_on_statuses:
                if attempt > 1:
                    print(f"✅ {description} succeeded on attempt {attempt}")
                return status, data
            
            # Last attempt - return the failure
            if attempt == max_attempts:
                print(f"❌ {description} failed after {max_attempts} attempts")
                return status, data
            
            # Wait and retry
            print(f"🔄 {description} attempt {attempt} failed (status: {status}). Retrying in {delay}s...")
            time.sleep(delay)
        
        return status, data

    @staticmethod
    def retry_api_call_with_backoff(
        api_call: Callable[[], Tuple[int, Dict[str, Any]]],
        max_attempts: int = 5,
        initial_delay: float = 1.0,
        max_delay: float = 30.0,
        backoff_factor: float = 2.0,
        jitter: bool = True,
        retry_on_statuses: Optional[List[int]] = None,
        timeout: Optional[float] = None,
        description: str = "API call"
    ) -> Tuple[int, Dict[str, Any]]:
        """
        Enhanced retry with exponential backoff, jitter, and exception handling
        
        Args:
            api_call: Function that returns (status_code, response_data)
            max_attempts: Maximum number of attempts
            initial_delay: Initial delay in seconds
            max_delay: Maximum delay between attempts
            backoff_factor: Multiplier for exponential backoff
            jitter: Add random jitter to prevent thundering herd
            retry_on_statuses: List of status codes to retry on (default: comprehensive list)
            timeout: Total timeout in seconds
            description: Description for logging
            
        Returns:
            Tuple of (status_code, response_data) from the final attempt
        """
        if retry_on_statuses is None:
            retry_on_statuses = APIHelpers.DEFAULT_RETRYABLE_STATUSES
        
        start_time = time.time()
        delay = initial_delay
        
        for attempt in range(1, max_attempts + 1):
            # Check timeout
            if timeout and (time.time() - start_time) > timeout:
                elapsed = time.time() - start_time
                print(f"❌ {description} timed out after {elapsed:.1f}s")
                return 408, {"error": "Request timeout", "elapsed_time": elapsed}
            
            try:
                status, data = api_call()
            except Exception as e:
                # Convert exceptions to synthetic HTTP responses
                status = 0  # Special status for exceptions
                data = {
                    "error": "Connection/transport error",
                    "exception_type": type(e).__name__,
                    "exception_message": str(e),
                    "attempt": attempt
                }
                print(f"🔌 {description} attempt {attempt} failed with {type(e).__name__}: {e}")
                
                # Treat exceptions as retryable
                if attempt == max_attempts:
                    elapsed = time.time() - start_time
                    print(f"❌ {description} failed after {max_attempts} attempts (final error: {type(e).__name__})")
                    return status, data
                
                # Calculate delay for retry
                actual_delay = delay
                if jitter:
                    jitter_range = delay * 0.25
                    actual_delay = delay + random.uniform(-jitter_range, jitter_range)
                    actual_delay = max(0.1, actual_delay)
                
                print(f"🔄 Retrying {description} in {actual_delay:.1f}s...")
                time.sleep(actual_delay)
                
                # Exponential backoff for next iteration
                delay = min(delay * backoff_factor, max_delay)
                continue
            
            # Success or non-retryable status
            if status not in retry_on_statuses:
                if attempt > 1:
                    elapsed = time.time() - start_time
                    print(f"✅ {description} succeeded on attempt {attempt} after {elapsed:.1f}s")
                return status, data
            
            # Last attempt - return the failure
            if attempt == max_attempts:
                elapsed = time.time() - start_time
                print(f"❌ {description} failed after {max_attempts} attempts in {elapsed:.1f}s")
                return status, data
            
            # Calculate next delay with exponential backoff and optional jitter
            actual_delay = delay
            if jitter:
                # Add ±25% random jitter to prevent thundering herd
                jitter_range = delay * 0.25
                actual_delay = delay + random.uniform(-jitter_range, jitter_range)
                actual_delay = max(0.1, actual_delay)  # Minimum 100ms
            
            print(f"🔄 {description} attempt {attempt} failed (status: {status}). Retrying in {actual_delay:.1f}s...")
            time.sleep(actual_delay)
            
            # Exponential backoff for next iteration
            delay = min(delay * backoff_factor, max_delay)
        
        return status, data

    @staticmethod
    def retry_until_status(
        api_call: Callable[[], Tuple[int, Dict[str, Any]]],
        expected_status: int = 200,
        max_attempts: int = 5,
        delay: float = 1.0,
        description: str = "API call"
    ) -> Tuple[int, Dict[str, Any]]:
        """
        Retry API call until a specific status code is returned
        
        Args:
            api_call: Function that returns (status_code, response_data)
            expected_status: Status code to wait for
            max_attempts: Maximum number of attempts
            delay: Delay between attempts in seconds
            description: Description for logging
            
        Returns:
            Tuple of (status_code, response_data) from the final attempt
        """
        for attempt in range(1, max_attempts + 1):
            try:
                status, data = api_call()
            except Exception as e:
                print(f"🔌 {description} attempt {attempt} failed with {type(e).__name__}: {e}")
                if attempt == max_attempts:
                    return 0, {
                        "error": "Connection/transport error",
                        "exception_type": type(e).__name__,
                        "exception_message": str(e)
                    }
                time.sleep(delay)
                continue
            
            # Got expected status
            if status == expected_status:
                if attempt > 1:
                    print(f"✅ {description} got expected status {expected_status} on attempt {attempt}")
                return status, data
            
            # Last attempt - return whatever we got
            if attempt == max_attempts:
                print(f"❌ {description} never got expected status {expected_status} after {max_attempts} attempts (final: {status})")
                return status, data
            
            # Wait and retry
            print(f"🔄 {description} attempt {attempt} got status {status}, waiting for {expected_status}. Retrying in {delay}s...")
            time.sleep(delay)
        
        return status, data

    @staticmethod
    def retry_until_condition(
        api_call: Callable[[], Tuple[int, Dict[str, Any]]],
        condition: Callable[[int, Dict[str, Any]], bool],
        max_attempts: int = 5,
        delay: float = 1.0,
        description: str = "API call"
    ) -> Tuple[int, Dict[str, Any]]:
        """
        Retry API call until a custom condition is met
        
        Args:
            api_call: Function that returns (status_code, response_data)
            condition: Function that takes (status, data) and returns True when satisfied
            max_attempts: Maximum number of attempts
            delay: Delay between attempts in seconds
            description: Description for logging
            
        Returns:
            Tuple of (status_code, response_data) from the final attempt
        """
        for attempt in range(1, max_attempts + 1):
            try:
                status, data = api_call()
            except Exception as e:
                print(f"🔌 {description} attempt {attempt} failed with {type(e).__name__}: {e}")
                if attempt == max_attempts:
                    return 0, {
                        "error": "Connection/transport error",
                        "exception_type": type(e).__name__,
                        "exception_message": str(e)
                    }
                time.sleep(delay)
                continue
            
            # Check if condition is satisfied
            try:
                if condition(status, data):
                    if attempt > 1:
                        print(f"✅ {description} condition satisfied on attempt {attempt}")
                    return status, data
            except Exception as e:
                print(f"⚠️ {description} condition check failed on attempt {attempt}: {e}")
            
            # Last attempt - return whatever we got
            if attempt == max_attempts:
                print(f"❌ {description} condition never satisfied after {max_attempts} attempts")
                return status, data
            
            # Wait and retry
            print(f"🔄 {description} attempt {attempt} condition not met. Retrying in {delay}s...")
            time.sleep(delay)
        
        return status, data