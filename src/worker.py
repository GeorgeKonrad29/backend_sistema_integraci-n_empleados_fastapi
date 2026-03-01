import jinja2
import base64
import hashlib
import hmac
import secrets
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from workers import WorkerEntrypoint

environment = jinja2.Environment()
template = environment.from_string("Hello, {{ name }}!")

app = FastAPI()

PBKDF2_ALGORITHM = "sha256"
PBKDF2_ITERATIONS = 390000


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    derived_key = hashlib.pbkdf2_hmac(
        PBKDF2_ALGORITHM,
        password.encode("utf-8"),
        salt.encode("utf-8"),
        PBKDF2_ITERATIONS,
    )
    encoded_key = base64.b64encode(derived_key).decode("utf-8")
    return f"pbkdf2_sha256${PBKDF2_ITERATIONS}${salt}${encoded_key}"


def verify_password(plain_password: str, stored_password: str) -> bool:
    if stored_password.startswith("pbkdf2_sha256$"):
        try:
            _, iterations, salt, stored_key = stored_password.split("$", 3)
            calculated_key = hashlib.pbkdf2_hmac(
                PBKDF2_ALGORITHM,
                plain_password.encode("utf-8"),
                salt.encode("utf-8"),
                int(iterations),
            )
            calculated_key_b64 = base64.b64encode(calculated_key).decode("utf-8")
            return hmac.compare_digest(calculated_key_b64, stored_key)
        except Exception:
            return False

    return hmac.compare_digest(plain_password, stored_password)


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

    if not verify_password(payload.contrasena, result.contrasena):
        raise HTTPException(status_code=401, detail="Credenciales inválidas")

    if not result.contrasena.startswith("pbkdf2_sha256$"):
        try:
            upgraded_hash = hash_password(payload.contrasena)
            await db.prepare("UPDATE USUARIO SET contrasena = ? WHERE id = ?") \
                .bind(upgraded_hash, result.id) \
                .run()
        except Exception:
            pass

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
