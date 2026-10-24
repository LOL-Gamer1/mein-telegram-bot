# owner_commands.py — globale Owner-Werkzeuge für LOL Studios Manager

import time

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, CallbackQueryHandler, ContextTypes

import database
from config import OWNER_ID


async def owner_startup(application):
    application.bot_data["started_at"] = time.time()


def owner_only(update: Update) -> bool:
    user = update.effective_user
    return bool(user and user.id == OWNER_ID)


async def denied(update: Update):
    msg = update.effective_message
    if msg:
        await msg.reply_text("⛔ Dieser Befehl ist nur für den Bot-Owner.")


def _target_id(update, context):
    msg = update.effective_message

    if msg and msg.reply_to_message and msg.reply_to_message.from_user:
        return msg.reply_to_message.from_user.id

    if context.args:
        try:
            return int(context.args[0])
        except (ValueError, TypeError):
            return None

    return None


async def id_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message

    if not msg:
        return

    if msg.reply_to_message and msg.reply_to_message.from_user:
        target = msg.reply_to_message.from_user
    else:
        target = update.effective_user

    if context.args:
        await msg.reply_text(
            "ℹ️ Eine Telefonnummer kann nicht zuverlässig in eine Telegram-ID "
            "umgewandelt werden.\n\n"
            "Nutze /id ohne Argument für deine eigene ID oder antworte mit "
            "/id auf eine Nachricht der Person."
        )
        return

    if target:
        await msg.reply_text(
            f"🆔 Telegram-ID: {target.id}\n"
            f"Name: {target.full_name}\n"
            f"Username: @{target.username or 'nicht gesetzt'}"
        )


async def ban_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not owner_only(update):
        await denied(update)
        return

    target = _target_id(update, context)

    if target is None:
        await update.effective_message.reply_text(
            "Verwendung: /ban TELEGRAM_ID oder antworte mit /ban auf eine Nachricht."
        )
        return

    if target == OWNER_ID:
        await update.effective_message.reply_text(
            "⛔ Der Owner kann nicht gesperrt werden."
        )
        return

    if not database.get_account(target):
        await update.effective_message.reply_text(
            "Kein registrierter Bot-Account mit dieser ID gefunden."
        )
        return

    changed = database.set_suspended(target, True)

    await update.effective_message.reply_text(
        f"⛔ Bot-Account {target} wurde gesperrt."
        if changed
        else "Account nicht gefunden."
    )

    try:
        await context.bot.send_message(
            target,
            "⛔ Dein LOL Studios Manager Account wurde vom Owner gesperrt.",
        )
    except Exception:
        pass


async def unban_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not owner_only(update):
        await denied(update)
        return

    target = _target_id(update, context)

    if target is None:
        await update.effective_message.reply_text(
            "Verwendung: /unban TELEGRAM_ID"
        )
        return

    changed = database.set_suspended(target, False)

    await update.effective_message.reply_text(
        f"✅ Account {target} entsperrt."
        if changed
        else "Kein passender Account gefunden."
    )


async def userinfo_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not owner_only(update):
        await denied(update)
        return

    target = _target_id(update, context)

    if target is None:
        await update.effective_message.reply_text(
            "Verwendung: /userinfo TELEGRAM_ID"
        )
        return

    account = database.get_account(target)

    if not account:
        await update.effective_message.reply_text("Account nicht gefunden.")
        return

    await update.effective_message.reply_text(
        "👤 ACCOUNT-INFO\n"
        f"Name: {account.get('name') or '—'}\n"
        f"Username: @{account.get('username') or '—'}\n"
        f"ID: {account['user_id']}\n"
        f"Altersgruppe: {account.get('agegroup') or '—'}\n"
        f"Registriert: {account.get('registered_at') or '—'}\n"
        f"Gesperrt: {'Ja' if account.get('suspended') else 'Nein'}\n"
        f"Punkte: {database.get_points(target)}"
    )


async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not owner_only(update):
        await denied(update)
        return

    total = database.account_count()
    suspended = database.suspended_count()

    await update.effective_message.reply_text(
        "📊 BOT-STATS\n"
        f"Registrierte Accounts: {total}\n"
        f"Gesperrte Accounts: {suspended}\n"
        f"Aktive Accounts: {total - suspended}"
    )


async def health_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not owner_only(update):
        await denied(update)
        return

    try:
        with database.connect() as db:
            cur = db.cursor()
            cur.execute("SELECT 1")
            cur.fetchone()
            cur.close()

        db_text = "✅ MySQL erreichbar"

    except Exception as exc:
        db_text = f"❌ MySQL-Fehler: {type(exc).__name__}"

    started_at = context.application.bot_data.get(
        "started_at",
        time.time(),
    )
    uptime = int(time.time() - started_at)

    await update.effective_message.reply_text(
        f"🩺 BOT HEALTH\n{db_text}\n⏱️ Laufzeit: {uptime} Sekunden"
    )


