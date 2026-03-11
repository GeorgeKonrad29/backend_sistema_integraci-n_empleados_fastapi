from workers import WorkerEntrypoint

try:
    from main import app
except ImportError:
    from .main import app


class Default(WorkerEntrypoint):
    async def fetch(self, request):
        try:
            from workers.asgi import ASGIApp

            asgi_app = ASGIApp(app)
            return await asgi_app.fetch(request, self.env, self.ctx)
        except Exception:
            import workers

            if not hasattr(workers, "wait_until"):
                def _wait_until(awaitable):
                    try:
                        self.ctx.wait_until(awaitable)
                    except Exception:
                        pass

                workers.wait_until = _wait_until

            import asgi

            return await asgi.fetch(app, request.js_object, self.env)
