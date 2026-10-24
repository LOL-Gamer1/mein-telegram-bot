import os
import time
import random
import sqlite3
import threading
import asyncio
from http.server import BaseHTTPRequestHandler, HTTPServer

from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup,
    ChatPermissions
)
from telegram.constants import ChatType
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ContextTypes
)

TOKEN = os.getenv("8511282233:AAF05ySHJNJyHxi5ctZbvHhUhSB4fMrrlzc", "").strip()
DB_PATH = os.getenv("DB_PATH", "bot_data.sqlite3")


# =============== DATENBANK ===============

def connect_db():
    return sqlite3.connect(DB_PATH, timeout=10)


def init_db():
    with connect_db() as db:
        db.execute("""
            CREATE TABLE IF NOT EXISTS stats (
                chat_id INTEGER,
                user_id INTEGER,
                xp INTEGER DEFAULT 0,
                coins INTEGER DEFAULT 0,
                daily INTEGER DEFAULT 0,
                PRIMARY KEY(chat_id, user_id)
            )
        """)
        db.execute("""
            CREATE TABLE IF NOT EXISTS warnings (
                chat_id INTEGER,
                user_id INTEGER,
                amount INTEGER DEFAULT 0,
                PRIMARY KEY(chat_id, user_id)
            )
        """)


def get_stats(chat_id, user_id):
    with connect_db() as db:
        row = db.execute(
            "SELECT xp,coins,daily FROM stats WHERE chat_id=? AND user_id=?",
            (chat_id, user_id)
        ).fetchone()

    return row or (0, 0, 0)


def change_stats(chat_id, user_id, xp=0, coins=0):
    with connect_db() as db:
        db.execute("""
            INSERT INTO stats(chat_id,user_id,xp,coins,daily)
            VALUES(?,?,?, ?,0)
            ON CONFLICT(chat_id,user_id) DO UPDATE SET
            xp=xp+excluded.xp, coins=coins+excluded.coins
        """, (chat_id, user_id, xp, coins))


def get_warns(chat_id, user_id):
    with connect_db() as db:
        row = db.execute(
            "SELECT amount FROM warnings WHERE chat_id=? AND user_id=?",
            (chat_id, user_id)
        ).fetchone()
    return row[0] if row else 0


def set_warns(chat_id, user_id, amount):
    with connect_db() as db:
        db.execute("""
            INSERT INTO warnings(chat_id,user_id,amount)
            VALUES(?,?,?)
            ON CONFLICT(chat_id,user_id)
            DO UPDATE SET amount=excluded.amount
        """, (chat_id, user_id, max(0, amount)))


# =============== HILFSFUNKTIONEN ===============

async def is_admin(update, context):
    chat = update.effective_chat
    user = update.effective_user

    if not chat or not user or chat.type == ChatType.PRIVATE:
        return False

    try:
        member = await context.bot.get_chat_member(chat.id, user.id)
        return member.status in ("administrator", "creator")
    except Exception:
        return False


async def admin_required(update, context):
    if await is_admin(update, context):
        return True

    await update.effective_message.reply_text(
        "❌ Du brauchst Admin-Rechte für diesen Befehl."
    )
    return False


def target_user(update):
    msg = update.effective_message
    if msg and msg.reply_to_message:
        return msg.reply_to_message.from_user
    return None


def menu_keyboard():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🎮 Spiele", callback_data="games"),
            InlineKeyboardButton("🛡️ Moderation", callback_data="moderation")
        ],
        [
            InlineKeyboardButton("🏆 Profil", callback_data="profile"),
            InlineKeyboardButton("😂 Fun", callback_data="fun")
        ],
        [
            InlineKeyboardButton("⚙️ Admin", callback_data="admin"),
            InlineKeyboardButton("📜 Hilfe", callback_data="help")
        ]
    ])


def back_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("⬅️ Hauptmenü", callback_data="home")]
    ])


# =============== MENÜ ===============

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await menu(update, context)


async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.effective_message.reply_text(
        "🤖 LOL STUDIOS MANAGER\n\n"
        "Willkommen! Wähle eine Kategorie.\n\n"
        "🎮 Spiele\n🛡️ Gruppenmoderation\n"
        "🏆 Level und Coins\n😂 Fun-Befehle\n⚙️ Admin-Werkzeuge",
        reply_markup=menu_keyboard()
    )


