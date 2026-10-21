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
> filled in yet. Dish photos are openly licensed stock photos (see
> [Dish photos](#dish-photos)) until Cookie's own photos are ready.

## Features

- **Menu** of 13 Nigerian dishes (Jollof Rice & Peppered Chicken, Fried Rice,
  Nigerian Shawarma, Puff-Puff, Meat Pie, Jollof Spaghetti, Beef Stir-fry
  Spaghetti, Grilled Chicken, Meat or Fish, Stew (Beef), Stew (Chicken),
  Stew (Fish), Egusi and Beans Porridge) with a photo, quantity picker and
  "Learn to make it" button on each card, and an order summary that counts
  selected items. The grilled plate comes with a choice of protein (chicken,
  meat (beef) or fish) and side (sweet potatoes, fries or fried plantain).
- **Ordering contacts:** email and tap-to-call links for pickup orders and
  bulk/event orders (order summary, bulk orders section and footer).
- **Learn to Make It:** every dish card has a "Learn to make it" button that
  asks Cookie for that dish's recipe, plus a section inviting customers to ask
  Cookie for recipes,
  with an optional email link for in-person lesson enquiries.
- **Ask Cookie chatbot:**
  - friendly, conversational tone: short answers, follow-up questions, and
    it remembers the last few messages, so "how long do I fry it?" works;
  - optional web search grounds general cooking, recipe and nutrition
    answers in online sources and shows the links it used (facts about the
    shop itself always come from the database);
  - chat window with a typing indicator, quick-reply suggestion chips, safe
    links and simple formatting, a Sources list and friendly error messages;
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
    short typical recipe for every dish. These replies vary their wording,
    handle greetings, thanks and small talk, forgive typos in dish names
    ("jolof", "egusy", "shwarma") and suggest related questions;
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
├── images/             # Dish photos, CREDITS.md and placeholder-dish.svg
├── backend/
│   ├── app.py          # Flask app: website, JSON API, chatbot, pricing
│   ├── search.py       # Optional web search (Tavily or Brave)
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
   ├──► AI model (optional, only when OPENAI_API_KEY is set)
   └──► Web search (optional, backend/search.py, only when SEARCH_API_KEY is
        also set, and only for general cooking questions)
```

- Flask serves the website and the API from one address,
  <http://127.0.0.1:5000>.
- The database is the single source of truth for the menu. The page loads
  menu details from `/api/menu` when it starts.
- For the chatbot, the server builds instructions for the AI from the live
  menu (names, descriptions, ingredients, allergens, calories, typical recipe
  steps, whether each value is verified and, only if enabled, prices). The
  AI key never leaves the server.
- The browser keeps the conversation in memory and sends the last 10
  messages (each cut to 1,000 characters) with every question, so Cookie
  understands follow-ups. Nothing is stored on the server.
- If the page is opened directly as a file (without Flask), it still works
  with simple built-in chat replies and no prices.

### How a chat message is answered

1. `/api/chat` checks the message (1 to 500 characters), the rate limit and
   the `history` list.
2. If AI is on, web search is on, and the question is a general cooking,
   recipe or nutrition question (for example "How long do I fry plantain?"),
   the server searches the web (`backend/search.py`) and keeps the top 3
   results. Questions about the shop are never searched: allergens, prices,
   ordering, pickup, events, and the calories or ingredients of Cookie's own
   dishes. If search is slow (over `SEARCH_TIMEOUT_SECONDS`) or fails, the
   question is answered without it.
3. The AI gets the system prompt (personality, the live menu and the safety
   rules), the web results marked as untrusted text, the recent
   conversation and the new question.
4. The server checks the reply: links that weren't in the web results become
   plain text, cited results are returned as `sources`, prices are blocked
   while they are hidden, and the allergy note is added when allergies come up.
5. Without AI (or if it fails), the rule-based replies answer from the
   database instead.
6. Either way, the reply includes up to 3 suggested follow-up questions,
   shown as quick-reply chips.

Safety rules that always apply: allergens are "likely, based on a typical
recipe, not verified" with a cross-contamination note; calories are never
guessed; prices say "coming soon" while hidden; pickup only in the Halifax
area; contact details only for placing orders.

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
| `SEARCH_API_KEY`             | (empty)      | Turns on web search for general cooking questions (needs AI on) |
| `SEARCH_PROVIDER`            | `tavily`     | `tavily` or `brave`                               |
| `SEARCH_TIMEOUT_SECONDS`     | `6`          | Answer without web results if search is slower    |
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

## Turning on web search (optional)

Web search lets Ask Cookie base general cooking answers on current online
sources and list the links it used under the reply. It only works when AI
chat is on.

1. Get a search API key:
   - **Tavily** (default): sign up at <https://tavily.com> and copy the key
     from the dashboard. The free plan has 1,000 searches a month with no
     credit card.
   - **Brave Search API**: sign up at <https://brave.com/search/api/>. It
     needs a credit card, and includes $5 of free credit a month (about
     1,000 searches). Brave asks you to credit the Brave Search API on your
     site to use the free credit.
2. In `.env`, set `SEARCH_API_KEY=your-key` and `SEARCH_PROVIDER=tavily` (or
   `brave`).
3. Restart the app and ask "How long do I fry plantain?". The JSON reply
   from `/api/chat` has a `sources` list, and the chat window shows the
   links under the answer.

**Costs:** each searched question uses one search plus one AI request, and
the conversation history makes AI requests a bit larger. Only general
cooking questions are searched, and the 10-messages-per-minute limit applies
to everything. Check your provider's current prices and set spending limits
in its dashboard.

To add another provider, write a function in `backend/search.py` that
returns `[{"title", "url", "snippet"}, ...]` and add it to `PROVIDERS`.

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
| `options`              | Customer choices, e.g. protein and side; empty = none     |
| `image`, `image_alt`   | Photo path (under `images/`) and its description          |

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

## Dish photos

The menu photos in `images/` are **stock photos from Wikimedia Commons**,
used under CC BY-SA, CC BY or CC0 licences. They are placeholders until
Cooking with Cookie has photos of its own food, so they don't show Cookie's
own cooking. Author, licence and source for every photo are in
[`images/CREDITS.md`](images/CREDITS.md), and the site footer links to that
page (CC BY and CC BY-SA require visible credit).

Each photo is a JPEG embedded in an `.svg` file because the tool used to
publish this repository can only upload text files; browsers show it like a
normal image. If a photo fails to load, the card falls back to
`images/placeholder-dish.svg`.

To use your own photos: save them in `images/` (about 800 px wide, JPEG or
WebP, under 200 KB), update the `src` and `alt` of each card's `<img>` in
`index.html` and the `image` / `image_alt` values in `backend/schema.sql`,
and remove the matching rows from `images/CREDITS.md` (and the footer credit
once no stock photos are left).

## API

| Method | Path          | Body                                        | Response |
| ------ | ------------- | ------------------------------------------- | -------- |
| GET    | `/api/health` |                                             | `{"status": "ok"}` |
| GET    | `/api/menu`   |                                             | Available items (with `price` only if prices are on) |
| POST   | `/api/chat`   | `{"message": "...", "history": [{"role": "user" or "assistant", "content": "..."}]}` (message 1 to 500 characters; history optional, last 10 kept) | `{"reply": "...", "source": "ai" or "fallback", "sources": [{"title", "url"}], "suggestions": ["..."]}` |
| POST   | `/api/quote`  | `{"items": [{"id": 1, "quantity": 2}]}`     | Line totals and `total` in CAD; `403` while prices are off |

Errors are JSON: `400` for bad input, `403` for pricing while prices are
off, `404` for unknown `/api/...` paths, and `429` for too many chat messages.

## Tests

```bash
python -m pip install -r requirements-dev.txt
python -m pytest
```

The tests cover the 13-dish menu, its photos and safety flags, the removal
of Dirty Rice, the grilled plate and its choices, the menu and quote
APIs with prices on and off, chat input checks and rate limiting, the
built-in replies (recipes, "likely, not verified" allergens, unavailable
calories, contact details only for orders), the AI instructions with a fake
AI client, database upgrades with backups, and that the website contains no
prices. They also cover conversation history, follow-up questions, typo-
tolerant dish matching, small talk, suggestions, and web search with a fake
search provider (when to search, sources, made-up links removed, timeouts
and errors). The tests never use the network or a real API key.

To try the chatbot by hand without any keys, run the app and ask "hi",
"tell me about the jolof", then "how do I make it?".

## Before going live

- Finalize prices (and any labour costs in them), then turn on `SHOW_PRICES`.
- Replace the stock photos with real photos of your dishes (see
  [Dish photos](#dish-photos)).
- Check the ingredients, allergens and recipes for every dish against your
  own recipes, add calories, and mark them verified.
- If the contact email or phone changes, update it in `index.html` (bulk
  orders section and footer), `js/script.js` (`ORDER_CONTACT`) and `.env`.
- Run Flask behind a production server (for example Waitress or Gunicorn)
  rather than `python backend/app.py`. The chat rate limit is kept in memory
  and resets when the app restarts; behind a proxy, make sure visitors' real
  IP addresses reach the app.
