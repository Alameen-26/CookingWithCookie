# Cooking with Cookie

Nigerian food, your way. **Cooking with Cookie** is a prototype website for a
Nigerian food business serving the Halifax area, Nova Scotia. Customers can
browse the menu, pick quantities, ask about bulk orders for events, enquire
about cooking lessons, and chat with **Ask Cookie**, an assistant that answers
questions about the food, ingredients, calories and allergens.

> **Prototype status:** pricing is not finalized, so prices are hidden
> everywhere by default (see [Turning prices on](#turning-prices-on)).
> Calorie and allergen details are also waiting for the owner to confirm them.

## Features

- **Menu** with photos, descriptions and quantity pickers, plus an order
  summary that counts selected items.
- **Bulk orders** section with an email enquiry button and a tap-to-call
  phone link for parties and events (also in the footer).
- **Learn to Make It** section offering cooking lessons for the menu dishes,
  with an email enquiry button (subject "Cooking Lesson Enquiry") and phone
  link. Lesson format is still to be decided ("details on request").
- **Ask Cookie chatbot:**
  - answers about meals, ingredients, calories, allergens, ordering and bulk
    orders, using only what is in the menu database;
  - never guesses calories or allergens: anything not confirmed is reported
    as "hasn't been confirmed yet", and allergy questions always get a
    safety note about cross-contamination;
  - points customers to the business email and phone for allergy
    questions, orders and bulk orders, and mentions the Halifax service area
    for location or delivery questions, and suggests cooking lessons when
    asked about recipes or how to cook a dish;
  - uses an AI model when an API key is set, and built-in rule-based replies
    otherwise (or if the AI service fails);
  - limited to 10 messages per visitor per minute to protect AI costs.
- **Prices switch (`SHOW_PRICES`):** off by default. When off, no prices
  appear on the site, in the API or in chatbot replies, which say pricing is
  coming soon. When on, menu cards show prices, the order summary shows an
  estimated total, and the quote API works.
- **Responsive design:** 3 menu columns on desktop, 2 on tablets, 1 on phones.

## Tech stack

| Part      | Technology                                             |
| --------- | ------------------------------------------------------ |
| Frontend  | HTML, CSS, vanilla JavaScript (no build step)          |
| Backend   | Python 3, Flask                                        |
| Database  | SQLite (`backend/cookie.db`, created automatically)    |
| AI        | OpenAI Python SDK; any OpenAI-compatible API works     |
| Config    | `.env` file loaded with python-dotenv                  |
| Tests     | pytest                                                 |

## Project structure

```
CookingWithCookie/
├── index.html          # The website
├── css/style.css       # Styles
├── js/script.js        # Order summary, live menu, chat window
├── images/             # Put your own photos here
├── backend/
│   ├── app.py          # Flask app: website, JSON API, chatbot, pricing
│   └── schema.sql      # Database tables and starter menu items
├── tests/test_app.py   # Backend tests
├── .env.example        # Copy to .env for settings (AI key, prices)
├── requirements.txt    # App dependencies
└── requirements-dev.txt  # App + test dependencies
```

## How it works

```
Browser (index.html + script.js)
   │  GET  /api/menu   → menu items (prices only if SHOW_PRICES is on)
   │  POST /api/chat   → Ask Cookie reply
   │  POST /api/quote  → order total (only if SHOW_PRICES is on)
   ▼
Flask (backend/app.py) ──► SQLite (backend/cookie.db, built from schema.sql)
   │
   └──► AI model (optional, only when OPENAI_API_KEY is set)
```

- Flask serves the website and the API from one address,
  <http://127.0.0.1:5000>.
- The database is the single source of truth for the menu. The page loads
  menu details from `/api/menu` when it starts.
- For the chatbot, the server builds instructions for the AI from the live
  menu (names, descriptions, ingredients, calories, allergens and, only if
  enabled, prices). The AI key never leaves the server.
- If the page is opened directly as a file (without Flask), it still works
  with simple built-in chat replies and no prices.

## Setup

You need Python 3.10 or newer.

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

### Settings (`.env`)

Copy `.env.example` to `.env` (PowerShell: `Copy-Item .env.example .env`,
macOS/Linux: `cp .env.example .env`), edit it, and restart the app.

| Setting                      | Default      | What it does                                      |
| ---------------------------- | ------------ | ------------------------------------------------- |
| `SHOW_PRICES`                | `false`      | Show prices on the site, API and chatbot          |
| `OPENAI_API_KEY`             | (empty)      | Turns on AI chat replies                          |
| `OPENAI_MODEL`               | `gpt-6-luna` | AI model to use                                   |
| `OPENAI_BASE_URL`            | (empty)      | Use another OpenAI-compatible provider            |
| `CONTACT_EMAIL`              | `alajiadeniyi@gmail.com` | Email the chatbot gives customers     |
| `CONTACT_PHONE`              | `(902) 495-1781` | Phone the chatbot gives customers         |
| `CHAT_RATE_LIMIT_PER_MINUTE` | `10`         | Chat messages allowed per visitor per minute      |
| `FLASK_DEBUG`                | `0`          | `1` for auto-reload and detailed errors (local only) |

`.env` is listed in `.gitignore`, so your settings and key are never
uploaded to GitHub.

## Turning on AI chat

1. Get an API key from OpenAI (<https://platform.openai.com/api-keys>), or from
   any provider with an OpenAI-compatible API.
2. In `.env`, set `OPENAI_API_KEY=your-key-here`. Optionally set
   `OPENAI_MODEL`, and `OPENAI_BASE_URL` for other providers.
3. Restart `python backend/app.py`.

Chat replies now come from the AI. The API's response shows
`"source": "ai"` (or `"fallback"` for built-in replies). Never put your key in
`index.html` or `script.js`.

## Turning prices on

Prices are a prototype placeholder and will be finalized later, including
any labour or other costs built into them. The prices currently in the
database are placeholders only.

1. Set the real prices in the database (see below) or in `backend/schema.sql`.
2. In `.env`, set `SHOW_PRICES=true`.
3. Restart the app.

Prices then appear on the menu cards, the order summary shows an estimated
total, `/api/menu` includes prices, `/api/quote` works, and the chatbot can
answer price questions. Set `SHOW_PRICES=false` to hide them again.

## Managing the menu

On first run the app creates `backend/cookie.db` from `backend/schema.sql`.
Each item has a `name`, `description`, `price` (CAD), `available` flag
(`0` hides it), `ingredients`, `calories` (per serving) and `allergens`
(comma-separated, for example `Wheat, Sesame, Soy`). A `cookie.db` from an
older version gets any new columns automatically; nothing is deleted.

> **Important:** calorie and allergen information must come from you, the
> owner, and be checked against your real recipes and ingredient labels.
> Until a value is filled in, the chatbot says it "hasn't been confirmed yet"
> and asks customers to contact you. Wrong allergen information can make
> someone seriously ill, so only enter values you have verified.

**Option 1: update the database.** Stop the app, open `backend/cookie.db`
with a free app like [DB Browser for SQLite](https://sqlitebrowser.org/) (or
the `sqlite3` command-line tool), and run, for example:

```sql
UPDATE menu_items
SET ingredients = 'REPLACE with every ingredient in this dish',
    calories = NULL,  -- REPLACE NULL with the verified calories per serving
    allergens = 'REPLACE with allergens, e.g. Wheat, Sesame',
    price = 0.00      -- REPLACE with the final price
WHERE name = 'Jollof Rice Plate';
```

Replace each value with your own verified information before running it.

**Option 2: edit the starting data.** Change the `INSERT` statements in
`backend/schema.sql`, then delete `backend/cookie.db` and restart the app to
rebuild it. This resets any other changes made to the database.

New dishes added to the database appear in the API and chatbot right away;
add a matching card to `index.html` to show them on the page.

## API

| Method | Path          | Body                                        | Response |
| ------ | ------------- | ------------------------------------------- | -------- |
| GET    | `/api/health` |                                             | `{"status": "ok"}` |
| GET    | `/api/menu`   |                                             | Available items (with `price` only if prices are on) |
| POST   | `/api/chat`   | `{"message": "..."}` (1 to 500 characters)  | `{"reply": "...", "source": "ai" or "fallback"}` |
| POST   | `/api/quote`  | `{"items": [{"id": 1, "quantity": 2}]}`     | Line totals and `total` in CAD; `403` while prices are off |

Errors are JSON: `400` for bad input, `403` for pricing while prices are
off, `404` for unknown `/api/...` paths, and `429` for too many chat messages.

## Tests

```bash
python -m pip install -r requirements-dev.txt
python -m pytest
```

The tests cover the menu and quote APIs with prices on and off, chat input
checks and rate limiting, the built-in replies (including "not confirmed"
calories and allergens), the AI path with a fake AI client, database
upgrades, and that the website files contain no prices.

## Before going live

- Finalize prices (and any labour costs in them), then turn on `SHOW_PRICES`.
- Decide the cooking lesson format and update the "Learn to Make It" section
  in `index.html`.
- Fill in verified ingredients, calories and allergens for every dish.
- If the contact email or phone changes, update it in `index.html` (bulk
  orders section and footer), `js/script.js` (`CONTACT`) and `.env`.
- Replace the stock photos with your own in `images/`.
- Run Flask behind a production server (for example Waitress or Gunicorn)
  rather than `python backend/app.py`. The chat rate limit is kept in memory
  and resets when the app restarts; behind a proxy, make sure visitors' real
  IP addresses reach the app.
