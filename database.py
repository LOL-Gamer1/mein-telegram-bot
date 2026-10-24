
# database.py
# MySQL-Datenbank für den LOL Studios Manager

import os
from contextlib import contextmanager
from datetime import date, datetime, timedelta, timezone

import mysql.connector
from mysql.connector import IntegrityError


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
        "autocommit": False,
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
    """Erstellt fehlende Tabellen, ohne vorhandene Tabellen zu löschen."""
    statements = [
        """
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
        """,
        """
        CREATE TABLE IF NOT EXISTS points (
            user_id BIGINT PRIMARY KEY,
            amount BIGINT NOT NULL DEFAULT 0
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS daily_claims (
            user_id BIGINT NOT NULL,
            claim_date DATE NOT NULL,
            PRIMARY KEY (user_id, claim_date)
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS reward_claims (
            user_id BIGINT NOT NULL,
            reward_type VARCHAR(20) NOT NULL,
            period_key VARCHAR(20) NOT NULL,
            claimed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (user_id, reward_type, period_key)
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS point_history (
            id BIGINT AUTO_INCREMENT PRIMARY KEY,
            user_id BIGINT NOT NULL,
            amount BIGINT NOT NULL,
            reason VARCHAR(255) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS reports (
            id BIGINT AUTO_INCREMENT PRIMARY KEY,
            user_id BIGINT NOT NULL,
            message TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS support_tickets (
            id BIGINT AUTO_INCREMENT PRIMARY KEY,
            user_id BIGINT NOT NULL,
            message TEXT NOT NULL,
            status VARCHAR(20) NOT NULL DEFAULT 'open',
            reply TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                ON UPDATE CURRENT_TIMESTAMP
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS user_settings (
            user_id BIGINT PRIMARY KEY,
            afk_reason VARCHAR(255) NOT NULL DEFAULT '',
            afk_since TIMESTAMP NULL,
            optout TINYINT NOT NULL DEFAULT 0
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS user_team (
            user_id BIGINT PRIMARY KEY,
            team_name VARCHAR(100) NOT NULL DEFAULT 'Member'
        )
        """,
    ]

    with connect() as db:
        cur = db.cursor()
        try:
            for statement in statements:
                cur.execute(statement)
        finally:
            cur.close()


def get_account(user_id):
    with connect() as db:
        cur = db.cursor(dictionary=True)
        try:
            cur.execute(
                "SELECT * FROM accounts WHERE user_id = %s",
                (int(user_id),),
            )
            return cur.fetchone()
        finally:
            cur.close()


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
    agegroup="",
):
    with connect() as db:
        cur = db.cursor()
        try:
            cur.execute(
                """
                INSERT INTO accounts
                    (user_id, username, name, bio, avatar, agegroup)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    username = VALUES(username),
                    name = VALUES(name),
                    bio = VALUES(bio),
                    avatar = VALUES(avatar),
                    agegroup = VALUES(agegroup)
                """,
                (
                    int(user_id),
                    username or "",
                    name or "",
                    bio or "",
                    avatar or "",
                    agegroup or "",
                ),
            )

            cur.execute(
                """
                INSERT IGNORE INTO points (user_id, amount)
                VALUES (%s, 0)
                """,
                (int(user_id),),
            )

            cur.execute(
                """
                INSERT IGNORE INTO user_settings (user_id)
                VALUES (%s)
                """,
                (int(user_id),),
            )
        finally:
            cur.close()


def unregister_account(user_id):
    """Löscht das Profil und zugehörige persönliche Bot-Daten."""
    user_id = int(user_id)

    with connect() as db:
        cur = db.cursor()
        try:
            for table in (
                "accounts",
                "points",
                "daily_claims",
                "reward_claims",
                "point_history",
                "reports",
                "support_tickets",
                "user_settings",
                "user_team",
            ):
                cur.execute(
                    f"DELETE FROM {table} WHERE user_id = %s",
                    (user_id,),
                )
        finally:
            cur.close()


def set_suspended(user_id, suspended=True):
    with connect() as db:
        cur = db.cursor()
        try:
            cur.execute(
                "UPDATE accounts SET suspended = %s WHERE user_id = %s",
                (int(bool(suspended)), int(user_id)),
            )
            return cur.rowcount > 0
        finally:
            cur.close()


def account_count():
    with connect() as db:
        cur = db.cursor()
        try:
            cur.execute("SELECT COUNT(*) FROM accounts")
            return int(cur.fetchone()[0])
        finally:
            cur.close()


def suspended_count():
    with connect() as db:
        cur = db.cursor()
        try:
            cur.execute(
                "SELECT COUNT(*) FROM accounts WHERE suspended = 1"
            )
            return int(cur.fetchone()[0])
        finally:
            cur.close()


def list_accounts(limit=50, offset=0):
    limit = max(1, min(int(limit), 100))
    offset = max(0, int(offset))

    with connect() as db:
        cur = db.cursor(dictionary=True)
        try:
            cur.execute(
                """
                SELECT * FROM accounts
                ORDER BY registered_at DESC
                LIMIT %s OFFSET %s
                """,
                (limit, offset),
            )
            return cur.fetchall()
        finally:
            cur.close()


