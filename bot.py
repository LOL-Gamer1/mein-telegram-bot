
import os
import random
import sqlite3
import threading
import logging
from http.server import BaseHTTPRequestHandler, HTTPServer

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ChatPermissions,
)
from telegram.error import (
    InvalidToken,
    TelegramError,
    NetworkError,
    TimedOut,
)
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

# ---------------- CONFIG ----------------

TOKEN = os.getenv("BOT_TOKEN", "").strip()
PORT = int(os.getenv("PORT", "10000"))
DB_FILE = os.getenv("DB_FILE", "bot_data.db")

logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    level=logging.INFO,
)
logging.getLogger("httpx").setLevel(logging.WARNING)
log = logging.getLogger("LOLStudiosManager")

# ---------------- HEALTH CHECK ----------------

class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path not in ("/", "/health"):
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"Not found")
            return

        self.send_response(200)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.end_headers()
        self.wfile.write(b"LOL Studios Manager is running!")

    def log_message(self, format, *args):
        pass


def start_health_server():
    try:
        server = HTTPServer(("0.0.0.0", PORT), HealthHandler)
        threading.Thread(
            target=server.serve_forever,
            daemon=True,
        ).start()
        log.info("Health server started on port %s", PORT)
    except OSError:
        log.exception("Could not start health server")


# ---------------- DATABASE ----------------

