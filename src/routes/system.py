import jinja2
from fastapi import APIRouter, Request

router = APIRouter()

environment = jinja2.Environment()
template = environment.from_string("Hello, {{ name }}!")


@router.get("/")
async def root():
    """Endpoint raíz con información general"""
    message = "Sistema de integración de empleados - FastAPI en Cloudflare Workers"
    return {"message": message}


@router.get("/hi/{name}")
async def say_hi(name: str):
    """Endpoint de ejemplo con template Jinja2"""
    message = template.render(name=name)
    return {"message": message}


@router.get("/env")
async def env(req: Request):
    """Obtiene variables de entorno del worker"""
    env = req.scope["env"]
    message = f"Here is an example of getting an environment variable: {env.MESSAGE}"
    return {"message": message}


@router.get("/database/tables")
async def get_database_tables(req: Request):
    """
    Obtiene todas las tablas de la base de datos.
    
    Returns:
        Lista de nombres de tablas y conteo total
    """
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