async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    chat = update.effective_chat
    user = update.effective_user
    data = q.data

    if data == "home":
        await q.edit_message_text(
            "🤖 LOL STUDIOS MANAGER\nWähle eine Kategorie:",
            reply_markup=menu_keyboard()
        )

    elif data == "games":
        await q.edit_message_text(
            "🎮 **SPIELE**\n\n"
            "/dice – Würfeln\n"
            "/coin – Münzwurf\n"
            "/rps – Stein-Schere-Papier\n"
            "/guess – Zahl erraten\n"
            "/quiz – Quiz\n"
            "/roll – Zufallszahl\n"
            "/daily – tägliche Belohnung",
            reply_markup=back_keyboard()
        )

    elif data == "moderation":
        await q.edit_message_text(
            "🛡️ **GRUPPENMODERATION**\n\n"
            "/kick – Nutzer kicken\n"
            "/ban – Nutzer bannen\n"
            "/unban USER_ID – Bann aufheben\n"
            "/mute – 10 Minuten stummschalten\n"
            "/unmute – Stummschaltung aufheben\n"
            "/warn – Verwarnung\n"
            "/warnings – Verwarnungen anzeigen\n"
            "/clearwarns – Verwarnungen löschen\n"
            "/purge ZAHL – Nachrichten löschen\n"
            "/pin /unpin – Nachrichten anheften/lösen\n"
            "/lock /unlock – Gruppe sperren/öffnen\n"
            "/admins – Adminliste",
            reply_markup=back_keyboard()
        )

    elif data == "profile":
        xp, coins, _ = get_stats(chat.id, user.id)
        await q.edit_message_text(
            f"🏆 PROFIL\n\n👤 {user.first_name}\n"
            f"⭐ Level: {xp // 100 + 1}\n"
            f"✨ XP: {xp}\n🪙 Coins: {coins}\n\n"
            "/profile /top /daily",
            reply_markup=back_keyboard()
        )

    elif data == "fun":
        await q.edit_message_text(
            "😂 FUN-BEFEHLE\n\n"
            "/joke – Witz\n"
            "/8ball FRAGE – magische Kugel\n"
            "/choose A | B – Zufallsauswahl\n"
            "/hug – virtuelle Umarmung\n"
            "/roll – Zufallszahl",
            reply_markup=back_keyboard()
        )

    elif data == "help":
        await q.edit_message_text(
            "📜 HILFE\n\n"
            "/menu – Hauptmenü\n/start – Start\n"
            "/info – Chat-Informationen\n"
            "/id – IDs anzeigen\n"
            "/say TEXT – Text senden\n\n"
            "Moderationsbefehle benötigen Admin-Rechte. "
            "Der Bot braucht ebenfalls die entsprechenden Telegram-Rechte.",
            reply_markup=back_keyboard()
        )

    elif data == "admin":
        if chat.type != ChatType.PRIVATE and not await is_admin(update, context):
            await q.edit_message_text("❌ Nur Gruppenadmins dürfen das Admin-Menü öffnen.")
            return

        await q.edit_message_text(
            "⚙️ ADMIN-PANEL\n\n"
            "/lock – Gruppe sperren\n"
            "/unlock – Gruppe öffnen\n"
            "/purge ZAHL – Nachrichten löschen\n"
            "/admins – Adminliste\n"
            "/pin /unpin – Anheften",
            reply_markup=back_keyboard()
        )

    elif data.startswith("rps_"):
        choice = data.split("_", 1)[1]
        bot_choice = random.choice(["stein", "schere", "papier"])

        if choice == bot_choice:
            result = "Unentschieden!"
        elif (
            (choice == "stein" and bot_choice == "schere")
            or (choice == "schere" and bot_choice == "papier")
            or (choice == "papier" and bot_choice == "stein")
        ):
            result = "🎉 Du gewinnst! +5 Coins"
            change_stats(chat.id, user.id, coins=5)
        else:
            result = "🤖 Der Bot gewinnt!"

        await q.edit_message_text(
            f"Du: {choice}\nBot: {bot_choice}\n\n{result}"
        )

    elif data.startswith("quiz_"):
        answer = data.split("_", 1)[1]
        if answer == "paris":
            change_stats(chat.id, user.id, coins=5)
            result = "✅ Richtig! +5 Coins"
        else:
            result = "❌ Falsch! Die Antwort ist Paris."

        await q.edit_message_text(result)


