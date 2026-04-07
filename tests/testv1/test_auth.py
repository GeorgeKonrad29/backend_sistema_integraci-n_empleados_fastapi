def test_auth_login_returns_token_and_cargo(client, monkeypatch):
    from src.api.v1.auth import login as login_module

    monkeypatch.setattr(login_module, "verify_password", lambda *_args, **_kwargs: True)
    response = client.post(
        "/v1/auth/login",
        json={"correo": "rrhh@sinergia.com", "contrasena": "cualquier-clave"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["token_type"] == "bearer"
    assert payload["access_token"]
    assert payload["user"]["cargo"] == 48


def test_auth_me_returns_authenticated_user(client, rrhh_token):
    response = client.get(
        "/v1/auth/me",
        headers={"Authorization": f"Bearer {rrhh_token}"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["user"]["cargo"] == 48


def test_auth_logout_returns_ok_with_token(client, rrhh_token):
    response = client.post(
        "/v1/auth/logout",
        headers={"Authorization": f"Bearer {rrhh_token}"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["message"] == "Logout exitoso"


def test_auth_cargos_requires_jwt_and_returns_list(client, rrhh_token):
    response = client.get(
        "/v1/auth/cargos",
        headers={"Authorization": f"Bearer {rrhh_token}"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert isinstance(payload, list)
    assert payload[0]["id"] == 1


def test_auth_cargo_by_id_returns_item(client, rrhh_token):
    response = client.get(
        "/v1/auth/cargos/1",
        headers={"Authorization": f"Bearer {rrhh_token}"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["id"] == 1
    assert payload["nombre_cargo"] == "Asamblea de Socios"


def test_auth_cargo_by_id_not_found_returns_404(client, rrhh_token):
    response = client.get(
        "/v1/auth/cargos/999",
        headers={"Authorization": f"Bearer {rrhh_token}"},
    )
    assert response.status_code == 404


def test_auth_signup_returns_activation_link_for_rrhh(client, rrhh_token, monkeypatch):
    from src.api.v1.auth import signin as signin_module

    async def fake_send_activation_email(*_args, **_kwargs):
        return True

    monkeypatch.setattr(signin_module, "send_activation_email", fake_send_activation_email)
    response = client.post(
        "/v1/auth/signup",
        headers={"Authorization": f"Bearer {rrhh_token}"},
        json={
            "nombre": "Usuario Nuevo",
            "correo": "nuevo@empresa.com",
            "contrasena": "",
            "rol": "Operador",
            "cargo": 44,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["user"]["cargo"] == 44
    assert "activation_link" in payload


def test_auth_signup_creates_default_onboarding_requests(client, rrhh_token, monkeypatch):
    from src.api.v1.auth import signin as signin_module

    called = {"value": False}

    async def fake_send_activation_email(*_args, **_kwargs):
        return True

    async def fake_create_default_onboarding_requests(*_args, **_kwargs):
        called["value"] = True

    monkeypatch.setattr(signin_module, "send_activation_email", fake_send_activation_email)
    monkeypatch.setattr(signin_module, "_create_default_onboarding_requests", fake_create_default_onboarding_requests)

    response = client.post(
        "/v1/auth/signup",
        headers={"Authorization": f"Bearer {rrhh_token}"},
        json={
            "nombre": "Usuario Nuevo 2",
            "correo": "nuevo2@empresa.com",
            "contrasena": "",
            "rol": "Operador",
            "cargo": 44,
        },
    )

    assert response.status_code == 200
    assert called["value"] is True


def test_auth_activate_password_updates_user_password(client):
    response = client.post(
        "/v1/auth/activate-password",
        json={
            "token": "token-de-prueba",
            "contrasena": "NuevaClaveSegura123",
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"


def test_auth_signup_without_token_returns_401(client):
    response = client.post(
        "/v1/auth/signup",
        json={
            "nombre": "Usuario Sin Token",
            "correo": "sin.token@empresa.com",
            "contrasena": "",
            "rol": "Operador",
            "cargo": 44,
        },
    )
    assert response.status_code == 401


def test_auth_cargos_without_token_returns_401(client):
    response = client.get("/v1/auth/cargos")
    assert response.status_code == 401


def test_auth_logout_without_token_returns_401(client):
    response = client.post("/v1/auth/logout")
    assert response.status_code == 401
