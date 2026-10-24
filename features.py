
# features.py — LOL Studios Manager v5.0.0

import random
import time

import database
from config import (
    BOT_NAME,
    BOT_VERSION,
    OWNER_ID,
    REWARDS,
    COMMUNITY_RULES,
    MAX_GIFT_POINTS,
    MAX_SUPPORT_LENGTH,
)
from permissions import is_owner
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
)


def keyboard(rows):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(label, callback_data=data) for label, data in row]
        for row in rows
    ])


def main_keyboard():
    return keyboard([
        [("👤 Profil", "menu:profile"), ("🏆 Ränge", "menu:ranks")],
        [("🎮 Fun & Games", "menu:fun"), ("💰 Economy", "menu:economy")],
        [("🎰 Casino", "menu:casino"), ("🎁 Rewards", "menu:rewards")],
        [("🎫 Support", "menu:support"), ("🔒 Datenschutz", "menu:privacy")],
        [("📋 Patchnotes", "menu:patchnotes"), ("ℹ️ Über uns", "menu:about")],
        [("🛡️ Admin", "menu:admin")],
    ])


def back_keyboard(target="home"):
    return keyboard([[("⬅️ Zurück", f"menu:{target}")]])


async def menu_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    section = context.args[0].lower() if context.args else "home"
    await show_menu(update.effective_message, section, update.effective_user.id)


async def show_menu(message, section, user_id):
    if section in ("home", "start"):
        await message.reply_text(
            f"🌩️ {BOT_NAME.upper()}\n"
            f"Version {BOT_VERSION}\n\n"
            "Wähle einen Bereich:",
            reply_markup=main_keyboard(),
        )
        return

    if section in ("fun", "games"):
        text = (
            "🎮 FUN & GAMES\n\n"
            "/roll – Würfeln\n"
            "/coinflip – Münzwurf\n"
            "/guess – Zahl erraten\n"
            "/afk [Grund] – AFK-Status setzen\n"
            "/streak – Reward-Status ansehen"
        )
        await message.reply_text(text, reply_markup=back_keyboard())
        return

    if section == "economy":
        await message.reply_text(
            "💰 ECONOMY\n\n"
            "/points – Punktestand\n"
            "/daily – tägliche Belohnung\n"
            "/weekly – wöchentliche Belohnung\n"
            "/monthly – monatliche Belohnung\n"
            "/yearly – jährliche Belohnung\n"
            "/history – Punkteverlauf\n"
            "/leaderboard – Rangliste\n"
            "/gift ID Anzahl – Punkte verschenken",
            reply_markup=back_keyboard(),
        )
        return

    if section == "rewards":
        await message.reply_text(
            "🎁 REWARDS\n\n"
            f"☀️ Daily: {REWARDS['daily']} Punkte\n"
            f"📅 Weekly: {REWARDS['weekly']} Punkte\n"
            f"🗓️ Monthly: {REWARDS['monthly']} Punkte\n"
            f"🎆 Yearly: {REWARDS['yearly']} Punkte\n\n"
            "Belohnungen kannst du über die Commands abholen.",
            reply_markup=back_keyboard(),
        )
        return

    if section == "casino":
        await message.reply_text(
            "🎰 VIRTUELLES PUNKTE-CASINO\n\n"
            "/casino – Spielregeln und Optionen\n"
            "/coinflip – kostenloser Münzwurf\n\n"
            "Hier gibt es keine Echtgeld-Einsätze oder Auszahlungen.",
            reply_markup=back_keyboard(),
        )
        return

    if section == "support":
        await message.reply_text(
            "🎫 SUPPORT\n\n"
            "/support Nachricht – Ticket erstellen\n"
            "/ticket ID – eigenes Ticket ansehen\n"
            "/tos – Nutzungsregeln\n"
            "/gdpr – Datenschutzhinweise",
            reply_markup=back_keyboard(),
        )
        return

    if section == "privacy":
        await message.reply_text(
            "🔒 DATENSCHUTZ\n\n"
            "/permissions – Berechtigungen\n"
            "/policy – Sicherheitsregeln\n"
            "/optout – nicht notwendige Funktionen abschalten\n"
            "/gdpr – Datenschutzhinweise",
            reply_markup=back_keyboard(),
        )
        return

    if section == "ranks":
        await message.reply_text(
            "🏆 RÄNGE\n\n"
            "/rank – dein Rang\n"
            "/ranks – Rangliste\n"
            "/team – Team-Zugehörigkeit\n"
            "/leaderboard – Punkte-Rangliste",
            reply_markup=back_keyboard(),
        )
        return

    if section == "profile":
        account = database.get_account(user_id)
        if not account:
            await message.reply_text(
                "🔒 Bitte zuerst /register ausführen.",
                reply_markup=back_keyboard(),
            )
            return

        await message.reply_text(
            "👤 DEIN PROFIL\n\n"
            f"Name: {account.get('name') or 'Nicht gesetzt'}\n"
            f"Bio: {account.get('bio') or 'Keine Bio'}\n"
            f"Altersgruppe: {account.get('agegroup') or 'Nicht angegeben'}\n"
            f"Punkte: {database.get_points(user_id)}\n\n"
            "/me – vollständiges Profil\n"
            "/setname Neuer Name\n"
            "/setbio Neue Bio",
            reply_markup=back_keyboard(),
        )
        return

    if section == "patchnotes":
        await message.reply_text(
            f"📋 PATCHNOTES — v{BOT_VERSION}\n\n"
            "• Neues Hauptmenü\n"
            "• Mehr Economy- und Reward-Commands\n"
            "• Support-Tickets\n"
            "• AFK- und Datenschutz-Einstellungen\n"
            "• Verbesserte Admin-Bereiche",
            reply_markup=back_keyboard(),
        )
        return

    if section == "about":
        await message.reply_text(
            f"🌩️ {BOT_NAME}\n\n"
            "Ein Community-Bot von LOL Studios.\n"
            f"Aktuelle Version: {BOT_VERSION}",
            reply_markup=back_keyboard(),
        )
        return

    if section == "admin":
        if not is_owner(user_id):
            await message.reply_text("⛔ Nur der Owner darf das Admin-Center öffnen.")
            return
        await message.reply_text(
            "🛡️ ADMIN-CENTER\n\n/admin – Admin-Menü\n/stats – Bot-Statistiken",
            reply_markup=back_keyboard(),
        )
        return

    await message.reply_text(
        "Dieser Menübereich wurde nicht gefunden.",
        reply_markup=back_keyboard(),
    )


