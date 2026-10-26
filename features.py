
# features.py — LOL Studios Manager
# MySQL-Version mit Support-Dialog, Minispielen und Moderationsmenü

import random

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
    MessageHandler,
    filters,
)


# ---------------- MENÜ ----------------

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
                "🛡️ Moderation",
                callback_data="menu:moderation",
            ),
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
            InlineKeyboardButton(
                "👮 Admins anzeigen",
                callback_data="mod:admins",
            ),
        ],
        [
            InlineKeyboardButton(
                "📋 Gruppeninformationen",
                callback_data="mod:groupinfo",
            ),
        ],
        [
            InlineKeyboardButton(
                "📜 Gruppenregeln",
                callback_data="mod:rules",
            ),
        ],
        [
            InlineKeyboardButton(
                "⚙️ Moderationsbefehle",
                callback_data="mod:commands",
            ),
        ],
        [
            InlineKeyboardButton(
                "⬅️ Zurück zum Hauptmenü",
                callback_data="menu:home",
            ),
        ],
    ])


async def menu_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.effective_message.reply_text(
        "🚀 LOL STUDIOS MANAGER\n\nWas möchtest du machen?",
        reply_markup=main_keyboard(),
    )


async def menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    data = query.data or ""

    if data == "menu:home":
        await query.edit_message_text(
            "🚀 LOL STUDIOS MANAGER\n\nWas möchtest du machen?",
            reply_markup=main_keyboard(),
        )

    elif data == "menu:profile":
        account = database.get_account(user_id)

        if not account:
            await query.edit_message_text(
                "🔒 Ich finde dein Konto gerade nicht. "
                "Registriere dich bitte mit /register.",
                reply_markup=back_keyboard(),
            )
            return

        await query.edit_message_text(
            "👤 DEIN PROFIL\n\n"
            f"Name: {account.get('name') or 'Nicht angegeben'}\n"
            f"Bio: {account.get('bio') or 'Noch keine Bio'}\n"
            f"Altersgruppe: {account.get('agegroup') or 'Nicht angegeben'}\n"
            f"Telegram-ID: {user_id}\n\n"
            "Mit /setname und /setbio kannst du dein Profil bearbeiten.",
            reply_markup=back_keyboard(),
        )

    elif data == "menu:games":
        await query.edit_message_text(
            "🎮 MINI-SPIELE\n\n"
            "/roll – Würfeln\n"
            "/coinflip – Münzwurf\n"
            "/guess – Zahl erraten\n"
            "/rps – Schere, Stein, Papier\n"
            "/quiz – Quizfrage\n\n"
            "Viel Spaß!",
            reply_markup=back_keyboard(),
        )

    elif data == "menu:daily":
        await query.edit_message_text(
            "🎁 TÄGLICHE BELOHNUNG\n\n"
            "Mit /daily kannst du einmal täglich 100 Punkte abholen.",
            reply_markup=back_keyboard(),
        )

    elif data == "menu:leaderboard":
        await query.edit_message_text(
            leaderboard_text(),
            reply_markup=back_keyboard(),
        )

    elif data == "menu:moderation":
        await query.edit_message_text(
            "🛡️ MODERATIONSVERWALTUNG\n\n"
            "Hier findest du die Verwaltung deiner Telegram-Gruppe.\n\n"
            "Wähle eine Option aus. Gruppenbefehle funktionieren "
            "nur, wenn der Bot in der betreffenden Gruppe ist und "
            "die nötigen Telegram-Rechte besitzt.",
            reply_markup=moderation_keyboard(),
        )

    elif data == "menu:rules":
        await query.edit_message_text(
            "📜 REGELN\n\n"
            "1. Bleib respektvoll.\n"
            "2. Kein Spam oder Missbrauch.\n"
            "3. Melde Probleme mit /report.\n"
            "4. Respektiere andere Mitglieder.",
            reply_markup=back_keyboard(),
        )

    elif data == "menu:about":
        await query.edit_message_text(
            "ℹ️ LOL STUDIOS MANAGER\n\n"
            "Ein Community-Bot von LOL Studios mit Profilen, "
            "Minispielen, Punkten und Support.",
            reply_markup=back_keyboard(),
        )


