
# admin_panel.py — LOL Studios Manager

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    Application,
    ContextTypes,
    CommandHandler,
    CallbackQueryHandler,
)

import database
from permissions import is_owner


def admin_keyboard():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("📊 Statistiken", callback_data="admin:stats"),
            InlineKeyboardButton("👥 Accounts", callback_data="admin:users:0"),
        ],
        [
            InlineKeyboardButton("🎫 Support-Tickets", callback_data="admin:tickets"),
            InlineKeyboardButton("🔎 Suche", callback_data="admin:search"),
        ],
        [
            InlineKeyboardButton("🔄 Aktualisieren", callback_data="admin:home"),
        ],
    ])


def back_button(target="admin:home"):
    return InlineKeyboardMarkup([[
        InlineKeyboardButton("⬅️ Zurück", callback_data=target)
    ]])


async def admin_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    user = update.effective_user

    if not user or not is_owner(user.id):
        await update.effective_message.reply_text(
            "⛔ Zugriff verweigert. Nur der Bot-Owner darf dieses Menü öffnen."
        )
        return

    await update.effective_message.reply_text(
        "🛡️ LOL STUDIOS MANAGER — ADMIN CENTER\n\n"
        "Willkommen im Verwaltungsbereich.\n"
        "Wähle eine Funktion:",
        reply_markup=admin_keyboard(),
    )


async def stats_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    user = update.effective_user

    if not user or not is_owner(user.id):
        await update.effective_message.reply_text("⛔ Zugriff verweigert.")
        return

    await update.effective_message.reply_text(
        f"📊 BOT-STATISTIKEN\n\n"
        f"👥 Registrierte Accounts: {database.account_count()}\n"
        f"⛔ Gesperrte Accounts: {database.suspended_count()}"
    )


async def show_stats(query):
    total = database.account_count()
    suspended = database.suspended_count()

    await query.edit_message_text(
        "📊 BOT-STATISTIKEN\n\n"
        f"👥 Registrierte Accounts: {total}\n"
        f"✅ Aktive Accounts: {total - suspended}\n"
        f"⛔ Gesperrte Accounts: {suspended}",
        reply_markup=back_button(),
    )


async def show_users(query, offset=0):
    offset = max(0, int(offset))
    accounts = database.list_accounts(limit=8, offset=offset)
    total = database.account_count()

    buttons = []

    for account in accounts:
        status = "⛔" if account.get("suspended") else "✅"
        name = account.get("name") or "Unbenannt"
        user_id = int(account["user_id"])

        buttons.append([
            InlineKeyboardButton(
                f"{status} {name[:25]} · {user_id}",
                callback_data=f"admin:user:{user_id}",
            )
        ])

    navigation = []
    if offset > 0:
        navigation.append(
            InlineKeyboardButton(
                "⬅️ Zurück",
                callback_data=f"admin:users:{max(0, offset - 8)}",
            )
        )

    if offset + 8 < total:
        navigation.append(
            InlineKeyboardButton(
                "Weiter ➡️",
                callback_data=f"admin:users:{offset + 8}",
            )
        )

    if navigation:
        buttons.append(navigation)

    buttons.append([
        InlineKeyboardButton("🏠 Admin-Startseite", callback_data="admin:home")
    ])

    await query.edit_message_text(
        f"👥 ACCOUNT-VERWALTUNG\n"
        f"Accounts: {total}\n"
        f"Seite: {offset // 8 + 1}\n\n"
        "Wähle einen Account:",
        reply_markup=InlineKeyboardMarkup(buttons),
    )


async def show_account(query, user_id):
    account = database.get_account(user_id)

    if not account:
        await query.edit_message_text(
            "Account nicht gefunden.",
            reply_markup=back_button("admin:users:0"),
        )
        return

    status = "⛔ Gesperrt" if account.get("suspended") else "✅ Aktiv"
    username = account.get("username") or "Nicht gesetzt"

    text = (
        "👤 ACCOUNT-DETAILS\n\n"
        f"Name: {account.get('name') or 'Unbenannt'}\n"
        f"ID: {account['user_id']}\n"
        f"Username: {username}\n"
        f"Altersgruppe: {account.get('agegroup') or 'Nicht angegeben'}\n"
        f"Bio: {account.get('bio') or 'Keine Bio'}\n"
        f"Status: {status}\n"
        f"Punkte: {database.get_points(user_id)}"
    )

    action = "Entsperren" if account.get("suspended") else "Sperren"

    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    f"🔒 {action}",
                    callback_data=f"admin:toggle:{user_id}",
                )
            ],
            [
                InlineKeyboardButton(
                    "⬅️ Zur Account-Liste",
                    callback_data="admin:users:0",
                )
            ],
            [
                InlineKeyboardButton(
                    "🏠 Admin-Startseite",
                    callback_data="admin:home",
                )
            ],
        ]),
    )


async def show_tickets(query):
    tickets = database.list_tickets(status="open", limit=10)
    buttons = []

    for ticket in tickets:
        ticket_id = int(ticket["id"])
        label = f"🎫 #{ticket_id} · Nutzer {ticket['user_id']}"
        buttons.append([
            InlineKeyboardButton(
                label[:60],
                callback_data=f"admin:ticket:{ticket_id}",
            )
        ])

    buttons.append([
        InlineKeyboardButton("🏠 Admin-Startseite", callback_data="admin:home")
    ])

    text = "🎫 OFFENE SUPPORT-TICKETS\n\n"
    if not tickets:
        text += "Es gibt derzeit keine offenen Tickets."
    else:
        text += "Wähle ein Ticket, um die Details anzusehen."

    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(buttons),
    )