async def menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    section = (query.data or "menu:home").split(":", 1)[-1]

    # Menüs werden als neue Nachricht dargestellt, damit es auch dann
    # funktioniert, wenn das ursprüngliche Menü nicht bearbeitet werden kann.
    await show_menu(query.message, section, query.from_user.id)


async def ping_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    start = time.monotonic()
    msg = await update.effective_message.reply_text("🏓 Pong!")
    ms = round((time.monotonic() - start) * 1000)
    await msg.edit_text(f"🏓 Pong!\n⚡ Antwortzeit: {ms} ms")


async def about_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.effective_message.reply_text(
        f"🌩️ {BOT_NAME}\nVersion {BOT_VERSION}\nCommunity-Bot von LOL Studios."
    )


async def rules_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.effective_message.reply_text(
        "📜 COMMUNITY-REGELN\n\n" +
        "\n".join(f"{i}. {rule}" for i, rule in enumerate(COMMUNITY_RULES, 1))
    )


async def tos_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.effective_message.reply_text(
        "📜 NUTZUNGSREGELN\n\n"
        "Nutze den Bot respektvoll und missbrauche keine Funktionen. "
        "Punkte sind virtuelle Bot-Punkte und haben keinen Echtgeldwert. "
        "Bei Problemen nutze /support.\n\n"
        "Dies ist eine allgemeine Bot-Regelübersicht und keine Rechtsberatung."
    )


