
# database.py
import os
import sqlite3
from pathlib import Path
from contextlib import contextmanager

# FadeHost: DATABASE_PATH kann auf einen dauerhaft gespeicherten
# Dateipfad gesetzt werden. Ohne Einstellung bleibt der alte Pfad aktiv.
_default_path = Path(__file__).with_name("lol_manager.db")
DB_PATH = Path(os.getenv("DATABASE_PATH", str(_default_path))).expanduser()


@contextmanager
def connect():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(DB_PATH, timeout=30)
    db.row_factory = sqlite3.Row

    try:
        db.execute("PRAGMA busy_timeout = 30000")
        db.execute("PRAGMA foreign_keys = ON")
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


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

        db.execute("""
            CREATE TABLE IF NOT EXISTS points (
                user_id INTEGER PRIMARY KEY,
                amount INTEGER NOT NULL DEFAULT 0
            )
        """)

        db.execute("""
            CREATE TABLE IF NOT EXISTS daily_claims (
                user_id INTEGER NOT NULL,
                claim_date TEXT NOT NULL,
                PRIMARY KEY (user_id, claim_date)
            )
        """)

        db.execute("""
            CREATE TABLE IF NOT EXISTS reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                message TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
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
    return bool(account and account.get("suspended", 0))


def save_account(
    user_id,
    username="",
    name="",
    bio="",
    avatar="",
    agegroup=""
):
    with connect() as db:
        db.execute("""
            INSERT INTO accounts
                (user_id, username, name, bio, avatar, agegroup)
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
            name or "",
            bio or "",
            avatar or "",
            agegroup or ""
        ))


def set_suspended(user_id, suspended=True):
    with connect() as db:
        result = db.execute(
            "UPDATE accounts SET suspended = ? WHERE user_id = ?",
            (1 if suspended else 0, int(user_id))
        )
        return result.rowcount > 0


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


def list_accounts(limit=50, offset=0):
    with connect() as db:
        rows = db.execute("""
            SELECT * FROM accounts
            ORDER BY registered_at DESC
            LIMIT ? OFFSET ?
        """, (int(limit), int(offset))).fetchall()
        return [dict(row) for row in rows]


def search_accounts(query, limit=20):
    term = f"%{query.strip()}%"
    with connect() as db:
        rows = db.execute("""
            SELECT * FROM accounts
            WHERE name LIKE ? COLLATE NOCASE
               OR username LIKE ? COLLATE NOCASE
            ORDER BY name COLLATE NOCASE
            LIMIT ?
        """, (term, term, int(limit))).fetchall()
        return [dict(row) for row in rows]


def get_points(user_id):
    with connect() as db:
        row = db.execute(
            "SELECT amount FROM points WHERE user_id = ?",
            (int(user_id),)
        ).fetchone()
        return row["amount"] if row else 0


def add_points(user_id, amount):
    with connect() as db:
        db.execute("""
            INSERT INTO points (user_id, amount)
            VALUES (?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                amount = amount + excluded.amount
        """, (int(user_id), int(amount)))
        row = db.execute(
            "SELECT amount FROM points WHERE user_id = ?",
            (int(user_id),)
        ).fetchone()
        return row["amount"]


def claim_daily(user_id, amount=100):
    from datetime import datetime, timezone

    today = datetime.now(timezone.utc).date().isoformat()

    with connect() as db:
        db.execute("BEGIN IMMEDIATE")

        already_claimed = db.execute("""
            SELECT 1 FROM daily_claims
            WHERE user_id = ? AND claim_date = ?
        """, (int(user_id), today)).fetchone()

        if already_claimed:
            row = db.execute(
                "SELECT amount FROM points WHERE user_id = ?",
                (int(user_id),)
            ).fetchone()
            return False, row["amount"] if row else 0

        db.execute("""
            INSERT INTO daily_claims (user_id, claim_date)
            VALUES (?, ?)
        """, (int(user_id), today))

        db.execute("""
            INSERT INTO points (user_id, amount)
            VALUES (?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                amount = amount + excluded.amount
        """, (int(user_id), int(amount)))

        row = db.execute(
            "SELECT amount FROM points WHERE user_id = ?",
            (int(user_id),)
        ).fetchone()

        return True, row["amount"]


def leaderboard(limit=10):
    with connect() as db:
        rows = db.execute("""
            SELECT p.user_id, p.amount,
                   a.name, a.username
            FROM points p
            LEFT JOIN accounts a ON a.user_id = p.user_id
            ORDER BY p.amount DESC, p.user_id ASC
            LIMIT ?
        """, (int(limit),)).fetchall()
        return [dict(row) for row in rows]


def create_report(user_id, message):
    with connect() as db:
        cursor = db.execute("""
            INSERT INTO reports (user_id, message)
            VALUES (?, ?)
        """, (int(user_id), str(message)))
        return cursor.lastrowid
