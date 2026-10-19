# Cooking with Cookie

Nigerian food, your way. **Cooking with Cookie** is a prototype website for a
Nigerian food business serving the Halifax area, Nova Scotia. Customers can
browse the 13-dish menu, pick quantities, ask about bulk orders for events,
and chat with **Ask Cookie**, an assistant that answers questions about the
food and its likely allergens, and shares recipes and cooking tips.

> **Prototype status:** pricing is not finalized, so prices are hidden
> everywhere by default (see [Turning prices on](#turning-prices-on)).
> Ingredients, allergens and recipes come from typical recipes for each dish
> and are marked unverified until the owner checks them. Calories are not
> filled in yet. Dish photos are placeholders.

## Features

- **Menu** of 13 Nigerian dishes (Jollof Rice & Peppered Chicken, Fried Rice,
  Nigerian Shawarma, Puff-Puff, Meat Pie, Jollof Spaghetti, Beef Stir-fry
  Spaghetti, Dirty Rice, Stew (Beef), Stew (Chicken), Stew (Fish), Egusi and
  Beans Porridge) with quantity pickers and an order summary that counts
  selected items.
- **Ordering contacts:** email and tap-to-call links for pickup orders and
  bulk/event orders (order summary, bulk orders section and footer).
- **Learn to Make It** section inviting customers to ask Cookie for recipes,
  with an optional email link for in-person lesson enquiries.
- **Ask Cookie chatbot:**
  - answers questions about the menu, ingredients and likely allergens;
  - answers cooking questions itself: recipes, step-by-step instructions,
    tips and substitutions for the menu dishes and Nigerian cooking in
    general, so the owner doesn't have to;
  - always says allergen information is likely, based on a typical recipe,
    and not verified, adds a cross-contamination note, and advises caution
    for severe allergies;
  - never guesses calories;
  - only gives the business email and phone for placing pickup or bulk
    orders, and mentions the Halifax service area for location questions;
  - uses an AI model when an API key is set. Without a key (or if the AI
    service fails) it uses built-in replies from the database, including a
    short typical recipe for every dish;
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
├── images/             # Dish photos (placeholder-dish.svg for now)
├── backend/
│   ├── app.py          # Flask app: website, JSON API, chatbot, pricing
│   └── schema.sql      # Database table and the 13-dish starter menu
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
  menu (names, descriptions, ingredients, allergens, calories, typical recipe
  steps, whether each value is verified and, only if enabled, prices). The
  AI key never leaves the server.
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
| `CONTACT_EMAIL`              | `alajiadeniyi@gmail.com` | Email the chatbot gives for orders    |
| `CONTACT_PHONE`              | `(902) 495-1781` | Phone the chatbot gives for orders        |
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

Chat replies now come from the AI, including full recipes, tips and
substitutions for any Nigerian dish. The API's response shows
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
Each dish has:

| Column                 | Meaning                                                   |
| ---------------------- | --------------------------------------------------------- |
| `name`, `description`  | Shown on the site and used by the chatbot                 |
| `price`                | CAD placeholder; hidden while `SHOW_PRICES` is off        |
| `available`            | `1` = on the menu, `0` = hidden                           |
| `ingredients`          | Comma-separated list                                      |
| `ingredients_verified` | `0` = typical recipe (default), `1` = checked by you      |
| `allergens`            | Comma-separated list, e.g. `Wheat (gluten), Eggs`         |
| `allergens_verified`   | `0` = likely, not verified (default), `1` = checked by you |
| `calories`             | Per serving; empty (NULL) = not available                 |
| `recipe_steps`         | Numbered steps, one per line (used when AI is off)        |

> **Important:** the starting ingredients, allergens and recipes describe a
> typical version of each dish from general knowledge, not your own recipes.
> Allergens were worked out from those typical ingredients (stock cubes, for
> example, often contain wheat and soy). Check every dish against your real
> recipes and ingredient labels, then set the `_verified` columns to `1`.
> Until then, the chatbot says allergens are "likely, based on a typical
> recipe, not verified". Wrong allergen information can make someone
> seriously ill.

**Option 1: update the database.** Stop the app, open `backend/cookie.db`
with a free app like [DB Browser for SQLite](https://sqlitebrowser.org/) (or
the `sqlite3` command-line tool), and run, for example:

```sql
UPDATE menu_items
SET ingredients = 'REPLACE with every ingredient in your recipe',
    ingredients_verified = 1,
    allergens = 'REPLACE with verified allergens, e.g. Wheat, Eggs',
    allergens_verified = 1,
    calories = NULL,  -- REPLACE NULL with the verified calories per serving
    price = 0.00      -- REPLACE with the final price
WHERE name = 'Meat Pie';
```

Replace each value with your own verified information before running it.

**Option 2: edit the starting data.** Change the `INSERT` statements in
`backend/schema.sql`, then delete `backend/cookie.db` and restart the app to
rebuild it. This resets any other changes made to the database.

When the starting menu changes in a new version of the app, the
`PRAGMA user_version` number in `schema.sql` goes up. On the next start, an
older `cookie.db` is copied to `cookie.v<old number>-backup.db` and a fresh one
is built, so earlier edits can still be recovered from the backup.

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

The tests cover the 13-dish menu and its safety flags, the menu and quote
APIs with prices on and off, chat input checks and rate limiting, the
built-in replies (recipes, "likely, not verified" allergens, unavailable
calories, contact details only for orders), the AI instructions with a fake
AI client, database upgrades with backups, and that the website contains no
prices.

## Before going live

- Finalize prices (and any labour costs in them), then turn on `SHOW_PRICES`.
- Replace `images/placeholder-dish.svg` with real photos of your dishes and
  update the `<img>` tags in `index.html`.
- Check the ingredients, allergens and recipes for every dish against your
  own recipes, add calories, and mark them verified.
- If the contact email or phone changes, update it in `index.html` (bulk
  orders section and footer), `js/script.js` (`ORDER_CONTACT`) and `.env`.
- Run Flask behind a production server (for example Waitress or Gunicorn)
  rather than `python backend/app.py`. The chat rate limit is kept in memory
  and resets when the app restarts; behind a proxy, make sure visitors' real
  IP addresses reach the app.
