# Cooking with Cookie

Nigerian food, your way. A small restaurant website with a menu and live
order estimate, a bulk-order enquiry section, and an "Ask Cookie" chatbot
that answers questions about the food, calories and allergens. It is served
by a Flask backend with a SQLite menu database.

## Project structure

```
CookingWithCookie/
├── index.html          # The website
├── css/style.css       # Styles (responsive: 3 / 2 / 1 column menu)
├── js/script.js        # Order calculator, live menu prices, chat window
├── images/             # Put your own photos here
├── backend/
│   ├── app.py          # Flask app: serves the site, JSON API and chatbot
│   └── schema.sql      # SQLite schema and starter menu items
├── tests/test_app.py   # Pytest tests for the backend
├── .env.example        # Copy to .env for the AI key and settings
├── requirements.txt
└── requirements-dev.txt
```

## Run it locally

### Windows (PowerShell)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python backend/app.py
```

If PowerShell says running scripts is disabled, run this once and try again:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

### macOS / Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python backend/app.py
```

Then open <http://127.0.0.1:5000>.

To turn on Flask debug mode (auto-reload, detailed errors), set `FLASK_DEBUG=1`
first: `$env:FLASK_DEBUG = "1"` in PowerShell, or `export FLASK_DEBUG=1` on
macOS/Linux. Leave it off for anything public.

## The menu database

On first run the app creates `backend/cookie.db` from `backend/schema.sql`.
Each menu item has a name, description, price (CAD), `available` flag,
`ingredients`, `calories` and `allergens`. Items with `available = 0` are
hidden. If you already have a `cookie.db` from an older version, the app adds
the new columns automatically the next time it starts; nothing is deleted.

The page shows prices written in `index.html`; when it is served by Flask it
updates them from `/api/menu`, so the database is the source of truth.

## Ask Cookie chatbot

Customers can ask about meals, prices, ingredients, calories, allergens,
ordering and bulk orders. The chatbot only uses what is in the database.

- **With an AI key:** answers come from an AI model, given your live menu and
  strict rules (menu topics only, never guess calories or allergens, always
  add an allergy safety note, keep replies short).
- **Without a key, or if the AI service fails:** the server answers with
  built-in rule-based replies that read the same database.
- **If the page is opened directly as a file:** the browser uses simple
  local replies.

Each visitor (by IP address) can send up to 10 messages a minute, to protect
your AI costs. Change this with `CHAT_RATE_LIMIT_PER_MINUTE` in `.env`.

### Setting up the AI key

1. Get an API key from OpenAI (<https://platform.openai.com/api-keys>), or from
   any provider with an OpenAI-compatible API.
2. Copy `.env.example` to `.env` in the project folder:
   - PowerShell: `Copy-Item .env.example .env`
   - macOS/Linux: `cp .env.example .env`
3. Open `.env` and set `OPENAI_API_KEY=your-key-here`. Optionally set
   `OPENAI_MODEL` (default `gpt-6-luna`) and `OPENAI_BASE_URL` for other
   providers.
4. Restart `python backend/app.py`.

The key stays on the server. It is never sent to the browser, and `.env` is
listed in `.gitignore` so it won't be uploaded to GitHub. Never paste your key
into `index.html` or `script.js`.

### Filling in ingredients, calories and allergens

> **Important:** calorie and allergen information must come from you, the
> owner, and be checked against your real recipes and ingredient labels.
> Until a value is filled in, the chatbot says it "hasn't been confirmed yet"
> and asks customers to contact you. Wrong allergen information can make
> someone seriously ill, so only enter values you have verified.

Calories are per serving. Allergens are a comma-separated list, for example
`Wheat, Sesame, Soy`.

**Option 1: update the running database.** Stop the app, then open the
database with the `sqlite3` tool (or a free app like
[DB Browser for SQLite](https://sqlitebrowser.org/)) and run:

```sql
UPDATE menu_items
SET ingredients = 'REPLACE with every ingredient in this dish',
    calories = NULL,  -- REPLACE NULL with the verified calories per serving
    allergens = 'REPLACE with allergens, e.g. Wheat, Sesame'
WHERE name = 'Jollof Rice Plate';
```

Replace each value with your own verified information before running it.
With the `sqlite3` command-line tool: `sqlite3 backend/cookie.db`, paste the
statement, then `.quit`.

**Option 2: edit the starting data.** Change the `INSERT` statements in
`backend/schema.sql` to include `ingredients`, `calories` and `allergens`,
then delete `backend/cookie.db` and restart the app to rebuild it. This also
resets any other changes made to the database.

## API

| Method | Path          | Description                                  |
| ------ | ------------- | -------------------------------------------- |
| GET    | `/api/menu`   | Available menu items as JSON                 |
| GET    | `/api/health` | Returns `{"status": "ok"}`                   |
| POST   | `/api/chat`   | `{"message": "..."}` (max 500 characters) → `{"reply": "...", "source": "ai" or "fallback"}` |

Unknown `/api/...` paths return a JSON 404. Too many chat messages return 429.

## Tests

```bash
python -m pip install -r requirements-dev.txt
python -m pytest
```

## Notes

- Prices are in Canadian dollars (CAD).
- The bulk-order button uses `orders@example.com`; replace it with your
  business email in `index.html`.
- The rate limit is kept in memory, so it resets when the app restarts. If you
  later host the site behind a proxy (for example on a hosting service),
  check that visitors' real IP addresses reach the app.
