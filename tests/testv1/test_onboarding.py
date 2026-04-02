import asyncio

from src.api.v1.onboarding.onboarding import (
    create_onboarding_request,
    list_onboarding_requests,
)
from src.models.onboarding import OnboardingRequest


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
        if "select id from usuario where id = ?" in self.query:
            return FakeRow(id=48)

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

        return None

    async def all(self):
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

    async def run(self):
        return FakeRow(success=True)


class FakeDatabase:
    def prepare(self, query):
        return FakePreparedQuery(query)


class FakeEnv:
    MESSAGE = "My env var"

    def __init__(self):
        self.dataBase = FakeDatabase()


class FakeRequest:
    def __init__(self):
        self.scope = {"env": FakeEnv()}
        self.base_url = "https://test.local/"


def test_onboarding_create_requires_permission_and_returns_request():
    payload = OnboardingRequest(
        id_empleado=48,
        fecha_fin="2026-04-15T00:00:00",
        destinatario="Recursos Humanos",
        especificaciones="Inducción corporativa",
        estado="Pendiente",
    )
    result = asyncio.run(
        create_onboarding_request(
            payload=payload,
            req=FakeRequest(),
            token_payload={"cargo": 48},
        )
    )
    assert result.id == 321
    assert result.id_empleado == 48


def test_onboarding_list_returns_requests():
    result = asyncio.run(
        list_onboarding_requests(
            req=FakeRequest(),
            token_payload={"cargo": 48},
        )
    )
    assert isinstance(result, list)
    assert result[0]["id"] == 321


def test_onboarding_create_without_token_returns_401(client):
    response = client.post(
        "/v1/onboarding/",
        json={
            "id_empleado": 48,
            "fecha_fin": "2026-04-15T00:00:00",
            "destinatario": "Recursos Humanos",
            "especificaciones": "Inducción corporativa",
            "estado": "Pendiente",
        },
    )
    assert response.status_code == 401


def test_onboarding_create_with_forbidden_cargo_returns_403(client, token_factory):
    token = token_factory(
        44,
        sub="44",
        correo="dev@sinergia.com",
        rol="Operador",
        nombre="Dev",
    )
    response = client.post(
        "/v1/onboarding/",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "id_empleado": 48,
            "fecha_fin": "2026-04-15T00:00:00",
            "destinatario": "Recursos Humanos",
            "especificaciones": "Inducción corporativa",
            "estado": "Pendiente",
        },
    )
    assert response.status_code == 403


def test_team_onboarding_requests_returns_direct_reports(client, rrhh_token):
    response = client.get(
        "/v1/onboarding/solicitudes-equipo",
        headers={"Authorization": f"Bearer {rrhh_token}"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert isinstance(payload, list)
    assert payload[0]["id"] == 555
    assert payload[0]["id_empleado"] == 50


def test_team_onboarding_requests_without_token_returns_401(client):
    response = client.get("/v1/onboarding/solicitudes-equipo")
    assert response.status_code == 401
