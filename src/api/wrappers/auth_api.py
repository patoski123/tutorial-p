from ..base.base_api import BaseAPI
from typing import Any, Dict, Tuple, Optional
from src.utils.api.api_helpers import APIHelpers


class AuthAPI(BaseAPI):
    def login(self, ctx, username: str, password: str) -> Tuple[int, Dict[str, Any]]:
        """
        Original login method without retry logic
        """
        status, data = self._call(
            ctx=ctx,
            step="Auth: login",
            method="POST",
            endpoint="/login",
            req_json={"username": username, "password": password},
        )
        if status == 200 and isinstance(data, dict) and "access_token" in data:
            self.set_auth_token(data["access_token"])
        return status, data

    def login_with_retry(self, ctx, username: str, password: str, max_attempts: int = 5, delay: float = 2.0) -> Tuple[int, Dict[str, Any]]:
        """
        Login method with retry logic for when auth service is temporarily unavailable
        
        Args:
            ctx: Test context
            username: Username for login
            password: Password for login
            max_attempts: Maximum number of login attempts (default: 5)
            delay: Delay between retry attempts in seconds (default: 2.0)
        
        Returns:
            Tuple of (status_code, response_data)
        """
        def attempt_login():
            status, data = self._call(
                ctx=ctx,
                step="Auth: login attempt",
                method="POST",
                endpoint="/login",
                req_json={"username": username, "password": password},
            )
            return status, data
        
        def is_login_successful(status: int, data: Dict[str, Any]) -> bool:
            """
            Check if login was successful based on response
            
            Returns True when:
            - Status is 200 AND has access_token (successful login)
            - Status is 401/403 (invalid credentials - don't retry)
            - Status is 400 (bad request - don't retry)
            
            Returns False when:
            - Status indicates service unavailable (should retry)
            - Response indicates "Running" status (service starting up)
            """
            # Successful login
            if status == 200 and isinstance(data, dict) and "access_token" in data:
                return True
            
            # Authentication/authorization errors - don't retry these
            if status in [401, 403, 400]:
                return True
            
            # Check for "Running" status in response (service not ready)
            if isinstance(data, dict) and data.get("status") == "Running":
                return False
            
            # Server errors that might be temporary - retry these
            if status in [500, 502, 503, 504]:
                return False
            
            # For any other status, don't retry
            return True
        
        # Use retry_until_condition for more sophisticated logic
        status, data = APIHelpers.retry_until_condition(
            api_call=attempt_login,
            condition=is_login_successful,
            max_attempts=max_attempts,
            delay=delay,
            description=f"Login for user '{username}'"
        )
        
        # Set auth token if login was successful
        if status == 200 and isinstance(data, dict) and "access_token" in data:
            self.set_auth_token(data["access_token"])
        
        return status, data

    def login_simple_retry(self, ctx, username: str, password: str, max_attempts: int = 3) -> Tuple[int, Dict[str, Any]]:
        """
        Simpler version - just retry on 503 status codes
        """
        def attempt_login():
            status, data = self._call(
                ctx=ctx,
                step="Auth: login attempt",
                method="POST", 
                endpoint="/login",
                req_json={"username": username, "password": password},
            )
            return status, data
        
        status, data = APIHelpers.retry_api_call(
            api_call=attempt_login,
            max_attempts=max_attempts,
            retry_on_statuses=[503],  # Service Unavailable
            delay=1.5,
            description=f"Simple login retry for '{username}'"
        )
        
        # Set auth token if successful
        if status == 200 and isinstance(data, dict) and "access_token" in data:
            self.set_auth_token(data["access_token"])
        
        return status, data
    
    def get_list_instance_with_retry(self, ctx, username: str, password: str, endpoint: str, 
                               payload: Optional[Dict[str, Any]] = None, 
                               max_attempts: int = 5, 
                               timeout: float = 30.0) -> Tuple[int, Dict[str, Any]]:
        """Get list instance with retry logic and clean recording"""
    
        def attempt_get_list_silent():
            # Use thread-safe context manager for silent recording
            with self._executor.silent_recording():
                return self._call(
                    ctx=ctx,
                    step="Get list instance attempt",
                    method="GET",
                    endpoint=endpoint,
                    req_json=payload,
                    req_headers={"Authorization": f"Basic {self._encoded_credentials(username, password)}"}
                )
    
        # Do retry with silent attempts
        status, data = APIHelpers.retry_api_call(
            api_call=attempt_get_list_silent,
            max_attempts=max_attempts,
            timeout=timeout,
            delay=1.0,  # Fixed typo: was "elay"
            description=f"Get list instance {endpoint}"
        )
    
        # Record only the final result using enhanced method
        if hasattr(self, '_executor'):
            self._executor.record_final_retry_attempt(
            step="Get list instance request",
            method="GET",
            path=endpoint,
            req_json=payload,
            req_headers={"Authorization": f"Basic {self._encoded_credentials(username, password)}"}
        )
    
        return status, data
    
    def get_list_instance_with_exponential_retry(self, ctx, username: str, password: str, endpoint: str,
                                           payload: Optional[Dict[str, Any]] = None,
                                           max_attempts: int = 5,
                                           initial_delay: float = 1.0,
                                           timeout: float = 30.0) -> Tuple[int, Dict[str, Any]]:
    
        def attempt_get_list_silent():
            with self._executor.silent_recording():
                return self._call(...)
    
        status, data = APIHelpers.retry_api_call_with_backoff(
            api_call=attempt_get_list_silent,
            max_attempts=max_attempts,
            initial_delay=initial_delay,
            timeout=timeout,
            description=f"Get list instance with backoff {endpoint}"
        )
    
        if hasattr(self, '_executor'):
            self._executor.record_final_retry_attempt(...)
    
        return status, data
    
    
    # def get_list_instance_with_retry(self, ctx, username: str, password: str, endpoint: str, 
    #                            payload: Optional[Dict[str, Any]] = None, 
    #                            max_attempts: int = 5, 
    #                            timeout: float = 30.0) -> Tuple[int, Dict[str, Any]]:
    
    #     def attempt_get_list():
    #         return self._call(...)
    
    #     return APIHelpers.retry_api_call(
    #         api_call=attempt_get_list,
    #         max_attempts=max_attempts,
    #         timeout=timeout,
    #         retry_on_statuses=[503],
    #         delay=1.0,
    #         description=f"Get list instance {endpoint}"
    #     )
    
    # def get_list_instance_with_retry(self, ctx, username: str, password: str, endpoint: str, 
    #                            payload: Optional[Dict[str, Any]] = None, max_attempts: int = 5) -> Tuple[int, Dict[str, Any]]:
    #     """Get list instance with retry logic"""
    
    #     def attempt_get_list():
    #         return self._call(
    #             ctx=ctx,
    #             step="Get list instance attempt",
    #             method="GET",
    #             endpoint=endpoint,
    #             req_json=payload,
    #             req_headers={"Authorization": f"Basic {self._encoded_credentials(username, password)}"}
    #         )
    
    #     return APIHelpers.retry_api_call(
    #         api_call=attempt_get_list,
    #         max_attempts=max_attempts,
    #         retry_on_statuses=[503],
    #         delay=1.0,
    #         description=f"Get list instance {endpoint}"
    #     )