# ---------------- MODERATIONSMENÜ ----------------

async def moderation_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    query = update.callback_query
    await query.answer()

    data = query.data or ""

    if data == "mod:admins":
        await query.edit_message_text(
            "👮 GRUPPENADMINS\n\n"
            "Öffne deine Telegram-Gruppe und nutze dort:\n"
            "/admins\n\n"
            "Der Bot muss Mitglied der Gruppe sein.",
            reply_markup=moderation_keyboard(),
        )

    elif data == "mod:groupinfo":
        await query.edit_message_text(
            "📋 GRUPPENINFORMATIONEN\n\n"
            "Öffne die Gruppe, die du verwalten möchtest, "
            "und sende dort:\n"
            "/groupinfo",
            reply_markup=moderation_keyboard(),
        )

    elif data == "mod:rules":
        await query.edit_message_text(
            "📜 GRUPPENREGELN\n\n"
            "Öffne die betreffende Telegram-Gruppe und nutze:\n"
            "/grouprules\n\n"
            "Die Regeln werden über die Gruppenverwaltung "
            "festgelegt, sofern diese Funktion dort unterstützt wird.",
            reply_markup=moderation_keyboard(),
        )

    elif data == "mod:commands":
        await query.edit_message_text(
            "⚙️ MODERATIONSBEFEHLE\n\n"
            "👮 /admins – Admins anzeigen\n"
            "📋 /groupinfo – Gruppeninformationen\n"
            "🔗 /grouplink – Gruppenlink\n"
            "📜 /grouprules – Gruppenregeln\n"
            "📌 /pin – Nachricht anheften\n"
            "🗑️ /del – Nachricht löschen\n"
            "🔇 /usermute – Mitglied stummschalten\n"
            "🔊 /userunmute – Stummschaltung aufheben\n"
            "⬆️ /promote – Mitglied befördern\n"
            "⬇️ /demote – Adminrechte entziehen\n"
            "👋 /welcome – Begrüßung konfigurieren\n\n"
            "Hinweis: Ob ein Befehl funktioniert, hängt von "
            "der implementierten Funktion und den Bot-Rechten ab.",
            reply_markup=moderation_keyboard(),
        )


# ---------------- ALLGEMEINE BEFEHLE ----------------

async def ping_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.effective_message.reply_text("🏓 Pong! Ich bin online.")