async def show_ticket(query, ticket_id):
    ticket = database.get_ticket(ticket_id)

    if not ticket:
        await query.edit_message_text(
            "Ticket nicht gefunden.",
            reply_markup=back_button("admin:tickets"),
        )
        return

    message = ticket.get("message") or ""
    if len(message) > 2500:
        message = message[:2500] + "…"

    reply = ticket.get("reply") or "Noch keine Antwort"

    await query.edit_message_text(
        f"🎫 TICKET #{ticket['id']}\n\n"
        f"Nutzer-ID: {ticket['user_id']}\n"
        f"Status: {ticket['status']}\n\n"
        f"Nachricht:\n{message}\n\n"
        f"Antwort:\n{reply}\n\n"
        f"Antworten mit:\n/ticketreply {ticket['id']} Deine Antwort",
        reply_markup=back_button("admin:tickets"),
    )


async def admin_search_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    user = update.effective_user

    if not user or not is_owner(user.id):
        await update.effective_message.reply_text("⛔ Zugriff verweigert.")
        return

    query = " ".join(context.args).strip()
    if not query:
        await update.effective_message.reply_text(
            "Verwendung: /adminsearch Name, Username oder Telegram-ID"
        )
        return

    results = database.search_accounts(query, limit=10)

    if not results:
        await update.effective_message.reply_text("Keine passenden Accounts gefunden.")
        return

    buttons = []
    for account in results:
        name = account.get("name") or "Unbenannt"
        user_id = int(account["user_id"])
        buttons.append([
            InlineKeyboardButton(
                f"{name[:25]} · {user_id}",
                callback_data=f"admin:user:{user_id}",
            )
        ])

    buttons.append([
        InlineKeyboardButton("🛡️ Admin-Center", callback_data="admin:home")
    ])

    await update.effective_message.reply_text(
        "🔎 SUCHERGEBNISSE",
        reply_markup=InlineKeyboardMarkup(buttons),
    )


async def admin_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    query = update.callback_query
    user = update.effective_user

    # Jede Admin-Aktion wird serverseitig geprüft.
    if not user or not is_owner(user.id):
        await query.answer("⛔ Keine Berechtigung.", show_alert=True)
        return

    await query.answer()
    data = query.data or ""

    if data == "admin:home":
        await query.edit_message_text(
            "🛡️ LOL STUDIOS MANAGER — ADMIN CENTER\n\n"
            "Wähle eine Funktion:",
            reply_markup=admin_keyboard(),
        )
        return

    if data == "admin:stats":
        await show_stats(query)
        return

    if data.startswith("admin:users:"):
        try:
            offset = max(0, int(data.rsplit(":", 1)[1]))
        except ValueError:
            offset = 0

        await show_users(query, offset)
        return

    if data.startswith("admin:user:"):
        try:
            user_id = int(data.rsplit(":", 1)[1])
        except ValueError:
            await query.edit_message_text("Ungültige Account-ID.")
            return

        await show_account(query, user_id)
        return

    if data.startswith("admin:toggle:"):
        try:
            user_id = int(data.rsplit(":", 1)[1])
        except ValueError:
            await query.edit_message_text("Ungültige Account-ID.")
            return

        if user_id == user.id:
            await query.answer(
                "Du kannst dich nicht über dieses Menü selbst sperren.",
                show_alert=True,
            )
            return

        account = database.get_account(user_id)
        if not account:
            await query.edit_message_text("Account nicht gefunden.")
            return

        new_status = not bool(account.get("suspended"))
        if not database.set_suspended(user_id, new_status):
            await query.edit_message_text("Der Status konnte nicht geändert werden.")
            return

        await query.answer(
            "Account gesperrt." if new_status else "Account entsperrt."
        )
        await show_account(query, user_id)
        return

    if data == "admin:tickets":
        await show_tickets(query)
        return

    if data.startswith("admin:ticket:"):
        try:
            ticket_id = int(data.rsplit(":", 1)[1])
        except ValueError:
            await query.edit_message_text("Ungültige Ticket-ID.")
            return

        await show_ticket(query, ticket_id)
        return

    if data == "admin:search":
        await query.edit_message_text(
            "🔎 ACCOUNT-SUCHE\n\n"
            "Verwende:\n"
            "/adminsearch Name\n"
            "/adminsearch @username\n"
            "/adminsearch 123456789",
            reply_markup=back_button(),
        )
        return

    await query.edit_message_text(
        "Unbekannte Admin-Aktion.",
        reply_markup=back_button(),
    )


def register_admin_handlers(application: Application):
    application.add_handler(CommandHandler("admin", admin_command), group=1)
    application.add_handler(CommandHandler("adminpanel", admin_command), group=1)
    application.add_handler(CommandHandler("adminsearch", admin_search_command), group=1)
    application.add_handler(CallbackQueryHandler(
        admin_callback,
        pattern=r"^admin:",
    ), group=1)