# =============== MODERATION ===============

async def kick(update, context):
    if not await admin_required(update, context):
        return

    target = target_user(update)
    if not target:
        await update.effective_message.reply_text(
            "Antworte mit /kick auf eine Nachricht."
        )
        return

    try:
        await context.bot.ban_chat_member(
            update.effective_chat.id, target.id
        )
        await context.bot.unban_chat_member(
            update.effective_chat.id, target.id,
            only_if_banned=True
        )
        await update.effective_message.reply_text(
            f"👢 {target.first_name} wurde gekickt."
        )
    except Exception:
        await update.effective_message.reply_text(
            "❌ Kicken fehlgeschlagen. Prüfe meine Admin-Rechte."
        )


async def ban(update, context):
    if not await admin_required(update, context):
        return

    target = target_user(update)
    user_id = target.id if target else None

    if not user_id and context.args and context.args[0].isdigit():
        user_id = int(context.args[0])

    if not user_id:
        await update.effective_message.reply_text(
            "Antworte mit /ban auf eine Nachricht oder nutze /ban USER_ID."
        )
        return

    try:
        await context.bot.ban_chat_member(update.effective_chat.id, user_id)
        await update.effective_message.reply_text(f"⛔ Nutzer {user_id} gebannt.")
    except Exception:
        await update.effective_message.reply_text("❌ Bann fehlgeschlagen.")


async def unban(update, context):
    if not await admin_required(update, context):
        return

    if not context.args or not context.args[0].lstrip("-").isdigit():
        await update.effective_message.reply_text("Nutzung: /unban USER_ID")
        return

    try:
        await context.bot.unban_chat_member(
            update.effective_chat.id, int(context.args[0]),
            only_if_banned=True
        )
        await update.effective_message.reply_text("✅ Bann aufgehoben.")
    except Exception:
        await update.effective_message.reply_text("❌ Entbannen fehlgeschlagen.")


async def mute(update, context):
    if not await admin_required(update, context):
        return

    target = target_user(update)
    user_id = target.id if target else None
    minutes = 10

    if context.args:
        if user_id is None and context.args[0].isdigit():
            user_id = int(context.args[0])
            if len(context.args) > 1 and context.args[1].isdigit():
                minutes = int(context.args[1])
        elif context.args[0].isdigit():
            minutes = int(context.args[0])

    minutes = max(1, min(minutes, 10080))

    if not user_id:
        await update.effective_message.reply_text(
            "Antworte mit /mute oder nutze /mute USER_ID MINUTEN."
        )
        return

    try:
        await context.bot.restrict_chat_member(
            update.effective_chat.id, user_id,
            permissions=ChatPermissions(can_send_messages=False),
            until_date=int(time.time() + minutes * 60)
        )
        await update.effective_message.reply_text(
            f"🤫 Nutzer {user_id} für {minutes} Minuten stummgeschaltet."
        )
    except Exception:
        await update.effective_message.reply_text("❌ Stummschalten fehlgeschlagen.")


async def unmute(update, context):
    if not await admin_required(update, context):
        return

    target = target_user(update)
    user_id = target.id if target else None

    if not user_id and context.args and context.args[0].isdigit():
        user_id = int(context.args[0])

    if not user_id:
        await update.effective_message.reply_text(
            "Antworte mit /unmute oder nutze /unmute USER_ID."
        )
        return

    try:
        await context.bot.restrict_chat_member(
            update.effective_chat.id, user_id,
            permissions=ChatPermissions(
                can_send_messages=True,
                can_send_audios=True,
                can_send_documents=True,
                can_send_photos=True,
                can_send_videos=True,
                can_send_video_notes=True,
                can_send_voice_notes=True,
                can_send_polls=True,
                can_send_other_messages=True,
                can_add_web_page_previews=True
            )
        )
        await update.effective_message.reply_text("🔊 Stummschaltung aufgehoben.")
    except Exception:
        await update.effective_message.reply_text("❌ Entstummen fehlgeschlagen.")


