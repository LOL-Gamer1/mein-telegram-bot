# admin_panel.py

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    ContextTypes,
    CommandHandler,
    CallbackQueryHandler,
)

import database
from permissions import is_owner


def home_keyboard():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("📊 Statistiken", callback_data="admin:stats"),
            InlineKeyboardButton("👥 Accounts", callback_data="admin:users:0"),
        ],
        [
            InlineKeyboardButton("🔎 Account suchen", callback_data="admin:search"),
            InlineKeyboardButton("🔄 Aktualisieren", callback_data="admin:home"),
        ],
    ])


async def admin_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    user = update.effective_user

    if not user or not is_owner(user.id):
        await update.effective_message.reply_text(
            "⛔ Zugriff verweigert. Dieses Panel gehört nur dem Owner."
        )
        return

    await update.effective_message.reply_text(
        "🛡️ LOL STUDIOS MANAGER — ADMIN CENTER\n\n"
        "Wähle eine Funktion:",
        reply_markup=home_keyboard(),
    )


async def show_stats(query):
    total = database.account_count()
    suspended = database.suspended_count()
    active = total - suspended

    text = (
        "📊 **BOT-STATISTIKEN**\n\n"
        f"👥 Registrierte Accounts: **{total}**\n"
        f"✅ Aktive Accounts: **{active}**\n"
        f"⛔ Gesperrte Accounts: **{suspended}**"
    )

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("⬅️ Admin-Startseite", callback_data="admin:home")]
    ])

    await query.edit_message_text(
        text,
        parse_mode="Markdown",
        reply_markup=keyboard,
    )


async def show_users(query, offset=0):
    accounts = database.list_accounts(limit=8, offset=offset)
    total = database.account_count()

    buttons = []

    for account in accounts:
        status = "⛔" if account["suspended"] else "✅"
        label = f"{status} {account['name']} · {account['user_id']}"
        buttons.append([
            InlineKeyboardButton(
                label[:60],
                callback_data=f"admin:user:{account['user_id']}"
            )
        ])

    navigation = []
    if offset > 0:
        navigation.append(
            InlineKeyboardButton(
                "⬅️ Zurück",
                callback_data=f"admin:users:{max(0, offset - 8)}"
            )
        )

    if offset + 8 < total:
        navigation.append(
            InlineKeyboardButton(
                "Weiter ➡️",
                callback_data=f"admin:users:{offset + 8}"
            )
        )

    if navigation:
        buttons.append(navigation)

    buttons.append([
        InlineKeyboardButton("🏠 Startseite", callback_data="admin:home")
    ])

    await query.edit_message_text(
        f"👥 **ACCOUNT-VERWALTUNG**\n"
        f"Accounts: {total}\n"
        f"Seite: {offset // 8 + 1}\n\n"
        "Wähle einen Account aus:",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(buttons),
    )


async def show_account(query, user_id):
    account = database.get_account(user_id)

    if not account:
        await query.edit_message_text(
            "Dieser Account wurde nicht gefunden.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("⬅️ Accounts", callback_data="admin:users:0")]
            ]),
        )
        return

    status = "⛔ Gesperrt" if account["suspended"] else "✅ Aktiv"
    username = (
        f"@{account['username']}" if account["username"] else "Nicht gesetzt"
    )

    text = (
        "👤 **ACCOUNT-DETAILS**\n\n"
        f"Name: {account['name']}\n"
        f"Telegram-ID: `{account['user_id']}`\n"
        f"Username: {username}\n"
        f"Altersgruppe: {account['agegroup'] or 'Nicht angegeben'}\n"
        f"Bio: {account['bio'] or 'Keine Bio'}\n"
        f"Registriert: {account['registered_at']}\n"
        f"Status: {status}"
    )

    action = "Entsperren" if account["suspended"] else "Sperren"

    await query.edit_message_text(
        text,
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    f"⛔ {action}",
                    callback_data=f"admin:toggle:{user_id}"
                )
            ],
            [
                InlineKeyboardButton(
                    "⬅️ Zurück zur Liste",
                    callback_data="admin:users:0"
                )
            ],
            [
                InlineKeyboardButton(
                    "🏠 Startseite",
                    callback_data="admin:home"
                )
            ],
        ]),
    )


async def admin_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    query = update.callback_query
    user = update.effective_user

    if not user or not is_owner(user.id):
        await query.answer("⛔ Keine Berechtigung.", show_alert=True)
        return

    await query.answer()
    data = query.data or ""

    if data == "admin:home":
        await query.edit_message_text(
            "🛡️ LOL STUDIOS MANAGER — ADMIN CENTER\n\n"
            "Wähle eine Funktion:",
            reply_markup=home_keyboard(),
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

    if data == "admin:search":
        await query.edit_message_text(
            "🔎 **ACCOUNT-SUCHE**\n\n"
            "Sende jetzt den Befehl:\n"
            "`/adminsearch Name`, ` /adminsearch @username` "
            "oder `/adminsearch 123456789`.",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🏠 Startseite", callback_data="admin:home")]
            ]),
        )
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

        # Sicherheitscheck: Owner darf nicht versehentlich sich selbst sperren.
        if user_id == user.id:
            await query.answer(
                "Dein eigenes Konto kann hier nicht gesperrt werden.",
                show_alert=True,
            )
            return

        account = database.get_account(user_id)
        if not account:
            await query.edit_message_text("Account nicht gefunden.")
            return

        new_status = not bool(account["suspended"])
        changed = database.set_suspended(user_id, new_status)

        if not changed:
            await query.edit_message_text("Status konnte nicht geändert werden.")
            return

        await query.answer(
            "Account gesperrt." if new_status else "Account entsperrt."
        )
        await show_account(query, user_id)
        return

    await query.edit_message_text("Unbekannte Admin-Aktion.")


async def admin_search_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    user = update.effective_user

    if not user or not is_owner(user.id):
        await update.effective_message.reply_text("⛔ Zugriff verweigert.")
        return

    query_text = " ".join(context.args).strip()

    if not query_text:
        await update.effective_message.reply_text(
            "Verwendung: /adminsearch Name oder /adminsearch Telegram-ID"
        )
        return

    accounts = database.search_accounts(query_text, limit=8)

    if not accounts:
        await update.effective_message.reply_text(
            "Keine passenden Accounts gefunden."
        )
        return

    buttons = []
    for account in accounts:
        status = "⛔" if account["suspended"] else "✅"
        buttons.append([
            InlineKeyboardButton(
                f"{status} {account['name']} · {account['user_id']}"[:60],
                callback_data=f"admin:user:{account['user_id']}",
            )
        ])

    buttons.append([
        InlineKeyboardButton("🏠 Admin-Startseite", callback_data="admin:home")
    ])

    await update.effective_message.reply_text(
        f"🔎 Suchergebnisse für: {query_text}",
        reply_markup=InlineKeyboardMarkup(buttons),
    )


def register_admin_handlers(application):
    application.add_handler(CommandHandler("admin", admin_command))
    application.add_handler(CommandHandler("adminpanel", admin_command))
    application.add_handler(CommandHandler("adminsearch", admin_search_command))
    application.add_handler(
        CallbackQueryHandler(admin_callback, pattern=r"^admin:")
    )