async def gdpr_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.effective_message.reply_text(
        "🔒 DATENSCHUTZHINWEISE\n\n"
        "Der Bot speichert für seine Funktionen Telegram-IDs, Profilangaben, "
        "Punktestände und nötige Funktionsdaten in einer MySQL-Datenbank.\n\n"
        "Nutze /unregister, um dein Bot-Profil und zugehörige Daten zu löschen. "
        "Technische Protokolle oder gesetzlich erforderliche Aufbewahrung "
        "können gesondert behandelt werden. Frage den Betreiber bei Anliegen "
        "über /support."
    )


async def permissions_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.effective_message.reply_text(
        "🔑 BERECHTIGUNGEN\n\n"
        "• Normale Nutzer: Profil, Spiele, Rewards und Support\n"
        "• Team: nur ausdrücklich freigegebene Team-Funktionen\n"
        "• Owner: Admin-Center und Nutzerverwaltung\n\n"
        "Berechtigungen werden auf dem Server geprüft."
    )


async def policy_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.effective_message.reply_text(
        "🛡️ BOT SAFETY POLICY\n\n"
        "• Kein Zugriff auf fremde Konten\n"
        "• Keine Umgehung von Sperren\n"
        "• Keine Weitergabe von Zugangsdaten\n"
        "• Keine Echtgeld-Casino-Funktionen\n"
        "• Support-Anfragen werden verantwortungsvoll behandelt"
    )


async def optout_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    current = database.get_optout(user.id)
    database.set_optout(user.id, not current)

    if current:
        text = (
            "✅ Opt-out deaktiviert. Nicht notwendige optionale Funktionen "
            "können wieder verwendet werden."
        )
    else:
        text = (
            "🔒 Opt-out aktiviert. Optionale Funktionen werden, soweit "
            "implementiert, abgeschaltet. Kernfunktionen wie Sicherheit "
            "und notwendige Datenbankeinträge bleiben bestehen."
        )

    await update.effective_message.reply_text(text)


async def points_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await update.effective_message.reply_text(
        f"💰 Dein Punktestand: {database.get_points(user.id)} Punkte"
    )


async def reward_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    reward_type = update.effective_message.text.split()[0].split("@")[0][1:].lower()
    amount = REWARDS.get(reward_type)

    if amount is None:
        await update.effective_message.reply_text("Unbekannte Belohnung.")
        return

    success, total = database.claim_reward(user.id, reward_type, amount)

    if success:
        await update.effective_message.reply_text(
            f"🎁 {reward_type.title()} abgeholt!\n"
            f"Du erhältst {amount} Punkte.\n"
            f"💰 Neuer Punktestand: {total}"
        )
    else:
        await update.effective_message.reply_text(
            f"⏳ Deine {reward_type.title()}-Belohnung wurde in diesem Zeitraum "
            f"bereits abgeholt.\n💰 Punktestand: {total}"
        )


async def daily_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await reward_command(update, context)


async def weekly_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await reward_command(update, context)


async def monthly_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await reward_command(update, context)


async def yearly_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await reward_command(update, context)


async def leaderboard_text():
    rows = database.leaderboard(10)
    if not rows:
        return "🏆 Noch gibt es keine Ranglisten-Einträge."

    lines = ["🏆 PUNKTE-RANGLISTE"]
    for index, row in enumerate(rows, 1):
        name = row.get("name") or row.get("username") or str(row["user_id"])
        lines.append(f"{index}. {name} — {row['amount']} Punkte")
    return "\n".join(lines)


async def leaderboard_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.effective_message.reply_text(await leaderboard_text())


async def rank_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await update.effective_message.reply_text(
        f"🏆 Dein Rang: #{database.get_rank(user.id)}\n"
        f"💰 Punkte: {database.get_points(user.id)}"
    )


async def team_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await update.effective_message.reply_text(
        f"👥 Deine Team-Zugehörigkeit: {database.get_team(user.id)}"
    )


async def afk_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    reason = " ".join(context.args).strip() or "AFK"
    database.set_afk(user.id, reason)
    await update.effective_message.reply_text(
        f"💤 AFK-Status aktiviert.\nGrund: {reason[:255]}"
    )


