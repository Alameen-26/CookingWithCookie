# Cooking with Cookie

Nigerian food, your way. A small restaurant website with a menu and live
order estimate, a bulk-order enquiry section, and a demo "Ask Cookie" chat
assistant, served by a Flask backend with a SQLite menu database.

## Project structure

```
CookingWithCookie/
├── index.html          # The website
├── css/style.css       # Styles (responsive: 3 / 2 / 1 column menu)
├── js/script.js        # Order calculator, live menu prices, chat assistant
├── images/             # Put your own photos here
├── backend/
│   ├── app.py          # Flask app: serves the site + JSON API
│   └── schema.sql      # SQLite schema and starter menu items
├── tests/test_app.py   # Pytest tests for the backend
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
To change the menu, edit `schema.sql`, delete `cookie.db`, and restart the app.
Items with `available = 0` are hidden from the menu API.

The page shows prices written in `index.html`; when it is served by Flask it
updates them from `/api/menu`, so the database is the source of truth.

## API

| Method | Path          | Description                          |
| ------ | ------------- | ------------------------------------ |
| GET    | `/api/menu`   | Available menu items as JSON         |
| GET    | `/api/health` | Returns `{"status": "ok"}`           |

Unknown `/api/...` paths return a JSON 404.

## Tests

```bash
python -m pip install -r requirements-dev.txt
python -m pytest
```

## Notes

- Prices are in Canadian dollars (CAD).
- The bulk-order button uses `orders@example.com`; replace it with your
  business email in `index.html`.
- The chat assistant is a demo with keyword-based replies in `js/script.js`.
