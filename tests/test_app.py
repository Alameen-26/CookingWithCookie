import re
import sqlite3
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

import app as cookie_app  # noqa: E402


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    cookie_app.app.config["TESTING"] = True
    cookie_app.app.config["DATABASE"] = str(tmp_path / "test.db")
    cookie_app.app.config["CHAT_RATE_LIMIT"] = 10
    cookie_app.app.config["SHOW_PRICES"] = False
    cookie_app.chat_rate_limiter.reset()
    with cookie_app.app.test_client() as client:
        yield client


@pytest.fixture
def priced_client(client):
    cookie_app.app.config["SHOW_PRICES"] = True
    yield client
    cookie_app.app.config["SHOW_PRICES"] = False


PRICE_PATTERN = r"\$\s?\d|\d+\.\d\d|\bCAD\b"


def assert_no_price(text):
    assert not re.search(PRICE_PATTERN, text), text


def chat(client, message):
    return client.post("/api/chat", json={"message": message})


class FakeOpenAI:
    """Stands in for the OpenAI client and records what was sent."""

    def __init__(self, reply="AI reply", error=None):
        self.calls = []
        self.reply = reply
        self.error = error
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self.create))

    def create(self, **kwargs):
        self.calls.append(kwargs)
        if self.error:
            raise self.error
        message = SimpleNamespace(content=self.reply)
        return SimpleNamespace(choices=[SimpleNamespace(message=message)])


# ---------- Basic API ----------

