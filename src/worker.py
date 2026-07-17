"""Cloudflare Workers entry point (wrangler.jsonc "main").

Only the Workers runtime imports this module; local dev keeps using uvicorn
via `uv run mathkids`. The D1 binding (env.DB) reaches route handlers through
request.scope["env"].
"""

from workers import WorkerEntrypoint

from mathkids.app import app


class Default(WorkerEntrypoint):
    async def fetch(self, request):
        import asgi

        return await asgi.fetch(app, request.js_object, self.env)
