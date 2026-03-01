from workers import WorkerEntrypoint

try:
    from main import app
except ImportError:
    from .main import app


class Default(WorkerEntrypoint):
    async def fetch(self, request):
        import asgi

        return await asgi.fetch(app, request.js_object, self.env)
