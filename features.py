
# features.py — LOL Studios Manager
# Hauptmenü, Spiele, Profil, Rangliste und Support-Tickets

import random
import logging

import database
from config import OWNER_ID

from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Update,
)
from telegram.constants import ChatType
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

logger = logging.getLogger(__name__)


# --------------------------------------------------
# MENÜS
# --------------------------------------------------

def main_keyboard():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "👤 Profil", callback_data="menu:profile"
            ),
            InlineKeyboardButton(
                "🎮 Spiele", callback_data="menu:games"
            ),
        ],
        [
            InlineKeyboardButton(
                "🎁 Daily", callback_data="menu:daily"
            ),
            InlineKeyboardButton(
                "🏆 Rangliste", callback_data="menu:leaderboard"
            ),
        ],
        [
            InlineKeyboardButton(
                "🎫 Support", callback_data="menu:support"
            ),
            InlineKeyboardButton(
                "📜 Regeln", callback_data="menu:rules"
            ),
        ],
        [
            InlineKeyboardButton(
                "ℹ️ Über uns", callback_data="menu:about"
            ),
            InlineKeyboardButton(
                "🔄 Aktualisieren", callback_data="menu:home"
            ),
        ],
    ])


def back_keyboard(target="menu:home"):
    return InlineKeyboardMarkup([[
        InlineKeyboardButton("⬅️ Zurück", callback_data=target)
    ]])


def cancel_ticket_keyboard():
    return InlineKeyboardMarkup([[
        InlineKeyboardButton(
            "❌ Abbrechen", callback_data="ticket:cancel"
        )
    ]])


def ticket_created_keyboard(ticket_id):
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "🎫 Meine Tickets", callback_data="ticket:mine"
            )
        ],
        [
            InlineKeyboardButton(
                "🏠 Hauptmenü", callback_data="menu:home"
            )
        ],
    ])


# --------------------------------------------------
# HAUPTMENÜ
# --------------------------------------------------

async def menu_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    context.user_data.pop("waiting_for_ticket", None)

    await update.effective_message.reply_text(
        "🚀 LOL STUDIOS MANAGER\n\n"
        "👋 Willkommen!\n"
        "Wähle eine Funktion aus:",
        reply_markup=main_keyboard(),
    )


async def menu_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    data = query.data or ""

    if data == "menu:home":
        context.user_data.pop("waiting_for_ticket", None)
        await query.edit_message_text(
            "🚀 LOL STUDIOS MANAGER\n\n"
            "👋 Wähle eine Funktion aus:",
            reply_markup=main_keyboard(),
        )

    elif data == "menu:profile":
        account = database.get_account(user_id)

        if not account:
            await query.edit_message_text(
                "🔒 Dein Konto wurde nicht gefunden.\n"
                "Bitte nutze /register.",
                reply_markup=back_keyboard(),
            )
            return

        await query.edit_message_text(
            "👤 DEIN PROFIL\n\n"
            f"Name: {account.get('name') or 'Nicht angegeben'}\n"
            f"Bio: {account.get('bio') or 'Noch keine Bio'}\n"
            f"Altersgruppe: "
            f"{account.get('agegroup') or 'Nicht angegeben'}\n"
            f"🆔 ID: {user_id}\n\n"
            "✏️ Profil bearbeiten:\n"
            "/setname Neuer Name\n"
            "/setbio Deine Bio",
            reply_markup=back_keyboard(),
        )

    elif data == "menu:games":
        await query.edit_message_text(
            "🎮 MINI-SPIELE\n\n"
            "🎲 /roll – Würfeln\n"
            "🪙 /coinflip – Münzwurf\n"
            "🔢 /guess – Zahl erraten\n\n"
            "Viel Spaß beim Spielen!",
            reply_markup=back_keyboard(),
        )

    elif data == "menu:daily":
        await query.edit_message_text(
            "🎁 TÄGLICHE BELOHNUNG\n\n"
            "Hole dir einmal täglich 100 Punkte!\n\n"
            "👉 Nutze /daily.",
            reply_markup=back_keyboard(),
        )

    elif data == "menu:leaderboard":
        try:
            text = leaderboard_text()
        except Exception:
            logger.exception("Fehler beim Laden der Rangliste")
            text = "⚠️ Die Rangliste ist gerade nicht verfügbar."

        await query.edit_message_text(
            text,
            reply_markup=back_keyboard(),
        )

    elif data == "menu:support":
        context.user_data["waiting_for_ticket"] = True

        await query.edit_message_text(
            "🎫 SUPPORT-CENTER\n\n"
            "Beschreibe dein Problem in einer Nachricht.\n\n"
            "📩 Deine Nachricht wird als Support-Ticket "
            "gespeichert und an den Bot-Owner gemeldet.\n\n"
            "✍️ Schreibe jetzt deine Nachricht hier in den Chat.",
            reply_markup=cancel_ticket_keyboard(),
        )

    elif data == "menu:rules":
        await query.edit_message_text(
            "📜 REGELN\n\n"
            "1. 🤝 Sei respektvoll.\n"
            "2. 🚫 Kein Spam oder Missbrauch.\n"
            "3. 📩 Probleme kannst du mit /report melden.\n"
            "4. 🔒 Versuche nicht, andere Accounts zu umgehen.\n",
            reply_markup=back_keyboard(),
        )

    elif data == "menu:about":
        await query.edit_message_text(
            "ℹ️ LOL STUDIOS MANAGER\n\n"
            "🚀 Ein Community-Bot von LOL Studios.\n\n"
            "👤 Profile\n"
            "🎮 Mini-Spiele\n"
            "🎁 Tägliche Belohnungen\n"
            "🏆 Ranglisten\n"
            "🎫 Support-Tickets",
            reply_markup=back_keyboard(),
        )


