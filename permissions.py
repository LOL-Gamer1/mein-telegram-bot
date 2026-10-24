
# permissions.py

from telegram import Update
from telegram.ext import ContextTypes, ApplicationHandlerStop

import database
from config import OWNER_ID, PUBLIC_COMMANDS


ALWAYS_ALLOWED_COMMANDS = {
    "start", "myid", "id", "register", "unregister",
    "cancel", "skip", "help", "ping", "tos", "gdpr",
    "permissions", "policy", "optout", "support",
}


def is_owner(user_id):
    return user_id is not None and int(user_id) == OWNER_ID


def require_owner(user_id):
    return is_owner(user_id)


async def registration_gate(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    user = update.effective_user
    if user is None:
        return

    owner = is_owner(user.id)
    message = update.effective_message
    query = update.callback_query

    if query:
        data = query.data or ""

        if data.startswith("reg:"):
            return

        if data.startswith(("admin:", "owner:", "dev:")):
            if not owner:
                await query.answer(
                    "⛔ Dieser Bereich ist nur für den Owner.",
                    show_alert=True,
                )
                raise ApplicationHandlerStop
            return

        if data.startswith("team:") and not (
            owner or database.is_registered(user.id)
        ):
            await query.answer(
                "🔒 Bitte zuerst /register ausführen.",
                show_alert=True,
            )
            raise ApplicationHandlerStop

        if not owner and database.is_suspended(user.id):
            await query.answer(
                "⛔ Dein Konto ist gesperrt.",
                show_alert=True,
            )
            raise ApplicationHandlerStop

        if not database.is_registered(user.id) and not owner:
            await query.answer(
                "🔒 Bitte zuerst /register ausführen.",
                show_alert=True,
            )
            raise ApplicationHandlerStop

        return

    if message is None:
        return

    text = message.text or ""
    command = ""

    if text.startswith("/"):
        command = text.split()[0].split("@")[0][1:].lower()

    if command in {"admin", "adminpanel", "owner", "dev"}:
        if not owner:
            await message.reply_text(
                "⛔ Dieser Bereich ist nur für den Owner."
            )
            raise ApplicationHandlerStop
        return

    if command in ALWAYS_ALLOWED_COMMANDS:
        return

    if command in PUBLIC_COMMANDS:
        return

    if context.user_data.get("registration_active"):
        await message.reply_text(
            "Du bist gerade bei der Registrierung. "
            "Beantworte bitte den aktuellen Schritt oder nutze /cancel."
        )
        raise ApplicationHandlerStop

    if not owner and not database.is_registered(user.id):
        await message.reply_text(
            "🔒 Du musst dich zuerst registrieren.\n\n"
            "Starte mit /register."
        )
        raise ApplicationHandlerStop

    if not owner and database.is_suspended(user.id):
        await message.reply_text(
            "⛔ Dein Konto wurde gesperrt. "
            "Du kannst diese Funktion aktuell nicht verwenden."
        )
        raise ApplicationHandlerStop
