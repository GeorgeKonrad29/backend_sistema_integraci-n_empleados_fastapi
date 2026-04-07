from fastapi.testclient import TestClient
import pytest

from src.main import app
from src.utils import create_access_token


TEST_JWT_SECRET = "test-secret"


class FakeRow:
    def __init__(self, **data):
        self.__dict__.update(data)

    def to_py(self):
        return dict(self.__dict__)


class FakePreparedQuery:
    def __init__(self, query: str):
        self.query = " ".join(query.lower().split())
        self.args = ()

    def bind(self, *args):
        self.args = args
        return self

    async def first(self):
        if "select id, nombre_cargo, area, id_jefe_inmediato from jerarquia where id = ? limit 1" in self.query:
            cargo_id = self.args[0] if self.args else None
            if cargo_id == 1:
                return FakeRow(id=1, nombre_cargo="Asamblea de Socios", area="Máximo Órgano", id_jefe_inmediato=None)
            if cargo_id == 48:
                return FakeRow(id=48, nombre_cargo="Gerente Talento Humano", area="Gerencia de talento humano", id_jefe_inmediato=2)
            return None

        if "from usuario where correo = ? limit 1" in self.query:
            correo = self.args[0] if self.args else None
            if correo == "rrhh@sinergia.com":
                return FakeRow(
                    id=48,
                    correo="rrhh@sinergia.com",
                    contrasena="hashed-password",
                    rol="Administrador",
                    nombre="Gerente RRHH",
                    cargo=48,
                )
            return None

        if "select id, correo, rol, nombre, cargo from usuario where id = ? limit 1" in self.query:
            return FakeRow(
                id=48,
                correo="rrhh@sinergia.com",
                rol="Administrador",
                nombre="Gerente RRHH",
                cargo=48,
            )

        if "select id, cargo from usuario where id = ? limit 1" in self.query:
            empleado_id = self.args[0] if self.args else None
            if empleado_id == 48:
                return FakeRow(id=48, cargo=8)
            return FakeRow(id=empleado_id or 48, cargo=8)

        if "select id from usuario where id = ?" in self.query:
            return FakeRow(id=48)

        if "select id from dotacion where lower(trim(especificacion)) = lower(trim(?)) limit 1" in self.query:
            especificacion = str(self.args[0] if self.args else "").strip().lower()
            known = {
                "asignación de herramientas y accesos base",
                "programación de inducción inicial",
                "validación de puesto y logística de ingreso",
                "inducción corporativa",
                "plantilla existente",
            }
            if especificacion in known:
                return FakeRow(id=10)
            return None

        if "select id, encargado, tipo, especificacion from dotacion where lower(trim(especificacion)) = lower(trim(?)) limit 1" in self.query:
            especificacion = str(self.args[0] if self.args else "").strip().lower()
            if especificacion == "plantilla existente":
                return FakeRow(id=10, encargado="RRHH", tipo="Onboarding", especificacion="Plantilla existente")
            return None

        if "select nombre_cargo, area from jerarquia where id = ? limit 1" in self.query:
            cargo_id = self.args[0] if self.args else None
            if cargo_id == 7:
                return FakeRow(nombre_cargo="Jefe de Infraestructura y Mantenimiento", area="Mantenimiento")
            if cargo_id == 4:
                return FakeRow(nombre_cargo="Coordinador de servicios corporativos", area="Servicios generales")
            if cargo_id == 48:
                return FakeRow(nombre_cargo="Gerente Talento Humano", area="Gerencia de talento humano")
            if cargo_id == 44:
                return FakeRow(nombre_cargo="Analista de Operaciones", area="Operaciones")
            return None

        if "select nombre_cargo, area from jerarquia where id_jefe_inmediato = ? order by id limit 1" in self.query:
            cargo_id = self.args[0] if self.args else None
            if cargo_id == 7:
                return FakeRow(nombre_cargo="Coordinador de servicios corporativos", area="Servicios generales")
            if cargo_id == 48:
                return FakeRow(nombre_cargo="Analista de procesos", area="Procesos")
            return None

        if "select id from usuario where correo = ? limit 1" in self.query:
            return None

        if "insert into usuario" in self.query:
            return FakeRow(id=99, cargo=self.args[4] if len(self.args) > 4 else 44)

        if "insert into solicitudes" in self.query:
            return FakeRow(
                id=321,
                id_empleado=self.args[0] if self.args else 48,
                fecha_creacion="2026-04-01T00:00:00",
                fecha_fin=self.args[1] if len(self.args) > 1 else "2026-04-15T00:00:00",
                estado=self.args[2] if len(self.args) > 2 else "Pendiente",
                especificaciones=self.args[3] if len(self.args) > 3 else "",
                destinatario=self.args[4] if len(self.args) > 4 else None,
            )

        if "insert into dotacion (encargado, tipo, especificacion) values (?, ?, ?) returning id, encargado, tipo, especificacion" in self.query:
            return FakeRow(
                id=700,
                encargado=self.args[0] if len(self.args) > 0 else None,
                tipo=self.args[1] if len(self.args) > 1 else "Onboarding",
                especificacion=self.args[2] if len(self.args) > 2 else "",
            )

        if "from solicitudes where id = ? limit 1" in self.query:
            solicitud_id = self.args[0] if self.args else None
            if solicitud_id == 556:
                return FakeRow(
                    id=556,
                    id_empleado=51,
                    fecha_creacion="2026-04-03T00:00:00",
                    fecha_fin="2026-04-20T00:00:00",
                    estado="Pendiente",
                    especificaciones="Asignar hardware y credenciales de acceso",
                    destinatario="Jefe de Infraestructura y Mantenimiento",
                )
            if solicitud_id == 321:
                return FakeRow(
                    id=321,
                    id_empleado=48,
                    fecha_creacion="2026-04-01T00:00:00",
                    fecha_fin="2026-04-15T00:00:00",
                    estado="Pendiente",
                    especificaciones="Inducción corporativa",
                    destinatario="Recursos Humanos",
                )
            if solicitud_id == 557:
                return FakeRow(
                    id=557,
                    id_empleado=52,
                    fecha_creacion="2026-04-04T00:00:00",
                    fecha_fin="2026-04-25T00:00:00",
                    estado="Finalizado",
                    especificaciones="Adecuación de puesto físico en oficina",
                    destinatario="Mantenimiento",
                )
            return None

        if "select id, estado_onboarding from usuario where id = ? limit 1" in self.query:
            user_id = self.args[0] if self.args else None
            if user_id == 48:
                return FakeRow(id=48, estado_onboarding="Pendiente")
            if user_id == 47:
                return FakeRow(id=47, estado_onboarding="En proceso")
            if user_id == 49:
                return FakeRow(id=49, estado_onboarding="Finalizado")
            return None

        if "from solicitudes s join usuario u on u.id = s.id_empleado where s.id = ? limit 1" in self.query:
            solicitud_id = self.args[0] if self.args else None
            if solicitud_id == 556:
                return FakeRow(
                    id=556,
                    id_empleado=51,
                    fecha_creacion="2026-04-03T00:00:00",
                    fecha_fin="2026-04-20T00:00:00",
                    estado="Pendiente",
                    especificaciones="Asignar hardware y credenciales de acceso",
                    destinatario="Jefe de Infraestructura y Mantenimiento",
                    cargo_empleado=8,
                )
            if solicitud_id == 321:
                return FakeRow(
                    id=321,
                    id_empleado=48,
                    fecha_creacion="2026-04-01T00:00:00",
                    fecha_fin="2026-04-15T00:00:00",
                    estado="Pendiente",
                    especificaciones="Inducción corporativa",
                    destinatario="Recursos Humanos",
                    cargo_empleado=48,
                )
            return None

        if "select id_jefe_inmediato from jerarquia where id = ? limit 1" in self.query:
            cargo_id = self.args[0] if self.args else None
            if cargo_id == 8:
                return FakeRow(id_jefe_inmediato=7)
            if cargo_id == 48:
                return FakeRow(id_jefe_inmediato=2)
            return FakeRow(id_jefe_inmediato=None)

        if "select id from jerarquia where id_jefe_inmediato = ? limit 1" in self.query:
            cargo_id = self.args[0] if self.args else None
            if cargo_id == 7:
                return FakeRow(id=8)
            return None

        if "update solicitudes set fecha_fin = ?, estado = ?, especificaciones = ?, destinatario = ? where id = ? returning" in self.query:
            return FakeRow(
                id=self.args[4] if len(self.args) > 4 else 556,
                id_empleado=51,
                fecha_creacion="2026-04-03T00:00:00",
                fecha_fin=self.args[0] if len(self.args) > 0 else "2026-04-20T00:00:00",
                estado=self.args[1] if len(self.args) > 1 else "Pendiente",
                especificaciones=self.args[2] if len(self.args) > 2 else "Asignar hardware y credenciales de acceso",
                destinatario=self.args[3] if len(self.args) > 3 else "Jefe de Infraestructura y Mantenimiento",
            )

        if "update solicitudes set estado = ? where id = ? returning" in self.query:
            solicitud_id = self.args[1] if len(self.args) > 1 else 556
            return FakeRow(
                id=solicitud_id,
                id_empleado=51,
                fecha_creacion="2026-04-03T00:00:00",
                fecha_fin="2026-04-20T00:00:00",
                estado=self.args[0] if len(self.args) > 0 else "En proceso",
                especificaciones="Asignar hardware y credenciales de acceso",
                destinatario="Jefe de Infraestructura y Mantenimiento",
            )

        if "update usuario set estado_onboarding = ? where id = ? returning id, estado_onboarding" in self.query:
            return FakeRow(
                id=self.args[1] if len(self.args) > 1 else 48,
                estado_onboarding=self.args[0] if len(self.args) > 0 else "En proceso",
            )

        if "select id from puesto_de_trabajo where coordenadas = ? limit 1" in self.query:
            coordenadas = self.args[0] if self.args else None
            if coordenadas == "P1-F01-C01":
                return FakeRow(id=1)
            return None
        if "insert into puesto_de_trabajo" in self.query:
            return FakeRow(
                id=777,
                coordenadas=self.args[0] if self.args else "P1-F01-C01",
                id_empleado=self.args[1] if len(self.args) > 1 else 48,
                tipo_puesto=self.args[2] if len(self.args) > 2 else "Fijo",
            )
        if "from puesto_de_trabajo p" in self.query and "join usuario u on u.id = p.id_empleado" in self.query and "join jerarquia j on j.id = u.cargo" in self.query:
            return FakeRow(
                results=[
                    FakeRow(
                        id=777,
                        coordenadas="P1-F01-C01",
                        id_empleado=48,
                        nombre_empleado="Gerente RRHH",
                        area="Gerencia de talento humano",
                        tipo_puesto="Fijo",
                    ),
                ]
            )
        if "select id, coordenadas, id_empleado, tipo_puesto from puesto_de_trabajo" in self.query:
            return FakeRow(
                results=[
                    FakeRow(id=777, coordenadas="P1-F01-C01", id_empleado=48, tipo_puesto="Fijo"),
                    FakeRow(id=778, coordenadas="P2-F20-C20", id_empleado=None, tipo_puesto="Libre"),
                ]
            )
        if "insert or replace into activacion_usuario" in self.query:
            return FakeRow(success=True)

        if "select user_id, expires_at, used from activacion_usuario" in self.query:
            return FakeRow(user_id=48, expires_at=9999999999, used=0)

        if "update usuario set contrasena = ? where id = ?" in self.query:
            return FakeRow(success=True)

        if "update activacion_usuario set used = 1 where token = ?" in self.query:
            return FakeRow(success=True)

        return None

    async def all(self):
        if "from jerarquia order by id" in self.query:
            return FakeRow(
                results=[
                    FakeRow(id=1, nombre_cargo="Asamblea de Socios", area="Máximo Órgano", id_jefe_inmediato=None),
                    FakeRow(id=48, nombre_cargo="Gerente Talento Humano", area="Gerencia de talento humano", id_jefe_inmediato=2),
                ]
            )
        if "from puesto_de_trabajo p" in self.query and "where p.id_empleado is not null" in self.query:
            return FakeRow(
                results=[
                    FakeRow(
                        id=777,
                        coordenadas="P1-F01-C01",
                        id_empleado=48,
                        nombre_empleado="Gerente RRHH",
                        area="Gerencia de talento humano",
                        tipo_puesto="Fijo",
                    ),
                ]
            )
        if "select * from solicitudes" in self.query:
            return FakeRow(
                results=[
                    FakeRow(
                        id=321,
                        id_empleado=48,
                        fecha_creacion="2026-04-01T00:00:00",
                        fecha_fin="2026-04-15T00:00:00",
                        estado="Pendiente",
                        especificaciones="Inducción corporativa",
                        destinatario="Recursos Humanos",
                    )
                ]
            )
        if "join usuario u on u.id = s.id_empleado" in self.query and "where j.id_jefe_inmediato = ?" in self.query:
            rows = [
                FakeRow(
                    id=555,
                    id_empleado=50,
                    fecha_creacion="2026-04-02T00:00:00",
                    fecha_fin="2026-04-15T00:00:00",
                    estado="Pendiente",
                    especificaciones="Entregar laptop y credenciales",
                    destinatario="TI",
                ),
                FakeRow(
                    id=558,
                    id_empleado=53,
                    fecha_creacion="2026-04-04T00:00:00",
                    fecha_fin="2026-04-18T00:00:00",
                    estado="Finalizado",
                    especificaciones="Entrega de acceso y equipo",
                    destinatario="TI",
                ),
            ]

            filtered = rows

            arg_index = 1
            if "s.estado != ?" in self.query:
                estado_excluido = self.args[arg_index] if len(self.args) > arg_index else None
                filtered = [r for r in filtered if r.estado != estado_excluido]
                arg_index += 1

            if "s.estado = ?" in self.query:
                estado = self.args[arg_index] if len(self.args) > arg_index else None
                filtered = [r for r in filtered if r.estado == estado]
                arg_index += 1

            if "s.fecha_creacion >= ?" in self.query:
                fecha_desde = self.args[arg_index] if len(self.args) > arg_index else None
                filtered = [r for r in filtered if r.fecha_creacion >= fecha_desde]
                arg_index += 1

            if "s.fecha_creacion <= ?" in self.query:
                fecha_hasta = self.args[arg_index] if len(self.args) > arg_index else None
                filtered = [r for r in filtered if r.fecha_creacion <= fecha_hasta]

            return FakeRow(results=filtered)
        if "from solicitudes s" in self.query and "lower(trim(s.destinatario)) = lower(trim(?))" in self.query:
            destinatario_cargo = str((self.args[0] if len(self.args) > 0 else "") or "").strip().lower()
            destinatario_area = str((self.args[1] if len(self.args) > 1 else "") or "").strip().lower()

            rows = [
                FakeRow(
                    id=556,
                    id_empleado=51,
                    fecha_creacion="2026-04-03T00:00:00",
                    fecha_fin="2026-04-20T00:00:00",
                    estado="En proceso",
                    especificaciones="Asignar hardware y credenciales de acceso",
                    destinatario="Jefe de Infraestructura y Mantenimiento",
                ),
                FakeRow(
                    id=557,
                    id_empleado=52,
                    fecha_creacion="2026-04-04T00:00:00",
                    fecha_fin="2026-04-25T00:00:00",
                    estado="Finalizado",
                    especificaciones="Adecuación de puesto físico en oficina",
                    destinatario="Mantenimiento",
                ),
            ]

            filtered = [
                r
                for r in rows
                if str(r.destinatario).strip().lower() in {destinatario_cargo, destinatario_area}
            ]

            arg_index = 2
            if "s.estado != ?" in self.query:
                estado_excluido = self.args[arg_index] if len(self.args) > arg_index else None
                filtered = [r for r in filtered if r.estado != estado_excluido]
                arg_index += 1

            if "s.estado = ?" in self.query:
                estado = self.args[arg_index] if len(self.args) > arg_index else None
                filtered = [r for r in filtered if r.estado == estado]
                arg_index += 1

            if "s.fecha_creacion >= ?" in self.query:
                fecha_desde = self.args[arg_index] if len(self.args) > arg_index else None
                filtered = [r for r in filtered if r.fecha_creacion >= fecha_desde]
                arg_index += 1

            if "s.fecha_creacion <= ?" in self.query:
                fecha_hasta = self.args[arg_index] if len(self.args) > arg_index else None
                filtered = [r for r in filtered if r.fecha_creacion <= fecha_hasta]

            return FakeRow(results=filtered)
        if "from solicitudes" in self.query and "where id_empleado = ?" in self.query:
            user_id = self.args[0] if len(self.args) > 0 else None

            rows = [
                FakeRow(
                    id=321,
                    id_empleado=48,
                    fecha_creacion="2026-04-01T00:00:00",
                    fecha_fin="2026-04-15T00:00:00",
                    estado="Pendiente",
                    especificaciones="Inducción corporativa",
                    destinatario="Recursos Humanos",
                ),
                FakeRow(
                    id=322,
                    id_empleado=48,
                    fecha_creacion="2026-04-06T00:00:00",
                    fecha_fin="2026-04-20T00:00:00",
                    estado="En proceso",
                    especificaciones="Entrega de credenciales",
                    destinatario="TI",
                ),
                FakeRow(
                    id=700,
                    id_empleado=50,
                    fecha_creacion="2026-04-02T00:00:00",
                    fecha_fin="2026-04-18T00:00:00",
                    estado="Pendiente",
                    especificaciones="Solicitud de otro usuario",
                    destinatario="RRHH",
                ),
            ]

            filtered = [r for r in rows if r.id_empleado == user_id]

            arg_index = 1
            if "estado = ?" in self.query:
                estado = self.args[arg_index] if len(self.args) > arg_index else None
                filtered = [r for r in filtered if r.estado == estado]
                arg_index += 1

            if "fecha_creacion >= ?" in self.query:
                fecha_desde = self.args[arg_index] if len(self.args) > arg_index else None
                filtered = [r for r in filtered if r.fecha_creacion >= fecha_desde]
                arg_index += 1

            if "fecha_creacion <= ?" in self.query:
                fecha_hasta = self.args[arg_index] if len(self.args) > arg_index else None
                filtered = [r for r in filtered if r.fecha_creacion <= fecha_hasta]

            return FakeRow(results=filtered)
        if "from historial" in self.query and "where id_solicitud = ?" in self.query:
            solicitud_id = self.args[0] if self.args else None
            if solicitud_id == 556:
                return FakeRow(
                    results=[
                        FakeRow(
                            id=9002,
                            id_solicitud=556,
                            fecha_cambio="2026-04-03T10:00:00",
                            tipo_cambio="CAMBIO_ESTADO",
                            estado_antiguo="Pendiente",
                            nuevo_estado="En proceso",
                        ),
                        FakeRow(
                            id=9001,
                            id_solicitud=556,
                            fecha_cambio="2026-04-03T09:00:00",
                            tipo_cambio="CREACION",
                            estado_antiguo=None,
                            nuevo_estado="Pendiente",
                        ),
                    ]
                )
            if solicitud_id == 321:
                return FakeRow(
                    results=[
                        FakeRow(
                            id=8001,
                            id_solicitud=321,
                            fecha_cambio="2026-04-01T09:00:00",
                            tipo_cambio="CREACION",
                            estado_antiguo=None,
                            nuevo_estado="Pendiente",
                        )
                    ]
                )
            return FakeRow(results=[])
        return FakeRow(results=[])

    async def run(self):
        return FakeRow(success=True)


