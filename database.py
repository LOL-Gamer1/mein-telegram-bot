
# database.py
import os
from contextlib import contextmanager
import mysql.connector


def mysql_config():
    required = [
        "MYSQL_HOST",
        "MYSQL_DATABASE",
        "MYSQL_USER",
        "MYSQL_PASSWORD",
    ]
    missing = [key for key in required if not os.getenv(key)]
    if missing:
        raise RuntimeError(
            "Fehlende Umgebungsvariablen: " + ", ".join(missing)
        )

    return {
        "host": os.environ["MYSQL_HOST"],
        "port": int(os.getenv("MYSQL_PORT", "3306")),
        "database": os.environ["MYSQL_DATABASE"],
        "user": os.environ["MYSQL_USER"],
        "password": os.environ["MYSQL_PASSWORD"],
        "connection_timeout": 15,
    }


@contextmanager
def connect():
    db = mysql.connector.connect(**mysql_config())
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def init_db():
    with connect() as db:
        cur = db.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS accounts (
                user_id BIGINT PRIMARY KEY,
                username VARCHAR(255) NOT NULL DEFAULT '',
                name VARCHAR(255) NOT NULL DEFAULT '',
                bio TEXT NOT NULL,
                avatar TEXT NOT NULL,
                agegroup VARCHAR(20) NOT NULL DEFAULT '',
                registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                suspended TINYINT NOT NULL DEFAULT 0
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS points (
                user_id BIGINT PRIMARY KEY,
                amount BIGINT NOT NULL DEFAULT 0
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS daily_claims (
                user_id BIGINT NOT NULL,
                claim_date DATE NOT NULL,
                PRIMARY KEY (user_id, claim_date)
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS reports (
                id BIGINT AUTO_INCREMENT PRIMARY KEY,
                user_id BIGINT NOT NULL,
                message TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cur.execute("""
            CREATE INDEX idx_accounts_name
            ON accounts (name)
        """)
        cur.close()


def get_account(user_id):
    with connect() as db:
        cur = db.cursor(dictionary=True)
        cur.execute(
            "SELECT * FROM accounts WHERE user_id = %s",
            (int(user_id),)
        )
        row = cur.fetchone()
        cur.close()
        return row


def is_registered(user_id):
    return get_account(user_id) is not None


def is_suspended(user_id):
    account = get_account(user_id)
    return bool(account and account.get("suspended", 0))


def save_account(
    user_id, username="", name="", bio="", avatar="", agegroup=""
):
    with connect() as db:
        cur = db.cursor()
        cur.execute("""
            INSERT INTO accounts
                (user_id, username, name, bio, avatar, agegroup)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                username = VALUES(username),
                name = VALUES(name),
                bio = VALUES(bio),
                avatar = VALUES(avatar),
                agegroup = VALUES(agegroup)
        """, (
            int(user_id), username or "", name or "",
            bio or "", avatar or "", agegroup or ""
        ))
        cur.close()


def set_suspended(user_id, suspended=True):
    with connect() as db:
        cur = db.cursor()
        cur.execute(
            "UPDATE accounts SET suspended=%s WHERE user_id=%s",
            (int(bool(suspended)), int(user_id))
        )
        changed = cur.rowcount > 0
        cur.close()
        return changed


def account_count():
    with connect() as db:
        cur = db.cursor()
        cur.execute("SELECT COUNT(*) FROM accounts")
        result = cur.fetchone()[0]
        cur.close()
        return result


def suspended_count():
    with connect() as db:
        cur = db.cursor()
        cur.execute("SELECT COUNT(*) FROM accounts WHERE suspended=1")
        result = cur.fetchone()[0]
        cur.close()
        return result


def list_accounts(limit=50, offset=0):
    with connect() as db:
        cur = db.cursor(dictionary=True)
        cur.execute("""
            SELECT * FROM accounts
            ORDER BY registered_at DESC
            LIMIT %s OFFSET %s
        """, (int(limit), int(offset)))
        rows = cur.fetchall()
        cur.close()
        return rows


def search_accounts(query, limit=20):
    term = "%" + query.strip() + "%"
    with connect() as db:
        cur = db.cursor(dictionary=True)
        cur.execute("""
            SELECT * FROM accounts
            WHERE name LIKE %s OR username LIKE %s
            ORDER BY name
            LIMIT %s
        """, (term, term, int(limit)))
        rows = cur.fetchall()
        cur.close()
        return rows


def get_points(user_id):
    with connect() as db:
        cur = db.cursor()
        cur.execute(
            "SELECT amount FROM points WHERE user_id=%s",
            (int(user_id),)
        )
        row = cur.fetchone()
        cur.close()
        return row[0] if row else 0


def add_points(user_id, amount):
    with connect() as db:
        cur = db.cursor()
        cur.execute("""
            INSERT INTO points (user_id, amount)
            VALUES (%s, %s)
            ON DUPLICATE KEY UPDATE amount = amount + %s
        """, (int(user_id), int(amount), int(amount)))
        cur.execute(
            "SELECT amount FROM points WHERE user_id=%s",
            (int(user_id),)
        )
        result = cur.fetchone()[0]
        cur.close()
        return result


def claim_daily(user_id, amount=100):
    from datetime import datetime, timezone

    today = datetime.now(timezone.utc).date()

    with connect() as db:
        cur = db.cursor()
        cur.execute(
            "SELECT amount FROM points WHERE user_id=%s",
            (int(user_id),)
        )
        row = cur.fetchone()
        current = row[0] if row else 0

        try:
            cur.execute("""
                INSERT INTO daily_claims (user_id, claim_date)
                VALUES (%s, %s)
            """, (int(user_id), today))
        except mysql.connector.IntegrityError:
            cur.close()
            return False, current

        cur.execute("""
            INSERT INTO points (user_id, amount)
            VALUES (%s, %s)
            ON DUPLICATE KEY UPDATE amount = amount + %s
        """, (int(user_id), int(amount), int(amount)))
        cur.execute(
            "SELECT amount FROM points WHERE user_id=%s",
            (int(user_id),)
        )
        total = cur.fetchone()[0]
        cur.close()
        return True, total


def leaderboard(limit=10):
    with connect() as db:
        cur = db.cursor(dictionary=True)
        cur.execute("""
            SELECT p.user_id, p.amount, a.name, a.username
            FROM points p
            LEFT JOIN accounts a ON a.user_id = p.user_id
            ORDER BY p.amount DESC, p.user_id ASC
            LIMIT %s
        """, (int(limit),))
        rows = cur.fetchall()
        cur.close()
        return rows


def create_report(user_id, message):
    with connect() as db:
        cur = db.cursor()
        cur.execute("""
            INSERT INTO reports (user_id, message)
            VALUES (%s, %s)
        """, (int(user_id), str(message)))
        report_id = cur.lastrowid
        cur.close()
        return report_id