async def botinfo_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not owner_only(update):
        await denied(update)
        return

    me = await context.bot.get_me()

    await update.effective_message.reply_text(
        f"🤖 {me.first_name}\n"
        f"Username: @{me.username or '—'}\n"
        f"Bot-ID: {me.id}\n"
        f"Owner-ID: {OWNER_ID}\n"
        "Bibliothek: python-telegram-bot"
    )


async def points_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not owner_only(update):
        await denied(update)
        return

    if len(context.args) != 2:
        await update.effective_message.reply_text(
            "Verwendung:\n"
            "/givepoints ID ANZAHL\n"
            "/removepoints ID ANZAHL"
        )
        return

    try:
        target = int(context.args[0])
        amount = int(context.args[1])
    except ValueError:
        await update.effective_message.reply_text(
            "ID und Anzahl müssen Zahlen sein."
        )
        return

    if amount <= 0 or amount > 1_000_000_000:
        await update.effective_message.reply_text(
            "Die Anzahl muss zwischen 1 und 1.000.000.000 liegen."
        )
        return

    command = update.effective_message.text.split()[0].split("@")[0].lower()

    if command == "/removepoints":
        amount = -amount

    total = database.add_points(target, amount)

    await update.effective_message.reply_text(
        f"✅ Punkte angepasst.\nAccount: {target}\nNeuer Stand: {total}"
    )


async def setbio_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not owner_only(update):
        await denied(update)
        return

    if len(context.args) < 2:
        await update.effective_message.reply_text(
            "Verwendung: /setbio TELEGRAM_ID neue Bio"
        )
        return

    try:
        target = int(context.args[0])
    except ValueError:
        await update.effective_message.reply_text("Die ID muss eine Zahl sein.")
        return

    bio = " ".join(context.args[1:])[:250]

    with database.connect() as db:
        cur = db.cursor()
        cur.execute(
            "UPDATE accounts SET bio=%s WHERE user_id=%s",
            (bio, target),
        )
        changed = cur.rowcount
        cur.close()

    await update.effective_message.reply_text(
        "✅ Bio aktualisiert." if changed else "Account nicht gefunden."
    )


async def resetprofile_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    if not owner_only(update):
        await denied(update)
        return

    target = _target_id(update, context)

    if target is None:
        await update.effective_message.reply_text(
            "Verwendung: /resetprofile TELEGRAM_ID"
        )
        return

    if target == OWNER_ID:
        await update.effective_message.reply_text(
            "⛔ Das Owner-Profil wird nicht zurückgesetzt."
        )
        return

    with database.connect() as db:
        cur = db.cursor()
        cur.execute(
            "UPDATE accounts SET bio='', avatar='', agegroup='' WHERE user_id=%s",
            (target,),
        )
        changed = cur.rowcount
        cur.close()

    await update.effective_message.reply_text(
        "✅ Bio, Avatar und Altersgruppe zurückgesetzt."
        if changed
        else "Account nicht gefunden."
    )


async def broadcast_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not owner_only(update):
        await denied(update)
        return

    text = " ".join(context.args).strip()

    if not text:
        await update.effective_message.reply_text(
            "Verwendung: /broadcast Deine Nachricht"
        )
        return

    with database.connect() as db:
        cur = db.cursor()
        cur.execute("SELECT user_id FROM accounts WHERE suspended=0")
        ids = [row[0] for row in cur.fetchall()]
        cur.close()

    await update.effective_message.reply_text(
        f"📣 Broadcast startet an {len(ids)} aktive Accounts."
    )

    sent = 0
    failed = 0

    for user_id in ids:
        try:
            await context.bot.send_message(
                user_id,
                f"📣 Nachricht von LOL Studios\n\n{text}",
            )
            sent += 1
        except Exception:
            failed += 1

    await update.effective_message.reply_text(
        f"Broadcast beendet.\n✅ Gesendet: {sent}\n⚠️ Nicht erreichbar: {failed}"
    )


async def maintenance_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    if not owner_only(update):
        await denied(update)
        return

    if not context.args or context.args[0].lower() not in {"on", "off"}:
        await update.effective_message.reply_text(
            "Verwendung: /maintenance on oder /maintenance off"
        )
        return

    enabled = context.args[0].lower() == "on"
    context.application.bot_data["maintenance_mode"] = enabled

    await update.effective_message.reply_text(
        "🛠️ Wartungsmodus eingeschaltet."
        if enabled
        else "✅ Wartungsmodus ausgeschaltet."
    )