def search_accounts(query, limit=20):
    term = "%" + query.strip() + "%"
    limit = max(1, min(int(limit), 100))

    with connect() as db:
        cur = db.cursor(dictionary=True)
        try:
            cur.execute(
                """
                SELECT * FROM accounts
                WHERE name LIKE %s OR username LIKE %s
                    OR CAST(user_id AS CHAR) LIKE %s
                ORDER BY name
                LIMIT %s
                """,
                (term, term, term, limit),
            )
            return cur.fetchall()
        finally:
            cur.close()


def get_points(user_id):
    with connect() as db:
        cur = db.cursor()
        try:
            cur.execute(
                "SELECT amount FROM points WHERE user_id = %s",
                (int(user_id),),
            )
            row = cur.fetchone()
            return int(row[0]) if row else 0
        finally:
            cur.close()


def add_points(user_id, amount, reason="Änderung"):
    amount = int(amount)
    user_id = int(user_id)

    if amount == 0:
        return get_points(user_id)

    with connect() as db:
        cur = db.cursor()
        try:
            cur.execute(
                """
                INSERT INTO points (user_id, amount)
                VALUES (%s, %s)
                ON DUPLICATE KEY UPDATE amount = amount + %s
                """,
                (user_id, amount, amount),
            )

            cur.execute(
                "SELECT amount FROM points WHERE user_id = %s",
                (user_id,),
            )
            total = int(cur.fetchone()[0])

            cur.execute(
                """
                INSERT INTO point_history (user_id, amount, reason)
                VALUES (%s, %s, %s)
                """,
                (user_id, amount, str(reason)[:255]),
            )

            return total
        finally:
            cur.close()


def claim_reward(user_id, reward_type, amount):
    """Belohnung einmal pro Tag/Woche/Monat/Jahr abholen."""
    user_id = int(user_id)
    reward_type = str(reward_type).lower()
    amount = int(amount)

    now = datetime.now(timezone.utc)
    today = now.date()

    if reward_type == "daily":
        period_key = today.isoformat()
    elif reward_type == "weekly":
        year, week, _ = today.isocalendar()
        period_key = f"{year}-W{week:02d}"
    elif reward_type == "monthly":
        period_key = f"{today.year}-{today.month:02d}"
    elif reward_type == "yearly":
        period_key = str(today.year)
    else:
        raise ValueError("Unbekannter Belohnungstyp.")

    with connect() as db:
        cur = db.cursor()
        try:
            cur.execute(
                "SELECT amount FROM points WHERE user_id = %s",
                (user_id,),
            )
            row = cur.fetchone()
            current = int(row[0]) if row else 0

            try:
                cur.execute(
                    """
                    INSERT INTO reward_claims
                        (user_id, reward_type, period_key)
                    VALUES (%s, %s, %s)
                    """,
                    (user_id, reward_type, period_key),
                )
            except IntegrityError:
                return False, current

            cur.execute(
                """
                INSERT INTO points (user_id, amount)
                VALUES (%s, %s)
                ON DUPLICATE KEY UPDATE amount = amount + %s
                """,
                (user_id, amount, amount),
            )

            cur.execute(
                """
                INSERT INTO point_history (user_id, amount, reason)
                VALUES (%s, %s, %s)
                """,
                (user_id, amount, f"{reward_type.title()}-Belohnung"),
            )

            cur.execute(
                "SELECT amount FROM points WHERE user_id = %s",
                (user_id,),
            )
            total = int(cur.fetchone()[0])
            return True, total
        finally:
            cur.close()


def claim_daily(user_id, amount=100):
    """Kompatibilität mit dem bisherigen Daily-Command."""
    return claim_reward(user_id, "daily", amount)


def leaderboard(limit=10):
    limit = max(1, min(int(limit), 100))

    with connect() as db:
        cur = db.cursor(dictionary=True)
        try:
            cur.execute(
                """
                SELECT p.user_id, p.amount, a.name, a.username
                FROM points AS p
                LEFT JOIN accounts AS a ON a.user_id = p.user_id
                WHERE COALESCE(a.suspended, 0) = 0
                ORDER BY p.amount DESC, p.user_id ASC
                LIMIT %s
                """,
                (limit,),
            )
            return cur.fetchall()
        finally:
            cur.close()


def get_rank(user_id):
    user_id = int(user_id)

    with connect() as db:
        cur = db.cursor()
        try:
            cur.execute(
                """
                SELECT COUNT(*) + 1
                FROM points p
                JOIN accounts a ON a.user_id = p.user_id
                WHERE p.amount > (
                    SELECT COALESCE(amount, 0)
                    FROM points WHERE user_id = %s
                )
                AND a.suspended = 0
                """,
                (user_id,),
            )
            return int(cur.fetchone()[0])
        finally:
            cur.close()


