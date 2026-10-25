# features.py — LOL Studios Manager
# Hauptmenü, Spiele, Profil, Rangliste, Support und Gruppenmoderation

import random

import database
from config import OWNER_ID
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
)


# --------------------------------------------------
# MENÜS
# --------------------------------------------------

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
            InlineKeyboardButton(
                "🛡️ Gruppenmoderation",
                callback_data="menu:moderation",
            ),
        ],
        [
            InlineKeyboardButton("🎫 Support", callback_data="menu:support"),
        ],
        [
            InlineKeyboardButton("📜 Regeln", callback_data="menu:rules"),
            InlineKeyboardButton("ℹ️ Über uns", callback_data="menu:about"),
        ],
        [
            InlineKeyboardButton("🔄 Aktualisieren", callback_data="menu:home"),
        ],
    ])


def back_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("⬅️ Zurück", callback_data="menu:home")]
    ])


def moderation_keyboard():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("👮 Admins", callback_data="mod:admins"),
            InlineKeyboardButton("ℹ️ Gruppeninfo", callback_data="mod:groupinfo"),
        ],
        [
            InlineKeyboardButton("🔗 Gruppenlink", callback_data="mod:grouplink"),
            InlineKeyboardButton("📜 Regeln", callback_data="mod:rules"),
        ],
        [
            InlineKeyboardButton("👢 Mitglied entfernen", callback_data="mod:kick"),
        ],
        [
            InlineKeyboardButton("🔇 Stummschalten", callback_data="mod:mute"),
            InlineKeyboardButton("🔊 Entstummen", callback_data="mod:unmute"),
        ],
        [
            InlineKeyboardButton("⬆️ Befördern", callback_data="mod:promote"),
            InlineKeyboardButton("⬇️ Degradieren", callback_data="mod:demote"),
        ],
        [
            InlineKeyboardButton("📌 Anpinnen", callback_data="mod:pin"),
            InlineKeyboardButton("🗑️ Löschen", callback_data="mod:delete"),
        ],
        [
            InlineKeyboardButton("✍️ Regeln einstellen", callback_data="mod:setrules"),
            InlineKeyboardButton("👋 Begrüßung", callback_data="mod:welcome"),
        ],
        [
            InlineKeyboardButton("❓ Alle Befehle", callback_data="mod:help"),
        ],
        [
            InlineKeyboardButton("⬅️ Zurück zum Hauptmenü", callback_data="menu:home"),
        ],
    ])


# --------------------------------------------------
# START UND MENÜ
# --------------------------------------------------

async def menu_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.effective_message.reply_text(
        "🚀 LOL STUDIOS MANAGER\n\n"
        "Willkommen im Hauptmenü!\n"
        "Wähle aus, was du machen möchtest:",
        reply_markup=main_keyboard(),
    )


