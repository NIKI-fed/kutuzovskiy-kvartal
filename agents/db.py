import json
import os
import secrets
import sqlite3
import string

from flask import current_app, g
from werkzeug.security import generate_password_hash

# Readable alphabet (no easily confused characters like 0/O, 1/l/I).
_PASSWORD_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnpqrstuvwxyz23456789"
_PASSWORD_LENGTH = 10

# Hardcoded administrator credentials.
ADMIN_USERNAME = "superuser"
ADMIN_PASSWORD = "july2026"
ADMIN_NAME = "Администратор"


def generate_password(length: int = _PASSWORD_LENGTH) -> str:
    return "".join(secrets.choice(_PASSWORD_ALPHABET) for _ in range(length))

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INSTANCE_DIR = os.path.join(BASE_DIR, "instance")
DB_PATH = os.path.join(INSTANCE_DIR, "kutuzov.db")

# Uploaded flat plans are stored here and served from the site static folder.
PLANS_DIR = os.path.join(BASE_DIR, "testing", "assets", "images", "plans")
PLANS_URL_PREFIX = "/assets/images/plans"

SCHEMA = """
CREATE TABLE IF NOT EXISTS agents (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    username      TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    name          TEXT NOT NULL DEFAULT '',
    is_admin      INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS houses (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    slug            TEXT UNIQUE NOT NULL,
    name            TEXT NOT NULL,
    address         TEXT NOT NULL DEFAULT '',
    delivery_quarter TEXT NOT NULL DEFAULT '',
    image_url       TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS flats (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    house_id      INTEGER NOT NULL,
    flat_number   TEXT NOT NULL,
    floor         INTEGER NOT NULL,
    rooms         INTEGER NOT NULL,
    area_m2       REAL NOT NULL,
    price_per_m2  REAL NOT NULL DEFAULT 0,
    price         INTEGER NOT NULL,
    status        TEXT NOT NULL DEFAULT 'available',
    plan_images   TEXT NOT NULL DEFAULT '[]',
    FOREIGN KEY (house_id) REFERENCES houses (id)
);

CREATE TABLE IF NOT EXISTS reservations (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    flat_id       INTEGER NOT NULL UNIQUE,
    agent_id      INTEGER NOT NULL,
    client_name   TEXT NOT NULL,
    client_phone  TEXT NOT NULL,
    client_email  TEXT NOT NULL DEFAULT '',
    created_at    TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (flat_id) REFERENCES flats (id),
    FOREIGN KEY (agent_id) REFERENCES agents (id)
);
"""


def connect() -> sqlite3.Connection:
    db = sqlite3.connect(DB_PATH)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys = ON")
    return db


def get_db() -> sqlite3.Connection:
    """Connection reused for the lifetime of one request."""
    if "db" not in g:
        g.db = connect()
    return g.db


