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
        if "select id, cargo from usuario where id = ? limit 1" in self.query:
            return FakeRow(id=48, cargo=8)

        if "select id_jefe_inmediato from jerarquia where id = ? limit 1" in self.query:
            return FakeRow(id_jefe_inmediato=7)

        if "select id from dotacion where lower(trim(especificacion)) = lower(trim(?)) limit 1" in self.query:
            return None

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
            token_payload={"cargo": 7},
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


def test_my_onboarding_requests_returns_only_authenticated_user_requests(client, rrhh_token):
    response = client.get(
        "/v1/onboarding/mis-solicitudes",
        headers={"Authorization": f"Bearer {rrhh_token}"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert isinstance(payload, list)
    assert len(payload) == 2
    assert all(item["id_empleado"] == 48 for item in payload)


def test_my_onboarding_requests_filters_by_estado(client, rrhh_token):
    response = client.get(
        "/v1/onboarding/mis-solicitudes?estado=En%20proceso",
        headers={"Authorization": f"Bearer {rrhh_token}"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 1
    assert payload[0]["id"] == 322


def test_my_onboarding_requests_without_token_returns_401(client):
    response = client.get("/v1/onboarding/mis-solicitudes")
    assert response.status_code == 401


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


def test_create_dotacion_template_by_immediate_boss(client, token_factory):
    jefe_token = token_factory(
        7,
        sub="7",
        correo="infraestructura@sinergia.com",
        rol="Encargado de Area",
        nombre="Jefe Infraestructura",
    )
    response = client.post(
        "/v1/onboarding/dotacion",
        headers={"Authorization": f"Bearer {jefe_token}"},
        json={
            "encargado": "Coordinador de servicios corporativos",
            "tipo": "Onboarding",
            "especificacion": "Plantilla nueva onboarding",
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["id"] == 700
    assert payload["especificacion"] == "Plantilla nueva onboarding"


def test_create_dotacion_template_duplicate_returns_409(client, rrhh_token):
    response = client.post(
        "/v1/onboarding/dotacion",
        headers={"Authorization": f"Bearer {rrhh_token}"},
        json={
            "encargado": "RRHH",
            "tipo": "Onboarding",
            "especificacion": "Plantilla existente",
        },
    )
    assert response.status_code == 409


def test_create_dotacion_template_forbidden_for_user_without_team(client, token_factory):
    operador_token = token_factory(
        44,
        sub="44",
        correo="operador@sinergia.com",
        rol="Operador",
        nombre="Operador",
    )
    response = client.post(
        "/v1/onboarding/dotacion",
        headers={"Authorization": f"Bearer {operador_token}"},
        json={
            "encargado": "RRHH",
            "tipo": "Onboarding",
            "especificacion": "Plantilla no permitida",
        },
    )
    assert response.status_code == 403


def test_create_dotacion_template_without_token_returns_401(client):
    response = client.post(
        "/v1/onboarding/dotacion",
        json={
            "encargado": "RRHH",
            "tipo": "Onboarding",
            "especificacion": "Plantilla sin token",
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


def test_onboarding_create_by_immediate_boss_creates_missing_template_and_returns_aviso(client, token_factory):
    jefe_token = token_factory(
        7,
        sub="7",
        correo="infraestructura@sinergia.com",
        rol="Encargado de Area",
        nombre="Jefe Infraestructura",
    )
    response = client.post(
        "/v1/onboarding/",
        headers={"Authorization": f"Bearer {jefe_token}"},
        json={
            "id_empleado": 48,
            "fecha_fin": "2026-04-15T00:00:00",
            "destinatario": "Coordinador de servicios corporativos",
            "especificaciones": "Plantilla no existente",
            "estado": "Pendiente",
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["id"] == 321
    assert payload["aviso"] is not None


def test_team_onboarding_requests_returns_direct_reports(client, rrhh_token):
    response = client.get(
        "/v1/onboarding/solicitudes-equipo",
        headers={"Authorization": f"Bearer {rrhh_token}"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert isinstance(payload, list)
    assert payload[0]["id"] == 558
    assert payload[0]["id_empleado"] == 53


def test_team_onboarding_requests_filters_by_estado(client, rrhh_token):
    response = client.get(
        "/v1/onboarding/solicitudes-equipo?estado=Finalizado",
        headers={"Authorization": f"Bearer {rrhh_token}"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 1
    assert payload[0]["id"] == 558
    assert payload[0]["estado"] == "Finalizado"


def test_team_onboarding_requests_filters_by_date_range(client, rrhh_token):
    response = client.get(
        "/v1/onboarding/solicitudes-equipo?fecha_desde=2026-04-04T00:00:00&fecha_hasta=2026-04-04T23:59:59",
        headers={"Authorization": f"Bearer {rrhh_token}"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 1
    assert payload[0]["id"] == 558


def test_team_onboarding_requests_invalid_estado_returns_400(client, rrhh_token):
    response = client.get(
        "/v1/onboarding/solicitudes-equipo?estado=Pendiente",
        headers={"Authorization": f"Bearer {rrhh_token}"},
    )
    assert response.status_code == 400


def test_team_onboarding_requests_invalid_date_range_returns_400(client, rrhh_token):
    response = client.get(
        "/v1/onboarding/solicitudes-equipo?fecha_desde=2026-04-05T00:00:00&fecha_hasta=2026-04-04T00:00:00",
        headers={"Authorization": f"Bearer {rrhh_token}"},
    )
    assert response.status_code == 400


def test_team_onboarding_requests_without_token_returns_401(client):
    response = client.get("/v1/onboarding/solicitudes-equipo")
    assert response.status_code == 401


def test_assigned_onboarding_requests_returns_for_resolver(client, token_factory):
    infraestructura_token = token_factory(
        7,
        sub="7",
        correo="infraestructura@sinergia.com",
        rol="Encargado de Area",
        nombre="Jefe Infraestructura",
    )
    response = client.get(
        "/v1/onboarding/solicitudes-asignadas",
        headers={"Authorization": f"Bearer {infraestructura_token}"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert isinstance(payload, list)
    assert payload[0]["id"] == 557
    assert payload[0]["destinatario"] == "Mantenimiento"


def test_assigned_onboarding_requests_filters_by_estado(client, token_factory):
    infraestructura_token = token_factory(
        7,
        sub="7",
        correo="infraestructura@sinergia.com",
        rol="Encargado de Area",
        nombre="Jefe Infraestructura",
    )
    response = client.get(
        "/v1/onboarding/solicitudes-asignadas?estado=Finalizado",
        headers={"Authorization": f"Bearer {infraestructura_token}"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 1
    assert payload[0]["id"] == 557
    assert payload[0]["estado"] == "Finalizado"


def test_assigned_onboarding_requests_filters_by_date_range(client, token_factory):
    infraestructura_token = token_factory(
        7,
        sub="7",
        correo="infraestructura@sinergia.com",
        rol="Encargado de Area",
        nombre="Jefe Infraestructura",
    )
    response = client.get(
        "/v1/onboarding/solicitudes-asignadas?fecha_desde=2026-04-04T00:00:00&fecha_hasta=2026-04-04T23:59:59",
        headers={"Authorization": f"Bearer {infraestructura_token}"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 1
    assert payload[0]["id"] == 557


def test_assigned_onboarding_requests_invalid_estado_returns_400(client, token_factory):
    infraestructura_token = token_factory(
        7,
        sub="7",
        correo="infraestructura@sinergia.com",
        rol="Encargado de Area",
        nombre="Jefe Infraestructura",
    )
    response = client.get(
        "/v1/onboarding/solicitudes-asignadas?estado=Abierto",
        headers={"Authorization": f"Bearer {infraestructura_token}"},
    )
    assert response.status_code == 400


def test_assigned_onboarding_requests_invalid_date_range_returns_400(client, token_factory):
    infraestructura_token = token_factory(
        7,
        sub="7",
        correo="infraestructura@sinergia.com",
        rol="Encargado de Area",
        nombre="Jefe Infraestructura",
    )
    response = client.get(
        "/v1/onboarding/solicitudes-asignadas?fecha_desde=2026-04-05T00:00:00&fecha_hasta=2026-04-04T00:00:00",
        headers={"Authorization": f"Bearer {infraestructura_token}"},
    )
    assert response.status_code == 400


def test_assigned_onboarding_requests_invalid_date_format_returns_400(client, token_factory):
    infraestructura_token = token_factory(
        7,
        sub="7",
        correo="infraestructura@sinergia.com",
        rol="Encargado de Area",
        nombre="Jefe Infraestructura",
    )
    response = client.get(
        "/v1/onboarding/solicitudes-asignadas?fecha_desde=2026/04/04",
        headers={"Authorization": f"Bearer {infraestructura_token}"},
    )
    assert response.status_code == 400


def test_assigned_onboarding_requests_without_token_returns_401(client):
    response = client.get("/v1/onboarding/solicitudes-asignadas")
    assert response.status_code == 401


def test_update_onboarding_request_by_assigned_resolver(client, token_factory):
    infraestructura_token = token_factory(
        7,
        sub="7",
        correo="infraestructura@sinergia.com",
        rol="Encargado de Area",
        nombre="Jefe Infraestructura",
    )
    response = client.patch(
        "/v1/onboarding/556",
        headers={"Authorization": f"Bearer {infraestructura_token}"},
        json={"estado": "En proceso", "especificaciones": "Equipo asignado"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["id"] == 556
    assert payload["estado"] == "En proceso"
    assert payload["especificaciones"] == "Equipo asignado"


def test_update_onboarding_request_keeps_destinatario_fixed(client, token_factory):
    jefe_token = token_factory(
        7,
        sub="7",
        correo="infraestructura@sinergia.com",
        rol="Encargado de Area",
        nombre="Jefe Infraestructura",
    )
    response = client.patch(
        "/v1/onboarding/556",
        headers={"Authorization": f"Bearer {jefe_token}"},
        json={"estado": "En proceso"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["id"] == 556
    assert payload["estado"] == "En proceso"
    assert payload["destinatario"] == "Jefe de Infraestructura y Mantenimiento"


def test_update_onboarding_request_by_rrhh(client, rrhh_token):
    response = client.patch(
        "/v1/onboarding/321",
        headers={"Authorization": f"Bearer {rrhh_token}"},
        json={"estado": "Finalizado"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["id"] == 321
    assert payload["estado"] == "Finalizado"


def test_update_onboarding_request_forbidden_for_unassigned_user(client, token_factory):
    operador_token = token_factory(
        44,
        sub="44",
        correo="operador@sinergia.com",
        rol="Operador",
        nombre="Operador",
    )
    response = client.patch(
        "/v1/onboarding/556",
        headers={"Authorization": f"Bearer {operador_token}"},
        json={"estado": "En proceso"},
    )
    assert response.status_code == 403


def test_update_onboarding_request_without_payload_returns_400(client, rrhh_token):
    response = client.patch(
        "/v1/onboarding/321",
        headers={"Authorization": f"Bearer {rrhh_token}"},
        json={},
    )
    assert response.status_code == 400


def test_advance_onboarding_request_state_moves_to_next_state(client, token_factory):
    infraestructura_token = token_factory(
        7,
        sub="7",
        correo="infraestructura@sinergia.com",
        rol="Encargado de Area",
        nombre="Jefe Infraestructura",
    )
    response = client.post(
        "/v1/onboarding/solicitudes/556/estado/siguiente",
        headers={"Authorization": f"Bearer {infraestructura_token}"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["id"] == 556
    assert payload["estado"] == "En proceso"


def test_advance_onboarding_request_state_in_final_returns_400(client, rrhh_token):
    response = client.post(
        "/v1/onboarding/solicitudes/557/estado/siguiente",
        headers={"Authorization": f"Bearer {rrhh_token}"},
    )
    assert response.status_code == 400


def test_advance_user_onboarding_state_moves_to_next_state(client, rrhh_token):
    response = client.post(
        "/v1/onboarding/usuarios/48/estado-onboarding/siguiente",
        headers={"Authorization": f"Bearer {rrhh_token}"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["id"] == 48
    assert payload["estado_anterior"] == "Pendiente"
    assert payload["estado_actual"] == "En proceso"


def test_advance_user_onboarding_state_allows_user_to_finalize_own_process(client, token_factory):
    user_token = token_factory(
        47,
        sub="47",
        correo="soporte1@sinergia.com",
        rol="Operador",
        nombre="Técnico Soporte",
    )
    response = client.post(
        "/v1/onboarding/usuarios/47/estado-onboarding/siguiente",
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["id"] == 47
    assert payload["estado_anterior"] == "En proceso"
    assert payload["estado_actual"] == "Finalizado"


def test_advance_user_onboarding_state_forbidden_for_other_user(client, rrhh_token):
    response = client.post(
        "/v1/onboarding/usuarios/49/estado-onboarding/siguiente",
        headers={"Authorization": f"Bearer {rrhh_token}"},
    )
    assert response.status_code == 403


def test_reject_onboarding_request_by_assigned_resolver(client, token_factory):
    infraestructura_token = token_factory(
        7,
        sub="7",
        correo="infraestructura@sinergia.com",
        rol="Encargado de Area",
        nombre="Jefe Infraestructura",
    )
    response = client.post(
        "/v1/onboarding/solicitudes/556/rechazar",
        headers={"Authorization": f"Bearer {infraestructura_token}"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["id"] == 556
    assert payload["estado"] == "Rechazado"


def test_reject_onboarding_request_in_final_returns_400(client, rrhh_token):
    response = client.post(
        "/v1/onboarding/solicitudes/557/rechazar",
        headers={"Authorization": f"Bearer {rrhh_token}"},
    )
    assert response.status_code == 400


def test_onboarding_history_visible_for_rrhh(client, rrhh_token):
    response = client.get(
        "/v1/onboarding/solicitudes/321/historial",
        headers={"Authorization": f"Bearer {rrhh_token}"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 1
    assert payload[0]["id_solicitud"] == 321
    assert payload[0]["tipo_cambio"] == "CREACION"


def test_onboarding_history_visible_for_direct_boss(client, token_factory):
    jefe_token = token_factory(
        7,
        sub="7",
        correo="infraestructura@sinergia.com",
        rol="Encargado de Area",
        nombre="Jefe Infraestructura",
    )
    response = client.get(
        "/v1/onboarding/solicitudes/556/historial",
        headers={"Authorization": f"Bearer {jefe_token}"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 2
    assert payload[0]["id_solicitud"] == 556


def test_onboarding_history_forbidden_for_unrelated_user(client, token_factory):
    operador_token = token_factory(
        44,
        sub="44",
        correo="operador@sinergia.com",
        rol="Operador",
        nombre="Operador",
    )
    response = client.get(
        "/v1/onboarding/solicitudes/556/historial",
        headers={"Authorization": f"Bearer {operador_token}"},
    )
    assert response.status_code == 403


def test_onboarding_history_not_found_returns_404(client, rrhh_token):
    response = client.get(
        "/v1/onboarding/solicitudes/999/historial",
        headers={"Authorization": f"Bearer {rrhh_token}"},
    )
    assert response.status_code == 404


def test_onboarding_history_without_token_returns_401(client):
    response = client.get("/v1/onboarding/solicitudes/321/historial")
    assert response.status_code == 401