# --------------------------------------------------
# SUPPORT-TICKETS
# --------------------------------------------------

async def cancel_ticket_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    query = update.callback_query
    await query.answer("Ticket-Erstellung abgebrochen.")

    context.user_data.pop("waiting_for_ticket", None)

    await query.edit_message_text(
        "❌ Ticket-Erstellung abgebrochen.",
        reply_markup=back_keyboard(),
    )


async def receive_ticket_message(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    message = update.effective_message
    user = update.effective_user

    if not message or not user:
        return

    if not context.user_data.get("waiting_for_ticket"):
        return

    if message.chat.type != ChatType.PRIVATE:
        await message.reply_text(
            "🔒 Bitte erstelle Support-Tickets im privaten Chat "
            "mit dem Bot."
        )
        return

    text = (message.text or "").strip()

    if not text:
        await message.reply_text(
            "✍️ Bitte sende dein Anliegen als Textnachricht."
        )
        return

    if len(text) > 3000:
        await message.reply_text(
            "⚠️ Deine Nachricht ist zu lang. "
            "Bitte nutze maximal 3000 Zeichen."
        )
        return

    try:
        ticket_id = database.create_ticket(user.id, text)
    except Exception:
        logger.exception("Support-Ticket konnte nicht gespeichert werden")
        await message.reply_text(
            "❌ Dein Ticket konnte gerade nicht gespeichert werden.\n"
            "Bitte versuche es später erneut."
        )
        return

    context.user_data.pop("waiting_for_ticket", None)

    await message.reply_text(
        f"✅ Dein Support-Ticket #{ticket_id} wurde erstellt!\n\n"
        "📨 Der Support wurde über dein Anliegen informiert.\n"
        "Du kannst deine Tickets über den Button unten ansehen.",
        reply_markup=ticket_created_keyboard(ticket_id),
    )

    try:
        await context.bot.send_message(
            chat_id=OWNER_ID,
            text=(
                f"🎫 NEUES SUPPORT-TICKET #{ticket_id}\n\n"
                f"👤 Nutzer: {user.full_name}\n"
                f"🆔 Telegram-ID: {user.id}\n"
                f"🔗 Username: @{user.username or 'nicht vorhanden'}\n\n"
                f"📝 Nachricht:\n{text}\n\n"
                f"💬 Antworten:\n"
                f"/ticketreply {ticket_id} Deine Antwort"
            ),
        )
    except Exception:
        logger.exception(
            "Ticket wurde gespeichert, aber Owner-Benachrichtigung "
            "konnte nicht gesendet werden"
        )


async def my_tickets_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    query = update.callback_query
    await query.answer()

    try:
        tickets = database.list_user_tickets(
            query.from_user.id,
            limit=10,
        )
    except Exception:
        logger.exception("Eigene Tickets konnten nicht geladen werden")
        await query.edit_message_text(
            "⚠️ Deine Tickets konnten nicht geladen werden.",
            reply_markup=back_keyboard(),
        )
        return

    if not tickets:
        await query.edit_message_text(
            "🎫 DU HAST NOCH KEINE TICKETS\n\n"
            "Wenn du Hilfe brauchst, öffne das Support-Center.",
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(
                        "🎫 Support öffnen",
                        callback_data="menu:support",
                    )
                ],
                [
                    InlineKeyboardButton(
                        "🏠 Hauptmenü",
                        callback_data="menu:home",
                    )
                ],
            ]),
        )
        return

    lines = ["🎫 DEINE SUPPORT-TICKETS\n"]

    for ticket in tickets:
        status = ticket.get("status", "open")
        status_emoji = {
            "open": "🟡 Offen",
            "answered": "🟢 Beantwortet",
            "closed": "⚫ Geschlossen",
        }.get(status, status)

        lines.append(
            f"#{ticket['id']} — {status_emoji}\n"
            f"📝 {str(ticket.get('message') or '')[:180]}"
        )

        if ticket.get("reply"):
            lines.append(
                f"💬 Antwort: {str(ticket['reply'])[:300]}"
            )

        lines.append("")

    await query.edit_message_text(
        "\n".join(lines),
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    "🎫 Neues Ticket",
                    callback_data="menu:support",
                )
            ],
            [
                InlineKeyboardButton(
                    "🏠 Hauptmenü",
                    callback_data="menu:home",
                )
            ],
        ]),
    )


