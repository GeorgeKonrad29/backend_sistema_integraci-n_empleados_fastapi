import jinja2
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from workers import WorkerEntrypoint

environment = jinja2.Environment()
template = environment.from_string("Hello, {{ name }}!")

app = FastAPI()


class LoginRequest(BaseModel):
    correo: str
    contrasena: str


class LoginUser(BaseModel):
    id: int
    correo: str
    rol: int | None = None
    nombre: str


class LoginResponse(BaseModel):
    status: str
    message: str
    user: LoginUser


@app.get("/")
async def root():
    message = "This is an example of FastAPI with Jinja2 - go to /hi/<name> to see a template rendered"
    return {"message": message}


@app.get("/hi/{name}")
async def say_hi(name: str):
    message = template.render(name=name)
    return {"message": message}


@app.get("/env")
async def env(req: Request):
    env = req.scope["env"]
    message = f"Here is an example of getting an environment variable: {env.MESSAGE}"
    return {"message": message}


@app.get("/dataBase")
async def get_database_tables(req: Request):
    env = req.scope["env"]
    db = env.dataBase
    
    try:
        # Obtener todas las tablas de la base de datos
        result = await db.prepare("SELECT name FROM sqlite_master WHERE type='table'").all()
        tables = [row.name for row in result.results]
        return {"tables": tables, "count": len(tables)}
    except Exception as e:
        return {"error": str(e), "status": "error"}


@app.post("/login", response_model=LoginResponse, tags=["Auth"])
async def login(payload: LoginRequest, req: Request):
    env = req.scope["env"]
    db = env.dataBase

    try:
        result = (
            await db.prepare(
                "SELECT id, correo, contrasena, rol, nombre FROM USUARIO WHERE correo = ? LIMIT 1"
            )
            .bind(payload.correo)
            .first()
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error consultando la base de datos: {e}")

    if not result:
        raise HTTPException(status_code=401, detail="Credenciales inválidas")

    if result.contrasena != payload.contrasena:
        raise HTTPException(status_code=401, detail="Credenciales inválidas")

    return {
        "status": "ok",
        "message": "Login exitoso",
        "user": {
            "id": result.id,
            "correo": result.correo,
            "rol": result.rol,
            "nombre": result.nombre,
        },
    }


class Default(WorkerEntrypoint):
    async def fetch(self, request):
        import asgi

        return await asgi.fetch(app, request.js_object, self.env)
