import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

import app as cookie_app  # noqa: E402


@pytest.fixture
def client(tmp_path):
    cookie_app.app.config["TESTING"] = True
    cookie_app.app.config["DATABASE"] = str(tmp_path / "test.db")
    with cookie_app.app.test_client() as client:
        yield client


def test_health(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.get_json() == {"status": "ok"}


def test_menu_returns_all_available_items(client):
    response = client.get("/api/menu")
    assert response.status_code == 200
    menu = response.get_json()
    names = [item["name"] for item in menu]
    assert names == ["Jollof Rice Plate", "Fried Rice Plate", "Chicken Shawarma"]
    prices = {item["name"]: item["price"] for item in menu}
    assert prices["Chicken Shawarma"] == 15.0
    assert set(menu[0]) == {"id", "name", "description", "price"}


def test_menu_hides_unavailable_items(client):
    client.get("/api/menu")  # creates the database
    connection = cookie_app.get_connection()
    with connection:
        connection.execute(
            "UPDATE menu_items SET available = 0 WHERE name = 'Fried Rice Plate'"
        )
    connection.close()
    names = [item["name"] for item in client.get("/api/menu").get_json()]
    assert "Fried Rice Plate" not in names


def test_unknown_api_route_returns_json_404(client):
    response = client.get("/api/does-not-exist")
    assert response.status_code == 404
    assert response.get_json() == {"error": "Not Found", "status": 404}


def test_site_pages_are_served(client):
    assert b"Cooking with Cookie" in client.get("/").data
    assert client.get("/css/style.css").status_code == 200
    assert client.get("/js/script.js").status_code == 200
    assert client.get("/backend/app.py").status_code == 404
