from faker import Faker
import random
import string
from datetime import datetime, timedelta

fake = Faker()


class DataFactory:
    """Generate test data"""

    @staticmethod
    def generate_user_data():
        """Generate random user data"""
        return {
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
            }
        }

    @staticmethod
    def generate_product_data():
        """Generate random product data"""
        return {
            "name": fake.catch_phrase(),
            "description": fake.text(max_nb_chars=200),
            "price": round(random.uniform(10.0, 1000.0), 2),
            "category": random.choice(["Electronics", "Clothing", "Books", "Home", "Sports"]),
            "sku": ''.join(random.choices(string.ascii_uppercase + string.digits, k=8)),
            "in_stock": random.choice([True, False])
        }

    @staticmethod
    def generate_order_data():
        """Generate random order data"""
        return {
            "order_id": ''.join(random.choices(string.ascii_uppercase + string.digits, k=10)),
            "user_id": random.randint(1, 1000),
            "items": [
                {
                    "product_id": random.randint(1, 100),
                    "quantity": random.randint(1, 5),
                    "price": round(random.uniform(10.0, 100.0), 2)
                }
                for _ in range(random.randint(1, 3))
            ],
            "order_date": fake.date_time_between(start_date="-30d", end_date="now"),
            "status": random.choice(["pending", "processing", "shipped", "delivered"])
        }

    @staticmethod
    def generate_random_string(length: int = 10):
        """Generate random string"""
        return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

    @staticmethod
    def generate_random_email():
        """Generate random email"""
        return f"{DataFactory.generate_random_string(8)}@example.com"