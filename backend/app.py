"""Cooking with Cookie backend.

Serves the website (index.html, css/, js/, images/) and a small JSON API.
Run from the project root with:  python backend/app.py
"""
import os
import sqlite3
from pathlib import Path

from flask import Flask, abort, jsonify, request, send_from_directory
from werkzeug.exceptions import HTTPException

BACKEND_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BACKEND_DIR.parent
SCHEMA_PATH = BACKEND_DIR / "schema.sql"
DEFAULT_DB_PATH = BACKEND_DIR / "cookie.db"

# Only these folders from the project root are served as static files.
STATIC_FOLDERS = {"css", "js", "images"}

app = Flask(__name__, static_folder=None)
app.config["DATABASE"] = os.environ.get("COOKIE_DB_PATH", str(DEFAULT_DB_PATH))


def get_connection():
    """Open a connection to the SQLite database."""
    connection = sqlite3.connect(app.config["DATABASE"])
    connection.row_factory = sqlite3.Row
    return connection


def init_db():
    """Create the database from schema.sql if it doesn't exist yet."""
    db_path = Path(app.config["DATABASE"])
    if db_path.exists():
        return
    db_path.parent.mkdir(parents=True, exist_ok=True)
    connection = get_connection()
    try:
        connection.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
        connection.commit()
    finally:
        connection.close()


# ---------- API ----------

@app.route("/api/menu", methods=["GET"])
def get_menu():
    """Return the available menu items as JSON."""
    init_db()
    connection = get_connection()
    try:
        rows = connection.execute(
            "SELECT id, name, description, price "
            "FROM menu_items WHERE available = 1 ORDER BY id"
        ).fetchall()
    finally:
        connection.close()
    return jsonify([dict(row) for row in rows])


@app.route("/api/health", methods=["GET"])
def health_check():
    """Check that the backend is running."""
    return jsonify({"status": "ok"})


@app.errorhandler(HTTPException)
def handle_http_error(error):
    """Return JSON errors for /api/* routes, normal pages elsewhere."""
    if request.path.startswith("/api/"):
        response = jsonify({"error": error.name, "status": error.code})
        response.status_code = error.code
        return response
    return error


# ---------- Website ----------

@app.route("/")
def index():
    """Serve the home page."""
    return send_from_directory(PROJECT_ROOT, "index.html")


@app.route("/<folder>/<path:filename>")
def static_files(folder, filename):
    """Serve files from css/, js/ and images/."""
    if folder not in STATIC_FOLDERS:
        abort(404)
    return send_from_directory(PROJECT_ROOT / folder, filename)


if __name__ == "__main__":
    init_db()
    debug = os.environ.get("FLASK_DEBUG", "0").lower() in {"1", "true", "yes"}
    app.run(debug=debug)