async def menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    data = query.data or ""

    if data == "menu:home":
        await query.edit_message_text(
            "🚀 LOL STUDIOS MANAGER\n\n"
            "Wähle aus, was du machen möchtest:",
            reply_markup=main_keyboard(),
        )

    elif data == "menu:profile":
        account = database.get_account(user_id)

        if not account:
            await query.edit_message_text(
                "🔒 Dein Konto wurde nicht gefunden.\n"
                "Bitte registriere dich mit /register.",
                reply_markup=back_keyboard(),
            )
            return

        await query.edit_message_text(
            "👤 DEIN PROFIL\n\n"
            f"Name: {account.get('name') or 'Nicht angegeben'}\n"
            f"Bio: {account.get('bio') or 'Noch keine Bio'}\n"
            f"Altersgruppe: {account.get('agegroup') or 'Nicht angegeben'}\n"
            f"ID: {user_id}\n\n"
            "✏️ Profil bearbeiten:\n"
            "/setname Neuer Name\n"
            "/setbio Deine Bio",
            reply_markup=back_keyboard(),
        )

    elif data == "menu:games":
        await query.edit_message_text(
            "🎮 MINI-SPIELE\n\n"
            "/roll – Zufallszahl würfeln\n"
            "/coinflip – Münzwurf\n"
            "/guess – Zahl erraten\n\n"
            "Viel Spaß beim Spielen! 🎉",
            reply_markup=back_keyboard(),
        )

    elif data == "menu:daily":
        await query.edit_message_text(
            "🎁 TÄGLICHE BELOHNUNG\n\n"
            "Hole dir täglich deine Belohnung!\n\n"
            "👉 Nutze /daily, um deine Punkte abzuholen.",
            reply_markup=back_keyboard(),
        )

    elif data == "menu:leaderboard":
        await query.edit_message_text(
            leaderboard_text(),
            reply_markup=back_keyboard(),
        )

    elif data == "menu:rules":
        await query.edit_message_text(
            "📜 COMMUNITY-REGELN\n\n"
            "1. 🤝 Sei respektvoll zu anderen.\n"
            "2. 🚫 Kein Spam oder Missbrauch.\n"
            "3. 📩 Melde Probleme mit /report.\n"
            "4. 🔐 Umgehe keine Accountsperren.\n"
            "5. 🛡️ Respektiere die Moderation.",
            reply_markup=back_keyboard(),
        )

    elif data == "menu:about":
        await query.edit_message_text(
            "ℹ️ LOL STUDIOS MANAGER\n\n"
            "🚀 Ein Community-Bot von LOL Studios.\n\n"
            "Funktionen:\n"
            "👤 Profile\n"
            "🎮 Minispiele\n"
            "🎁 Tägliche Belohnungen\n"
            "🏆 Rangliste\n"
            "🛡️ Gruppenmoderation\n"
            "🎫 Support",
            reply_markup=back_keyboard(),
        )

    elif data == "menu:moderation":
        await query.edit_message_text(
            "🛡️ GRUPPENMODERATION\n\n"
            "Hier findest du die Moderationsbefehle für Gruppen.\n\n"
            "⚠️ Die Befehle funktionieren in Telegram-Gruppen.\n"
            "Für Moderationsaktionen benötigt der Bot die passenden "
            "Administratorrechte. Du selbst musst ebenfalls die nötigen "
            "Rechte besitzen.\n\n"
            "Wähle eine Funktion:",
            reply_markup=moderation_keyboard(),
        )

    elif data == "menu:support":
        await query.edit_message_text(
            "🎫 LOL STUDIOS SUPPORT\n\n"
            "Du hast ein Problem oder möchtest etwas melden?\n\n"
            "📩 Schreibe:\n"
            "/support Deine Nachricht\n\n"
            "Beispiel:\n"
            "/support Ich brauche Hilfe mit meinem Account\n\n"
            "💡 Beschreibe dein Problem möglichst genau.",
            reply_markup=back_keyboard(),
        )


# --------------------------------------------------
# GRUPPENMODERATION: BUTTON-POPUPS
# --------------------------------------------------

