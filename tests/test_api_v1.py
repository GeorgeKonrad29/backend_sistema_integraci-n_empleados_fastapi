from fastapi.testclient import TestClient

from src.main import app


client = TestClient(app)


def test_v1_root_endpoint():
    response = client.get("/v1/")
    assert response.status_code == 200
    payload = response.json()
    assert "message" in payload


def test_v1_hi_endpoint():
    response = client.get("/v1/hi/George")
    assert response.status_code == 200
    payload = response.json()
    assert payload["message"] == "Hello, George!"


def test_openapi_contains_v1_login_path():
    response = client.get("/openapi.json")
    assert response.status_code == 200
    paths = response.json().get("paths", {})
    assert "/v1/auth/login" in paths
