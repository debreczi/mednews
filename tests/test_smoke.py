"""Phase 0 smoke tests — verifies the app starts and health endpoint works."""


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "mednews-api"


def test_articles_empty(client):
    response = client.get("/articles")
    assert response.status_code == 200
    data = response.json()
    assert data["articles"] == []
    assert data["next_cursor"] is None
    assert data["total_count"] == 0


def test_search_empty(client):
    response = client.get("/search?q=test")
    assert response.status_code == 200
    assert response.json() == []
