import json
import os
import sqlite3

from flask import current_app, g
from werkzeug.security import generate_password_hash

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INSTANCE_DIR = os.path.join(BASE_DIR, "instance")
DB_PATH = os.path.join(INSTANCE_DIR, "kutuzov.db")

SCHEMA = """
CREATE TABLE IF NOT EXISTS agents (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    username      TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    name          TEXT NOT NULL DEFAULT ''
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
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    house_id     INTEGER NOT NULL,
    flat_number  TEXT NOT NULL,
    floor        INTEGER NOT NULL,
    rooms        INTEGER NOT NULL,
    area_m2      REAL NOT NULL,
    price        INTEGER NOT NULL,
    status       TEXT NOT NULL DEFAULT 'available',
    plan_images  TEXT NOT NULL DEFAULT '[]',
    FOREIGN KEY (house_id) REFERENCES houses (id)
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
                "image_url": "/testing/assets/images/na_kutuzova.jpg",
                "plans": [
                    "/testing/assets/images/kutuzov/1_1.jpg",
                    "/testing/assets/images/kutuzov/1_2.jpg",
                    "/testing/assets/images/kutuzov/1_3.jpg",
                    "/testing/assets/images/kutuzov/1_4.jpg",
                ],
            },
            {
                "slug": "tolstoy",
                "name": "Клубный дом «Толстой»",
                "address": "г. Тула",
                "delivery_quarter": "II квартал 2028",
                "image_url": "/testing/assets/images/tolstoy.jpg",
                "plans": [
                    "/testing/assets/images/tolstoy/2_1.png",
                    "/testing/assets/images/tolstoy/2_2.png",
                    "/testing/assets/images/tolstoy/2_3.png",
                    "/testing/assets/images/tolstoy/2_4.png",
                    "/testing/assets/images/tolstoy/2_5.png",
                    "/testing/assets/images/tolstoy/2_6.png",
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
        _seed(db)
    finally:
        db.close()


def add_agent(db, username, password, name=""):
    """Insert or update an agent account (password is hashed)."""
    password_hash = generate_password_hash(password)
    db.execute(
        "INSERT INTO agents (username, password_hash, name) VALUES (?, ?, ?) "
        "ON CONFLICT(username) DO UPDATE SET password_hash=excluded.password_hash, name=excluded.name",
        (username, password_hash, name),
    )
    db.commit()
