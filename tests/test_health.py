import pytest


@pytest.mark.django_db
def test_health_ok(client):
    response = client.get("/api/v1/health/")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_home_page(client):
    assert client.get("/").status_code == 200
