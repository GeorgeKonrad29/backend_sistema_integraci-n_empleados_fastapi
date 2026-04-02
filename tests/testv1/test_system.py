def test_v1_root_endpoint(client):
    response = client.get("/v1/")
    assert response.status_code == 200
    payload = response.json()
    assert "message" in payload


def test_v1_hi_endpoint(client):
    response = client.get("/v1/hi/George")
    assert response.status_code == 200
    payload = response.json()
    assert payload["message"] == "Hello, George!"


def test_openapi_contains_v1_login_path(client):
    response = client.get("/openapi.json")
    assert response.status_code == 200
    paths = response.json().get("paths", {})
    assert "/v1/auth/login" in paths


def test_openapi_contains_auth_security_scheme(client):
    response = client.get("/openapi.json")
    assert response.status_code == 200
    components = response.json().get("components", {})
    security_schemes = components.get("securitySchemes", {})
    assert "HTTPBearer" in security_schemes
