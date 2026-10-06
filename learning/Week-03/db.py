"""SQLite persistence for reports (Week 03, new-report feature).

The database is the long-term store for every report: the 44 seeded dataset
cases (source='dataset') plus every report a user submits through the app
(source='user').

Design choices
--------------
- SQLite via the standard-library ``sqlite3`` module: zero extra dependencies,
  a single file (``lostify.db``), and enough for an FYP demo (millions of rows).
  Swapping to PostgreSQL later only changes this module, not the API or UI.
- ``source`` column keeps the seeded dataset separate from
  user-submitted reports so the UI can label them.
- All helpers take ``db_path``/``metadata_path`` so unit tests can point at
  temporary files.
"""

import json
import os
import sqlite3

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "lostify.db")
METADATA_PATH = os.path.join(BASE_DIR, "metadata.json")

SCHEMA = """
CREATE TABLE IF NOT EXISTS reports (
    case_id     TEXT PRIMARY KEY,
    case_type   TEXT NOT NULL,
    category    TEXT,
    title       TEXT,
    description TEXT,
    location    TEXT,
    latitude    REAL,
    longitude   REAL,
    date_lost   TEXT,
    image_path  TEXT,
    status      TEXT NOT NULL DEFAULT 'open',
    source      TEXT NOT NULL DEFAULT 'user',
    created_at  TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
"""

TYPE_PREFIXES = {
    "lost_pet": "PETS",
    "lost_person": "PERS",
    "lost_item": "ITEMS",
}


def connect(db_path=DB_PATH):
    """Open a connection with row access by column name."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path=DB_PATH):
    """Create the reports table if it does not exist yet."""
    with connect(db_path) as conn:
        conn.execute(SCHEMA)
    return db_path


def count(db_path=DB_PATH):
    with connect(db_path) as conn:
        return conn.execute("SELECT COUNT(*) FROM reports").fetchone()[0]


def insert_report(record, db_path=DB_PATH):
    """Insert one report. Returns the number of rows written (1 on success)."""
    with connect(db_path) as conn:
        cur = conn.execute(
            """
            INSERT INTO reports (
                case_id, case_type, category, title, description, location,
                latitude, longitude, date_lost, image_path, status, source
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                record["case_id"],
                record.get("case_type"),
                record.get("category"),
                record.get("title"),
                record.get("description"),
                record.get("location"),
                record.get("latitude"),
                record.get("longitude"),
                record.get("date_lost"),
                record.get("image_path"),
                record.get("status", "open"),
                record.get("source", "user"),
            ),
        )
    return cur.rowcount


def seed_from_metadata(db_path=DB_PATH, metadata_path=METADATA_PATH):
    """Copy the static dataset into the DB once (idempotent).

    Returns the number of rows already stored after seeding. Safe to call on
    every startup: it only seeds when the table is empty.
    """
    if count(db_path) > 0:
        return count(db_path)

    with open(metadata_path, "r") as f:
        metadata = json.load(f)

    for case_id, record in metadata.items():
        insert_report(
            {
                **record,
                "case_id": case_id,
                "source": "dataset",
            },
            db_path=db_path,
        )
    return count(db_path)


def list_reports(limit=500, db_path=DB_PATH):
    """Newest first (created_at desc, then case_id desc)."""
    with connect(db_path) as conn:
        rows = conn.execute(
            "SELECT * FROM reports ORDER BY created_at DESC, case_id DESC LIMIT ?",
            (limit,),
        ).fetchall()
    return [dict(r) for r in rows]


def next_case_id(case_type, db_path=DB_PATH):
    """Next sequential id for a case type, e.g. PETS-15, PERS-11, ITEMS-21."""
    prefix = TYPE_PREFIXES.get(case_type, "CASE")
    highest = 0
    with connect(db_path) as conn:
        rows = conn.execute(
            "SELECT case_id FROM reports WHERE case_id LIKE ?", (f"{prefix}-%",)
        ).fetchall()
    for row in rows:
        try:
            num = int(row["case_id"].split("-")[-1])
            highest = max(highest, num)
        except (ValueError, IndexError):
            continue
    return f"{prefix}-{highest + 1:02d}"