# database.py

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).with_name("lol_manager.db")


def connect():
    db = sqlite3.connect(DB_PATH)
    db.row_factory = sqlite3.Row
    return db


def init_db():
    with connect() as db:
        db.execute("""
            CREATE TABLE IF NOT EXISTS accounts (
                user_id INTEGER PRIMARY KEY,
                username TEXT NOT NULL DEFAULT '',
                name TEXT NOT NULL,
                bio TEXT NOT NULL DEFAULT '',
                avatar TEXT NOT NULL DEFAULT '',
                agegroup TEXT NOT NULL DEFAULT '',
                registered_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                suspended INTEGER NOT NULL DEFAULT 0
            )
        """)

        db.execute("""
            CREATE INDEX IF NOT EXISTS idx_accounts_name
            ON accounts(name COLLATE NOCASE)
        """)


def get_account(user_id):
    with connect() as db:
        row = db.execute(
            "SELECT * FROM accounts WHERE user_id = ?",
            (int(user_id),)
        ).fetchone()
        return dict(row) if row else None


def is_registered(user_id):
    return get_account(user_id) is not None


def is_suspended(user_id):
    account = get_account(user_id)
    return bool(account and account["suspended"])


def save_account(
    user_id,
    username,
    name,
    bio="",
    avatar="",
    agegroup=""
):
    with connect() as db:
        db.execute("""
            INSERT INTO accounts (
                user_id, username, name, bio, avatar, agegroup
            )
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                username = excluded.username,
                name = excluded.name,
                bio = excluded.bio,
                avatar = excluded.avatar,
                agegroup = excluded.agegroup
        """, (
            int(user_id),
            username or "",
            name.strip(),
            bio.strip(),
            avatar or "",
            agegroup or ""
        ))


def set_suspended(user_id, suspended):
    with connect() as db:
        cursor = db.execute(
            "UPDATE accounts SET suspended = ? WHERE user_id = ?",
            (1 if suspended else 0, int(user_id))
        )
        return cursor.rowcount > 0


def account_count():
    with connect() as db:
        return db.execute(
            "SELECT COUNT(*) FROM accounts"
        ).fetchone()[0]


def suspended_count():
    with connect() as db:
        return db.execute(
            "SELECT COUNT(*) FROM accounts WHERE suspended = 1"
        ).fetchone()[0]


def list_accounts(limit=8, offset=0):
    with connect() as db:
        rows = db.execute("""
            SELECT user_id, username, name, agegroup, suspended
            FROM accounts
            ORDER BY registered_at DESC
            LIMIT ? OFFSET ?
        """, (int(limit), int(offset))).fetchall()

        return [dict(row) for row in rows]


def search_accounts(query, limit=8):
    query = query.strip().replace("%", "").replace("_", "")
    pattern = f"%{query}%"

    with connect() as db:
        rows = db.execute("""
            SELECT user_id, username, name, agegroup, suspended
            FROM accounts
            WHERE name LIKE ? COLLATE NOCASE
               OR username LIKE ? COLLATE NOCASE
               OR CAST(user_id AS TEXT) LIKE ?
            ORDER BY registered_at DESC
            LIMIT ?
        """, (pattern, pattern, pattern, int(limit))).fetchall()

        return [dict(row) for row in rows]