def get_history(user_id, limit=10):
    limit = max(1, min(int(limit), 50))

    with connect() as db:
        cur = db.cursor(dictionary=True)
        try:
            cur.execute(
                """
                SELECT amount, reason, created_at
                FROM point_history
                WHERE user_id = %s
                ORDER BY id DESC
                LIMIT %s
                """,
                (int(user_id), limit),
            )
            return cur.fetchall()
        finally:
            cur.close()


def set_afk(user_id, reason="AFK"):
    with connect() as db:
        cur = db.cursor()
        try:
            cur.execute(
                """
                INSERT INTO user_settings (user_id, afk_reason, afk_since)
                VALUES (%s, %s, UTC_TIMESTAMP())
                ON DUPLICATE KEY UPDATE
                    afk_reason = VALUES(afk_reason),
                    afk_since = VALUES(afk_since)
                """,
                (int(user_id), str(reason)[:255]),
            )
        finally:
            cur.close()


def clear_afk(user_id):
    with connect() as db:
        cur = db.cursor()
        try:
            cur.execute(
                """
                UPDATE user_settings
                SET afk_reason = '', afk_since = NULL
                WHERE user_id = %s
                """,
                (int(user_id),),
            )
        finally:
            cur.close()


def get_afk(user_id):
    with connect() as db:
        cur = db.cursor(dictionary=True)
        try:
            cur.execute(
                """
                SELECT afk_reason, afk_since
                FROM user_settings
                WHERE user_id = %s
                """,
                (int(user_id),),
            )
            return cur.fetchone()
        finally:
            cur.close()


def set_optout(user_id, enabled=True):
    with connect() as db:
        cur = db.cursor()
        try:
            cur.execute(
                """
                INSERT INTO user_settings (user_id, optout)
                VALUES (%s, %s)
                ON DUPLICATE KEY UPDATE optout = VALUES(optout)
                """,
                (int(user_id), int(bool(enabled))),
            )
        finally:
            cur.close()


def get_optout(user_id):
    with connect() as db:
        cur = db.cursor()
        try:
            cur.execute(
                "SELECT optout FROM user_settings WHERE user_id = %s",
                (int(user_id),),
            )
            row = cur.fetchone()
            return bool(row and row[0])
        finally:
            cur.close()


def create_report(user_id, message):
    with connect() as db:
        cur = db.cursor()
        try:
            cur.execute(
                """
                INSERT INTO reports (user_id, message)
                VALUES (%s, %s)
                """,
                (int(user_id), str(message)[:4000]),
            )
            return int(cur.lastrowid)
        finally:
            cur.close()


def create_ticket(user_id, message):
    with connect() as db:
        cur = db.cursor()
        try:
            cur.execute(
                """
                INSERT INTO support_tickets (user_id, message, reply)
                VALUES (%s, %s, '')
                """,
                (int(user_id), str(message)[:4000]),
            )
            return int(cur.lastrowid)
        finally:
            cur.close()


def get_ticket(ticket_id):
    with connect() as db:
        cur = db.cursor(dictionary=True)
        try:
            cur.execute(
                "SELECT * FROM support_tickets WHERE id = %s",
                (int(ticket_id),),
            )
            return cur.fetchone()
        finally:
            cur.close()


def list_tickets(user_id=None, status=None, limit=20):
    limit = max(1, min(int(limit), 100))
    clauses = []
    params = []

    if user_id is not None:
        clauses.append("user_id = %s")
        params.append(int(user_id))

    if status:
        clauses.append("status = %s")
        params.append(str(status))

    where = ("WHERE " + " AND ".join(clauses)) if clauses else ""
    params.append(limit)

    with connect() as db:
        cur = db.cursor(dictionary=True)
        try:
            cur.execute(
                f"""
                SELECT * FROM support_tickets
                {where}
                ORDER BY id DESC
                LIMIT %s
                """,
                tuple(params),
            )
            return cur.fetchall()
        finally:
            cur.close()


def close_ticket(ticket_id):
    with connect() as db:
        cur = db.cursor()
        try:
            cur.execute(
                """
                UPDATE support_tickets
                SET status = 'closed'
                WHERE id = %s
                """,
                (int(ticket_id),),
            )
            return cur.rowcount > 0
        finally:
            cur.close()


def reply_ticket(ticket_id, reply):
    with connect() as db:
        cur = db.cursor()
        try:
            cur.execute(
                """
                UPDATE support_tickets
                SET reply = %s, status = 'answered'
                WHERE id = %s
                """,
                (str(reply)[:4000], int(ticket_id)),
            )
            return cur.rowcount > 0
        finally:
            cur.close()


def set_team(user_id, team_name):
    with connect() as db:
        cur = db.cursor()
        try:
            cur.execute(
                """
                INSERT INTO user_team (user_id, team_name)
                VALUES (%s, %s)
                ON DUPLICATE KEY UPDATE team_name = VALUES(team_name)
                """,
                (int(user_id), str(team_name)[:100]),
            )
        finally:
            cur.close()


def get_team(user_id):
    with connect() as db:
        cur = db.cursor()
        try:
            cur.execute(
                "SELECT team_name FROM user_team WHERE user_id = %s",
                (int(user_id),),
            )
            row = cur.fetchone()
            return row[0] if row else "Member"
        finally:
            cur.close()
