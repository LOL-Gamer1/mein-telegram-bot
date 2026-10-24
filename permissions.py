
# permissions.py — LOL Studios Manager

from telegram import Update
from telegram.ext import ContextTypes, ApplicationHandlerStop

import database
from config import OWNER_ID, PUBLIC_COMMANDS


def is_owner(user_id):
    return user_id is not None and int(user_id) == OWNER_ID


def require_owner(user_id):
    return is_owner(user_id)


async def registration_gate(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    user = update.effective_user

    if user is None:
        return

    user_id = user.id
    owner = is_owner(user_id)
    message = update.effective_message
    query = update.callback_query

    # Registrierungsschritte und Abbrechen immer erlauben.
    if query:
        data = query.data or ""

        if data.startswith("reg:"):
            return

        # Admin-Buttons ausschließlich für den Owner.
        if data.startswith("admin:"):
            if not owner:
                await query.answer(
                    "⛔ Nur der konfigurierte Owner darf das Admin-Panel nutzen.",
                    show_alert=True
                )
                raise ApplicationHandlerStop
            return

        # Registrierung einmal pro Update prüfen.
        registered = database.is_registered(user_id)

        if not owner and not registered:
            await query.answer(
                "🔒 Bitte zuerst /register ausführen.",
                show_alert=True
            )
            raise ApplicationHandlerStop

        if not owner and database.is_suspended(user_id):
            await query.answer(
                "⛔ Dein Bot-Konto ist gesperrt.",
                show_alert=True
            )
            raise ApplicationHandlerStop

        return

    if message is None:
        return

    text = message.text or ""
    command = ""

    if text.startswith("/"):
        command = text.split()[0].split("@")[0][1:].lower()

    # Admin-Befehle nur für den Owner.
    if command in {"admin", "adminpanel"}:
        if not owner:
            await message.reply_text(
                "⛔ Das Admin-Panel ist nur für den Owner verfügbar."
            )
            raise ApplicationHandlerStop
        return

    # Normale Nachrichten sind keine Commands.
    if not command:
        return

    # Öffentliche Commands ohne Registrierung erlauben.
    if command in PUBLIC_COMMANDS:
        return

    # Registrierungsdialog nicht durch andere Commands unterbrechen.
    if context.user_data.get("registration_active"):
        if command == "skip":
            return

        await message.reply_text(
            "Du bist gerade bei der Registrierung. "
            "Bitte beantworte den aktuellen Schritt oder nutze /cancel."
        )
        raise ApplicationHandlerStop

    # Owner von der normalen Registrierungspflicht ausnehmen.
    if owner:
        return

    # Registrierungsstatus prüfen.
    if not database.is_registered(user_id):
        await message.reply_text(
            "🔒 Du musst dich zuerst registrieren.\n\n"
            "Starte mit /register."
        )
        raise ApplicationHandlerStop

    if database.is_suspended(user_id):
        await message.reply_text(
            "⛔ Dein Bot-Konto wurde gesperrt. "
            "Du kannst aktuell keine Commands verwenden."
        )
        raise ApplicationHandlerStop
