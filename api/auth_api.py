from api.base_api import BaseAPI
from typing import Dict, Tuple
import structlog

logger = structlog.get_logger(__name__)

class AuthAPI(BaseAPI):
    """Authentication API client"""

    def login(self, username: str, password: str) -> Tuple[bool, Dict]:
        """
        Login user and return success status and response data
        Returns: (success: bool, response_data: dict)
        """
        payload = {
            "username": username,
            "password": password
        }

        response = self.post("/auth/login", json=payload)

        if response.status_code == 200:
            data = response.json()
            if 'access_token' in data:
                self.set_auth_token(data['access_token'])
                logger.info("Login successful", username=username)
                return True, data

        logger.error("Login failed",
                     username=username,
                     status_code=response.status_code,
                     response=response.text)
        return False, response.json() if response.content else {}

    def logout(self) -> bool:
        """Logout current user"""
        response = self.post("/auth/logout")

        if response.status_code == 200:
            # Remove auth token
            if 'Authorization' in self.session.headers:
                del self.session.headers['Authorization']
            logger.info("Logout successful")
            return True

        logger.error("Logout failed", status_code=response.status_code)
        return False

    def refresh_token(self, refresh_token: str) -> Tuple[bool, Dict]:
        """Refresh access token"""
        payload = {"refresh_token": refresh_token}
        response = self.post("/auth/refresh", json=payload)

        if response.status_code == 200:
            data = response.json()
            if 'access_token' in data:
                self.set_auth_token(data['access_token'])
                logger.info("Token refresh successful")
                return True, data

        logger.error("Token refresh failed", status_code=response.status_code)
        return False, response.json() if response.content else {}

    def get_user_profile(self) -> Tuple[bool, Dict]:
        """Get current user profile"""
        response = self.get("/auth/profile")

        if response.status_code == 200:
            return True, response.json()

        logger.error("Get profile failed", status_code=response.status_code)
        return False, response.json() if response.content else {}