async def ticket_reply_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    user = update.effective_user
    message = update.effective_message

    if not user or user.id != OWNER_ID:
        await message.reply_text(
            "⛔ Dieser Befehl ist nur für den Bot-Owner."
        )
        return

    if len(context.args) < 2:
        await message.reply_text(
            "Verwendung:\n"
            "/ticketreply TICKET_ID Deine Antwort\n\n"
            "Beispiel:\n"
            "/ticketreply 12 Wir helfen dir gerne!"
        )
        return

    try:
        ticket_id = int(context.args[0])
    except ValueError:
        await message.reply_text(
            "⚠️ Bitte gib eine gültige Ticket-ID an."
        )
        return

    reply = " ".join(context.args[1:]).strip()

    try:
        ticket = database.get_ticket(ticket_id)

        if not ticket:
            await message.reply_text(
                f"❌ Ticket #{ticket_id} wurde nicht gefunden."
            )
            return

        if ticket.get("status") == "closed":
            await message.reply_text(
                "⚠️ Dieses Ticket wurde bereits geschlossen."
            )
            return

        database.reply_ticket(ticket_id, reply)

        await context.bot.send_message(
            chat_id=int(ticket["user_id"]),
            text=(
                f"📨 ANTWORT AUF DEIN TICKET #{ticket_id}\n\n"
                f"💬 {reply}\n\n"
                "Vielen Dank, dass du LOL Studios kontaktierst!"
            ),
        )

        await message.reply_text(
            f"✅ Antwort auf Ticket #{ticket_id} wurde gespeichert "
            "und an den Nutzer gesendet."
        )

    except Exception:
        logger.exception("Fehler bei der Ticket-Antwort")
        await message.reply_text(
            "⚠️ Die Antwort konnte nicht verarbeitet werden. "
            "Prüfe die Bot-Logs."
        )


# --------------------------------------------------
# ALLGEMEINE BEFEHLE
# --------------------------------------------------

async def ping_command(update, context):
    await update.effective_message.reply_text(
        "🏓 Pong! Der Bot antwortet."
    )


async def about_command(update, context):
    await update.effective_message.reply_text(
        "ℹ️ LOL Studios Manager\n"
        "🚀 Community-Bot von LOL Studios."
    )