async def warn(update, context):
    if not await admin_required(update, context):
        return

    target = target_user(update)
    if not target:
        await update.effective_message.reply_text(
            "Antworte mit /warn auf eine Nachricht."
        )
        return

    chat_id = update.effective_chat.id
    count = get_warns(chat_id, target.id) + 1
    set_warns(chat_id, target.id, count)

    if count >= 3:
        try:
            await context.bot.ban_chat_member(chat_id, target.id)
            await context.bot.unban_chat_member(
                chat_id, target.id, only_if_banned=True
            )
            set_warns(chat_id, target.id, 0)
            await update.effective_message.reply_text(
                f"🚨 {target.first_name} hat 3 Verwarnungen erreicht und wurde gekickt."
            )
        except Exception:
            await update.effective_message.reply_text(
                f"⚠️ {target.first_name}: {count}/3 Verwarnungen. Kicken fehlgeschlagen."
            )
    else:
        await update.effective_message.reply_text(
            f"⚠️ {target.first_name}: Verwarnung {count}/3."
        )


async def warnings(update, context):
    target = target_user(update) or update.effective_user
    count = get_warns(update.effective_chat.id, target.id)
    await update.effective_message.reply_text(
        f"⚠️ {target.first_name}: {count}/3 Verwarnungen."
    )


async def clearwarns(update, context):
    if not await admin_required(update, context):
        return

    target = target_user(update)
    if not target:
        await update.effective_message.reply_text(
            "Antworte mit /clearwarns auf eine Nachricht."
        )
        return

    set_warns(update.effective_chat.id, target.id, 0)
    await update.effective_message.reply_text("✅ Verwarnungen gelöscht.")


async def purge(update, context):
    if not await admin_required(update, context):
        return

    if not context.args or not context.args[0].isdigit():
        await update.effective_message.reply_text("Nutzung: /purge ANZAHL (1–100)")
        return

    count = max(1, min(100, int(context.args[0])))
    chat_id = update.effective_chat.id
    current = update.effective_message.message_id
    start_id = (
        update.effective_message.reply_to_message.message_id
        if update.effective_message.reply_to_message
        else current - 1
    )

    deleted = 0
    for message_id in range(start_id, max(0, start_id - count), -1):
        try:
            await context.bot.delete_message(chat_id, message_id)
            deleted += 1
        except Exception:
            pass

    try:
        await context.bot.delete_message(chat_id, current)
    except Exception:
        pass

    notice = await context.bot.send_message(
        chat_id, f"🧹 {deleted} Nachrichten gelöscht."
    )
    await asyncio.sleep(4)
    try:
        await context.bot.delete_message(chat_id, notice.message_id)
    except Exception:
        pass


async def pin(update, context):
    if not await admin_required(update, context):
        return

    msg = update.effective_message.reply_to_message
    if not msg:
        await update.effective_message.reply_text(
            "Antworte mit /pin auf eine Nachricht."
        )
        return

    try:
        await context.bot.pin_chat_message(
            update.effective_chat.id, msg.message_id
        )
        await update.effective_message.reply_text("📌 Nachricht angeheftet.")
    except Exception:
        await update.effective_message.reply_text("❌ Anheften fehlgeschlagen.")


async def unpin(update, context):
    if not await admin_required(update, context):
        return

    try:
        msg = update.effective_message.reply_to_message
        if msg:
            await context.bot.unpin_chat_message(
                update.effective_chat.id, msg.message_id
            )
        else:
            await context.bot.unpin_all_chat_messages(update.effective_chat.id)
        await update.effective_message.reply_text("📌 Anheftung aufgehoben.")
    except Exception:
        await update.effective_message.reply_text("❌ Lösen fehlgeschlagen.")


async def lock(update, context):
    if not await admin_required(update, context):
        return

    try:
        await context.bot.set_chat_permissions(
            update.effective_chat.id,
            ChatPermissions(can_send_messages=False)
        )
        await update.effective_message.reply_text("🔒 Gruppe gesperrt.")
    except Exception:
        await update.effective_message.reply_text("❌ Sperren fehlgeschlagen.")


async def unlock(update, context):
    if not await admin_required(update, context):
        return

    try:
        await context.bot.set_chat_permissions(
            update.effective_chat.id,
            ChatPermissions(
                can_send_messages=True,
                can_send_audios=True,
                can_send_documents=True,
                can_send_photos=True,
                can_send_videos=True,
                can_send_video_notes=True,
                can_send_voice_notes=True,
                can_send_polls=True,
                can_send_other_messages=True,
                can_add_web_page_previews=True
            )
        )
        await update.effective_message.reply_text("🔓 Gruppe geöffnet.")
    except Exception:
        await update.effective_message.reply_text("❌ Öffnen fehlgeschlagen.")


