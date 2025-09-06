# Create the wrapper file

## src/api/wrappers/orders_api.py

###  class OrdersAPI:
-    def __init__(self, executor, base_path="/orders"):
-        self._exec = executor
-        self._base = base_path

-    def list(self, ctx, page=1):
-        return self._exec(
-            ctx=ctx, step="List Orders", method="GET",
-           path=f"{self._base}?page={page}"
-       )

-    def create(self, ctx, order):
-        return self._exec(
-            ctx=ctx, step="Create Order", method="POST",
-            path=self._base, req_json=order
-        )

-    def get(self, ctx, order_id: int):
-        return self._exec(
-            ctx=ctx, step="Get Order", method="GET",
-            path=f"{self._base}/{order_id}"
-        )