async def rules_command(update, context):
    await update.effective_message.reply_text(
        "📜 Regeln:\n"
        "1. 🤝 Respektvoll bleiben.\n"
        "2. 🚫 Nicht spammen.\n"
        "3. 📩 Probleme mit /report melden."
    )


async def id_command(update, context):
    user = update.effective_user
    if user:
        await update.effective_message.reply_text(
            f"🆔 Deine Telegram-ID: {user.id}"
        )


async def roll_command(update, context):
    await update.effective_message.reply_text(
        f"🎲 Du hast eine {random.randint(1, 6)} gewürfelt!"
    )


async def coinflip_command(update, context):
    await update.effective_message.reply_text(
        f"🪙 Ergebnis: {random.choice(['Kopf', 'Zahl'])}!"
    )


async def guess_command(update, context):
    number = random.randint(1, 10)
    context.user_data["guess_number"] = number

    await update.effective_message.reply_text(
        "🔢 Ich habe eine Zahl zwischen 1 und 10 gewählt.\n"
        "Rate mit /guess Zahl, zum Beispiel /guess 5."
    )


async def guess_answer(update, context):
    target = context.user_data.get("guess_number")

    if target is None:
        await guess_command(update, context)
        return

    if not context.args:
        await update.effective_message.reply_text(
            "Verwendung: /guess Zahl, zum Beispiel /guess 5."
        )
        return

    try:
        number = int(context.args[0])
    except ValueError:
        await update.effective_message.reply_text(
            "⚠️ Bitte gib eine Zahl von 1 bis 10 ein."
        )
        return

    if not 1 <= number <= 10:
        await update.effective_message.reply_text(
            "⚠️ Wähle eine Zahl zwischen 1 und 10."
        )
        return

    if number == target:
        context.user_data.pop("guess_number", None)
        await update.effective_message.reply_text(
            "🎉 Richtig geraten! Du hast gewonnen!"
        )
    else:
        await update.effective_message.reply_text(
            "❌ Leider falsch! Versuch es nochmal."
        )


def leaderboard_text():
    with database.connect() as db:
        cur = db.cursor(dictionary=True)
        cur.execute("""
            SELECT
                a.name,
                a.username,
                p.amount
            FROM accounts AS a
            LEFT JOIN points AS p ON p.user_id = a.user_id
            WHERE a.suspended = 0
            ORDER BY COALESCE(p.amount, 0) DESC, a.name ASC
            LIMIT 10
        """)
        rows = cur.fetchall()
        cur.close()

    if not rows:
        return "🏆 Noch gibt es keine Einträge."

    lines = ["🏆 RANGLISTE\n"]

    for index, row in enumerate(rows, 1):
        name = row.get("name") or row.get("username") or "Unbekannt"
        amount = row.get("amount") or 0
        lines.append(f"{index}. {name} — {amount} Punkte")

    return "\n".join(lines)


async def leaderboard_command(update, context):
    await update.effective_message.reply_text(leaderboard_text())


async def daily_command(update, context):
    user = update.effective_user
    if not user:
        return

    success, total = database.claim_daily(user.id, 100)

    if not success:
        await update.effective_message.reply_text(
            "⏳ Du hast deine tägliche Belohnung bereits abgeholt.\n"
            f"💰 Deine Punkte: {total}"
        )
        return

    await update.effective_message.reply_text(
        "🎁 Daily abgeholt!\n"
        "💰 +100 Punkte\n"
        f"🏦 Dein Punktestand: {total}"
    )


async def setname_command(update, context):
    user = update.effective_user
    if not user:
        return

    if not context.args:
        await update.effective_message.reply_text(
            "Verwendung: /setname Neuer Name"
        )
        return

    name = " ".join(context.args).strip()

    if len(name) > 50:
        await update.effective_message.reply_text(
            "⚠️ Der Name darf höchstens 50 Zeichen haben."
        )
        return

    with database.connect() as db:
        cur = db.cursor()
        cur.execute(
            "UPDATE accounts SET name = %s WHERE user_id = %s",
            (name, user.id),
        )
        changed = cur.rowcount > 0
        cur.close()

    await update.effective_message.reply_text(
        f"✅ Dein Name ist jetzt: {name}"
        if changed else
        "🔒 Bitte registriere dich zuerst mit /register."
    )


