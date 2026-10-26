
# database.py — LOL Studios Manager
# MySQL-Datenbank für Accounts, Support, Gruppenanfragen und Moderation

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
    """Erstellt fehlende Tabellen, ohne bestehende Tabellen zu löschen."""
    with connect() as db:
        cur = db.cursor()
        try:
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
                CREATE TABLE IF NOT EXISTS group_join_requests (
                    id BIGINT AUTO_INCREMENT PRIMARY KEY,
                    requester_id BIGINT NOT NULL,
                    group_link TEXT NOT NULL,
                    status VARCHAR(20) NOT NULL DEFAULT 'pending',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    decided_at TIMESTAMP NULL,
                    decided_by BIGINT NULL
                )
            """)

            # Wichtig: TEXT darf hier keinen DEFAULT-Wert haben.
            cur.execute("""
                CREATE TABLE IF NOT EXISTS support_tickets (
                    id BIGINT AUTO_INCREMENT PRIMARY KEY,
                    user_id BIGINT NOT NULL,
                    message TEXT NOT NULL,
                    reply TEXT NOT NULL,
                    status VARCHAR(20) NOT NULL DEFAULT 'open',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    replied_at TIMESTAMP NULL,
                    INDEX idx_support_status (status),
                    INDEX idx_support_user (user_id)
                )
            """)

            cur.execute("""
                CREATE TABLE IF NOT EXISTS group_moderation_settings (
                    chat_id BIGINT PRIMARY KEY,
                    anti_spam TINYINT NOT NULL DEFAULT 0,
                    anti_insult TINYINT NOT NULL DEFAULT 0,
                    anti_sticker TINYINT NOT NULL DEFAULT 0,
                    welcome_enabled TINYINT NOT NULL DEFAULT 0,
                    welcome_text TEXT NOT NULL,
                    rules TEXT NOT NULL,
                    warning_limit INT NOT NULL DEFAULT 3,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        ON UPDATE CURRENT_TIMESTAMP
                )
            """)

            cur.execute("""
                CREATE TABLE IF NOT EXISTS group_warnings (
                    chat_id BIGINT NOT NULL,
                    user_id BIGINT NOT NULL,
                    warning_count INT NOT NULL DEFAULT 0,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        ON UPDATE CURRENT_TIMESTAMP,
                    PRIMARY KEY (chat_id, user_id),
                    INDEX idx_group_warnings_user (user_id)
                )
            """)
        finally:
            cur.close()


# ---------------- ACCOUNTS ----------------

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
                int(user_id),
                username or "",
                name or "",
                bio or "",
                avatar or "",
                agegroup or "",
            ))
        finally:
            cur.close()


def set_suspended(user_id, suspended=True):
    with connect() as db:
        cur = db.cursor()
        try:
            cur.execute(
                "UPDATE accounts SET suspended=%s WHERE user_id=%s",
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
            return cur.fetchone()[0]
        finally:
            cur.close()


def suspended_count():
    with connect() as db:
        cur = db.cursor()
        try:
            cur.execute("SELECT COUNT(*) FROM accounts WHERE suspended=1")
            return cur.fetchone()[0]
        finally:
            cur.close()


def list_accounts(limit=50, offset=0):
    with connect() as db:
        cur = db.cursor(dictionary=True)
        try:
            cur.execute("""
                SELECT * FROM accounts
                ORDER BY registered_at DESC
                LIMIT %s OFFSET %s
            """, (int(limit), int(offset)))
            return cur.fetchall()
        finally:
            cur.close()


def search_accounts(query, limit=20):
    term = "%" + query.strip() + "%"
    with connect() as db:
        cur = db.cursor(dictionary=True)
        try:
            cur.execute("""
                SELECT * FROM accounts
                WHERE name LIKE %s OR username LIKE %s
                ORDER BY name
                LIMIT %s
            """, (term, term, int(limit)))
            return cur.fetchall()
        finally:
            cur.close()


# ---------------- POINTS ----------------

def get_points(user_id):
    with connect() as db:
        cur = db.cursor()
        try:
            cur.execute(
                "SELECT amount FROM points WHERE user_id=%s",
                (int(user_id),),
            )
            row = cur.fetchone()
            return row[0] if row else 0
        finally:
            cur.close()


def add_points(user_id, amount):
    amount = int(amount)
    with connect() as db:
        cur = db.cursor()
        try:
            cur.execute("""
                INSERT INTO points (user_id, amount)
                VALUES (%s, %s)
                ON DUPLICATE KEY UPDATE amount = amount + %s
            """, (int(user_id), amount, amount))
            cur.execute(
                "SELECT amount FROM points WHERE user_id=%s",
                (int(user_id),),
            )
            return cur.fetchone()[0]
        finally:
            cur.close()


def claim_daily(user_id, amount=100):
    from datetime import datetime, timezone

    today = datetime.now(timezone.utc).date()
    amount = int(amount)

    with connect() as db:
        cur = db.cursor()
        try:
            cur.execute(
                "SELECT amount FROM points WHERE user_id=%s",
                (int(user_id),),
            )
            row = cur.fetchone()
            current = row[0] if row else 0

            try:
                cur.execute("""
                    INSERT INTO daily_claims (user_id, claim_date)
                    VALUES (%s, %s)
                """, (int(user_id), today))
            except mysql.connector.IntegrityError:
                return False, current

            cur.execute("""
                INSERT INTO points (user_id, amount)
                VALUES (%s, %s)
                ON DUPLICATE KEY UPDATE amount = amount + %s
            """, (int(user_id), amount, amount))

            cur.execute(
                "SELECT amount FROM points WHERE user_id=%s",
                (int(user_id),),
            )
            return True, cur.fetchone()[0]
        finally:
            cur.close()


def leaderboard(limit=10):
    with connect() as db:
        cur = db.cursor(dictionary=True)
        try:
            cur.execute("""
                SELECT p.user_id, p.amount, a.name, a.username
                FROM points p
                LEFT JOIN accounts a ON a.user_id = p.user_id
                ORDER BY p.amount DESC, p.user_id ASC
                LIMIT %s
            """, (int(limit),))
            return cur.fetchall()
        finally:
            cur.close()


# ---------------- REPORTS ----------------

def create_report(user_id, message):
    with connect() as db:
        cur = db.cursor()
        try:
            cur.execute("""
                INSERT INTO reports (user_id, message)
                VALUES (%s, %s)
            """, (int(user_id), str(message)))
            return cur.lastrowid
        finally:
            cur.close()


# ---------------- SUPPORT TICKETS ----------------

def create_ticket(user_id, message):
    message = str(message).strip()
    if not message:
        raise ValueError("Die Ticketnachricht darf nicht leer sein.")

    with connect() as db:
        cur = db.cursor()
        try:
            # reply wird beim Anlegen ausdrücklich als leerer Text gesetzt.
            cur.execute("""
                INSERT INTO support_tickets
                    (user_id, message, reply, status)
                VALUES (%s, %s, %s, %s)
            """, (int(user_id), message, "", "open"))
            return cur.lastrowid
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


def list_tickets(status="open", limit=10):
    with connect() as db:
        cur = db.cursor(dictionary=True)
        try:
            cur.execute("""
                SELECT * FROM support_tickets
                WHERE status = %s
                ORDER BY created_at DESC
                LIMIT %s
            """, (str(status), int(limit)))
            return cur.fetchall()
        finally:
            cur.close()


def reply_ticket(ticket_id, reply):
    reply = str(reply).strip()
    if not reply:
        raise ValueError("Die Antwort darf nicht leer sein.")

    with connect() as db:
        cur = db.cursor()
        try:
            cur.execute("""
                UPDATE support_tickets
                SET reply = %s,
                    status = 'answered',
                    replied_at = CURRENT_TIMESTAMP
                WHERE id = %s
            """, (reply, int(ticket_id)))
            return cur.rowcount > 0
        finally:
            cur.close()


def close_ticket(ticket_id):
    with connect() as db:
        cur = db.cursor()
        try:
            cur.execute(
                "UPDATE support_tickets SET status='closed' WHERE id=%s",
                (int(ticket_id),),
            )
            return cur.rowcount > 0
        finally:
            cur.close()


def list_user_tickets(user_id, limit=10):
    with connect() as db:
        cur = db.cursor(dictionary=True)
        try:
            cur.execute("""
                SELECT * FROM support_tickets
                WHERE user_id = %s
                ORDER BY created_at DESC
                LIMIT %s
            """, (int(user_id), int(limit)))
            return cur.fetchall()
        finally:
            cur.close()


# ---------------- GROUP JOIN REQUESTS ----------------

def create_join_request(requester_id, group_link):
    with connect() as db:
        cur = db.cursor()
        try:
            cur.execute("""
                INSERT INTO group_join_requests
                    (requester_id, group_link, status)
                VALUES (%s, %s, 'pending')
            """, (int(requester_id), str(group_link)))
            return cur.lastrowid
        finally:
            cur.close()


def get_join_request(request_id):
    with connect() as db:
        cur = db.cursor(dictionary=True)
        try:
            cur.execute(
                "SELECT * FROM group_join_requests WHERE id=%s",
                (int(request_id),),
            )
            return cur.fetchone()
        finally:
            cur.close()


def list_join_requests(status="pending", limit=20):
    with connect() as db:
        cur = db.cursor(dictionary=True)
        try:
            cur.execute("""
                SELECT * FROM group_join_requests
                WHERE status = %s
                ORDER BY created_at DESC
                LIMIT %s
            """, (str(status), int(limit)))
            return cur.fetchall()
        finally:
            cur.close()


def decide_join_request(request_id, status, owner_id):
    if status not in ("approved", "rejected"):
        raise ValueError("Ungültiger Status.")

    with connect() as db:
        cur = db.cursor()
        try:
            cur.execute("""
                UPDATE group_join_requests
                SET status = %s,
                    decided_at = CURRENT_TIMESTAMP,
                    decided_by = %s
                WHERE id = %s AND status = 'pending'
            """, (status, int(owner_id), int(request_id)))
            return cur.rowcount > 0
        finally:
            cur.close()


# ---------------- GRUPPENMODERATION ----------------

DEFAULT_MODERATION_SETTINGS = {
    "anti_spam": 0,
    "anti_insult": 0,
    "anti_sticker": 0,
    "welcome_enabled": 0,
    "welcome_text": "Willkommen {name}!",
    "rules": "",
    "warning_limit": 3,
}


def get_group_settings(chat_id):
    """Liefert Gruppeneinstellungen und legt Standardwerte an."""
    chat_id = int(chat_id)

    with connect() as db:
        cur = db.cursor(dictionary=True)
        try:
            cur.execute("""
                INSERT IGNORE INTO group_moderation_settings
                    (chat_id, welcome_text, rules)
                VALUES (%s, %s, %s)
            """, (
                chat_id,
                DEFAULT_MODERATION_SETTINGS["welcome_text"],
                DEFAULT_MODERATION_SETTINGS["rules"],
            ))

            cur.execute("""
                SELECT * FROM group_moderation_settings WHERE chat_id=%s
            """, (chat_id,))
            row = cur.fetchone()
        finally:
            cur.close()

    if not row:
        return {"chat_id": chat_id, **DEFAULT_MODERATION_SETTINGS.copy()}

    for key, value in DEFAULT_MODERATION_SETTINGS.items():
        row.setdefault(key, value)

    return row


def set_group_setting(chat_id, setting, value):
    """Ändert genau eine erlaubte Gruppeneinstellung."""
    allowed = {
        "anti_spam",
        "anti_insult",
        "anti_sticker",
        "welcome_enabled",
        "welcome_text",
        "rules",
        "warning_limit",
    }
    if setting not in allowed:
        raise ValueError("Unbekannte Moderationseinstellung.")

    chat_id = int(chat_id)
    get_group_settings(chat_id)

    with connect() as db:
        cur = db.cursor()
        try:
            cur.execute(
                f"UPDATE group_moderation_settings SET {setting}=%s "
                "WHERE chat_id=%s",
                (value, chat_id),
            )
        finally:
            cur.close()

    return get_group_settings(chat_id)


def get_group_warnings(chat_id, user_id):
    with connect() as db:
        cur = db.cursor()
        try:
            cur.execute("""
                SELECT warning_count
                FROM group_warnings
                WHERE chat_id=%s AND user_id=%s
            """, (int(chat_id), int(user_id)))
            row = cur.fetchone()
            return int(row[0]) if row else 0
        finally:
            cur.close()


def add_group_warning(chat_id, user_id):
    """Erhöht die Verwarnungen eines Nutzers in einer Gruppe."""
    with connect() as db:
        cur = db.cursor()
        try:
            cur.execute("""
                INSERT INTO group_warnings (chat_id, user_id, warning_count)
                VALUES (%s, %s, 1)
                ON DUPLICATE KEY UPDATE
                    warning_count = warning_count + 1
            """, (int(chat_id), int(user_id)))

            cur.execute("""
                SELECT warning_count FROM group_warnings
                WHERE chat_id=%s AND user_id=%s
            """, (int(chat_id), int(user_id)))
            return int(cur.fetchone()[0])
        finally:
            cur.close()


def reset_group_warnings(chat_id, user_id):
    with connect() as db:
        cur = db.cursor()
        try:
            cur.execute("""
                DELETE FROM group_warnings
                WHERE chat_id=%s AND user_id=%s
            """, (int(chat_id), int(user_id)))
            return cur.rowcount > 0
        finally:
            cur.close()
