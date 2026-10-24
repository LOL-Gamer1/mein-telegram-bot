
# features.py — LOL Studios Manager
import random
from datetime import datetime, timezone

import database
from config import OWNER_ID
from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Update,
)
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
)


def main_keyboard():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("👤 Profil", callback_data="menu:profile"),
            InlineKeyboardButton("🎮 Spiele", callback_data="menu:games"),
        ],
        [
            InlineKeyboardButton("🎁 Daily", callback_data="menu:daily"),
            InlineKeyboardButton("🏆 Rangliste", callback_data="menu:leaderboard"),
        ],
        [
            InlineKeyboardButton("📜 Regeln", callback_data="menu:rules"),
            InlineKeyboardButton("ℹ️ Über uns", callback_data="menu:about"),
        ],
        [
            InlineKeyboardButton("🔄 Aktualisieren", callback_data="menu:home"),
        ],
    ])


async def menu_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.effective_message.reply_text(
        "🚀 LOL STUDIOS MANAGER\n\nWähle eine Funktion:",
        reply_markup=main_keyboard(),
    )


async def menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    data = query.data

    if data == "menu:home":
        await query.edit_message_text(
            "🚀 LOL STUDIOS MANAGER\n\nWähle eine Funktion:",
            reply_markup=main_keyboard(),
        )

    elif data == "menu:profile":
        account = database.get_account(user_id)
        if not account:
            await query.edit_message_text("Bitte registriere dich zuerst mit /register.")
            return

        await query.edit_message_text(
            f"👤 DEIN PROFIL\n\n"
            f"Name: {account['name']}\n"
            f"Bio: {account['bio'] or 'Noch keine Bio'}\n"
            f"Altersgruppe: {account['agegroup'] or 'Nicht angegeben'}\n"
            f"ID: {user_id}\n\n"
            "Bearbeiten: /setname NeuerName oder /setbio Deine Bio",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("⬅️ Zurück", callback_data="menu:home")
            ]]),
        )

    elif data == "menu:games":
        await query.edit_message_text(
            "🎮 MINI-SPIELE\n\n"
            "🎲 /roll – Zufallszahl würfeln\n"
            "🪙 /coinflip – Münzwurf\n"
            "🔢 /guess – Zahl erraten (Ziehung starten)\n\n"
            "Viel Spaß!",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("⬅️ Zurück", callback_data="menu:home")
            ]]),
        )

    elif data == "menu:daily":
        await query.edit_message_text(
            "🎁 TÄGLICHE BELOHNUNG\n\nNutze /daily, um deine Belohnung abzuholen.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("⬅️ Zurück", callback_data="menu:home")
            ]]),
        )

    elif data == "menu:leaderboard":
        await query.edit_message_text(
            leaderboard_text(),
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("⬅️ Zurück", callback_data="menu:home")
            ]]),
        )

    elif data == "menu:rules":
        await query.edit_message_text(
            "📜 REGELN\n\n"
            "1. Sei respektvoll.\n"
            "2. Kein Spam oder Missbrauch.\n"
            "3. Melde Probleme mit /report.\n"
            "4. Versuche nicht, andere Accounts zu umgehen.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("⬅️ Zurück", callback_data="menu:home")
            ]]),
        )

    elif data == "menu:about":
        await query.edit_message_text(
            "ℹ️ LOL STUDIOS MANAGER\n\n"
            "Ein Community-Bot von LOL Studios mit Profilen, "
            "Minispielen und Belohnungen.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("⬅️ Zurück", callback_data="menu:home")
            ]]),
        )


async def ping_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.effective_message.reply_text("🏓 Pong! Der Bot antwortet.")


async def about_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.effective_message.reply_text(
        "ℹ️ LOL Studios Manager\nCommunity-Bot von LOL Studios."
    )


async def rules_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.effective_message.reply_text(
        "📜 Regeln:\n1. Respektvoll bleiben.\n"
        "2. Nicht spammen.\n3. Probleme mit /report melden."
    )


async def id_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.effective_message.reply_text(
        f"🆔 Deine Telegram-ID: {update.effective_user.id}"
    )


async def roll_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.effective_message.reply_text(
        f"🎲 Du hast eine {random.randint(1, 6)} gewürfelt!"
    )


async def coinflip_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.effective_message.reply_text(
        f"🪙 Ergebnis: {random.choice(['Kopf', 'Zahl'])}!"
    )


async def guess_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    number = random.randint(1, 10)
    context.user_data["guess_number"] = number
    await update.effective_message.reply_text(
        "🔢 Ich habe eine Zahl zwischen 1 und 10 gewählt. "
        "Rate mit /guess Zahl, zum Beispiel /guess 5."
    )


async def guess_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    target = context.user_data.get("guess_number")
    if target is None:
        await guess_command(update, context)
        return

    if not context.args:
        await update.effective_message.reply_text("Nutze /guess Zahl, zum Beispiel /guess 5.")
        return

    try:
        number = int(context.args[0])
    except ValueError:
        await update.effective_message.reply_text("Bitte gib eine Zahl von 1 bis 10 ein.")
        return

    if number == target:
        context.user_data.pop("guess_number", None)
        await update.effective_message.reply_text("🎉 Richtig geraten!")
    else:
        await update.effective_message.reply_text(
            "❌ Leider falsch! Versuch es nochmal mit /guess Zahl."
        )