async def setbio_command(update, context):
    user = update.effective_user
    if not user:
        return

    bio = " ".join(context.args).strip()

    if not bio:
        await update.effective_message.reply_text(
            "Verwendung: /setbio Das ist meine Bio"
        )
        return

    if len(bio) > 200:
        await update.effective_message.reply_text(
            "⚠️ Die Bio darf höchstens 200 Zeichen haben."
        )
        return

    with database.connect() as db:
        cur = db.cursor()
        cur.execute(
            "UPDATE accounts SET bio = %s WHERE user_id = %s",
            (bio, user.id),
        )
        changed = cur.rowcount > 0
        cur.close()

    await update.effective_message.reply_text(
        "✅ Deine Bio wurde aktualisiert."
        if changed else
        "🔒 Bitte registriere dich zuerst mit /register."
    )


async def report_command(update, context):
    user = update.effective_user
    if not user:
        return

    message = " ".join(context.args).strip()

    if not message:
        await update.effective_message.reply_text(
            "Verwendung: /report Beschreibe das Problem"
        )
        return

    if len(message) > 1000:
        await update.effective_message.reply_text(
            "⚠️ Die Meldung darf höchstens 1000 Zeichen haben."
        )
        return

    report_id = database.create_report(user.id, message)

    await update.effective_message.reply_text(
        f"✅ Meldung #{report_id} wurde gespeichert. Danke!"
    )

    try:
        await context.bot.send_message(
            chat_id=OWNER_ID,
            text=(
                f"📩 NEUE MELDUNG #{report_id}\n"
                f"👤 Nutzer-ID: {user.id}\n\n{message}"
            ),
        )
    except Exception:
        logger.exception("Owner-Benachrichtigung fehlgeschlagen")


async def stats_command(update, context):
    await update.effective_message.reply_text(
        f"📊 Registrierte Accounts: {database.account_count()}\n"
        f"⛔ Gesperrte Accounts: {database.suspended_count()}"
    )


async def help_command(update, context):
    await update.effective_message.reply_text(
        "📚 LOL STUDIOS MANAGER\n\n"
        "/menu – Hauptmenü\n"
        "/profile – Profil\n"
        "/ping – Bot testen\n"
        "/myid – Telegram-ID\n"
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
        "/support – Support-Center\n"
        "/stats – Statistiken\n"
        "/cancel – Registrierung abbrechen"
    )


async def games_command(update, context):
    await update.effective_message.reply_text(
        "🎮 Spiele:\n"
        "/roll – Würfeln\n"
        "/coinflip – Münzwurf\n"
        "/guess – Zahl erraten"
    )


async def support_command(update, context):
    context.user_data["waiting_for_ticket"] = True
    await update.effective_message.reply_text(
        "🎫 SUPPORT-CENTER\n\n"
        "Schreibe jetzt dein Anliegen als Nachricht.",
        reply_markup=cancel_ticket_keyboard(),
    )


# --------------------------------------------------
# HANDLER REGISTRIEREN
# --------------------------------------------------

def register_feature_handlers(application: Application):
    application.add_handler(
        CommandHandler("menu", menu_command),
        group=1,
    )

    application.add_handler(
        CallbackQueryHandler(
            menu_callback,
            pattern=r"^menu:",
        ),
        group=1,
    )

    application.add_handler(
        CallbackQueryHandler(
            cancel_ticket_callback,
            pattern=r"^ticket:cancel$",
        ),
        group=1,
    )

    application.add_handler(
        CallbackQueryHandler(
            my_tickets_callback,
            pattern=r"^ticket:mine$",
        ),
        group=1,
    )

    application.add_handler(
        MessageHandler(
            filters.ChatType.PRIVATE
            & filters.TEXT
            & ~filters.COMMAND,
            receive_ticket_message,
        ),
        group=2,
    )

    commands = [
        ("ping", ping_command),
        ("about", about_command),
        ("rules", rules_command),
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
        ("support", support_command),
        ("ticketreply", ticket_reply_command),
    ]

    for name, callback in commands:
        application.add_handler(
            CommandHandler(name, callback),
            group=1,
        )