MODERATION_HELP = {
    "admins": (
        "👮 GRUPPENADMINS\n\n"
        "Zeigt die Administratoren der aktuellen Gruppe.\n\n"
        "Befehl: /admins"
    ),
    "groupinfo": (
        "ℹ️ GRUPPENINFO\n\n"
        "Zeigt Informationen über die aktuelle Gruppe.\n\n"
        "Befehl: /groupinfo"
    ),
    "grouplink": (
        "🔗 GRUPPENLINK\n\n"
        "Zeigt bzw. erstellt einen Einladungslink, sofern der Bot "
        "die nötigen Rechte besitzt.\n\n"
        "Befehl: /grouplink"
    ),
    "rules": (
        "📜 GRUPPENREGELN\n\n"
        "Zeigt die aktuell gespeicherten Gruppenregeln.\n\n"
        "Befehl: /grouprules"
    ),
    "kick": (
        "👢 MITGLIED ENTFERNEN\n\n"
        "Antworte auf eine Nachricht der Person und nutze /kick, "
        "oder folge der Verwendung deines Moderationsbefehls.\n\n"
        "Befehl: /kick\n\n"
        "⚠️ Du brauchst die nötigen Adminrechte."
    ),
    "mute": (
        "🔇 STUMMSCHALTEN\n\n"
        "Nutze den vorhandenen Moderationsbefehl für ein Mitglied.\n\n"
        "Befehl: /usermute\n\n"
        "⚠️ Der Bot benötigt die nötigen Gruppenrechte."
    ),
    "unmute": (
        "🔊 ENTSTUMMEN\n\n"
        "Hebt eine vorhandene Stummschaltung auf.\n\n"
        "Befehl: /userunmute"
    ),
    "promote": (
        "⬆️ BEFÖRDERN\n\n"
        "Vergibt Administratorrechte an ein Mitglied.\n\n"
        "Befehl: /promote\n\n"
        "⚠️ Verwende diesen Befehl nur, wenn du dazu berechtigt bist."
    ),
    "demote": (
        "⬇️ DEGRADIEREN\n\n"
        "Entfernt Administratorrechte, sofern Telegram und die "
        "Rechte des Bots dies erlauben.\n\n"
        "Befehl: /demote"
    ),
    "pin": (
        "📌 NACHRICHT ANPINNEN\n\n"
        "Antworte auf die gewünschte Nachricht und nutze /pin.\n\n"
        "⚠️ Der Bot benötigt die nötigen Rechte zum Anpinnen."
    ),
    "delete": (
        "🗑️ NACHRICHT LÖSCHEN\n\n"
        "Antworte auf eine Nachricht und nutze /del.\n\n"
        "⚠️ Telegram kann das Löschen älterer Nachrichten einschränken."
    ),
    "setrules": (
        "✍️ GRUPPENREGELN EINSTELLEN\n\n"
        "Schreibe die Regeln hinter den Befehl.\n\n"
        "Beispiel:\n"
        "/grouprules Sei respektvoll und spamme nicht.\n\n"
        "Nur berechtigte Gruppenadmins können die Regeln ändern."
    ),
    "welcome": (
        "👋 BEGRÜSSUNGSTEXT\n\n"
        "Lege einen Begrüßungstext fest.\n\n"
        "Beispiel:\n"
        "/welcome Willkommen {name}!\n\n"
        "Hinweis: Das Speichern eines Begrüßungstextes aktiviert "
        "nicht automatisch das Versenden von Begrüßungen."
    ),
    "help": (
        "❓ MODERATIONSHILFE\n\n"
        "Verwende /modhelp, um die Moderationsbefehle anzuzeigen.\n\n"
        "Weitere Befehle:\n"
        "/admins\n"
        "/groupinfo\n"
        "/grouplink\n"
        "/grouprules\n"
        "/kick\n"
        "/promote\n"
        "/demote\n"
        "/pin\n"
        "/del\n"
        "/usermute\n"
        "/userunmute\n"
        "/welcome"
    ),
}


async def moderation_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    query = update.callback_query
    data = query.data or ""
    action = data.partition(":")[2]

    message = MODERATION_HELP.get(action)

    if not message:
        await query.answer(
            "Diese Funktion wurde nicht gefunden.",
            show_alert=True,
        )
        return

    # Telegram zeigt eine Popup-Meldung an.
    await query.answer(message, show_alert=True)


# --------------------------------------------------
# ALLGEMEINE BEFEHLE
# --------------------------------------------------

async def ping_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.effective_message.reply_text(
        "🏓 Pong! Der Bot antwortet."
    )


async def about_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.effective_message.reply_text(
        "ℹ️ LOL Studios Manager\n"
        "Community-Bot von LOL Studios."
    )


async def rules_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.effective_message.reply_text(
        "📜 Regeln:\n"
        "1. Respektvoll bleiben.\n"
        "2. Nicht spammen.\n"
        "3. Probleme mit /report melden."
    )