def test_health(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.get_json() == {"status": "ok"}


def test_menu_returns_all_available_items_without_prices(client):
    response = client.get("/api/menu")
    assert response.status_code == 200
    menu = response.get_json()
    names = [item["name"] for item in menu]
    assert names == ["Jollof Rice Plate", "Fried Rice Plate", "Chicken Shawarma"]
    assert set(menu[0]) == {
        "id", "name", "description", "ingredients", "calories", "allergens"
    }


def test_menu_includes_prices_when_enabled(priced_client):
    menu = priced_client.get("/api/menu").get_json()
    assert [item["price"] for item in menu] == [18.0, 18.0, 15.0]


def test_prices_stay_in_the_database_while_hidden(client):
    client.get("/api/menu")
    assert [item["price"] for item in cookie_app.load_menu()] == [18.0, 18.0, 15.0]


@pytest.mark.parametrize(
    "value, expected",
    [(None, False), ("", False), ("false", False), ("0", False),
     ("true", True), ("1", True), ("YES", True), ("on", True)],
)
def test_show_prices_setting(monkeypatch, value, expected):
    if value is None:
        monkeypatch.delenv("SHOW_PRICES", raising=False)
    else:
        monkeypatch.setenv("SHOW_PRICES", value)
    assert cookie_app.env_flag("SHOW_PRICES") is expected


def test_calories_and_allergens_start_unconfirmed(client):
    for item in client.get("/api/menu").get_json():
        assert item["calories"] is None
        assert item["allergens"] is None
        assert item["ingredients"] == item["description"]


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


def test_old_database_is_migrated(client):
    # A cookie.db made by the first version has no nutrition columns.
    connection = sqlite3.connect(cookie_app.app.config["DATABASE"])
    connection.executescript(
        """
        CREATE TABLE menu_items (
            id INTEGER PRIMARY KEY, name TEXT NOT NULL, description TEXT,
            price REAL NOT NULL, available INTEGER NOT NULL DEFAULT 1
        );
        INSERT INTO menu_items (name, description, price)
        VALUES ('Jollof Rice Plate', 'Jollof rice, chicken, plantain and salad', 18.0);
        """
    )
    connection.close()
    menu = client.get("/api/menu").get_json()
    assert menu[0]["ingredients"] == "Jollof rice, chicken, plantain and salad"
    assert menu[0]["calories"] is None
    assert menu[0]["allergens"] is None


def test_unknown_api_route_returns_json_404(client):
    response = client.get("/api/does-not-exist")
    assert response.status_code == 404
    assert response.get_json() == {"error": "Not Found", "status": 404}


def test_site_pages_are_served(client):
    assert b"Cooking with Cookie" in client.get("/").data
    assert client.get("/css/style.css").status_code == 200
    assert client.get("/js/script.js").status_code == 200
    assert client.get("/backend/app.py").status_code == 404
    assert client.get("/.env").status_code == 404


# ---------- Chat validation ----------

@pytest.mark.parametrize(
    "kwargs",
    [
        {"data": "hello", "content_type": "text/plain"},
        {"data": "{not json", "content_type": "application/json"},
        {"json": ["hello"]},
        {"json": {}},
        {"json": {"message": ""}},
        {"json": {"message": "   "}},
        {"json": {"message": 42}},
        {"json": {"message": "x" * 501}},
    ],
)
def test_chat_rejects_bad_input(client, kwargs):
    response = client.post("/api/chat", **kwargs)
    assert response.status_code == 400
    assert "error" in response.get_json()


def test_chat_accepts_500_characters(client):
    assert chat(client, "x" * 500).status_code == 200


def test_chat_get_not_allowed(client):
    assert client.get("/api/chat").status_code == 405


def test_chat_rate_limit(client):
    cookie_app.app.config["CHAT_RATE_LIMIT"] = 3
    codes = [chat(client, "hi").status_code for _ in range(4)]
    assert codes == [200, 200, 200, 429]
    assert "Too many" in chat(client, "hi").get_json()["error"]


# ---------- Fallback mode (no API key) ----------

def test_fallback_used_without_key(client):
    data = chat(client, "Tell me about the jollof").get_json()
    assert data["source"] == "fallback"
    assert "Jollof Rice Plate" in data["reply"]
    assert_no_price(data["reply"])


@pytest.mark.parametrize(
    "question",
    ["How much is the jollof?", "What does the shawarma cost?", "prices?",
     "What's on the menu?", "Tell me about the fried rice", "hi", "party for 40"],
)
def test_fallback_never_states_prices_when_hidden(client, question):
    reply = chat(client, question).get_json()["reply"]
    assert_no_price(reply)


def test_fallback_price_question_says_coming_soon(client):
    reply = chat(client, "How much is the jollof?").get_json()["reply"]
    assert "Pricing is coming soon" in reply


def test_fallback_states_prices_when_enabled(priced_client):
    reply = chat(priced_client, "How much is the jollof?").get_json()["reply"]
    assert "$18.00 CAD" in reply
    listing = chat(priced_client, "What's on the menu?").get_json()["reply"]
    assert "Chicken Shawarma $15.00 CAD" in listing


def test_fallback_allergens_not_confirmed(client):
    reply = chat(client, "Does the shawarma have nuts?").get_json()["reply"]
    assert "Allergen information for the Chicken Shawarma hasn't been confirmed" in reply
    assert "cross-contamination" in reply
    assert "Jollof" not in reply


def test_fallback_calories_not_confirmed(client):
    reply = chat(client, "How many calories are in the fried rice?").get_json()["reply"]
    assert "Calorie information for the Fried Rice Plate hasn't been confirmed" in reply
    assert "cross-contamination" not in reply  # "nutrition"/"calories" isn't an allergy


def test_fallback_uses_confirmed_values(client):
    client.get("/api/menu")
    connection = cookie_app.get_connection()
    with connection:
        connection.execute(
            "UPDATE menu_items SET calories = 650, allergens = 'Soy, Sesame' "
            "WHERE name = 'Chicken Shawarma'"
        )
    connection.close()
    calories = chat(client, "calories in the shawarma?").get_json()["reply"]
    assert "about 650 calories" in calories
    allergens = chat(client, "shawarma allergens?").get_json()["reply"]
    assert "contains: Soy, Sesame" in allergens
    assert "cross-contamination" in allergens


def test_fallback_does_not_mention_beef_shawarma(client):
    reply = chat(client, "Tell me about the shawarma").get_json()["reply"]
    assert "Beef" not in reply


# ---------- AI mode (OpenAI client mocked) ----------

def test_ai_reply_used_when_key_set(client, monkeypatch):
    fake = FakeOpenAI(reply="The Jollof Rice Plate comes with chicken and plantain.")
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("OPENAI_MODEL", "test-model")
    monkeypatch.setattr(cookie_app, "get_ai_client", lambda: fake)

    data = chat(client, "What comes with jollof?").get_json()
    assert data == {
        "reply": "The Jollof Rice Plate comes with chicken and plantain.",
        "source": "ai",
    }

    sent = fake.calls[0]
    assert sent["model"] == "test-model"
    system, user = sent["messages"]
    assert user == {"role": "user", "content": "What comes with jollof?"}
    assert "- Jollof Rice Plate | description:" in system["content"]
    assert "allergens: NOT CONFIRMED" in system["content"]
    assert "Never guess" in system["content"]
    assert "Pricing has not been released yet" in system["content"]
    assert_no_price(system["content"])
    assert "test-key" not in system["content"]


def test_ai_prompt_includes_prices_when_enabled(priced_client, monkeypatch):
    fake = FakeOpenAI(reply="The Jollof Rice Plate is $18.00 CAD.")
    monkeypatch.setattr(cookie_app, "get_ai_client", lambda: fake)
    data = chat(priced_client, "How much is jollof?").get_json()
    assert data["reply"] == "The Jollof Rice Plate is $18.00 CAD."
    system = fake.calls[0]["messages"][0]["content"]
    assert "Jollof Rice Plate | price: $18.00 CAD" in system
    assert "Pricing has not been released yet" not in system


def test_ai_price_leak_is_blocked_when_hidden(client, monkeypatch):
    fake = FakeOpenAI(reply="It's about $20 a plate.")
    monkeypatch.setattr(cookie_app, "get_ai_client", lambda: fake)
    reply = chat(client, "Roughly what does it run?").get_json()["reply"]
    assert reply.startswith("Pricing is coming soon")


# ---------- Quote API ----------

def test_quote_disabled_when_prices_hidden(client):
    response = client.post("/api/quote", json={"items": [{"id": 1, "quantity": 2}]})
    assert response.status_code == 403
    assert response.get_json() == {"error": "Pricing is not available yet."}


def test_quote_when_prices_enabled(priced_client):
    response = priced_client.post(
        "/api/quote",
        json={"items": [{"id": 1, "quantity": 2}, {"id": 3, "quantity": 1}]},
    )
    assert response.status_code == 200
    quote = response.get_json()
    assert quote["total"] == 51.0
    assert quote["currency"] == "CAD"
    assert quote["items"][0] == {
        "id": 1, "name": "Jollof Rice Plate", "quantity": 2,
        "unit_price": 18.0, "line_total": 36.0,
    }


@pytest.mark.parametrize(
    "body",
    [None, {}, {"items": []}, {"items": [{"id": 99, "quantity": 1}]},
     {"items": [{"id": 1, "quantity": -1}]}, {"items": [{"id": 1, "quantity": 101}]},
     {"items": [{"id": 1, "quantity": 1.5}]}, {"items": [{"id": 1, "quantity": True}]},
     {"items": ["jollof"]}],
)
def test_quote_rejects_bad_input(priced_client, body):
    response = priced_client.post("/api/quote", json=body)
    assert response.status_code == 400
    assert "error" in response.get_json()


def test_ai_reply_gets_allergy_note(client, monkeypatch):
    fake = FakeOpenAI(reply="Allergen info for the shawarma hasn't been confirmed.")
    monkeypatch.setattr(cookie_app, "get_ai_client", lambda: fake)
    reply = chat(client, "Is the shawarma safe for a peanut allergy?").get_json()["reply"]
    assert "cross-contamination" in reply


def test_ai_failure_falls_back(client, monkeypatch):
    fake = FakeOpenAI(error=RuntimeError("API down"))
    monkeypatch.setattr(cookie_app, "get_ai_client", lambda: fake)
    data = chat(client, "Any allergens in jollof?").get_json()
    assert data["source"] == "fallback"
    assert "hasn't been confirmed" in data["reply"]


def test_ai_empty_reply_falls_back(client, monkeypatch):
    monkeypatch.setattr(cookie_app, "get_ai_client", lambda: FakeOpenAI(reply=""))
    assert chat(client, "hi").get_json()["source"] == "fallback"


def test_get_ai_client_needs_key(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    assert cookie_app.get_ai_client() is None
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    assert cookie_app.get_ai_client() is not None


# ---------- Static files ----------

def test_static_site_contains_no_prices(client):
    html = client.get("/").get_data(as_text=True)
    script = client.get("/js/script.js").get_data(as_text=True)
    assert not re.search(r"\$\s?\d", html)
    assert "data-price=" not in html
    assert not re.search(r"\$\s?\d", script)


# ---------- Contact details ----------

def test_contact_details_on_site(client):
    html = client.get("/").get_data(as_text=True)
    assert "mailto:alajiadeniyi@gmail.com?subject=Bulk%20Order%20Enquiry" in html
    assert html.count('href="tel:+19024951781"') == 3
    assert "example.com" not in html


@pytest.mark.parametrize(
    "question",
    ["Can you cater a party for 60?", "Is the jollof gluten free?", "How much is it?"],
)
def test_fallback_gives_contact_details(client, question):
    reply = chat(client, question).get_json()["reply"]
    assert "alajiadeniyi@gmail.com" in reply
    assert "(902) 495-1781" in reply


def test_ai_prompt_includes_contact_details(client, monkeypatch):
    fake = FakeOpenAI(reply="Sure!")
    monkeypatch.setattr(cookie_app, "get_ai_client", lambda: fake)
    chat(client, "hello")
    system = fake.calls[0]["messages"][0]["content"]
    assert "CONTACT: email alajiadeniyi@gmail.com, phone (902) 495-1781" in system


@pytest.mark.parametrize(
    "question",
    ["Do you deliver?", "Where are you located?", "Do you serve Dartmouth?"],
)
def test_fallback_mentions_service_area(client, question):
    reply = chat(client, question).get_json()["reply"]
    assert "Halifax area, Nova Scotia" in reply
    assert "alajiadeniyi@gmail.com" in reply


def test_service_area_on_site_and_in_ai_prompt(client, monkeypatch):
    html = client.get("/").get_data(as_text=True)
    assert html.count("Serving the Halifax area, Nova Scotia.") == 2
    fake = FakeOpenAI(reply="Sure!")
    monkeypatch.setattr(cookie_app, "get_ai_client", lambda: fake)
    chat(client, "Do you deliver?")
    assert "SERVICE AREA: the Halifax area, Nova Scotia" in fake.calls[0]["messages"][0]["content"]


# ---------- Cooking lessons ----------

def test_lessons_section_on_site(client):
    html = client.get("/").get_data(as_text=True)
    assert 'href="#lessons"' in html and 'id="lessons"' in html
    assert "mailto:alajiadeniyi@gmail.com?subject=Cooking%20Lesson%20Enquiry" in html
    assert "details on request" in html


@pytest.mark.parametrize(
    "question",
    ["Can I get the jollof recipe?", "How do I make fried rice?",
     "Do you teach cooking classes?", "I want to learn to cook shawarma",
     "How much are your lessons?"],
)
def test_fallback_mentions_lessons(client, question):
    reply = chat(client, question).get_json()["reply"]
    assert "cooking lessons" in reply
    assert "Cooking Lesson Enquiry" in reply
    assert "(902) 495-1781" in reply
    assert_no_price(reply)


def test_ai_prompt_mentions_lessons(client, monkeypatch):
    fake = FakeOpenAI(reply="Sure!")
    monkeypatch.setattr(cookie_app, "get_ai_client", lambda: fake)
    chat(client, "How do I cook jollof?")
    system = fake.calls[0]["messages"][0]["content"]
    assert "COOKING LESSONS:" in system
    assert "Never state lesson prices" in system
