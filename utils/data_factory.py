from faker import Faker
from typing import Dict, Any
import random
import uuid

fake = Faker()

class UserFactory:
    """Factory for generating user test data"""

    @staticmethod
    def create_user_data(override: Dict[str, Any] = None) -> Dict[str, Any]:
        """Create user data with optional overrides"""
        user_data = {
            "id": str(uuid.uuid4()),
            "username": fake.user_name(),
            "email": fake.email(),
            "first_name": fake.first_name(),
            "last_name": fake.last_name(),
            "phone": fake.phone_number(),
            "address": {
                "street": fake.street_address(),
                "city": fake.city(),
                "state": fake.state(),
                "zip_code": fake.zipcode(),
                "country": fake.country()
            },
            "date_of_birth": fake.date_of_birth(minimum_age=18, maximum_age=80).isoformat(),
            "created_at": fake.date_time_this_year().isoformat(),
            "is_active": True,
            "role": random.choice(["user", "admin", "moderator"])
        }

        if override:
            user_data.update(override)

        return user_data

    @staticmethod
    def create_multiple_users(count: int = 5) -> list:
        """Create multiple user records"""
        return [UserFactory.create_user_data() for _ in range(count)]

    @staticmethod
    def create_admin_user() -> Dict[str, Any]:
        """Create admin user data"""
        return UserFactory.create_user_data({"role": "admin", "is_active": True})

class ProductFactory:
    """Factory for generating product test data"""

    @staticmethod
    def create_product_data(override: Dict[str, Any] = None) -> Dict[str, Any]:
        """Create product data with optional overrides"""
        product_data = {
            "id": str(uuid.uuid4()),
            "name": fake.catch_phrase(),
            "description": fake.text(max_nb_chars=200),
            "price": round(random.uniform(10.00, 999.99), 2),
            "category": random.choice(["Electronics", "Clothing", "Books", "Home", "Sports"]),
            "sku": fake.ean13(),
            "stock_quantity": random.randint(0, 100),
            "manufacturer": fake.company(),
            "weight": round(random.uniform(0.1, 50.0), 2),
            "dimensions": {
                "length": round(random.uniform(1, 100), 2),
                "width": round(random.uniform(1, 100), 2),
                "height": round(random.uniform(1, 100), 2)
            },
            "is_available": True,
            "created_at": fake.date_time_this_year().isoformat()
        }

        if override:
            product_data.update(override)

        return product_data