async def streak_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.effective_message.reply_text(
        "🎁 Deine Rewards:\n"
        f"Daily: {REWARDS['daily']} Punkte\n"
        f"Weekly: {REWARDS['weekly']} Punkte\n"
        f"Monthly: {REWARDS['monthly']} Punkte\n"
        f"Yearly: {REWARDS['yearly']} Punkte\n\n"
        "Nutze /daily, /weekly, /monthly oder /yearly."
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
        "🔢 Ich habe eine Zahl von 1 bis 10 gewählt. "
        "Rate mit /guess Zahl."
    )


async def guess_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    target = context.user_data.get("guess_number")
    if target is None:
        await guess_command(update, context)
        return

    if not context.args:
        await update.effective_message.reply_text("Verwendung: /guess Zahl")
        return

    try:
        number = int(context.args[0])
    except ValueError:
        await update.effective_message.reply_text("Bitte gib eine Zahl von 1 bis 10 ein.")
        return

    if not 1 <= number <= 10:
        await update.effective_message.reply_text("Die Zahl muss zwischen 1 und 10 liegen.")
        return

    if number == target:
        context.user_data.pop("guess_number", None)
        await update.effective_message.reply_text("🎉 Richtig geraten!")
    else:
        await update.effective_message.reply_text("❌ Leider falsch. Versuch es erneut!")


async def casino_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.effective_message.reply_text(
        "🎰 Virtuelles Punkte-Casino\n\n"
        "Hier gibt es keine Echtgeld-Einsätze oder Auszahlungen. "
        "Nutze /coinflip für einen kostenlosen Münzwurf."
    )


async def history_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    rows = database.get_history(user.id, 10)

    if not rows:
        await update.effective_message.reply_text("📜 Noch keine Punktebewegungen.")
        return

    lines = ["📜 DEIN PUNKTEVERLAUF"]
    for row in rows:
        sign = "+" if row["amount"] > 0 else ""
        lines.append(
            f"{sign}{row['amount']} — {row['reason']} ({row['created_at']})"
        )

    await update.effective_message.reply_text("\n".join(lines))


async def gift_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    if len(context.args) != 2:
        await update.effective_message.reply_text(
            "Verwendung: /gift Telegram-ID Anzahl"
        )
        return

    try:
        target_id = int(context.args[0])
        amount = int(context.args[1])
    except ValueError:
        await update.effective_message.reply_text("ID und Anzahl müssen Zahlen sein.")
        return

    if target_id == user.id or amount <= 0 or amount > MAX_GIFT_POINTS:
        await update.effective_message.reply_text("Ungültiger Empfänger oder Betrag.")
        return

    if not database.is_registered(target_id):
        await update.effective_message.reply_text("Der Empfänger ist nicht registriert.")
        return

    if database.is_suspended(target_id):
        await update.effective_message.reply_text("Der Empfänger ist gesperrt.")
        return

    with database.connect() as db:
        cur = db.cursor()
        try:
            cur.execute(
                "SELECT amount FROM points WHERE user_id = %s FOR UPDATE",
                (user.id,),
            )
            row = cur.fetchone()
            balance = int(row[0]) if row else 0

            if balance < amount:
                await update.effective_message.reply_text("Du hast nicht genug Punkte.")
                return

            cur.execute(
                "UPDATE points SET amount = amount - %s WHERE user_id = %s",
                (amount, user.id),
            )
            cur.execute(
                """
                INSERT INTO points (user_id, amount) VALUES (%s, %s)
                ON DUPLICATE KEY UPDATE amount = amount + %s
                """,
                (target_id, amount, amount),
            )
            cur.execute(
                """
                INSERT INTO point_history (user_id, amount, reason)
                VALUES (%s, %s, %s), (%s, %s, %s)
                """,
                (
                    user.id, -amount, f"Geschenk an {target_id}",
                    target_id, amount, f"Geschenk von {user.id}",
                ),
            )
        finally:
            cur.close()

    await update.effective_message.reply_text(
        f"🎁 Du hast {amount} Punkte an {target_id} verschenkt."
    )


