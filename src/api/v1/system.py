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
def hay_ia(req: Request):
    import requests
    API_BASE_URL = "https://api.cloudflare.com/client/v4/accounts/712ea7d21b6397f0acea15142a4f3c76/ai/run/"
    headers = {f"Authorization": "Bearer {req.scope['env'].token_ia}"}
    model =  'openai/gpt-5.5'
    inputs = [
        { "role": "user", "content": "hay ia? "}
    ]
    input = { "messages": inputs }
    response = requests.post(f"{API_BASE_URL}{model}", headers=headers, json=input)
    return response.json()