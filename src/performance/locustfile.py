from locust import HttpUser, task, between
import json
import random
from src.config.settings import Settings

settings = Settings()

class WebsiteUser(HttpUser):
    wait_time = between(1, 3)
    host = settings.base_url

    def on_start(self):
        """Login before starting tests"""
        response = self.client.post("/api/auth/login", json={
            "username": settings.test_username,
            "password": settings.test_password
        })
        if response.status_code == 200:
            self.auth_token = response.json().get("token")
        else:
            self.auth_token = None

    @task(3)
    def view_homepage(self):
        """View homepage - highest weight"""
        self.client.post("/users", json=user_data, headers=self.headers)

    @task(1)
    def update_user(self):
        user_id = random.randint(1, 100)
        update_data = {"name": f"updated_user_{random.randint(1000, 9999)}"}
        self.client.put(f"/users/{user_id}", json=update_data, headers=self.headers)

    @task(1)
    def delete_user(self):
        user_id = random.randint(1, 100)
        self.client.delete(f"/users/{user_id}", headers=self.headers)