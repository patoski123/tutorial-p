from src.api.base.base_api import BaseAPI
from typing import Dict, Any
from src.utils.data_factory import DataFactory

class UserAPI(BaseAPI):
    """User management API wrapper"""

    def login(self, username: str, password: str):
        """Login and get authentication token"""
        response = self.post("/auth/login", {
            "username": username,
            "password": password
        })

        if response.status == 200:
            token = response.json().get("token")
            self.set_auth_token(token)
            return token

        return None

    def create_user(self, user_data: Dict[str, Any] = None):
        """Create new user"""
        if not user_data:
            user_data = DataFactory.generate_user_data()

        return self.post("/users", user_data)

    def get_user(self, user_id: str):
        """Get user by ID"""
        return self.get(f"/users/{user_id}")

    def get_all_users(self, page: int = 1, limit: int = 10):
        """Get all users with pagination"""
        params = {"page": page, "limit": limit}
        return self.get("/users", params=params)

    def update_user(self, user_id: str, update_data: Dict[str, Any]):
        """Update user"""
        return self.put(f"/users/{user_id}", update_data)

    def delete_user(self, user_id: str):
        """Delete user"""
        return self.delete(f"/users/{user_id}")

    def search_users(self, query: str):
        """Search users"""
        params = {"q": query}
        return self.get("/users/search", params=params)

    def get_user_profile(self, user_id: str):
        """Get user profile"""
        return self.get(f"/users/{user_id}/profile")

    def update_user_profile(self, user_id: str, profile_data: Dict[str, Any]):
        """Update user profile"""
        return self.put(f"/users/{user_id}/profile", profile_data)