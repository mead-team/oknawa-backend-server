from fastapi.testclient import TestClient


def test_get_api_health_check(client: TestClient):
    response = client.get("/api-health-check")
    content = response.json()
    assert response.status_code == 200


def test_get_redis_health_check(client: TestClient):
    response = client.get("/redis-health-check")
    content = response.json()
    assert response.status_code == 200