def leaderboard_text():
    with database.connect() as db:
        rows = db.execute("""
            SELECT a.name, p.balance
            FROM accounts a
            LEFT JOIN points p ON p.user_id = a.user_id
            WHERE a.suspended = 0
            ORDER BY COALESCE(p.balance, 0) DESC, a.name COLLATE NOCASE
            LIMIT 10
        """).fetchall()

    if not rows:
        return "🏆 Noch gibt es keine Einträge."

    lines = ["🏆 RANGLISTE\n"]
    for index, row in enumerate(rows, 1):
        lines.append(f"{index}. {row['name']} — {row['balance'] or 0} Punkte")
    return "\n".join(lines)


async def leaderboard_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.effective_message.reply_text(leaderboard_text())


async def daily_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    today = datetime.now(timezone.utc).date().isoformat()

    with database.connect() as db:
        row = db.execute(
            "SELECT last_claim FROM daily_claims WHERE user_id = ?",
            (user_id,),
        ).fetchone()

        if row and row["last_claim"] == today:
            await update.effective_message.reply_text(
                "⏳ Du hast deine tägliche Belohnung heute bereits abgeholt."
            )
            return

        db.execute("""
            INSERT INTO points(user_id, balance) VALUES (?, 100)
            ON CONFLICT(user_id) DO UPDATE SET balance = balance + 100
        """, (user_id,))
        db.execute("""
            INSERT INTO daily_claims(user_id, last_claim) VALUES (?, ?)
            ON CONFLICT(user_id) DO UPDATE SET last_claim = excluded.last_claim
        """, (user_id, today))

    await update.effective_message.reply_text(
        "🎁 Daily abgeholt! Du bekommst 100 Punkte."
    )


async def setname_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.effective_message.reply_text(
            "Verwendung: /setname Neuer Name"
        )
        return

    name = " ".join(context.args).strip()
    if len(name) > 50:
        await update.effective_message.reply_text("Der Name darf höchstens 50 Zeichen haben.")
        return

    with database.connect() as db:
        result = db.execute(
            "UPDATE accounts SET name = ? WHERE user_id = ?",
            (name, update.effective_user.id),
        )

    if result.rowcount:
        await update.effective_message.reply_text(f"✅ Dein Name ist jetzt: {name}")
    else:
        await update.effective_message.reply_text("Bitte registriere dich zuerst mit /register.")


async def setbio_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    bio = " ".join(context.args).strip()
    if not bio:
        await update.effective_message.reply_text("Verwendung: /setbio Das ist meine Bio")
        return
    if len(bio) > 200:
        await update.effective_message.reply_text("Die Bio darf höchstens 200 Zeichen haben.")
        return

    with database.connect() as db:
        result = db.execute(
            "UPDATE accounts SET bio = ? WHERE user_id = ?",
            (bio, update.effective_user.id),
        )

    if result.rowcount:
        await update.effective_message.reply_text("✅ Deine Bio wurde aktualisiert.")
    else:
        await update.effective_message.reply_text("Bitte registriere dich zuerst mit /register.")


async def report_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = " ".join(context.args).strip()
    if not message:
        await update.effective_message.reply_text(
            "Verwendung: /report Beschreibe das Problem"
        )
        return
    if len(message) > 1000:
        await update.effective_message.reply_text("Die Meldung darf höchstens 1000 Zeichen haben.")
        return

    with database.connect() as db:
        cursor = db.execute(
            "INSERT INTO reports(user_id, message) VALUES (?, ?)",
            (update.effective_user.id, message),
        )
        report_id = cursor.lastrowid

    await update.effective_message.reply_text(
        f"✅ Meldung #{report_id} wurde gespeichert. Danke!"
    )

    try:
        await context.bot.send_message(
            chat_id=OWNER_ID,
            text=f"📩 Neue Meldung #{report_id}\n"
                 f"Von: {update.effective_user.id}\n\n{message}",
        )
    except Exception:
        pass


async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.effective_message.reply_text(
        f"📊 Registrierte Accounts: {database.account_count()}\n"
        f"⛔ Gesperrte Accounts: {database.suspended_count()}"
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.effective_message.reply_text(
        "📚 LOL STUDIOS MANAGER — COMMANDS\n\n"
        "/menu – Button-Menü\n"
        "/profile – Profil\n"
        "/ping – Bot testen\n"
        "/id oder /myid – Telegram-ID\n"
        "/about – Über den Bot\n"
        "/rules – Regeln\n"
        "/games – Spielemenü\n"
        "/roll – Würfeln\n"
        "/coinflip – Münzwurf\n"
        "/guess – Zahl erraten\n"
        "/daily – 100 tägliche Punkte\n"
        "/leaderboard – Rangliste\n"
        "/setname Name – Namen ändern\n"
        "/setbio Text – Bio ändern\n"
        "/report Text – Problem melden\n"
        "/stats – Bot-Statistiken\n"
        "/cancel – Registrierung abbrechen"
    )


async def games_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.effective_message.reply_text(
        "🎮 Spiele:\n/roll – Würfeln\n/coinflip – Münzwurf\n/guess – Zahl erraten"
    )


def register_feature_handlers(application: Application):
    application.add_handler(CommandHandler("menu", menu_command), group=1)
    application.add_handler(CallbackQueryHandler(menu_callback, pattern=r"^menu:"), group=1)

    commands = [
        ("ping", ping_command),
        ("about", about_command),
        ("rules", rules_command),
        ("id", id_command),
        ("roll", roll_command),
        ("coinflip", coinflip_command),
        ("guess", guess_answer),
        ("daily", daily_command),
        ("leaderboard", leaderboard_command),
        ("setname", setname_command),
        ("setbio", setbio_command),
        ("report", report_command),
        ("stats", stats_command),
        ("games", games_command),
        ("help", help_command),
    ]

    for name, callback in commands:
        application.add_handler(CommandHandler(name, callback), group=1)
