import requests
import structlog
from typing import Dict, Any, Optional, Union
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from utils.config import config

logger = structlog.get_logger(__name__)

class BaseAPI:
    """Base API client with common functionality"""

    def __init__(self, base_url: str = None):
        self.base_url = base_url or config.api.base_url
        self.session = self._create_session()

    def _create_session(self) -> requests.Session:
        """Create requests session with retry strategy"""
        session = requests.Session()

        # Retry strategy
        retry_strategy = Retry(
            total=config.api.retries,
            status_forcelist=[429, 500, 502, 503, 504],
            backoff_factor=1
        )

        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)

        # Default headers
        session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'User-Agent': 'Test-Automation-Framework/1.0'
        })

        return session

    def set_auth_token(self, token: str):
        """Set authorization token"""
        self.session.headers.update({'Authorization': f'Bearer {token}'})

    def set_api_key(self, api_key: str):
        """Set API key"""
        self.session.headers.update({'X-API-Key': api_key})

    def get(self, endpoint: str, params: Dict = None, **kwargs) -> requests.Response:
        """GET request"""
        url = f"{self.base_url.rstrip('/')}/{endpoint.lstrip('/')}"
        logger.info("GET request", url=url, params=params)

        response = self.session.get(
            url,
            params=params,
            timeout=config.api.timeout,
            verify=config.api.verify_ssl,
            **kwargs
        )

        logger.info("GET response",
                    status_code=response.status_code,
                    response_time=response.elapsed.total_seconds())
        return response

    def post(self, endpoint: str, data: Dict = None, json: Dict = None, **kwargs) -> requests.Response:
        """POST request"""
        url = f"{self.base_url.rstrip('/')}/{endpoint.lstrip('/')}"
        logger.info("POST request", url=url, data=data, json=json)

        response = self.session.post(
            url,
            data=data,
            json=json,
            timeout=config.api.timeout,
            verify=config.api.verify_ssl,
            **kwargs
        )

        logger.info("POST response",
                    status_code=response.status_code,
                    response_time=response.elapsed.total_seconds())
        return response

    def put(self, endpoint: str, data: Dict = None, json: Dict = None, **kwargs) -> requests.Response:
        """PUT request"""
        url = f"{self.base_url.rstrip('/')}/{endpoint.lstrip('/')}"
        logger.info("PUT request", url=url, data=data, json=json)

        response = self.session.put(
            url,
            data=data,
            json=json,
            timeout=config.api.timeout,
            verify=config.api.verify_ssl,
            **kwargs
        )

        logger.info("PUT response",
                    status_code=response.status_code,
                    response_time=response.elapsed.total_seconds())
        return response

    def delete(self, endpoint: str, **kwargs) -> requests.Response:
        """DELETE request"""
        url = f"{self.base_url.rstrip('/')}/{endpoint.lstrip('/')}"
        logger.info("DELETE request", url=url)

        response = self.session.delete(
            url,
            timeout=config.api.timeout,
            verify=config.api.verify_ssl,
            **kwargs
        )

        logger.info("DELETE response",
                    status_code=response.status_code,
                    response_time=response.elapsed.total_seconds())
        return response

    def assert_status_code(self, response: requests.Response, expected_code: int):
        """Assert response status code"""
        assert response.status_code == expected_code, (
            f"Expected status code {expected_code}, got {response.status_code}. "
            f"Response: {response.text}"
        )

    def assert_response_time(self, response: requests.Response, max_time: float):
        """Assert response time is under threshold"""
        response_time = response.elapsed.total_seconds()
        assert response_time <= max_time, (
            f"Response time {response_time}s exceeded maximum {max_time}s"
        )