def init_db():
    with sqlite3.connect(DB_FILE) as db:
        db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                chat_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                xp INTEGER DEFAULT 0,
                coins INTEGER DEFAULT 0,
                warnings INTEGER DEFAULT 0,
                PRIMARY KEY (chat_id, user_id)
            )
        """)
        db.commit()


def ensure_user(chat_id, user_id, name):
    with sqlite3.connect(DB_FILE) as db:
        db.execute("""
            INSERT OR IGNORE INTO users
            (chat_id, user_id, name, xp, coins, warnings)
            VALUES (?, ?, ?, 0, 0, 0)
        """, (chat_id, user_id, name))


def add_reward(chat_id, user_id, name, xp=0, coins=0):
    ensure_user(chat_id, user_id, name)
    with sqlite3.connect(DB_FILE) as db:
        db.execute("""
            UPDATE users
            SET name = ?, xp = xp + ?, coins = coins + ?
            WHERE chat_id = ? AND user_id = ?
        """, (name, xp, coins, chat_id, user_id))


def get_stats(chat_id, user_id, name):
    ensure_user(chat_id, user_id, name)
    with sqlite3.connect(DB_FILE) as db:
        row = db.execute("""
            SELECT xp, coins, warnings FROM users
            WHERE chat_id = ? AND user_id = ?
        """, (chat_id, user_id)).fetchone()
    return row or (0, 0, 0)


# ---------------- HELPERS ----------------

def mention(user):
    name = user.full_name or "User"
    return f'<a href="tg://user?id={user.id}">{name}</a>'


async def reply(update, text, **kwargs):
    message = update.effective_message
    if message:
        await message.reply_text(text, **kwargs)


async def get_target(update, context):
    message = update.effective_message

    if message and message.reply_to_message:
        return message.reply_to_message.from_user

    if context.args:
        raw = context.args[0]
        if raw.isdigit():
            try:
                return await context.bot.get_chat(int(raw))
            except TelegramError:
                return None

    return None


async def is_admin(update, context):
    if not update.effective_chat or not update.effective_user:
        return False

    try:
        member = await context.bot.get_chat_member(
            update.effective_chat.id,
            update.effective_user.id,
        )
        return member.status in ("administrator", "creator")
    except TelegramError:
        return False


async def admin_required(update, context):
    if not await is_admin(update, context):
        await reply(update, "⛔ Dieser Befehl ist nur für Gruppenadmins.")
        return False
    return True


def group_only(update):
    chat = update.effective_chat
    return bool(chat and chat.type in ("group", "supergroup"))


# ---------------- MENU ----------------

MENU = InlineKeyboardMarkup([
    [
        InlineKeyboardButton("🎮 Spiele", callback_data="menu_games"),
        InlineKeyboardButton("😂 Fun", callback_data="menu_fun"),
    ],
    [
        InlineKeyboardButton("👤 Profil", callback_data="menu_profile"),
        InlineKeyboardButton("🏆 Rangliste", callback_data="menu_top"),
    ],
    [
        InlineKeyboardButton("🛡️ Moderation", callback_data="menu_mod"),
        InlineKeyboardButton("ℹ️ Hilfe", callback_data="menu_help"),
    ],
])


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    chat = update.effective_chat

    if user and chat:
        ensure_user(chat.id, user.id, user.full_name)

    await reply(
        update,
        "🚀 <b>LOL Studios Manager</b>\n\n"
        "Dein Bot für Gruppen, Spiele und Fun!\n"
        "Öffne das Menü und entdecke die Befehle.",
        parse_mode="HTML",
        reply_markup=MENU,
    )


async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await reply(
        update,
        "✨ <b>LOL Studios Manager – Hauptmenü</b>\n"
        "Wähle eine Kategorie:",
        parse_mode="HTML",
        reply_markup=MENU,
    )


async def menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    pages = {
        "menu_games": (
            "🎮 <b>SPIELE</b>\n\n"
            "/dice – Würfeln\n"
            "/coin – Münze werfen\n"
            "/rps – Schere, Stein, Papier\n"
            "/guess – Zahl erraten\n"
            "/quiz – Quizfrage\n"
            "/roll – Zufallszahl"
        ),
        "menu_fun": (
            "😂 <b>FUN</b>\n\n"
            "/joke – Zufallswitz\n"
            "/8ball – Magische Kugel\n"
            "/choose – Zufällige Auswahl\n"
            "/say Text – Text wiederholen\n"
            "/id – Deine ID"
        ),
        "menu_profile": (
            "👤 <b>PROFIL</b>\n\n"
            "/profile – XP, Coins und Warnungen\n"
            "/daily – Tägliche Coins\n"
            "/top – Rangliste"
        ),
        "menu_top": (
            "🏆 <b>RANGLISTE</b>\n\n"
            "/top – Die Top-Spieler dieses Chats"
        ),
        "menu_mod": (
            "🛡️ <b>GRUPPENMODERATION</b>\n\n"
            "Antworte auf eine Nachricht oder gib eine User-ID an:\n"
            "/kick – Mitglied entfernen\n"
            "/ban – Mitglied sperren\n"
            "/unban ID – Sperre aufheben\n"
            "/mute – Stummschalten\n"
            "/unmute – Stummschaltung aufheben\n"
            "/warn – Verwarnen\n"
            "/warnings – Verwarnungen anzeigen\n"
            "/clearwarns – Verwarnungen löschen\n"
            "/purge ZAHL – Nachrichten löschen\n"
            "/pin – Nachricht anheften\n"
            "/unpin – Anheftung lösen\n"
            "/lock – Chat sperren\n"
            "/unlock – Chat freigeben\n"
            "/admins – Admins anzeigen"
        ),
        "menu_help": (
            "ℹ️ <b>HILFE</b>\n\n"
            "/start – Start\n"
            "/menu – Hauptmenü\n"
            "/help – Alle Kategorien\n"
            "Bei Moderationsbefehlen brauchst du Adminrechte."
        ),
    }

    text = pages.get(query.data, "Menü nicht gefunden.")
    await query.edit_message_text(
        text,
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("⬅️ Hauptmenü", callback_data="menu_home")
        ]]),
    )

    if query.data == "menu_home":
        await query.edit_message_text(
            "✨ <b>LOL Studios Manager</b>\nWähle eine Kategorie:",
            parse_mode="HTML",
            reply_markup=MENU,
        )


# ---------------- PROFILE / REWARDS ----------------

async def profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    chat = update.effective_chat
    if not user or not chat:
        return

    xp, coins, warnings = get_stats(chat.id, user.id, user.full_name)
    level = xp // 100 + 1

    await reply(
        update,
        f"👤 <b>{user.full_name}</b>\n\n"
        f"⭐ XP: {xp}\n"
        f"📈 Level: {level}\n"
        f"🪙 Coins: {coins}\n"
        f"⚠️ Verwarnungen: {warnings}",
        parse_mode="HTML",
    )


async def daily(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    chat = update.effective_chat
    if not user or not chat:
        return

    # Einfache tägliche Belohnung; der Cooldown wird pro Prozess gespeichert.
    from datetime import date
    today = date.today().isoformat()
    key = f"daily_{chat.id}_{user.id}"
    if context.application.bot_data.get(key) == today:
        await reply(update, "⏳ Deine Tagesbelohnung hast du schon abgeholt.")
        return

    context.application.bot_data[key] = today
    add_reward(chat.id, user.id, user.full_name, xp=20, coins=100)
    await reply(update, "🎁 Du bekommst 100 Coins und 20 XP!")


async def top(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    if not chat:
        return

    with sqlite3.connect(DB_FILE) as db:
        rows = db.execute("""
            SELECT name, xp, coins FROM users
            WHERE chat_id = ?
            ORDER BY xp DESC, coins DESC
            LIMIT 10
        """, (chat.id,)).fetchall()

    if not rows:
        await reply(update, "Noch keine Spieler in der Rangliste!")
        return

    lines = ["🏆 <b>TOP 10</b>"]
    for i, (name, xp, coins) in enumerate(rows, 1):
        safe_name = (
            name.replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
        )
        lines.append(f"{i}. {safe_name} — ⭐ {xp} XP | 🪙 {coins}")

    await reply(update, "\n".join(lines), parse_mode="HTML")


# ---------------- GAMES ----------------

async def dice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if user and update.effective_chat:
        add_reward(update.effective_chat.id, user.id, user.full_name, xp=2, coins=1)
    await reply(update, "🎲 Du hast gewürfelt!")
    await context.bot.send_dice(update.effective_chat.id)


async def coin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await reply(update, random.choice(["🪙 Kopf!", "🪙 Zahl!"]))


async def rps(update: Update, context: ContextTypes.DEFAULT_TYPE):
    choices = ["✂️ Schere", "🪨 Stein", "📄 Papier"]
    bot_choice = random.choice(choices)

    if context.args:
        raw = context.args[0].lower()
        aliases = {
            "schere": "✂️ Schere",
            "stein": "🪨 Stein",
            "papier": "📄 Papier",
        }
        player = aliases.get(raw)
        if not player:
            await reply(update, "Benutze: /rps schere, /rps stein oder /rps papier")
            return

        if player == bot_choice:
            result = "Unentschieden!"
        elif (
            (player == "✂️ Schere" and bot_choice == "📄 Papier")
            or (player == "🪨 Stein" and bot_choice == "✂️ Schere")
            or (player == "📄 Papier" and bot_choice == "🪨 Stein")
        ):
            result = "🎉 Du gewinnst!"
            user = update.effective_user
            chat = update.effective_chat
            if user and chat:
                add_reward(chat.id, user.id, user.full_name, xp=10, coins=5)
        else:
            result = "🤖 Ich gewinne!"
        await reply(update, f"Du: {player}\nBot: {bot_choice}\n\n{result}")
    else:
        await reply(update, "Benutze: /rps schere, /rps stein oder /rps papier")


async def guess(update: Update, context: ContextTypes.DEFAULT_TYPE):
    key = f"guess_{update.effective_chat.id}"
    games = context.application.bot_data.setdefault("guess_games", {})
    chat_id = update.effective_chat.id

    if not context.args:
        games[chat_id] = random.randint(1, 10)
        await reply(update, "🔢 Ich denke an eine Zahl von 1 bis 10. Rate mit /guess ZAHL!")
        return

    if not context.args[0].isdigit():
        await reply(update, "Bitte gib eine Zahl von 1 bis 10 ein.")
        return

    number = int(context.args[0])
    if chat_id not in games:
        await reply(update, "Starte zuerst eine Runde mit /guess.")
        return

    if number == games[chat_id]:
        del games[chat_id]
        user = update.effective_user
        if user:
            add_reward(chat_id, user.id, user.full_name, xp=15, coins=10)
        await reply(update, "🎉 Richtig! Du bekommst 15 XP und 10 Coins.")
    elif 1 <= number <= 10:
        await reply(update, "❌ Leider falsch. Versuch es nochmal!")
    else:
        await reply(update, "Die Zahl muss zwischen 1 und 10 liegen.")


QUIZ = [
    ("Wie viele Tage hat eine Woche?", ["5", "7", "10"], 1),
    ("Welcher Planet ist als Roter Planet bekannt?", ["Mars", "Venus", "Jupiter"], 0),
    ("Wie viele Minuten hat eine Stunde?", ["30", "60", "100"], 1),
    ("Welche Farbe entsteht aus Blau und Gelb?", ["Lila", "Grün", "Orange"], 1),
]


async def quiz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    question, options, correct = random.choice(QUIZ)
    buttons = [
        [InlineKeyboardButton(option, callback_data=f"quiz_{correct}_{i}")]
        for i, option in enumerate(options)
    ]
    context.application.bot_data["quiz_question"] = question
    await reply(
        update,
        f"🧠 <b>Quizfrage</b>\n{question}",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(buttons),
    )


async def quiz_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    try:
        _, correct, chosen = query.data.split("_")
        if correct == chosen:
            user = query.from_user
            chat_id = query.message.chat_id
            add_reward(chat_id, user.id, user.full_name, xp=10, coins=5)
            text = "✅ Richtig! +10 XP und +5 Coins!"
        else:
            text = "❌ Leider falsch. Versuch es beim nächsten Mal!"
        await query.edit_message_text(text)
    except (ValueError, AttributeError):
        await query.edit_message_text("Diese Quizrunde ist nicht mehr gültig.")


async def roll(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        maximum = int(context.args[0]) if context.args else 100
        if not 1 <= maximum <= 1_000_000:
            raise ValueError
    except ValueError:
        await reply(update, "Benutze /roll oder /roll 500 (maximal 1.000.000).")
        return
    await reply(update, f"🎲 Ergebnis: {random.randint(1, maximum)}")


# ---------------- FUN ----------------

async def joke(update: Update, context: ContextTypes.DEFAULT_TYPE):
    jokes = [
        "Warum können Geister so schlecht lügen? Weil man durch sie hindurchsieht! 👻",
        "Was macht ein Keks unter einem Baum? Krümel! 🍪",
        "Treffen sich zwei Fische. Sagt der eine: Hi! Sagt der andere: Wo? 🐟",
        "Warum nehmen Programmierer immer eine Jacke mit? Wegen der vielen Bugs! 🐛",
    ]
    await reply(update, random.choice(jokes))


async def ball(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await reply(update, "Stell eine Frage dazu: /8ball Werde ich gewinnen?")
        return
    await reply(update, random.choice([
        "Ja, bestimmt! ✨",
        "Eher ja! 😎",
        "Vielleicht 🤔",
        "Frag später nochmal 🔮",
        "Heute eher nicht 😅",
    ]))


async def choose(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = " ".join(context.args)
    options = [x.strip() for x in text.split("|") if x.strip()]
    if len(options) < 2:
        await reply(update, "Beispiel: /choose Pizza | Burger | Nudeln")
        return
    await reply(update, f"🤔 Ich wähle: <b>{random.choice(options)}</b>", parse_mode="HTML")


async def say(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await reply(update, "Benutze /say Hallo zusammen!")
        return
    text = " ".join(context.args)
    await reply(update, text[:3000])


async def user_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    chat = update.effective_chat
    await reply(
        update,
        f"👤 Deine User-ID: <code>{user.id}</code>\n"
        f"💬 Chat-ID: <code>{chat.id}</code>",
        parse_mode="HTML",
    )


# ---------------- MODERATION ----------------

async def kick(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not group_only(update) or not await admin_required(update, context):
        return
    target = await get_target(update, context)
    if not target:
        await reply(update, "Antworte auf eine Nachricht oder nutze /kick USER_ID.")
        return
    if target.id == update.effective_user.id:
        await reply(update, "Du kannst dich nicht selbst kicken.")
        return
    try:
        await context.bot.ban_chat_member(update.effective_chat.id, target.id)
        await context.bot.unban_chat_member(update.effective_chat.id, target.id)
        await reply(update, f"👢 {target.full_name} wurde entfernt.")
    except TelegramError as e:
        await reply(update, f"❌ Konnte Mitglied nicht entfernen: {e}")


async def ban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not group_only(update) or not await admin_required(update, context):
        return
    target = await get_target(update, context)
    if not target:
        await reply(update, "Antworte auf eine Nachricht oder nutze /ban USER_ID.")
        return
    try:
        await context.bot.ban_chat_member(update.effective_chat.id, target.id)
        await reply(update, f"🔨 {target.full_name} wurde gesperrt.")
    except TelegramError as e:
        await reply(update, f"❌ Sperren fehlgeschlagen: {e}")


async def unban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not group_only(update) or not await admin_required(update, context):
        return
    if not context.args or not context.args[0].isdigit():
        await reply(update, "Benutze /unban USER_ID.")
        return
    try:
        await context.bot.unban_chat_member(
            update.effective_chat.id,
            int(context.args[0]),
            only_if_banned=True,
        )
        await reply(update, "✅ Sperre aufgehoben, sofern das Mitglied gesperrt war.")
    except TelegramError as e:
        await reply(update, f"❌ Fehler: {e}")


def restricted_permissions():
    return ChatPermissions(
        can_send_messages=False,
        can_send_audios=False,
        can_send_documents=False,
        can_send_photos=False,
        can_send_videos=False,
        can_send_video_notes=False,
        can_send_voice_notes=False,
        can_send_polls=False,
        can_send_other_messages=False,
        can_add_web_page_previews=False,
    )


def open_permissions():
    return ChatPermissions(
        can_send_messages=True,
        can_send_audios=True,
        can_send_documents=True,
        can_send_photos=True,
        can_send_videos=True,
        can_send_video_notes=True,
        can_send_voice_notes=True,
        can_send_polls=True,
        can_send_other_messages=True,
        can_add_web_page_previews=True,
    )


async def mute(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not group_only(update) or not await admin_required(update, context):
        return
    target = await get_target(update, context)
    if not target:
        await reply(update, "Antworte auf eine Nachricht oder nutze /mute USER_ID.")
        return
    try:
        await context.bot.restrict_chat_member(
            update.effective_chat.id,
            target.id,
            permissions=restricted_permissions(),
        )
        await reply(update, f"🔇 {target.full_name} wurde stummgeschaltet.")
    except TelegramError as e:
        await reply(update, f"❌ Fehler beim Stummschalten: {e}")


async def unmute(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not group_only(update) or not await admin_required(update, context):
        return
    target = await get_target(update, context)
    if not target:
        await reply(update, "Antworte auf eine Nachricht oder nutze /unmute USER_ID.")
        return
    try:
        await context.bot.restrict_chat_member(
            update.effective_chat.id,
            target.id,
            permissions=open_permissions(),
        )
        await reply(update, f"🔊 {target.full_name} kann wieder schreiben.")
    except TelegramError as e:
        await reply(update, f"❌ Fehler beim Entsperren: {e}")


async def warn(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not group_only(update) or not await admin_required(update, context):
        return
    target = await get_target(update, context)
    if not target:
        await reply(update, "Antworte auf eine Nachricht oder nutze /warn USER_ID.")
        return

    chat_id = update.effective_chat.id
    ensure_user(chat_id, target.id, target.full_name)
    with sqlite3.connect(DB_FILE) as db:
        db.execute("""
            UPDATE users SET warnings = warnings + 1
            WHERE chat_id = ? AND user_id = ?
        """, (chat_id, target.id))
        count = db.execute("""
            SELECT warnings FROM users WHERE chat_id = ? AND user_id = ?
        """, (chat_id, target.id)).fetchone()[0]

    await reply(update, f"⚠️ {target.full_name} wurde verwarnt. Verwarnungen: {count}/3")
    if count >= 3:
        try:
            await context.bot.ban_chat_member(chat_id, target.id)
            await reply(update, "🔨 3 Verwarnungen erreicht: Mitglied wurde gesperrt.")
        except TelegramError:
            await reply(update, "ℹ️ 3 Verwarnungen erreicht, aber Sperren fehlgeschlagen.")


async def warnings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not group_only(update):
        return
    target = await get_target(update, context)
    target_id = target.id if target else (
        update.effective_user.id if update.effective_user else None
    )
    if not target_id:
        return
    name = target.full_name if target else update.effective_user.full_name
    _, _, count = get_stats(update.effective_chat.id, target_id, name)
    await reply(update, f"⚠️ {name} hat {count} Verwarnung(en).")


async def clearwarns(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not group_only(update) or not await admin_required(update, context):
        return
    target = await get_target(update, context)
    if not target:
        await reply(update, "Antworte auf eine Nachricht oder nutze /clearwarns USER_ID.")
        return
    ensure_user(update.effective_chat.id, target.id, target.full_name)
    with sqlite3.connect(DB_FILE) as db:
        db.execute("""
            UPDATE users SET warnings = 0
            WHERE chat_id = ? AND user_id = ?
        """, (update.effective_chat.id, target.id))
    await reply(update, f"✅ Verwarnungen für {target.full_name} zurückgesetzt.")


async def purge(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not group_only(update) or not await admin_required(update, context):
        return
    message = update.effective_message
    if not message or not context.args or not context.args[0].isdigit():
        await reply(update, "Benutze /purge 10 als Antwort auf eine Nachricht.")
        return
    if not message.reply_to_message:
        await reply(update, "Antworte mit /purge 10 auf die erste zu löschende Nachricht.")
        return

    amount = min(int(context.args[0]), 100)
    start_id = message.reply_to_message.message_id
    deleted = 0
    for message_id in range(start_id, start_id + amount):
        try:
            await context.bot.delete_message(update.effective_chat.id, message_id)
            deleted += 1
        except TelegramError:
            pass
    try:
        await context.bot.delete_message(update.effective_chat.id, message.message_id)
    except TelegramError:
        pass
    await reply(update, f"🧹 {deleted} Nachricht(en) gelöscht.")


async def pin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not group_only(update) or not await admin_required(update, context):
        return
    message = update.effective_message
    if not message or not message.reply_to_message:
        await reply(update, "Antworte mit /pin auf die Nachricht, die angeheftet werden soll.")
        return
    try:
        await context.bot.pin_chat_message(
            update.effective_chat.id,
            message.reply_to_message.message_id,
        )
        await reply(update, "📌 Nachricht angeheftet.")
    except TelegramError as e:
        await reply(update, f"❌ Fehler: {e}")


async def unpin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not group_only(update) or not await admin_required(update, context):
        return
    try:
        await context.bot.unpin_chat_message(update.effective_chat.id)
        await reply(update, "📌 Anheftung gelöst.")
    except TelegramError as e:
        await reply(update, f"❌ Fehler: {e}")


async def lock(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not group_only(update) or not await admin_required(update, context):
        return
    try:
        await context.bot.set_chat_permissions(
            update.effective_chat.id,
            permissions=restricted_permissions(),
        )
        await reply(update, "🔒 Gruppenchat gesperrt.")
    except TelegramError as e:
        await reply(update, f"❌ Fehler: {e}")


async def unlock(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not group_only(update) or not await admin_required(update, context):
        return
    try:
        await context.bot.set_chat_permissions(
            update.effective_chat.id,
            permissions=open_permissions(),
        )
        await reply(update, "🔓 Gruppenchat freigegeben.")
    except TelegramError as e:
        await reply(update, f"❌ Fehler: {e}")


async def admins(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    if not chat:
        return
    try:
        members = await context.bot.get_chat_administrators(chat.id)
        lines = ["🛡️ <b>Gruppenadmins</b>"]
        for member in members:
            lines.append(f"• {mention(member.user)}")
        await reply(update, "\n".join(lines), parse_mode="HTML")
    except TelegramError as e:
        await reply(update, f"❌ Fehler: {e}")


# ---------------- HELP / ERRORS ----------------

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await menu(update, context)


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    error = context.error
    log.error("Unhandled bot error: %s", error)


# ---------------- STARTUP ----------------

def main():
    if not TOKEN:
        raise RuntimeError(
            "BOT_TOKEN fehlt. Render > Service > Environment: "
            "Variable BOT_TOKEN mit deinem BotFather-Token anlegen."
        )

    init_db()
    start_health_server()

    app = Application.builder().token(TOKEN).build()

    commands = {
        "start": start,
        "menu": menu,
        "help": help_command,
        "profile": profile,
        "daily": daily,
        "top": top,
        "dice": dice,
        "coin": coin,
        "rps": rps,
        "guess": guess,
        "quiz": quiz,
        "roll": roll,
        "joke": joke,
        "8ball": ball,
        "choose": choose,
        "say": say,
        "id": user_id,
        "kick": kick,
        "ban": ban,
        "unban": unban,
        "mute": mute,
        "unmute": unmute,
        "warn": warn,
        "warnings": warnings,
        "clearwarns": clearwarns,
        "purge": purge,
        "pin": pin,
        "unpin": unpin,
        "lock": lock,
        "unlock": unlock,
        "admins": admins,
    }

    for name, handler in commands.items():
        app.add_handler(CommandHandler(name, handler))

    app.add_handler(CallbackQueryHandler(quiz_callback, pattern=r"^quiz_"))
    app.add_handler(CallbackQueryHandler(menu_callback, pattern=r"^menu_"))
    app.add_error_handler(error_handler)

    log.info("Starting LOL Studios Manager...")
    try:
        app.run_polling(drop_pending_updates=True)
    except InvalidToken:
        log.critical(
            "Telegram lehnt BOT_TOKEN ab. Prüfe den Token in Render "
            "Environment und ob er von BotFather stammt."
        )
        raise
    except (NetworkError, TimedOut):
        log.exception(
            "Telegram ist nicht erreichbar. Prüfe Netzwerk und versuche es erneut."
        )
        raise


if __name__ == "__main__":
    main()