async def ownerhelp_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not owner_only(update):
        await denied(update)
        return

    await update.effective_message.reply_text(
        "👑 OWNER-BEFEHLE\n\n"
        "/id – ID anzeigen\n"
        "/ban ID – Bot-Account sperren\n"
        "/unban ID – entsperren\n"
        "/userinfo ID – Accountinfos\n"
        "/stats – Statistiken\n"
        "/health – MySQL und Laufzeit prüfen\n"
        "/botinfo – Botinfos\n"
        "/givepoints ID ANZAHL\n"
        "/removepoints ID ANZAHL\n"
        "/setbio ID TEXT\n"
        "/resetprofile ID\n"
        "/broadcast TEXT\n"
        "/maintenance on|off\n"
        "/join TELEGRAM_GRUPPENLINK\n\n"
        "Hinweis: /ban sperrt nur den Zugang zu diesem Bot. "
        "Telefonnummern lassen sich nicht in Telegram-IDs umwandeln."
    )


async def join_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    user = update.effective_user

    if not user or not msg:
        return

    link = " ".join(context.args).strip()

    if not link.startswith(("https://t.me/", "http://t.me/")):
        await msg.reply_text(
            "Verwendung: /join https://t.me/GRUPPENLINK\n"
            "Sende einen Telegram-Gruppenlink."
        )
        return

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "✅ Genehmigen",
                callback_data=f"joinreq:approve:{user.id}",
            ),
            InlineKeyboardButton(
                "❌ Ablehnen",
                callback_data=f"joinreq:reject:{user.id}",
            ),
        ]
    ])

    try:
        await context.bot.send_message(
            OWNER_ID,
            "📥 GRUPPENANFRAGE\n"
            f"Von: {user.full_name} (ID {user.id})\n"
            f"Link: {link}\n\n"
            "Nach Genehmigung muss ein Gruppenadmin den Bot manuell hinzufügen.",
            reply_markup=keyboard,
        )
    except Exception:
        await msg.reply_text(
            "Die Anfrage konnte den Owner nicht erreichen. Bitte später erneut versuchen."
        )
        return

    await msg.reply_text("✅ Deine Gruppenanfrage wurde an den Bot-Owner gesendet.")


async def join_request_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    query = update.callback_query

    if not query:
        return

    if not query.from_user or query.from_user.id != OWNER_ID:
        await query.answer(
            "Nur der Owner darf Anfragen bearbeiten.",
            show_alert=True,
        )
        return

    parts = (query.data or "").split(":")

    if len(parts) != 3:
        await query.answer("Ungültige Anfrage.", show_alert=True)
        return

    action = parts[1]

    try:
        target = int(parts[2])
    except ValueError:
        await query.answer("Ungültige Nutzer-ID.", show_alert=True)
        return

    approved = action == "approve"

    await query.answer("Genehmigt." if approved else "Abgelehnt.")
    await query.edit_message_reply_markup(reply_markup=None)

    try:
        if approved:
            me = await context.bot.get_me()
            await context.bot.send_message(
                target,
                "✅ Deine Gruppenanfrage wurde genehmigt!\n\n"
                f"Füge den Bot über https://t.me/{me.username}?startgroup=true "
                "zu deiner Gruppe hinzu und gib ihm nur die benötigten Adminrechte.",
            )
        else:
            await context.bot.send_message(
                target,
                "❌ Deine Gruppenanfrage wurde vom Owner abgelehnt.",
            )
    except Exception:
        pass

    status = "GENEHMIGT" if approved else "ABGELEHNT"
    await query.edit_message_text(
        (query.message.text or "") + f"\n\nStatus: {status}"
    )


def register_owner_handlers(application):
    handlers = [
        ("id", id_command),
        ("ban", ban_command),
        ("unban", unban_command),
        ("userinfo", userinfo_command),
        ("stats", stats_command),
        ("health", health_command),
        ("botinfo", botinfo_command),
        ("givepoints", points_command),
        ("removepoints", points_command),
        ("setbio", setbio_command),
        ("resetprofile", resetprofile_command),
        ("broadcast", broadcast_command),
        ("announce", broadcast_command),
        ("maintenance", maintenance_command),
        ("ownerhelp", ownerhelp_command),
        ("join", join_command),
    ]

    for name, callback in handlers:
        application.add_handler(
            CommandHandler(name, callback),
            group=1,
        )

    application.add_handler(
        CallbackQueryHandler(
            join_request_callback,
            pattern=r"^joinreq:",
        ),
        group=1,
    )