async def about_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.effective_message.reply_text(
        "ℹ️ LOL Studios Manager\nEin Community-Bot von LOL Studios."
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


async def roll_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.effective_message.reply_text(
        f"🎲 Du hast eine {random.randint(1, 6)} gewürfelt!"
    )


async def coinflip_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.effective_message.reply_text(
        f"🪙 Ergebnis: {random.choice(['Kopf', 'Zahl'])}!"
    )


# ---------------- ZAHLENRATEN ----------------

async def guess_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["guess_number"] = random.randint(1, 10)

    await update.effective_message.reply_text(
        "🔢 Ich habe eine Zahl zwischen 1 und 10 gewählt!\n"
        "Rate mit /guess ZAHL, zum Beispiel /guess 5."
    )


async def guess_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    target = context.user_data.get("guess_number")

    if target is None:
        await guess_command(update, context)
        return

    if not context.args:
        await update.effective_message.reply_text(
            "Gib deinen Tipp so ein: /guess 5"
        )
        return

    try:
        number = int(context.args[0])
    except ValueError:
        await update.effective_message.reply_text(
            "Das sieht nicht nach einer Zahl aus. Versuch es mit /guess 5."
        )
        return

    if not 1 <= number <= 10:
        await update.effective_message.reply_text(
            "Nimm eine Zahl zwischen 1 und 10."
        )
        return

    if number == target:
        context.user_data.pop("guess_number", None)
        points = database.add_points(update.effective_user.id, 10)
        await update.effective_message.reply_text(
            f"🎉 Richtig! Es war die {target}.\n"
            f"🏆 Du bekommst 10 Punkte. Punktestand: {points}"
        )
    elif number < target:
        await update.effective_message.reply_text(
            "Noch nicht! Meine Zahl ist größer. Versuch's nochmal."
        )
    else:
        await update.effective_message.reply_text(
            "Noch nicht! Meine Zahl ist kleiner. Versuch's nochmal."
        )


# ---------------- SCHERE, STEIN, PAPIER ----------------

async def rps_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.effective_message.reply_text(
            "✊✋✌️ Lass uns spielen!\n"
            "Nutze /rps schere, /rps stein oder /rps papier."
        )
        return

    choices = {
        "schere": "✌️ Schere",
        "stein": "✊ Stein",
        "papier": "✋ Papier",
    }

    player = context.args[0].lower()

    if player not in choices:
        await update.effective_message.reply_text(
            "Bitte wähle schere, stein oder papier."
        )
        return

    bot_choice = random.choice(list(choices))

    if player == bot_choice:
        result = "Unentschieden! 😄"
    elif (
        (player == "schere" and bot_choice == "papier")
        or (player == "stein" and bot_choice == "schere")
        or (player == "papier" and bot_choice == "stein")
    ):
        points = database.add_points(update.effective_user.id, 5)
        result = f"Du gewinnst! 🎉 +5 Punkte. Neuer Stand: {points}"
    else:
        result = "Diesmal habe ich gewonnen! Versuch's nochmal."

    await update.effective_message.reply_text(
        f"Du: {choices[player]}\n"
        f"Ich: {choices[bot_choice]}\n\n{result}"
    )


# ---------------- QUIZ ----------------

QUIZ_QUESTIONS = [
    {
        "question": "Wie viele Seiten hat ein Würfel?",
        "answers": ["4", "6", "8"],
        "correct": 1,
    },
    {
        "question": "Welcher Planet ist als Roter Planet bekannt?",
        "answers": ["Mars", "Venus", "Jupiter"],
        "correct": 0,
    },
    {
        "question": "Wie viele Minuten hat eine Stunde?",
        "answers": ["30", "60", "100"],
        "correct": 1,
    },
    {
        "question": "Welche Sprache wird für viele Telegram-Bots verwendet?",
        "answers": ["Python", "HTML allein", "CSS allein"],
        "correct": 0,
    },
]


async def quiz_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    question = random.choice(QUIZ_QUESTIONS)
    context.user_data["quiz_answer"] = question["correct"]
    context.user_data["quiz_active"] = True

    buttons = []
    for index, answer in enumerate(question["answers"]):
        buttons.append([
            InlineKeyboardButton(
                answer,
                callback_data=f"quiz:{index}",
            )
        ])

    await update.effective_message.reply_text(
        f"🧠 QUIZ\n\n{question['question']}",
        reply_markup=InlineKeyboardMarkup(buttons),
    )


async def quiz_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if not context.user_data.get("quiz_active"):
        await query.edit_message_text(
            "Diese Quizrunde ist nicht mehr aktiv. Starte mit /quiz eine neue!"
        )
        return

    try:
        answer = int((query.data or "").split(":")[1])
    except (IndexError, ValueError):
        return

    correct = context.user_data.get("quiz_answer")
    context.user_data.pop("quiz_active", None)
    context.user_data.pop("quiz_answer", None)

    if answer == correct:
        points = database.add_points(query.from_user.id, 10)
        await query.edit_message_text(
            f"🎉 Richtig beantwortet!\n"
            f"Du bekommst 10 Punkte.\nPunktestand: {points}"
        )
    else:
        await query.edit_message_text(
            "Nicht ganz! 😊 Starte mit /quiz eine neue Runde."
        )


# ---------------- PUNKTE / RANGLISTE / DAILY ----------------

def leaderboard_text():
    with database.connect() as db:
        cur = db.cursor(dictionary=True)
        cur.execute("""
            SELECT a.name, a.username, p.amount
            FROM accounts AS a
            LEFT JOIN points AS p ON p.user_id = a.user_id
            WHERE a.suspended = 0
            ORDER BY COALESCE(p.amount, 0) DESC, a.name ASC
            LIMIT 10
        """)
        rows = cur.fetchall()
        cur.close()

    if not rows:
        return "🏆 Noch gibt es keine Einträge in der Rangliste."

    lines = ["🏆 RANGLISTE\n"]

    for index, row in enumerate(rows, 1):
        name = row.get("name") or row.get("username") or "Unbekannt"
        amount = row.get("amount") or 0
        lines.append(f"{index}. {name} — {amount} Punkte")

    return "\n".join(lines)


async def leaderboard_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.effective_message.reply_text(leaderboard_text())


async def daily_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not user:
        return

    success, total = database.claim_daily(user.id, 100)

    if not success:
        await update.effective_message.reply_text(
            "🎁 Deine Tagesbelohnung hast du heute schon abgeholt.\n"
            f"💰 Punktestand: {total}\n"
            "Morgen wartet die nächste Belohnung!"
        )
        return

    await update.effective_message.reply_text(
        "🎉 Deine tägliche Belohnung ist da!\n"
        "+100 Punkte\n"
        f"💰 Punktestand: {total}"
    )


# ---------------- PROFIL ----------------

async def setname_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not user:
        return

    name = " ".join(context.args).strip()

    if not name:
        await update.effective_message.reply_text(
            "Wie soll dein Name lauten? Schreib zum Beispiel /setname Alex."
        )
        return

    if len(name) > 50:
        await update.effective_message.reply_text(
            "Der Name darf höchstens 50 Zeichen haben."
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
            f"Alles klar! Dein Name ist jetzt {name}."
        )
    else:
        await update.effective_message.reply_text(
            "Ich finde noch kein Konto für dich. Starte bitte mit /register."
        )


async def setbio_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not user:
        return

    bio = " ".join(context.args).strip()

    if not bio:
        await update.effective_message.reply_text(
            "Was soll in deiner Bio stehen? Beispiel: /setbio Ich mag Spiele."
        )
        return

    if len(bio) > 200:
        await update.effective_message.reply_text(
            "Deine Bio darf höchstens 200 Zeichen haben."
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
        await update.effective_message.reply_text("✅ Bio aktualisiert!")
    else:
        await update.effective_message.reply_text(
            "Ich finde noch kein Konto für dich. Starte bitte mit /register."
        )


# ---------------- PROBLEME MELDEN ----------------

async def report_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not user:
        return

    message = " ".join(context.args).strip()

    if not message:
        await update.effective_message.reply_text(
            "Was ist passiert? Schreib es einfach hinter den Befehl:\n"
            "/report Beschreibe das Problem"
        )
        return

    if len(message) > 1000:
        await update.effective_message.reply_text(
            "Deine Meldung ist etwas lang. Bitte beschränke sie auf 1000 Zeichen."
        )
        return

    report_id = database.create_report(user.id, message)

    await update.effective_message.reply_text(
        f"✅ Danke für die Meldung! Ich habe sie unter #{report_id} gespeichert."
    )

    try:
        await context.bot.send_message(
            chat_id=OWNER_ID,
            text=(
                f"📩 Neue Meldung #{report_id}\n"
                f"Von: {user.full_name} (ID {user.id})\n\n{message}"
            ),
        )
    except Exception:
        pass


# ---------------- SUPPORT-DIALOG ----------------

async def support_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    msg = update.effective_message

    if not user or not msg:
        return

    message = " ".join(context.args).strip()

    if message:
        await _create_support_ticket(update, context, message)
        return

    context.user_data["support_waiting_for_message"] = True

    await msg.reply_text(
        f"Hey {user.first_name}! 😊\n\n"
        "Klar, ich helfe dir gern weiter.\n"
        "Erzähl mir einfach, was passiert ist oder wobei du Hilfe brauchst. "
        "Schreib deine nächste Nachricht hier in den Chat.\n\n"
        "Wenn du es dir anders überlegst, kannst du mit /supportcancel abbrechen."
    )


async def _create_support_ticket(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    message: str,
):
    user = update.effective_user
    msg = update.effective_message

    if not user or not msg:
        return

    message = message.strip()

    if not message:
        await msg.reply_text("Schreib mir bitte kurz, worum es geht.")
        return

    if len(message) > 3000:
        await msg.reply_text(
            "Deine Nachricht ist ziemlich lang. "
            "Bitte kürze sie auf höchstens 3000 Zeichen."
        )
        return

    try:
        ticket_id = database.create_ticket(user.id, message)
    except Exception:
        await msg.reply_text(
            "Oh, das Ticket konnte gerade nicht gespeichert werden. "
            "Bitte versuch es später noch einmal."
        )
        return

    context.user_data.pop("support_waiting_for_message", None)

    await msg.reply_text(
        "Alles klar, danke dir! 😊\n\n"
        f"Ich habe dein Anliegen als Ticket #{ticket_id} aufgenommen "
        "und an den Bot-Owner weitergeleitet. Sobald eine Antwort vorliegt, "
        "kann sie dir über den Support mitgeteilt werden."
    )

    try:
        await context.bot.send_message(
            chat_id=OWNER_ID,
            text=(
                f"📩 Neues Support-Ticket #{ticket_id}\n\n"
                f"Von: {user.full_name}\n"
                f"Username: @{user.username if user.username else 'nicht vorhanden'}\n"
                f"Telegram-ID: {user.id}\n\n"
                f"Anliegen:\n{message}\n\n"
                f"Antworten mit:\n/supportreply {ticket_id} Deine Antwort"
            ),
        )
    except Exception:
        pass


async def support_message_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    user = update.effective_user
    msg = update.effective_message

    if not user or not msg or not msg.text:
        return

    if not context.user_data.get("support_waiting_for_message"):
        return

    if msg.text.startswith("/"):
        return

    await _create_support_ticket(update, context, msg.text)


async def supportreply_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    user = update.effective_user
    msg = update.effective_message

    if not user or user.id != OWNER_ID:
        await msg.reply_text(
            "⛔ Nur der Bot-Owner kann Support-Tickets beantworten."
        )
        return

    if len(context.args) < 2:
        await msg.reply_text(
            "So kannst du antworten:\n/supportreply TICKET_ID Deine Antwort"
        )
        return

    try:
        ticket_id = int(context.args[0])
    except ValueError:
        await msg.reply_text("Die Ticket-ID muss eine Zahl sein.")
        return

    reply = " ".join(context.args[1:]).strip()

    if not reply:
        await msg.reply_text("Schreib bitte noch deine Antwort dazu.")
        return

    ticket = database.get_ticket(ticket_id)

    if not ticket:
        await msg.reply_text("Ich finde dieses Ticket leider nicht.")
        return

    if ticket.get("status") == "closed":
        await msg.reply_text("Dieses Ticket ist bereits geschlossen.")
        return

    if not database.reply_ticket(ticket_id, reply):
        await msg.reply_text("Die Antwort konnte nicht gespeichert werden.")
        return

    try:
        await context.bot.send_message(
            chat_id=ticket["user_id"],
            text=(
                f"💬 Es gibt eine Antwort zu deinem Support-Ticket #{ticket_id}:\n\n"
                f"{reply}"
            ),
        )
        await msg.reply_text(
            f"✅ Antwort zu Ticket #{ticket_id} wurde gesendet."
        )
    except Exception:
        await msg.reply_text(
            "Die Antwort wurde gespeichert, aber ich konnte sie dem Nutzer nicht zustellen."
        )


async def mytickets_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    user = update.effective_user

    if not user:
        return

    tickets = database.list_user_tickets(user.id, limit=10)

    if not tickets:
        await update.effective_message.reply_text(
            "Du hast noch keine Support-Tickets. Mit /support kannst du mir schreiben."
        )
        return

    lines = ["📨 DEINE SUPPORT-TICKETS\n"]

    for ticket in tickets:
        lines.append(
            f"#{ticket['id']} — {ticket['status']} — "
            f"{str(ticket['message'])[:120]}"
        )

    await update.effective_message.reply_text("\n".join(lines))


async def supportcancel_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    was_waiting = context.user_data.pop("support_waiting_for_message", None)

    if was_waiting:
        await update.effective_message.reply_text(
            "Alles klar, ich habe den Support-Dialog abgebrochen. "
            "Wenn du später Hilfe brauchst, schreib einfach /support."
        )
    else:
        await update.effective_message.reply_text(
            "Es gibt gerade keinen offenen Support-Dialog."
        )


# ---------------- STATISTIK / HILFE ----------------

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.effective_message.reply_text(
        f"📊 Registrierte Accounts: {database.account_count()}\n"
        f"⛔ Gesperrte Accounts: {database.suspended_count()}"
    )


async def games_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.effective_message.reply_text(
        "🎮 MINI-SPIELE\n\n"
        "/roll – Würfeln\n"
        "/coinflip – Münzwurf\n"
        "/guess – Zahl erraten\n"
        "/rps schere|stein|papier – Schere, Stein, Papier\n"
        "/quiz – Quizfrage\n\n"
        "Bei richtigen Antworten kannst du Punkte verdienen!"
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.effective_message.reply_text(
        "📚 LOL STUDIOS MANAGER\n\n"
        "/menu – Hauptmenü\n"
        "/profile – Profil anzeigen\n"
        "/ping – Bot testen\n"
        "/id oder /myid – Telegram-ID anzeigen\n"
        "/about – Über den Bot\n"
        "/rules – Regeln\n"
        "/games – Spiele\n"
        "/roll – Würfeln\n"
        "/coinflip – Münzwurf\n"
        "/guess – Zahl erraten\n"
        "/rps schere|stein|papier – Spiel gegen den Bot\n"
        "/quiz – Quiz\n"
        "/daily – tägliche Punkte\n"
        "/leaderboard – Rangliste\n"
        "/setname NAME – Namen ändern\n"
        "/setbio TEXT – Bio ändern\n"
        "/report TEXT – Problem melden\n"
        "/support – Support-Dialog starten\n"
        "/supportcancel – Support-Dialog abbrechen\n"
        "/mytickets – eigene Tickets anzeigen"
    )


# ---------------- HANDLER REGISTRIEREN ----------------

def register_feature_handlers(application: Application):
    application.add_handler(
        CommandHandler("menu", menu_command),
        group=1,
    )

    application.add_handler(
        CallbackQueryHandler(menu_callback, pattern=r"^menu:"),
        group=1,
    )

    application.add_handler(
        CallbackQueryHandler(moderation_callback, pattern=r"^mod:"),
        group=1,
    )

    application.add_handler(
        CallbackQueryHandler(quiz_callback, pattern=r"^quiz:"),
        group=1,
    )

    commands = [
        ("ping", ping_command),
        ("about", about_command),
        ("rules", rules_command),
        ("id", id_command),
        ("roll", roll_command),
        ("coinflip", coinflip_command),
        ("guess", guess_answer),
        ("rps", rps_command),
        ("quiz", quiz_command),
        ("daily", daily_command),
        ("leaderboard", leaderboard_command),
        ("setname", setname_command),
        ("setbio", setbio_command),
        ("report", report_command),
        ("support", support_command),
        ("supportreply", supportreply_command),
        ("mytickets", mytickets_command),
        ("supportcancel", supportcancel_command),
        ("stats", stats_command),
        ("games", games_command),
        ("help", help_command),
    ]

    for name, callback in commands:
        application.add_handler(
            CommandHandler(name, callback),
            group=1,
        )

    application.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND & filters.ChatType.PRIVATE,
            support_message_handler,
        ),
        group=2,
    )
