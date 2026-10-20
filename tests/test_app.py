import re
import sqlite3
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

import app as cookie_app  # noqa: E402

MENU_NAMES = [
    "Jollof Rice & Peppered Chicken", "Fried Rice", "Nigerian Shawarma",
    "Puff-Puff", "Meat Pie", "Jollof Spaghetti", "Beef Stir-fry Spaghetti",
    "Grilled Chicken, Meat or Fish", "Stew (Beef)", "Stew (Chicken)", "Stew (Fish)", "Egusi",
    "Beans Porridge",
]
EMAIL = "alajiadeniyi@gmail.com"
PHONE = "(902) 495-1781"
PRICE_PATTERN = r"\$\s?\d|\d+\.\d\d|\bCAD\b"


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    cookie_app.app.config["TESTING"] = True
    cookie_app.app.config["DATABASE"] = str(tmp_path / "test.db")
    cookie_app.app.config["CHAT_RATE_LIMIT"] = 100
    cookie_app.app.config["SHOW_PRICES"] = False
    cookie_app.chat_rate_limiter.reset()
    with cookie_app.app.test_client() as client:
        yield client


@pytest.fixture
def priced_client(client):
    cookie_app.app.config["SHOW_PRICES"] = True
    yield client
    cookie_app.app.config["SHOW_PRICES"] = False


def assert_no_price(text):
    assert not re.search(PRICE_PATTERN, text), text


def assert_no_contact(text):
    assert EMAIL not in text and PHONE not in text, text


def chat(client, message):
    return client.post("/api/chat", json={"message": message})


def reply(client, message):
    return chat(client, message).get_json()["reply"]


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


def use_fake_ai(monkeypatch, fake):
    monkeypatch.setattr(cookie_app, "get_ai_client", lambda: fake)
    return fake


# ---------- Menu data ----------