class FakeDatabase:
    def prepare(self, query):
        return FakePreparedQuery(query)


class FakeEnv:
    MESSAGE = "My env var"

    class _Secret:
        async def get(self):
            return TEST_JWT_SECRET

    def __init__(self):
        self.dataBase = FakeDatabase()
        self.JWTSecret = self._Secret()


class FakeRequest:
    def __init__(self):
        self.scope = {"env": FakeEnv()}
        self.base_url = "https://test.local/"


async def inject_env_middleware(request, call_next):
    request.scope["env"] = FakeEnv()
    return await call_next(request)


if not getattr(app.state, "_fake_env_middleware_added", False):
    app.middleware("http")(inject_env_middleware)
    app.state._fake_env_middleware_added = True


@pytest.fixture(scope="session")
def client():
    return TestClient(app)


@pytest.fixture
def token_factory():
    def _build(cargo: int, sub: str = "48", correo: str = "rrhh@sinergia.com", rol: str = "Administrador", nombre: str = "Gerente RRHH"):
        return create_access_token(
            {
                "sub": sub,
                "correo": correo,
                "rol": rol,
                "nombre": nombre,
                "cargo": cargo,
            },
            TEST_JWT_SECRET,
            3600,
        )

    return _build


@pytest.fixture
def rrhh_token(token_factory):
    return token_factory(48)


@pytest.fixture
def servicios_generales_token(token_factory):
    return token_factory(
        4,
        sub="4",
        correo="servicios@sinergia.com",
        rol="Encargado de Area",
        nombre="Coord. de servicios corporativos",
    )
