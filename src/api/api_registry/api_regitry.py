# If in the future there loads of API wrappers
#  refactor the code to use api_registry
# src/api/api_registry/api_registry.py

from ..wrappers.auth_api import AuthAPI
from ..wrappers.user_api import UserAPI
from ..wrappers.product_management_api import ProductManagementAPI

class APIRegistry:
    def __init__(self, api_executor):
        self._executor = api_executor
    
    @property
    def auth(self) -> AuthAPI:
        return AuthAPI(self._executor)
    
    @property
    def users(self) -> UserAPI:
        return UserAPI(self._executor)
    
    @property
    def products(self) -> ProductManagementAPI:
        return ProductManagementAPI(self._executor)

# In your steps
# from src.api.api_registry import APIRegistry

# @when("I get user details")
# def get_user_details(ctx, api_executor):
#     apis = APIRegistry(api_executor)  # Clear where this comes from
#     status, data = apis.users.get_user(ctx, ctx["user_id"])
#     ctx["resp_status"], ctx["resp_json"] = status, data