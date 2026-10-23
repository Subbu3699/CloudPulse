
def test_health_endpoint(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_list_monitored_apis(client):
    response = client.get("/api/v1/monitored-apis")
    assert response.status_code == 200
    assert response.json() == []


def test_list_incidents(client):
    response = client.get("/api/v1/incidents")
    assert response.status_code == 200
    assert response.json() == []


def test_invalid_api_returns_404(client):
    response = client.get("/api/v1/monitored-apis/999999")
    assert response.status_code == 404


def test_create_monitored_api(client):
    response = client.post(
        "/api/v1/monitored-apis",
        json={
            "name": "Test API",
            "url": "https://example.com/",
            "method": "GET",
            "check_interval_seconds": 60,
            "timeout_seconds": 10,
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test API"
    assert data["method"] == "GET"
    assert data["is_active"] is True


def test_update_monitored_api(client):
    created = client.post(
        "/api/v1/monitored-apis",
        json={
            "name": "Original API",
            "url": "https://example.com/",
            "method": "GET",
            "check_interval_seconds": 60,
            "timeout_seconds": 10,
        },
    )
    api_id = created.json()["id"]

    response = client.put(
        f"/api/v1/monitored-apis/{api_id}",
        json={
            "name": "Updated API",
            "url": "https://jsonplaceholder.typicode.com/posts/1",
            "method": "GET",
            "check_interval_seconds": 60,
            "timeout_seconds": 10,
        },
    )

    assert response.status_code == 200
    assert response.json()["name"] == "Updated API"
    assert "jsonplaceholder.typicode.com" in response.json()["url"]


def test_update_missing_api_returns_404(client):
    response = client.put(
        "/api/v1/monitored-apis/999999",
        json={
            "name": "Missing API",
            "url": "https://example.com/",
            "method": "GET",
            "check_interval_seconds": 60,
            "timeout_seconds": 10,
        },
    )

    assert response.status_code == 404


def test_create_api_rejects_empty_name(client):
    response = client.post(
        "/api/v1/monitored-apis",
        json={
            "name": "",
            "url": "https://example.com/",
            "method": "GET",
            "check_interval_seconds": 60,
            "timeout_seconds": 10,
        },
    )
    assert response.status_code == 422


def test_create_api_rejects_invalid_url(client):
    response = client.post(
        "/api/v1/monitored-apis",
        json={
            "name": "Invalid URL Test",
            "url": "not-a-valid-url",
            "method": "GET",
            "check_interval_seconds": 60,
            "timeout_seconds": 10,
        },
    )
    assert response.status_code == 422


def test_create_api_rejects_invalid_method(client):
    response = client.post(
        "/api/v1/monitored-apis",
        json={
            "name": "Invalid Method Test",
            "url": "https://example.com/",
            "method": "OPTIONS",
            "check_interval_seconds": 60,
            "timeout_seconds": 10,
        },
    )
    assert response.status_code == 422


def test_create_api_rejects_too_short_interval(client):
    response = client.post(
        "/api/v1/monitored-apis",
        json={
            "name": "Invalid Interval Test",
            "url": "https://example.com/",
            "method": "GET",
            "check_interval_seconds": 5,
            "timeout_seconds": 10,
        },
    )
    assert response.status_code == 422


def test_create_api_rejects_invalid_timeout(client):
    response = client.post(
        "/api/v1/monitored-apis",
        json={
            "name": "Invalid Timeout Test",
            "url": "https://example.com/",
            "method": "GET",
            "check_interval_seconds": 60,
            "timeout_seconds": 0,
        },
    )
    assert response.status_code == 422
