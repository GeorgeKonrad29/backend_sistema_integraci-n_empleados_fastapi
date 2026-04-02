def test_assign_workstation_returns_valid_coordinate(client, servicios_generales_token):
    response = client.post(
        "/v1/puesto-trabajo/asignar",
        headers={"Authorization": f"Bearer {servicios_generales_token}"},
        json={
            "id_empleado": 48,
            "piso": 1,
            "fila": 1,
            "columna": 2,
            "tipo_puesto": "Fijo",
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["coordenadas"] == "P1-F01-C02"
    assert payload["piso"] == 1
    assert payload["fila"] == 1
    assert payload["columna"] == 2


def test_assign_workstation_rejects_rrhh_token(client, rrhh_token):
    response = client.post(
        "/v1/puesto-trabajo/asignar",
        headers={"Authorization": f"Bearer {rrhh_token}"},
        json={
            "id_empleado": 48,
            "piso": 1,
            "fila": 1,
            "columna": 2,
            "tipo_puesto": "Fijo",
        },
    )
    assert response.status_code == 403


def test_assign_workstation_rejects_invalid_floor(client, servicios_generales_token):
    response = client.post(
        "/v1/puesto-trabajo/asignar",
        headers={"Authorization": f"Bearer {servicios_generales_token}"},
        json={
            "id_empleado": 48,
            "piso": 3,
            "fila": 1,
            "columna": 1,
            "tipo_puesto": "Fijo",
        },
    )
    assert response.status_code == 422


def test_assign_workstation_rejects_invalid_grid_position(client, servicios_generales_token):
    response = client.post(
        "/v1/puesto-trabajo/asignar",
        headers={"Authorization": f"Bearer {servicios_generales_token}"},
        json={
            "id_empleado": 48,
            "piso": 1,
            "fila": 21,
            "columna": 1,
            "tipo_puesto": "Fijo",
        },
    )
    assert response.status_code == 422


def test_assign_workstation_rejects_occupied_coordinate(client, servicios_generales_token):
    response = client.post(
        "/v1/puesto-trabajo/asignar",
        headers={"Authorization": f"Bearer {servicios_generales_token}"},
        json={
            "id_empleado": 48,
            "piso": 1,
            "fila": 1,
            "columna": 1,
            "tipo_puesto": "Fijo",
        },
    )
    assert response.status_code == 409


def test_workstation_map_returns_two_floors(client, rrhh_token):
    response = client.get(
        "/v1/puesto-trabajo/mapa",
        headers={"Authorization": f"Bearer {rrhh_token}"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert len(payload["pisos"]) == 2
    assert payload["pisos"][0]["piso"] == 1
    assert payload["pisos"][1]["piso"] == 2
    assert len(payload["pisos"][0]["grid"]) == 20
    assert len(payload["pisos"][0]["grid"][0]) == 20


def test_occupied_workstations_returns_only_assigned_ones(client, rrhh_token):
    response = client.get(
        "/v1/puesto-trabajo/ocupadas",
        headers={"Authorization": f"Bearer {rrhh_token}"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["count"] == 1
    assert payload["ocupadas"][0]["coordenadas"] == "P1-F01-C01"
    assert payload["ocupadas"][0]["nombre_empleado"] == "Gerente RRHH"
    assert payload["ocupadas"][0]["area"] == "Gerencia de talento humano"
    assert payload["ocupadas"][0]["ocupado"] is True


def test_occupied_workstations_without_token_returns_401(client):
    response = client.get("/v1/puesto-trabajo/ocupadas")
    assert response.status_code == 401
