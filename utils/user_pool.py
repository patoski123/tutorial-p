import threading
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from queue import Queue
import time


@dataclass
class TestUser:
    username: str
    password: str
    role: str
    email: str
    status: str = "available"
    worker_id: str = None
    last_used: float = None


class UserPoolManager:
    """Manage pool of test users for parallel execution"""

    def __init__(self, users: List[Dict[str, Any]]):
        self._users = Queue()
        self._used_users = {}
        self._lock = threading.Lock()

        # Initialize user pool
        for user_data in users:
            user = TestUser(
                username=user_data["username"],
                password=user_data["password"],
                role=user_data.get("role", "user"),
                email=user_data.get("email", f"{user_data['username']}@example.com")
            )
            self._users.put(user)

    def get_user(self, role: str = None, worker_id: str = None) -> Optional[TestUser]:
        """Get available user from pool"""
        with self._lock:
            available_users = []

            # Collect all users from queue
            while not self._users.empty():
                user = self._users.get()
                available_users.append(user)

            # Find matching user
            selected_user = None
            for user in available_users:
                if role is None or user.role == role:
                    selected_user = user
                    selected_user.status = "in_use"
                    selected_user.worker_id = worker_id
                    selected_user.last_used = time.time()
                    self._used_users[user.username] = selected_user
                    break
                else:
                    # Put back non-matching users
                    self._users.put(user)

            # Put back remaining users
            for user in available_users:
                if user != selected_user:
                    self._users.put(user)

            return selected_user

    def return_user(self, username: str):
        """Return user to available pool"""
        with self._lock:
            if username in self._used_users:
                user = self._used_users.pop(username)
                user.status = "available"
                user.worker_id = None
                self._users.put(user)

    def get_user_stats(self) -> Dict[str, Any]:
        """Get user pool statistics"""
        with self._lock:
            return {
                "available": self._users.qsize(),
                "in_use": len(self._used_users),
                "total": self._users.qsize() + len(self._used_users)
            }


# Global user pool
user_pool = None


@pytest.fixture(scope="session", autouse=True)
def setup_user_pool(settings):
    """Initialize global user pool"""
    global user_pool
    users = settings.test_data.get("users", [])

    # Add default users if none provided
    if not users:
        users = [
            {"username": f"testuser{i}", "password": "testpass", "role": "user"}
            for i in range(1, 11)  # 10 default users
        ]

    user_pool = UserPoolManager(users)
    yield user_pool


@pytest.fixture
def unique_test_user(setup_user_pool, worker_id, request):
    """Get unique test user for parallel execution"""
    role = request.param if hasattr(request, 'param') else None
    user = user_pool.get_user(role=role, worker_id=worker_id)

    if not user:
        pytest.skip(f"No available test user with role: {role}")

    yield user

    # Return user to pool after test
    user_pool.return_user(user.username)