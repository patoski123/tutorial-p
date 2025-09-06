<!--

 New endpoint in an existing domain → add a method to that domain’s wrapper.

New domain (e.g., payments) → add a new file src/api/wrappers/payments_api.py.

Change base URL / timeouts / creds → config/settings.py or .env.

Change client mode → src/api/execution/router.py or pass a flag in ctx.

 -->
 