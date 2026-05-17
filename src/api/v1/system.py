import jinja2
from fastapi import APIRouter, Request

router = APIRouter()

environment = jinja2.Environment()
template = environment.from_string("Hello, {{ name }}!")


@router.get("/")
async def root():
    message = "Sistema de integración de empleados - FastAPI en Cloudflare Workers"
    return {"message": message}


@router.get("/hi/{name}")
async def say_hi(name: str):
    message = template.render(name=name)
    return {"message": message}


@router.get("/env")
async def env(req: Request):
    env = req.scope["env"]
    message = f"Here is an example of getting an environment variable: {env.MESSAGE}"
    return {"message": message}


@router.get("/database/tables")
async def get_database_tables(req: Request):
    env = req.scope["env"]
    db = env.dataBase

    try:
        result = await db.prepare(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).all()
        tables = [row.name for row in result.results]
        return {"tables": tables, "count": len(tables)}
    except Exception as e:
        return {"error": str(e), "status": "error"}

@router.get("/ia")
async def hay_ia(req: Request):
    import httpx

    API_BASE_URL = "https://api.cloudflare.com/client/v4/accounts/712ea7d21b6397f0acea15142a4f3c76/ai/run/"
    headers = {"Authorization": f"Bearer {req.scope['env'].token_ia}"}
    model = "@cf/meta/llama-3.1-8b-instruct"  # Modelo válido de Cloudflare AI
    
    payload = {
        "messages": [
            {"role": "user", "content": "hay ia? :/"}
        ]
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{API_BASE_URL}{model}",
            headers=headers,
            json=payload
        )
        response.raise_for_status()
        return response.json()