async def admins(update, context):
    if update.effective_chat.type == ChatType.PRIVATE:
        await update.effective_message.reply_text("Nur in Gruppen verfügbar.")
        return

    try:
        members = await context.bot.get_chat_administrators(
            update.effective_chat.id
        )
        lines = ["🛡️ GRUPPENADMINS"]
        for member in members:
            lines.append("• " + member.user.full_name)
        await update.effective_message.reply_text("\n".join(lines))
    except Exception:
        await update.effective_message.reply_text("❌ Adminliste nicht verfügbar.")


# =============== SPIELE ===============

async def dice(update, context):
    await context.bot.send_dice(update.effective_chat.id, emoji="🎲")


async def coin(update, context):
    await update.effective_message.reply_text(
        random.choice(["🪙 Kopf!", "🪙 Zahl!"])
    )


async def rps(update, context):
    kb = InlineKeyboardMarkup([[
        InlineKeyboardButton("✊ Stein", callback_data="rps_stein"),
        InlineKeyboardButton("✂️ Schere", callback_data="rps_schere"),
        InlineKeyboardButton("🖐️ Papier", callback_data="rps_papier")
    ]])
    await update.effective_message.reply_text(
        "✊ Stein, Schere oder Papier?", reply_markup=kb
    )


async def guess(update, context):
    context.user_data["guess"] = random.randint(1, 20)
    await update.effective_message.reply_text(
        "🔢 Ich denke an eine Zahl zwischen 1 und 20. Rate sie!"
    )


async def quiz(update, context):
    kb = InlineKeyboardMarkup([[
        InlineKeyboardButton("London", callback_data="quiz_london"),
        InlineKeyboardButton("Paris", callback_data="quiz_paris"),
        InlineKeyboardButton("Rom", callback_data="quiz_rom")
    ]])
    await update.effective_message.reply_text(
        "🧠 Was ist die Hauptstadt von Frankreich?", reply_markup=kb
    )


async def daily(update, context):
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    now = int(time.time())

    with connect_db() as db:
        row = db.execute(
            "SELECT daily FROM stats WHERE chat_id=? AND user_id=?",
            (chat_id, user_id)
        ).fetchone()

        last = row[0] if row else 0

        if now - last < 86400:
            hours = (86400 - (now - last)) // 3600
            await update.effective_message.reply_text(
                f"⏳ Deine Belohnung ist schon abgeholt. Noch etwa {hours} Stunden."
            )
            return

        db.execute("""
            INSERT INTO stats(chat_id,user_id,xp,coins,daily)
            VALUES(?,?,0,50,?)
            ON CONFLICT(chat_id,user_id) DO UPDATE SET
            coins=coins+50,daily=excluded.daily
        """, (chat_id, user_id, now))

    await update.effective_message.reply_text("🎁 +50 Coins! Komm morgen wieder.")


async def profile(update, context):
    chat_id = update.effective_chat.id
    user = update.effective_user
    xp, coins, _ = get_stats(chat_id, user.id)

    await update.effective_message.reply_text(
        f"🏆 PROFIL: {user.first_name}\n\n"
        f"⭐ Level: {xp // 100 + 1}\n"
        f"✨ XP: {xp}\n🪙 Coins: {coins}"
    )


async def top(update, context):
    with connect_db() as db:
        rows = db.execute(
            "SELECT user_id,xp FROM stats WHERE chat_id=? "
            "ORDER BY xp DESC LIMIT 10",
            (update.effective_chat.id,)
        ).fetchall()

    if not rows:
        await update.effective_message.reply_text("Noch keine Rangliste!")
        return

    lines = ["🏆 TOP 10"]
    for i, row in enumerate(rows, 1):
        lines.append(f"{i}. User {row[0]} — Level {row[1] // 100 + 1} ({row[1]} XP)")

    await update.effective_message.reply_text("\n".join(lines))


# =============== FUN ===============

async def joke(update, context):
    jokes = [
        "Warum können Geister so schlecht lügen? Man sieht durch sie hindurch! 👻",
        "Was macht ein Keks unter einem Baum? Krümel! 🍪",
        "Was ist orange und wandert? Eine Wanderine! 🍊",
        "Warum ging der Computer zum Arzt? Er hatte einen Virus! 💻"
    ]
    await update.effective_message.reply_text(random.choice(jokes))