async def id_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    if user:
        await update.effective_message.reply_text(
            f"🆔 Deine Telegram-ID: {user.id}"
        )


# --------------------------------------------------
# SPIELE
# --------------------------------------------------

async def roll_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.effective_message.reply_text(
        f"🎲 Du hast eine {random.randint(1, 6)} gewürfelt!"
    )


async def coinflip_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    await update.effective_message.reply_text(
        f"🪙 Ergebnis: {random.choice(['Kopf', 'Zahl'])}!"
    )


async def guess_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    number = random.randint(1, 10)
    context.user_data["guess_number"] = number

    await update.effective_message.reply_text(
        "🔢 Ich habe eine Zahl zwischen 1 und 10 gewählt.\n"
        "Rate mit /guess Zahl, zum Beispiel /guess 5."
    )


async def guess_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
            "❌ Bitte gib eine Zahl von 1 bis 10 ein."
        )
        return

    if not 1 <= number <= 10:
        await update.effective_message.reply_text(
            "❌ Bitte wähle eine Zahl zwischen 1 und 10."
        )
        return

    if number == target:
        context.user_data.pop("guess_number", None)
        await update.effective_message.reply_text(
            "🎉 Richtig geraten! Du hast gewonnen."
        )
    else:
        await update.effective_message.reply_text(
            "❌ Leider falsch! Versuch es nochmal mit /guess Zahl."
        )


# --------------------------------------------------
# RANGLISTE UND DAILY
# --------------------------------------------------

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


async def leaderboard_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    await update.effective_message.reply_text(leaderboard_text())


async def daily_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    if not user:
        return

    success, total = database.claim_daily(user.id, 100)

    if not success:
        await update.effective_message.reply_text(
            "⏳ Du hast deine tägliche Belohnung heute bereits abgeholt.\n"
            f"💰 Deine Punkte: {total}"
        )
        return

    await update.effective_message.reply_text(
        "🎁 Daily abgeholt!\n"
        "Du bekommst 100 Punkte.\n"
        f"💰 Dein Punktestand: {total}"
    )


# --------------------------------------------------
# PROFIL BEARBEITEN
# --------------------------------------------------

async def setname_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
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
            "❌ Der Name darf höchstens 50 Zeichen haben."
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

    if changed:
        await update.effective_message.reply_text(
            f"✅ Dein Name ist jetzt: {name}"
        )
    else:
        await update.effective_message.reply_text(
            "Bitte registriere dich zuerst mit /register."
        )


async def setbio_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
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
            "❌ Die Bio darf höchstens 200 Zeichen haben."
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

    if changed:
        await update.effective_message.reply_text(
            "✅ Deine Bio wurde aktualisiert."
        )
    else:
        await update.effective_message.reply_text(
            "Bitte registriere dich zuerst mit /register."
        )


# --------------------------------------------------
# MELDUNGEN UND STATISTIK
# --------------------------------------------------

async def report_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
            "❌ Die Meldung darf höchstens 1000 Zeichen haben."
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
                f"📩 Neue Meldung #{report_id}\n"
                f"Von: {user.id}\n\n"
                f"{message}"
            ),
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
        "📚 LOL STUDIOS MANAGER — BEFEHLE\n\n"
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
        "/support Text – Support kontaktieren\n"
        "/stats – Bot-Statistiken\n"
        "/modhelp – Gruppenmoderation\n"
        "/cancel – Registrierung abbrechen"
    )


async def games_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.effective_message.reply_text(
        "🎮 SPIELE\n\n"
        "/roll – Würfeln\n"
        "/coinflip – Münzwurf\n"
        "/guess – Zahl erraten"
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
            moderation_callback,
            pattern=r"^mod:",
        ),
        group=1,
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
    ]

    for name, callback in commands:
        application.add_handler(
            CommandHandler(name, callback),
            group=1,
        )