async def support_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    message = " ".join(context.args).strip()

    if not message:
        await update.effective_message.reply_text(
            "Verwendung: /support Beschreibe dein Anliegen"
        )
        return

    if len(message) > MAX_SUPPORT_LENGTH:
        await update.effective_message.reply_text(
            f"Deine Nachricht darf höchstens {MAX_SUPPORT_LENGTH} Zeichen haben."
        )
        return

    ticket_id = database.create_ticket(user.id, message)
    await update.effective_message.reply_text(
        f"🎫 Ticket #{ticket_id} erstellt.\n"
        f"Mit /ticket {ticket_id} kannst du den Status ansehen."
    )

    try:
        await context.bot.send_message(
            chat_id=OWNER_ID,
            text=(
                f"🎫 Neues Support-Ticket #{ticket_id}\n"
                f"Nutzer-ID: {user.id}\n\n{message}\n\n"
                f"Antwort: /ticketreply {ticket_id} Deine Antwort"
            ),
        )
    except Exception:
        pass


async def ticket_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    if not context.args:
        await update.effective_message.reply_text("Verwendung: /ticket ID")
        return

    try:
        ticket_id = int(context.args[0])
    except ValueError:
        await update.effective_message.reply_text("Die Ticket-ID muss eine Zahl sein.")
        return

    ticket = database.get_ticket(ticket_id)
    if not ticket:
        await update.effective_message.reply_text("Ticket nicht gefunden.")
        return

    if ticket["user_id"] != user.id and not is_owner(user.id):
        await update.effective_message.reply_text("⛔ Du darfst dieses Ticket nicht ansehen.")
        return

    await update.effective_message.reply_text(
        f"🎫 Ticket #{ticket['id']}\n"
        f"Status: {ticket['status']}\n"
        f"Nachricht: {ticket['message']}\n"
        f"Antwort: {ticket['reply'] or 'Noch keine Antwort'}"
    )


async def ticketreply_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    if not is_owner(user.id):
        await update.effective_message.reply_text("⛔ Nur der Owner darf Tickets beantworten.")
        return

    if len(context.args) < 2:
        await update.effective_message.reply_text(
            "Verwendung: /ticketreply ID Deine Antwort"
        )
        return

    try:
        ticket_id = int(context.args[0])
    except ValueError:
        await update.effective_message.reply_text("Ungültige Ticket-ID.")
        return

    reply = " ".join(context.args[1:])
    ticket = database.get_ticket(ticket_id)

    if not ticket:
        await update.effective_message.reply_text("Ticket nicht gefunden.")
        return

    if not database.reply_ticket(ticket_id, reply):
        await update.effective_message.reply_text("Antwort konnte nicht gespeichert werden.")
        return

    await update.effective_message.reply_text(f"✅ Antwort für Ticket #{ticket_id} gespeichert.")

    try:
        await context.bot.send_message(
            chat_id=ticket["user_id"],
            text=f"📩 Antwort auf dein Ticket #{ticket_id}:\n\n{reply}",
        )
    except Exception:
        pass


async def unregister_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not database.is_registered(user.id):
        await update.effective_message.reply_text("Du hast kein registriertes Konto.")
        return

    # Sicherheitsabfrage vor dem endgültigen Löschen
    await update.effective_message.reply_text(
        "⚠️ Möchtest du dein Bot-Profil und zugehörige Daten wirklich löschen?\n"
        "Wenn ja, bestätige mit /unregister_confirm."
    )