async def eightball(update, context):
    if not context.args:
        await update.effective_message.reply_text(
            "Nutzung: /8ball Werde ich heute Glück haben?"
        )
        return

    await update.effective_message.reply_text(
        "🔮 " + random.choice([
            "Ja, auf jeden Fall!", "Sieht gut aus!", "Vielleicht.",
            "Eher nicht.", "Frag später nochmal!"
        ])
    )


async def choose(update, context):
    options = " ".join(context.args).split("|")
    options = [x.strip() for x in options if x.strip()]

    if len(options) < 2:
        await update.effective_message.reply_text(
            "Nutzung: /choose Pizza | Burger"
        )
        return

    await update.effective_message.reply_text(
        "🎯 Meine Wahl: " + random.choice(options)
    )


async def roll(update, context):
    await update.effective_message.reply_text(
        f"🎲 Deine Zufallszahl: {random.randint(1, 100)}"
    )


async def hug(update, context):
    await update.effective_message.reply_text(
        "🤗 Eine freundliche virtuelle Umarmung!"
    )


async def info(update, context):
    chat = update.effective_chat
    user = update.effective_user
    text = (
        f"👤 Name: {user.full_name}\n"
        f"🆔 User-ID: {user.id}\n"
        f"💬 Chat-Typ: {chat.type}\n"
        f"🆔 Chat-ID: {chat.id}"
    )
    if chat.type != ChatType.PRIVATE:
        text += f"\n👥 Gruppe: {chat.title}"

    await update.effective_message.reply_text(text)


async def id_command(update, context):
    target = target_user(update) or update.effective_user
    await update.effective_message.reply_text(
        f"🆔 User-ID: {target.id}\n"
        f"Chat-ID: {update.effective_chat.id}"
    )


async def say(update, context):
    if update.effective_chat.type != ChatType.PRIVATE:
        if not await admin_required(update, context):
            return

    if not context.args:
        await update.effective_message.reply_text("Nutzung: /say Dein Text")
        return

    await context.bot.send_message(
        update.effective_chat.id, " ".join(context.args)
    )


# =============== NACHRICHTEN / XP ===============

async def text_handler(update, context):
    msg = update.effective_message
    user = update.effective_user
    chat = update.effective_chat

    if not msg or not user or user.is_bot:
        return

    if msg.text and "guess" in context.user_data and msg.text.isdigit():
        number = int(msg.text)
        answer = context.user_data["guess"]

        if number == answer:
            del context.user_data["guess"]
            change_stats(chat.id, user.id, coins=10)
            await msg.reply_text("🎉 Richtig! +10 Coins!")
        elif 1 <= number <= 20:
            await msg.reply_text("⬆️ Höher!" if number < answer else "⬇️ Tiefer!")
        else:
            await msg.reply_text("Bitte eine Zahl von 1 bis 20 eingeben.")
        return

    if chat.type == ChatType.PRIVATE:
        await msg.reply_text("🤖 Tippe /menu, um das Hauptmenü zu öffnen.")
        return

    if msg.text and not msg.text.startswith("/"):
        if random.random() < 0.35:
            change_stats(chat.id, user.id, xp=random.randint(1, 3))


# =============== RENDER HEALTH CHECK ===============

def run_health_server():
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"LOL Studios Bot is alive")

        def log_message(self, *args):
            pass

    port = int(os.getenv("PORT", "10000"))
    HTTPServer(("0.0.0.0", port), Handler).serve_forever()


# =============== START ===============

def main():
    if not TOKEN:
        raise RuntimeError(
            "BOT_TOKEN fehlt! Trage den Token in Render unter Environment ein."
        )

    init_db()
    threading.Thread(target=run_health_server, daemon=True).start()

    app = Application.builder().token(TOKEN).build()

    handlers = {
        "start": start,
        "menu": menu,
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
        "dice": dice,
        "coin": coin,
        "rps": rps,
        "guess": guess,
        "quiz": quiz,
        "daily": daily,
        "profile": profile,
        "top": top,
        "joke": joke,
        "8ball": eightball,
        "choose": choose,
        "roll": roll,
        "hug": hug,
        "info": info,
        "id": id_command,
        "say": say
    }

    for name, callback in handlers.items():
        app.add_handler(CommandHandler(name, callback))

    app.add_handler(CallbackQueryHandler(buttons))
    app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler)
    )

    print("LOL Studios Manager Bot gestartet!")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
