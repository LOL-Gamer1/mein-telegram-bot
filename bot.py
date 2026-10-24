# bot.py — LOL Studios Manager

import os
import logging

from telegram import Update
from telegram.ext import Application, CommandHandler, TypeHandler

import database
from config import OWNER_ID
from permissions import registration_gate
from accounts import build_registration_handler, profile_command
from admin_panel import register_admin_handlers
from features import register_feature_handlers
from owner_commands import register_owner_handlers, owner_startup
from group_moderation import register_group_handlers

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()

logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger("LOLStudiosManager")


async def start_command(update: Update, context):
    user = update.effective_user
    if not user:
        return

    account = database.get_account(user.id)

    if account:
        name = account.get("name") or user.first_name
        text = (
            f"👋 Moin {name}!\n\n"
            "Willkommen zurück beim LOL Studios Manager 🚀\n\n"
            "👤 /profile – Dein Profil\n"
            "🎮 /menu – Hauptmenü\n"
            "🎁 /daily – Tägliche Belohnung\n"
            "❓ /help – Alle Commands\n"
        )
    else:
        text = (
            f"👋 Moin {user.first_name}!\n\n"
            "Willkommen beim LOL Studios Manager 🚀\n\n"
            "📝 /register – Konto erstellen\n"
            "👤 /profile – Dein Profil\n"
            "🎮 /menu – Hauptmenü\n"
            "❓ /help – Alle Commands\n\n"
            "Registriere dich mit /register, um alle Funktionen zu nutzen."
        )

    await update.effective_message.reply_text(text)


async def myid_command(update: Update, context):
    user = update.effective_user
    if user:
        await update.effective_message.reply_text(
            f"🆔 Deine Telegram-ID:\n{user.id}\n\n"
            "Diese Zahl kannst du als OWNER_ID in config.py verwenden."
        )


async def error_handler(update: object, context):
    logger.error(
        "Fehler bei der Verarbeitung eines Updates",
        exc_info=context.error,
    )


def main():
    if not BOT_TOKEN:
        raise RuntimeError(
            "BOT_TOKEN fehlt! Lege die Umgebungsvariable BOT_TOKEN bei FadeHost an."
        )

    if not isinstance(OWNER_ID, int) or OWNER_ID <= 0:
        raise RuntimeError("Bitte eine gültige OWNER_ID in config.py eintragen.")

    database.init_db()

    application = (
        Application.builder()
        .token(BOT_TOKEN)
        .post_init(owner_startup)
        .build()
    )

    # Prüft Registrierung und Sperrstatus vor normalen Befehlen.
    application.add_handler(
        TypeHandler(Update, registration_gate),
        group=-1,
    )

    application.add_handler(build_registration_handler(), group=0)
    application.add_handler(
        CommandHandler("profile", profile_command),
        group=0,
    )
    application.add_handler(
        CommandHandler("start", start_command),
        group=1,
    )
    application.add_handler(
        CommandHandler("myid", myid_command),
        group=1,
    )

    register_feature_handlers(application)
    register_admin_handlers(application)
    register_owner_handlers(application)
    register_group_handlers(application)

    application.add_error_handler(error_handler)

    logger.info("LOL Studios Manager startet ...")
    application.run_polling()


if __name__ == "__main__":
    main()
