# src/api/clients/auth_api.py
from ..base.base_api import BaseAPI
from typing import Any, Dict, Tuple


class AuthAPI(BaseAPI):
    def login(self, ctx, username: str, password: str) -> Tuple[int, Dict[str, Any]]:
    # def login(self, ctx, username: str, password: str):
        # return self._call(
        #     ctx=ctx,
        #     step="Auth: login",
        #     method="POST",
        #     endpoint="/login",
        #     req_json={"username": username, "password": password},
        # )
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
