from __future__ import annotations
from typing import Any, Dict, Optional, Tuple

class ProductManagementAPI:
    """
    Minimal product client:
    - If mock=True, no network call – returns a fake product.
    - If mock=False, uses a Playwright APIRequestContext passed as `api` to POST.
    - Optionally logs/attaches via `recorder.record(...)` if provided.
    """

    def __init__(
        self,
        base_url: str,
        *,
        api=None,                # Playwright APIRequestContext or None (for mock)
        mock: bool = True,
        recorder: Optional[Any] = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.api = api
        self.mock = mock
        self.recorder = recorder

    def create_product(self, name: str) -> Tuple[int, Dict[str, Any]]:
        endpoint = f"{self.base_url}/products"
        body = {"name": name}
        headers = {"Content-Type": "application/json", "Accept": "application/json"}

        if self.mock or self.api is None:
            # --- mock result ---
            status = 201
            data = {"id": "p-123", "name": name, "status": "CREATED"}
        else:
            # --- real call with Playwright APIRequestContext ---
            resp = self.api.post(endpoint, json=body, headers=headers)
            status = resp.status
            try:
                data = resp.json()
            except Exception:
                data = {"_raw": resp.text()}

        # Optional: feed your ApiRecorder (Allure + custom HTML trace)
        if self.recorder:
            self.recorder.record(
                step="create product",
                method="POST",
                url=endpoint,
                status=status,
                req_headers=headers,
                req_json=body,
                resp_headers={"Content-Type": "application/json"},
                resp_json=data,
            )

        return status, data
