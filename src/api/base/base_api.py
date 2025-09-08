# Thin façade that delegates to the executor:

from __future__ import annotations
from typing import Any, Dict, Tuple, Optional

class BaseAPI:
    def __init__(self, api_executor, base_path: str = ""):
        self._exec = api_executor
        self._base = base_path.rstrip("/")
        self._token: Optional[str] = None

    def set_auth_token(self, token: str) -> None:
        self._token = token

    def _auth_headers(self, extra: Dict[str, str] | None = None) -> Dict[str, str]:
        h = {"Accept":"application/json","Content-Type":"application/json"}
        if self._token:
            h["Authorization"] = f"Bearer {self._token}"
        if extra:
            h.update(extra)
        return h

    def _call(self, ctx: dict, step: str, method: str, endpoint: str,
              req_json: Dict[str, Any] | None = None,
              req_headers: Dict[str, str] | None = None) -> Tuple[int, Dict[str, Any]]:
        path = f"{self._base}{endpoint}"
        headers = self._auth_headers(req_headers)
        return self._exec(
            ctx=ctx,
            step=step,
            method=method,
            path=path,
            req_json=req_json,
            req_headers=headers,
        )
    
    def get(self, ctx: dict, step: str, endpoint: str, 
            req_headers: Dict[str, str] | None = None) -> Tuple[int, Dict[str, Any]]:
        return self._call(ctx, step, "GET", endpoint, req_headers=req_headers)
    
    def post(self, ctx: dict, step: str, endpoint: str,
             req_json: Dict[str, Any] | None = None,
             req_headers: Dict[str, str] | None = None) -> Tuple[int, Dict[str, Any]]:
        return self._call(ctx, step, "POST", endpoint, req_json, req_headers)
    
    def put(self, ctx: dict, step: str, endpoint: str,
            req_json: Dict[str, Any] | None = None,
            req_headers: Dict[str, str] | None = None) -> Tuple[int, Dict[str, Any]]:
        return self._call(ctx, step, "PUT", endpoint, req_json, req_headers)
    
    def delete(self, ctx: dict, step: str, endpoint: str,
               req_headers: Dict[str, str] | None = None) -> Tuple[int, Dict[str, Any]]:
        return self._call(ctx, step, "DELETE", endpoint, req_headers=req_headers)
    
    def patch(self, ctx: dict, step: str, endpoint: str,
              req_json: Dict[str, Any] | None = None,
              req_headers: Dict[str, str] | None = None) -> Tuple[int, Dict[str, Any]]:
        return self._call(ctx, step, "PATCH", endpoint, req_json, req_headers)