def test_health(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.get_json() == {"status": "ok"}


def test_full_menu_is_seeded(client):
    menu = client.get("/api/menu").get_json()
    assert [item["name"] for item in menu] == MENU_NAMES


def test_menu_fields_and_safety_flags(client):
    for item in client.get("/api/menu").get_json():
        assert set(item) == {
            "id", "name", "description", "ingredients", "ingredients_verified",
            "calories", "allergens", "allergens_verified", "recipe_steps",
            "options", "image", "image_alt",
        }
        assert item["calories"] is None
        assert item["ingredients_verified"] is False
        assert item["allergens_verified"] is False
        assert item["ingredients"] and item["allergens"] and item["description"]
        assert item["recipe_steps"].startswith("1. ")
        assert item["image"].startswith("images/") and item["image"] != "images/placeholder-dish.svg"
        assert len(item["image_alt"]) > 15


def test_seed_allergens_follow_ingredients(client):
    menu = {item["name"]: item for item in client.get("/api/menu").get_json()}
    assert "Shellfish" in menu["Fried Rice"]["allergens"]
    assert "shrimp" in menu["Fried Rice"]["ingredients"]
    assert "Crustaceans" in menu["Egusi"]["allergens"]
    assert "Fish" in menu["Stew (Fish)"]["allergens"]
    assert "Eggs" in menu["Nigerian Shawarma"]["allergens"]
    assert "Wheat" in menu["Puff-Puff"]["allergens"]


def test_menu_prices_hidden_by_default_but_kept_in_db(client):
    assert all("price" not in item for item in client.get("/api/menu").get_json())
    prices = [item["price"] for item in cookie_app.load_menu()]
    assert len(prices) == 13 and all(15 <= p <= 25 for p in prices)


def test_menu_includes_prices_when_enabled(priced_client):
    menu = priced_client.get("/api/menu").get_json()
    assert all(15 <= item["price"] <= 25 for item in menu)


def test_menu_hides_unavailable_items(client):
    client.get("/api/menu")
    connection = cookie_app.get_connection()
    with connection:
        connection.execute("UPDATE menu_items SET available = 0 WHERE name = 'Egusi'")
    connection.close()
    names = [item["name"] for item in client.get("/api/menu").get_json()]
    assert "Egusi" not in names and len(names) == 12


def test_old_database_is_backed_up_and_rebuilt(client):
    db_path = Path(cookie_app.app.config["DATABASE"])
    connection = sqlite3.connect(db_path)
    connection.executescript(
        """
        CREATE TABLE menu_items (
            id INTEGER PRIMARY KEY, name TEXT NOT NULL, description TEXT,
            price REAL NOT NULL, available INTEGER NOT NULL DEFAULT 1
        );
        INSERT INTO menu_items (name, description, price)
        VALUES ('Jollof Rice Plate', 'Old item', 18.0);
        """
    )
    connection.close()
    names = [item["name"] for item in client.get("/api/menu").get_json()]
    assert names == MENU_NAMES
    backup = db_path.with_name("test.v0-backup.db")
    assert backup.exists()
    old = sqlite3.connect(backup)
    assert old.execute("SELECT name FROM menu_items").fetchall() == [("Jollof Rice Plate",)]
    old.close()


def test_current_database_is_kept(client):
    client.get("/api/menu")
    connection = cookie_app.get_connection()
    with connection:
        connection.execute("UPDATE menu_items SET calories = 700 WHERE name = 'Egusi'")
    connection.close()
    menu = {i["name"]: i for i in client.get("/api/menu").get_json()}
    assert menu["Egusi"]["calories"] == 700


def test_unknown_api_route_returns_json_404(client):
    response = client.get("/api/does-not-exist")
    assert response.status_code == 404
    assert response.get_json() == {"error": "Not Found", "status": 404}


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


def test_dirty_rice_removed_everywhere(client):
    names = [item["name"] for item in client.get("/api/menu").get_json()]
    assert "Dirty Rice" not in names
    assert "Dirty Rice" not in cookie_app.SCHEMA_PATH.read_text(encoding="utf-8")
    assert "Dirty Rice" not in client.get("/").get_data(as_text=True)
    assert "Dirty Rice" not in reply(client, "What's on the menu?")


def test_version_2_database_drops_dirty_rice(client):
    db_path = Path(cookie_app.app.config["DATABASE"])
    connection = sqlite3.connect(db_path)
    connection.executescript(
        """
        PRAGMA user_version = 2;
        CREATE TABLE menu_items (
            id INTEGER PRIMARY KEY, name TEXT NOT NULL, description TEXT,
            price REAL NOT NULL, available INTEGER NOT NULL DEFAULT 1,
            ingredients TEXT, ingredients_verified INTEGER NOT NULL DEFAULT 0,
            calories INTEGER, allergens TEXT,
            allergens_verified INTEGER NOT NULL DEFAULT 0, recipe_steps TEXT
        );
        INSERT INTO menu_items (name, description, price) VALUES ('Dirty Rice', 'Old', 18.0);
        """
    )
    connection.close()
    names = [item["name"] for item in client.get("/api/menu").get_json()]
    assert names == MENU_NAMES
    assert db_path.with_name("test.v2-backup.db").exists()


def test_grilled_plate_is_modelled_like_other_dishes(client):
    menu = {item["name"]: item for item in client.get("/api/menu").get_json()}
    grilled = menu["Grilled Chicken, Meat or Fish"]
    assert "price" not in grilled
    assert grilled["calories"] is None and grilled["allergens_verified"] is False
    assert "Fish (fish option)" in grilled["allergens"]
    for word in ("chicken", "beef", "fish", "sweet potatoes", "fries", "plantain"):
        assert word in grilled["options"].lower()
    for word in ("sweet potatoes", "fries", "plantain"):
        assert word in grilled["recipe_steps"].lower()
    price = {i["name"]: i["price"] for i in cookie_app.load_menu()}["Grilled Chicken, Meat or Fish"]
    assert 15 <= price <= 25
    assert all(item["options"] is None for name, item in menu.items() if name != grilled["name"])


def test_fallback_teaches_grilled_plate(client):
    text = reply(client, "How do I make grilled fish and plantain?")
    assert "Here's a typical way to make Grilled Chicken, Meat or Fish" in text
    assert "plantain" in text and "\n1. " in text
    assert_no_contact(text)
    about = reply(client, "Tell me about the grilled chicken")
    assert "sweet potatoes, fries or fried plantain" in about
    assert_no_price(about)
    fish = reply(client, "Does the grilled fish have fish allergens?")
    assert "Fish (fish option)" in fish and "cross-contamination" in fish


def test_ai_prompt_includes_grilled_choices(client, monkeypatch):
    fake = use_fake_ai(monkeypatch, FakeOpenAI(reply="Sure!"))
    chat(client, "hello")
    system = fake.calls[0]["messages"][0]["content"]
    assert "## Grilled Chicken, Meat or Fish\n" in system
    assert "Customer choices: Protein: chicken, meat (beef) or fish." in system
    assert "Dirty Rice" not in system


# ---------- Website ----------

def test_site_files_are_served(client):
    assert client.get("/css/style.css").status_code == 200
    assert client.get("/js/script.js").status_code == 200
    assert client.get("/images/placeholder-dish.svg").status_code == 200
    for item in cookie_app.load_menu():
        response = client.get("/" + item["image"])
        assert response.status_code == 200, item["image"]
        assert b"data:image/jpeg;base64," in response.data
    assert client.get("/backend/app.py").status_code == 404
    assert client.get("/.env").status_code == 404


def test_site_shows_all_dishes_without_prices(client):
    html = client.get("/").get_data(as_text=True)
    assert html.count('class="meal-card"') == 13
    for name in MENU_NAMES:
        assert f"<h3>{name.replace('&', '&amp;')}</h3>" in html
    assert not re.search(r"\$\s?\d", html)
    assert "data-price=" not in html
    assert "placeholder-dish.svg\"" not in html.replace("this.src='images/placeholder-dish.svg'", "")
    assert html.count("onerror=\"this.onerror=null; this.src='images/placeholder-dish.svg';\"") == 13
    assert html.count('class="learn-button"') == 13
    for item in cookie_app.load_menu():
        assert f'src="{item["image"]}"' in html


def test_site_has_photo_credits_link(client):
    html = client.get("/").get_data(as_text=True)
    assert "images/CREDITS.md" in html and "Photo credits" in html
    assert (cookie_app.PROJECT_ROOT / "images" / "CREDITS.md").exists()
    assert not re.search(r"\$\s?\d", client.get("/js/script.js").get_data(as_text=True))


def test_site_contact_details(client):
    html = client.get("/").get_data(as_text=True)
    assert f"mailto:{EMAIL}?subject=Bulk%20Order%20Enquiry" in html
    assert f"mailto:{EMAIL}?subject=Pickup%20Order" in html
    assert html.count('href="tel:+19024951781"') == 3  # order summary, bulk, footer
    assert html.count("Serving the Halifax area, Nova Scotia.") == 2
    assert "example.com" not in html


def test_lessons_section_points_to_ask_cookie(client):
    html = client.get("/").get_data(as_text=True)
    start = html.index('id="lessons"')
    section = html[start:html.index("</section>", start)]
    assert 'href="#assistant"' in section
    assert "Ask Cookie for a Recipe" in section
    assert "tel:" not in section  # no phone for recipe questions
    assert 'href="#lessons"' in html


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


# ---------- Fallback mode (no API key) ----------

def test_fallback_used_without_key(client):
    data = chat(client, "Tell me about the egusi").get_json()
    assert data["source"] == "fallback"
    assert "melon-seed soup" in data["reply"]


@pytest.mark.parametrize(
    "question, dish",
    [
        ("How do I make jollof rice?", "Jollof Rice & Peppered Chicken"),
        ("Can I get the beef stew recipe?", "Stew (Beef)"),
        ("how to make puff puff", "Puff-Puff"),
        ("What are the steps for egusi?", "Egusi"),
        ("How do I cook beans porridge?", "Beans Porridge"),
        ("how do you make meat pie at home", "Meat Pie"),
    ],
)
def test_fallback_answers_recipes_itself(client, question, dish):
    text = reply(client, question)
    assert f"Here's a typical way to make {dish}" in text
    assert "\n1. " in text and "\n2. " in text
    assert_no_contact(text)
    assert_no_price(text)


def test_every_dish_has_a_fallback_recipe(client):
    for item in cookie_app.load_menu():
        text = cookie_app.recipe_text(item)
        assert item["recipe_steps"] in text


def test_fallback_asks_which_dish_when_unclear(client):
    text = reply(client, "How do I make stew?")
    assert "Stew (Beef)" in text and "Stew (Chicken)" in text and "Stew (Fish)" in text
    general = reply(client, "Can you share a recipe?")
    assert "Egusi" in general and "Which one" in general
    assert_no_contact(general)


def test_fallback_recipe_with_allergen_adds_note(client):
    text = reply(client, "How do I make egusi without crayfish?")
    assert "Here's a typical way to make Egusi" in text
    assert "cross-contamination" in text


def test_fallback_allergens_are_likely_not_verified(client):
    text = reply(client, "Does the fried rice have shellfish?")
    assert "Fried Rice likely contains (based on a typical recipe, not verified)" in text
    assert "Shellfish (shrimp)" in text
    assert "cross-contamination" in text
    assert "severe allergy" in text
    assert_no_contact(text)


def test_fallback_allergen_not_listed_is_still_unverified(client):
    text = reply(client, "Is the meat pie safe for a nut allergy?")
    assert "Nuts: not listed in its typical recipe, but that hasn't been verified." in text
    assert "safe for you" in text


def test_fallback_which_dishes_contain_allergen(client):
    text = reply(client, "Which dishes have fish?")
    assert "likely or possibly contain fish: Grilled Chicken, Meat or Fish, Stew (Fish), Egusi." in text


def test_fallback_allergen_question_without_dish(client):
    text = reply(client, "I have allergies, what should I know?")
    assert "Tell me which dish" in text
    assert "cross-contamination" in text


def test_fallback_calories_not_available(client):
    text = reply(client, "How many calories in the puff-puff?")
    assert text == "Calorie information for Puff-Puff isn't available yet."


def test_fallback_uses_verified_values(client):
    client.get("/api/menu")
    connection = cookie_app.get_connection()
    with connection:
        connection.execute(
            "UPDATE menu_items SET calories = 650, allergens = 'Wheat, Eggs', "
            "allergens_verified = 1, ingredients_verified = 1 WHERE name = 'Meat Pie'"
        )
    connection.close()
    assert "about 650 calories" in reply(client, "calories in the meat pie?")
    assert "Meat Pie contains: Wheat, Eggs." in reply(client, "meat pie allergens?")
    assert "typical recipe" not in reply(client, "What's in the meat pie?")


def test_fallback_ingredients_marked_typical(client):
    text = reply(client, "What's in egusi?")
    assert "(typical recipe; Cookie's version may vary)" in text
    assert "melon seeds" in text


@pytest.mark.parametrize(
    "question, expected",
    [
        ("Can you cater a party for 60?", "bulk order"),
        ("I want to place an order", "pickup order"),
        ("Do you deliver to Dartmouth?", "Halifax area, Nova Scotia"),
    ],
)
def test_fallback_gives_contact_only_for_orders(client, question, expected):
    text = reply(client, question)
    assert expected in text
    assert EMAIL in text and PHONE in text


@pytest.mark.parametrize(
    "question",
    ["How do I make jollof rice?", "Does egusi contain fish?", "calories in fried rice",
     "What's in the shawarma?", "How much is the jollof?", "hi", "What's on the menu?"],
)
def test_fallback_no_contact_for_general_questions(client, question):
    assert_no_contact(reply(client, question))


@pytest.mark.parametrize(
    "question",
    ["How much is the jollof?", "What does the shawarma cost?", "prices?",
     "What's on the menu?", "Tell me about the fried rice", "party for 40",
     "How do I make egusi?"],
)
def test_fallback_never_states_prices_when_hidden(client, question):
    assert_no_price(reply(client, question))


def test_fallback_price_question_says_coming_soon(client):
    assert reply(client, "How much is the jollof?") == "Pricing is coming soon."


def test_fallback_states_prices_when_enabled(priced_client):
    text = reply(priced_client, "Tell me about the egusi")
    assert re.search(r"Egusi is \$\d+\.\d\d CAD", text)
    assert "CAD" in reply(priced_client, "What's on the menu?")


@pytest.mark.parametrize(
    "question, expected",
    [("beef stew", ["Stew (Beef)"]), ("fried rice", ["Fried Rice"]),
     ("chicken stew", ["Stew (Chicken)"]), ("puff-puff", ["Puff-Puff"]),
     ("spaghetti", ["Jollof Spaghetti", "Beef Stir-fry Spaghetti"]),
     ("the stews", ["Stew (Beef)", "Stew (Chicken)", "Stew (Fish)"]),
     ("grilled chicken", ["Grilled Chicken, Meat or Fish"]),
     ("grilled fish with plantain", ["Grilled Chicken, Meat or Fish"]),
     ("meat pie", ["Meat Pie"]), ("fish stew", ["Stew (Fish)"])],
)
def test_dish_matching(client, question, expected):
    names = [i["name"] for i in cookie_app.find_items(question, cookie_app.load_menu())]
    assert names == expected


# ---------- AI mode (OpenAI client mocked) ----------

def test_ai_reply_used_when_key_set(client, monkeypatch):
    fake = use_fake_ai(monkeypatch, FakeOpenAI(reply="1. Blend the peppers.\n2. Fry the base."))
    monkeypatch.setenv("OPENAI_MODEL", "test-model")
    data = chat(client, "How do I make jollof?").get_json()
    assert data == {"reply": "1. Blend the peppers.\n2. Fry the base.", "source": "ai"}
    sent = fake.calls[0]
    assert sent["model"] == "test-model"
    assert sent["messages"][1] == {"role": "user", "content": "How do I make jollof?"}


def test_ai_prompt_contents(client, monkeypatch):
    fake = use_fake_ai(monkeypatch, FakeOpenAI(reply="Sure!"))
    chat(client, "hello")
    system = fake.calls[0]["messages"][0]["content"]
    for name in MENU_NAMES:
        assert f"## {name}\n" in system
    assert "Allergens (likely, based on typical recipe, not verified)" in system
    assert "Ingredients (typical recipe, not verified)" in system
    assert "Typical recipe steps:\n1. " in system
    assert "Calories per serving: NOT AVAILABLE" in system
    assert "Answer all cooking and recipe questions yourself" in system
    assert "Nigerian cooking in general" in system
    assert "Never tell customers to contact the business for recipes" in system
    assert "Contact details are only for placing orders" in system
    assert f"email {EMAIL} or phone {PHONE}" in system
    assert "Halifax area, Nova Scotia" in system
    assert "Pricing has not been released yet" in system
    assert_no_price(system)
    assert "test-key" not in system


def test_ai_prompt_includes_prices_when_enabled(priced_client, monkeypatch):
    fake = use_fake_ai(monkeypatch, FakeOpenAI(reply="Egusi is $22.00 CAD."))
    assert reply(priced_client, "How much is egusi?") == "Egusi is $22.00 CAD."
    system = fake.calls[0]["messages"][0]["content"]
    assert re.search(r"## Egusi\nPrice: \$\d+\.\d\d CAD", system)
    assert "Pricing has not been released yet" not in system


def test_ai_price_leak_is_blocked_when_hidden(client, monkeypatch):
    use_fake_ai(monkeypatch, FakeOpenAI(reply="It's about $20 a plate."))
    assert reply(client, "Roughly what does it run?") == "Pricing is coming soon."


def test_ai_recipe_temperatures_are_not_mistaken_for_prices(client, monkeypatch):
    recipe = "Heat oil to 175°C (350°F) and fry for 3 minutes."
    use_fake_ai(monkeypatch, FakeOpenAI(reply=recipe))
    assert reply(client, "How do I fry puff-puff?") == recipe


def test_ai_reply_gets_allergy_note(client, monkeypatch):
    use_fake_ai(monkeypatch, FakeOpenAI(reply="The shawarma likely contains eggs."))
    text = reply(client, "Is the shawarma safe for an egg allergy?")
    assert text.startswith("The shawarma likely contains eggs.")
    assert "cross-contamination" in text


def test_ai_failure_falls_back(client, monkeypatch):
    use_fake_ai(monkeypatch, FakeOpenAI(error=RuntimeError("API down")))
    data = chat(client, "How do I make fried rice?").get_json()
    assert data["source"] == "fallback"
    assert "Here's a typical way to make Fried Rice" in data["reply"]


def test_ai_empty_reply_falls_back(client, monkeypatch):
    use_fake_ai(monkeypatch, FakeOpenAI(reply=""))
    assert chat(client, "hi").get_json()["source"] == "fallback"


def test_get_ai_client_needs_key(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    assert cookie_app.get_ai_client() is None
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    assert cookie_app.get_ai_client() is not None


# ---------- Quote API ----------

def test_quote_disabled_when_prices_hidden(client):
    response = client.post("/api/quote", json={"items": [{"id": 1, "quantity": 2}]})
    assert response.status_code == 403
    assert response.get_json() == {"error": "Pricing is not available yet."}


def test_quote_when_prices_enabled(priced_client):
    menu = {i["id"]: i for i in cookie_app.load_menu()}
    response = priced_client.post(
        "/api/quote", json={"items": [{"id": 1, "quantity": 2}, {"id": 4, "quantity": 1}]}
    )
    assert response.status_code == 200
    quote = response.get_json()
    assert quote["currency"] == "CAD"
    assert quote["total"] == round(menu[1]["price"] * 2 + menu[4]["price"], 2)
    assert quote["items"][0]["name"] == "Jollof Rice & Peppered Chicken"


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