async def unregister_confirm_command(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    user = update.effective_user
    if not database.is_registered(user.id):
        await update.effective_message.reply_text("Du hast kein registriertes Konto.")
        return

    database.unregister_account(user.id)
    await update.effective_message.reply_text(
        "✅ Dein Bot-Profil und zugehörige Daten wurden gelöscht."
    )


async def report_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    message = " ".join(context.args).strip()

    if not message:
        await update.effective_message.reply_text("Verwendung: /report Beschreibe das Problem")
        return

    report_id = database.create_report(user.id, message)
    await update.effective_message.reply_text(f"✅ Meldung #{report_id} gespeichert.")


async def setname_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    name = " ".join(context.args).strip()

    if not name or len(name) > 40:
        await update.effective_message.reply_text("Verwendung: /setname Neuer Name (max. 40 Zeichen)")
        return

    with database.connect() as db:
        cur = db.cursor()
        try:
            cur.execute(
                "UPDATE accounts SET name = %s WHERE user_id = %s",
                (name, user.id),
            )
            exists = cur.rowcount > 0
        finally:
            cur.close()

    if exists or database.is_registered(user.id):
        await update.effective_message.reply_text(f"✅ Dein Name lautet jetzt: {name}")
    else:
        await update.effective_message.reply_text("Bitte zuerst /register ausführen.")


async def setbio_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    bio = " ".join(context.args).strip()

    if len(bio) > 250:
        await update.effective_message.reply_text("Die Bio darf höchstens 250 Zeichen lang sein.")
        return

    with database.connect() as db:
        cur = db.cursor()
        try:
            cur.execute(
                "UPDATE accounts SET bio = %s WHERE user_id = %s",
                (bio, user.id),
            )
            exists = cur.rowcount > 0
        finally:
            cur.close()

    if exists or database.is_registered(user.id):
        await update.effective_message.reply_text("✅ Deine Bio wurde aktualisiert.")
    else:
        await update.effective_message.reply_text("Bitte zuerst /register ausführen.")


async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not is_owner(user.id):
        await update.effective_message.reply_text("⛔ Nur der Owner darf Statistiken sehen.")
        return

    await update.effective_message.reply_text(
        f"📊 Registrierte Accounts: {database.account_count()}\n"
        f"⛔ Gesperrte Accounts: {database.suspended_count()}"
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.effective_message.reply_text(
        "📚 LOL STUDIOS MANAGER — COMMANDS\n\n"
        "/start /menu /help\n"
        "/register /unregister /unregister_confirm\n"
        "/me /profile /setname /setbio\n"
        "/rank /ranks /team /afk /ping\n"
        "/roll /coinflip /guess /casino\n"
        "/points /daily /weekly /monthly /yearly\n"
        "/leaderboard /history /gift\n"
        "/support /ticket /ticketreply /report\n"
        "/tos /gdpr /permissions /policy /optout\n"
        "/patchnotes /about /rules\n"
        "/admin /stats"
    )


async def patchnotes_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.effective_message.reply_text(
        f"📋 PATCHNOTES v{BOT_VERSION}\n\n"
        "• Menü mit Unterbereichen\n"
        "• Daily, Weekly, Monthly und Yearly Rewards\n"
        "• AFK, Ränge und Punkteverlauf\n"
        "• Support-Tickets\n"
        "• Datenschutz- und Sicherheitsbefehle"
    )


async def games_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await show_menu(update.effective_message, "fun", update.effective_user.id)


def register_feature_handlers(application: Application):
    application.add_handler(CommandHandler("menu", menu_command), group=1)
    application.add_handler(
        CallbackQueryHandler(menu_callback, pattern=r"^menu:"),
        group=1,
    )

    commands = [
        ("ping", ping_command),
        ("about", about_command),
        ("rules", rules_command),
        ("tos", tos_command),
        ("gdpr", gdpr_command),
        ("permissions", permissions_command),
        ("policy", policy_command),
        ("optout", optout_command),
        ("roll", roll_command),
        ("coinflip", coinflip_command),
        ("guess", guess_answer),
        ("daily", daily_command),
        ("weekly", weekly_command),
        ("monthly", monthly_command),
        ("yearly", yearly_command),
        ("points", points_command),
        ("rank", rank_command),
        ("ranks", leaderboard_command),
        ("team", team_command),
        ("afk", afk_command),
        ("streak", streak_command),
        ("casino", casino_command),
        ("history", history_command),
        ("gift", gift_command),
        ("support", support_command),
        ("ticket", ticket_command),
        ("ticketreply", ticketreply_command),
        ("unregister", unregister_command),
        ("unregister_confirm", unregister_confirm_command),
        ("report", report_command),
        ("setname", setname_command),
        ("setbio", setbio_command),
        ("stats", stats_command),
        ("leaderboard", leaderboard_command),
        ("help", help_command),
        ("patchnotes", patchnotes_command),
        ("games", games_command),
    ]

    for name, callback in commands:
        application.add_handler(CommandHandler(name, callback), group=1)
