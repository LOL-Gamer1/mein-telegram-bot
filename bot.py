
# bot.py — LOL Studios Manager
# Mehrsprachiger Start und Sprachauswahl

import os
import logging

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    TypeHandler,
    ContextTypes,
)

import database
import translations

from config import OWNER_ID
from permissions import registration_gate
from accounts import (
    build_registration_handler,
    profile_command,
)
from admin_panel import register_admin_handlers
from features import register_feature_handlers


BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()

logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    level=logging.INFO,
)

logger = logging.getLogger("LOLStudiosManager")


async def start_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    user = update.effective_user
    message = update.effective_message

    if not user or not message:
        return

    # Standardmäßig Englisch, damit der Start auch ohne Auswahl verständlich ist.
    language = translations.get_language(user.id)
    welcome = translations.tr(user.id, "welcome")
    intro = translations.tr(user.id, "intro")
    language_command = translations.tr(user.id, "language_command")

    account = database.get_account(user.id)

    if account:
        name = account.get("name") or user.first_name
        status = translations.tr(user.id, "registered")
        extra = translations.tr(user.id, "menu_hint")
        text = (
            f"{welcome}\n\n"
            f"{status}\n"
            f"👋 {name}\n\n"
            f"{extra}\n\n"
            f"{language_command}"
        )
    else:
        register_hint = translations.tr(user.id, "register_hint")
        text = (
            f"{welcome}\n\n"
            f"{intro}\n\n"
            f"{register_hint}\n\n"
            f"{language_command}"
        )

    await message.reply_text(
        text,
        reply_markup=translations.language_button_keyboard(),
    )


async def language_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    user = update.effective_user
    message = update.effective_message

    if not user or not message:
        return

    await message.reply_text(
        translations.tr(user.id, "choose_language"),
        reply_markup=translations.language_keyboard(),
    )


async def language_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    query = update.callback_query
    user = update.effective_user

    if not query or not user:
        return

    data = query.data or ""

    if data == "lang:open":
        await query.answer()
        await query.message.reply_text(
            translations.tr(user.id, "choose_language"),
            reply_markup=translations.language_keyboard(),
        )
        return

    if not data.startswith("lang:"):
        await query.answer()
        return

    language = data.split(":", 1)[1]

    if not translations.set_language(user.id, language):
        await query.answer(
            "Unknown language / Unbekannte Sprache",
            show_alert=True,
        )
        return

    await query.answer("Language saved!")

    # Die Bestätigung wird bereits in der neu gewählten Sprache angezeigt.
    confirmation = translations.tr(user.id, "language_saved")
    welcome = translations.tr(user.id, "welcome")
    intro = translations.tr(user.id, "intro")
    language_command_text = translations.tr(user.id, "language_command")
    account = database.get_account(user.id)

    if account:
        name = account.get("name") or user.first_name
        text = (
            f"{confirmation}\n\n"
            f"{welcome}\n\n"
            f"{translations.tr(user.id, 'registered')}\n"
            f"👋 {name}\n\n"
            f"{translations.tr(user.id, 'menu_hint')}\n\n"
            f"{language_command_text}"
        )
    else:
        text = (
            f"{confirmation}\n\n"
            f"{welcome}\n\n"
            f"{intro}\n\n"
            f"{translations.tr(user.id, 'register_hint')}\n\n"
            f"{language_command_text}"
        )

    try:
        await query.edit_message_text(
            text,
            reply_markup=translations.language_button_keyboard(),
        )
    except Exception:
        # Falls Telegram die Nachricht nicht bearbeiten kann,
        # wird eine neue Nachricht gesendet.
        await query.message.reply_text(
            text,
            reply_markup=translations.language_button_keyboard(),
        )


async def myid_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    user = update.effective_user

    if not user:
        return

    await update.effective_message.reply_text(
        f"🆔 Telegram ID:\n{user.id}\n\n"
        "If you own this bot, configure OWNER_ID in config.py."
    )


async def error_handler(update: object, context):
    logger.error(
        "Fehler bei der Verarbeitung eines Updates",
        exc_info=context.error,
    )


def main():
    if not BOT_TOKEN:
        raise RuntimeError(
            "BOT_TOKEN fehlt! Lege die Umgebungsvariable "
            "BOT_TOKEN bei FadeHost an."
        )

    if not isinstance(OWNER_ID, int) or OWNER_ID <= 0:
        raise RuntimeError(
            "Bitte eine gültige numerische OWNER_ID in config.py eintragen."
        )

    database.init_db()
    translations.init_language_db()

    application = (
        Application.builder()
        .token(BOT_TOKEN)
        .build()
    )

    # Zugriffskontrolle vor normalen Commands und Callback-Handlern.
    application.add_handler(
        TypeHandler(Update, registration_gate),
        group=-1,
    )

    application.add_handler(
        build_registration_handler(),
        group=0,
    )

    application.add_handler(
        CommandHandler("profile", profile_command),
        group=0,
    )

    application.add_handler(
        CommandHandler("start", start_command),
        group=1,
    )

    application.add_handler(
        CommandHandler("language", language_command),
        group=1,
    )

    application.add_handler(
        CallbackQueryHandler(
            language_callback,
            pattern=r"^lang:",
        ),
        group=1,
    )

    application.add_handler(
        CommandHandler("myid", myid_command),
        group=1,
    )

    register_feature_handlers(application)
    register_admin_handlers(application)

    application.add_error_handler(error_handler)

    logger.info("LOL Studios Manager startet ...")
    application.run_polling()


if __name__ == "__main__":
    main()