def close_db(e=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def _create_schema(db: sqlite3.Connection):
    db.executescript(SCHEMA)
    db.commit()


def _migrate_asset_paths(db: sqlite3.Connection):
    """Rewrite legacy '/testing/assets/...' URLs to '/assets/...' in existing rows."""
    for row in db.execute("SELECT id, image_url FROM houses").fetchall():
        new_image = (row["image_url"] or "").replace("/testing/assets/", "/assets/")
        if new_image != row["image_url"]:
            db.execute("UPDATE houses SET image_url = ? WHERE id = ?", (new_image, row["id"]))
    for row in db.execute("SELECT id, plan_images FROM flats").fetchall():
        new_plans = (row["plan_images"] or "").replace("/testing/assets/", "/assets/")
        if new_plans != row["plan_images"]:
            db.execute("UPDATE flats SET plan_images = ? WHERE id = ?", (new_plans, row["id"]))
    db.commit()


def _migrate_admin_column(db: sqlite3.Connection):
    """Add the 'is_admin' column to a pre-existing agents table, if missing."""
    columns = {row["name"] for row in db.execute("PRAGMA table_info(agents)")}
    if "is_admin" not in columns:
        db.execute("ALTER TABLE agents ADD COLUMN is_admin INTEGER NOT NULL DEFAULT 0")
        db.commit()


def _migrate_price_per_m2(db: sqlite3.Connection):
    """Add the 'price_per_m2' column to a pre-existing flats table, if missing,
    and backfill it from price / area_m2 for existing rows."""
    columns = {row["name"] for row in db.execute("PRAGMA table_info(flats)")}
    if "price_per_m2" not in columns:
        db.execute("ALTER TABLE flats ADD COLUMN price_per_m2 REAL NOT NULL DEFAULT 0")
        db.commit()
    rows = db.execute(
        "SELECT id, area_m2, price FROM flats WHERE price_per_m2 = 0 AND area_m2 > 0"
    ).fetchall()
    for row in rows:
        ppm = round(row["price"] / row["area_m2"])
        db.execute(
            "UPDATE flats SET price_per_m2 = ? WHERE id = ?", (ppm, row["id"])
        )
    if rows:
        db.commit()


def _ensure_admin(db: sqlite3.Connection):
    """Make sure the hardcoded administrator account always exists."""
    add_agent(db, ADMIN_USERNAME, ADMIN_PASSWORD, ADMIN_NAME, is_admin=1)


def _seed(db: sqlite3.Connection):
    if db.execute("SELECT COUNT(*) FROM agents").fetchone()[0] == 0:
        add_agent(db, "agent", "agent123", "Агент по умолчанию")

    if db.execute("SELECT COUNT(*) FROM houses").fetchone()[0] == 0:
        houses = [
            {
                "slug": "na-kutuzova",
                "name": "Клубный дом «На Кутузова»",
                "address": "г. Тула, ул. Кутузова",
                "delivery_quarter": "III квартал 2027",
                "image_url": "/assets/images/na_kutuzova.jpg",
                "plans": [
                    "/assets/images/kutuzov/1_1.jpg",
                    "/assets/images/kutuzov/1_2.jpg",
                    "/assets/images/kutuzov/1_3.jpg",
                    "/assets/images/kutuzov/1_4.jpg",
                ],
            },
            {
                "slug": "tolstoy",
                "name": "Клубный дом «Толстой»",
                "address": "г. Тула",
                "delivery_quarter": "II квартал 2028",
                "image_url": "/assets/images/tolstoy.jpg",
                "plans": [
                    "/assets/images/tolstoy/2_1.png",
                    "/assets/images/tolstoy/2_2.png",
                    "/assets/images/tolstoy/2_3.png",
                    "/assets/images/tolstoy/2_4.png",
                    "/assets/images/tolstoy/2_5.png",
                    "/assets/images/tolstoy/2_6.png",
                ],
            },
        ]
        for h in houses:
            cur = db.execute(
                "INSERT INTO houses (slug, name, address, delivery_quarter, image_url) "
                "VALUES (?, ?, ?, ?, ?)",
                (h["slug"], h["name"], h["address"], h["delivery_quarter"], h["image_url"]),
            )
            house_id = cur.lastrowid
            for flat in _sample_flats(h["plans"]):
                db.execute(
                    "INSERT INTO flats "
                    "(house_id, flat_number, floor, rooms, area_m2, price, status, plan_images) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    (
                        house_id,
                        flat["flat_number"],
                        flat["floor"],
                        flat["rooms"],
                        flat["area_m2"],
                        flat["price"],
                        "available",
                        json.dumps(flat["plans"]),
                    ),
                )
        db.commit()


def _sample_flats(plan_pool):
    """Deterministic sample flats cycled through the given plan images."""
    rooms_cycle = [1, 2, 2, 3]
    base_area = {1: 38.0, 2: 54.0, 3: 78.0}
    price_per_m2 = 135000
    flats = []
    for i in range(10):
        floor = (i % 5) + 1
        rooms = rooms_cycle[i % len(rooms_cycle)]
        area = round(base_area[rooms] + (i * 2.4), 1)
        price = int(area * price_per_m2)
        plans = [plan_pool[i % len(plan_pool)]]
        flats.append(
            {
                "flat_number": f"{floor}{(i % 4) + 1:02d}",
                "floor": floor,
                "rooms": rooms,
                "area_m2": area,
                "price": price,
                "plans": plans,
            }
        )
    return flats


def init_db():
    """Create schema + seed. Idempotent and safe to run on every startup."""
    os.makedirs(INSTANCE_DIR, exist_ok=True)
    db = connect()
    try:
        _create_schema(db)
        _migrate_admin_column(db)
        _migrate_price_per_m2(db)
        _migrate_asset_paths(db)
        _ensure_admin(db)
        _seed(db)
    finally:
        db.close()


def add_agent(db, username, password, name="", is_admin=0):
    """Insert or update an agent account (password is hashed)."""
    password_hash = generate_password_hash(password)
    db.execute(
        "INSERT INTO agents (username, password_hash, name, is_admin) VALUES (?, ?, ?, ?) "
        "ON CONFLICT(username) DO UPDATE SET "
        "password_hash=excluded.password_hash, name=excluded.name, is_admin=excluded.is_admin",
        (username, password_hash, name, 1 if is_admin else 0),
    )
    db.commit()


def username_exists(db, username) -> bool:
    return db.execute(
        "SELECT 1 FROM agents WHERE username = ?", (username,)
    ).fetchone() is not None


def register_agent(db, username, name):
    """Create a new agent account with a server-generated password.

    Returns the generated plaintext password (shown to the agent once).
    Raises ValueError if the username is already taken.
    """
    username = (username or "").strip()
    if not username:
        raise ValueError("Логин обязателен")
    if username == ADMIN_USERNAME:
        raise ValueError("Этот логин недоступен")
    if username_exists(db, username):
        raise ValueError("Такой логин уже занят")
    password = generate_password()
    add_agent(db, username, password, name)
    return password
