# src/api/clients/auth_api.py
from ..base.base_api import BaseAPI

class AuthAPI(BaseAPI):
    def login(self, ctx, username: str, password: str):
        return self._call(
            ctx=ctx,
            step="Auth: login",
            method="POST",
            endpoint="/login",
            req_json={"username": username, "password": password},
        )
