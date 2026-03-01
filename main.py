import json

async def on_fetch(request):
    """Manejador principal para Cloudflare Workers"""
    url = request.url
    path = url.split("?")[0].split("/")[-1] or "/"
    
    if path == "/":
        return Response(
            json.dumps({"message": "Hola mundo desde Cloudflare Workers"}),
            headers={"Content-Type": "application/json"}
        )
    elif path == "health":
        return Response(
            json.dumps({"status": "ok"}),
            headers={"Content-Type": "application/json"}
        )
    else:
        return Response(
            json.dumps({"error": "Not found"}),
            status=404,
            headers={"Content-Type": "application/json"}
        )

class Response:
    def __init__(self, body, status=200, headers=None):
        self.body = body
        self.status = status
        self.headers = headers or {"Content-Type": "application/json"}
    
    def __iter__(self):
        yield (self.status, self.headers)
        yield self.body.encode() if isinstance(self.body, str) else self.body
