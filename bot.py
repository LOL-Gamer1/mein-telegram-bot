
# bot.py — LOL Studios Manager

import os
import logging

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    TypeHandler,
)

import database
from config import OWNER_ID, BOT_NAME, BOT_VERSION
from permissions import registration_gate
from accounts import build_registration_handler, profile_command
from admin_panel import register_admin_handlers
from features import register_feature_handlers


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
            f"Willkommen zurück bei {BOT_NAME} 🌩️\n"
            f"Version {BOT_VERSION}\n\n"
            "🎮 /menu – Hauptmenü\n"
            "👤 /me – Dein Profil\n"
            "⭐ /points – Punktestand\n"
            "🎁 /daily – Tägliche Belohnung\n"
            "❓ /help – Alle Commands"
        )
    else:
        text = (
            f"👋 Moin {user.first_name}!\n\n"
            f"Willkommen bei {BOT_NAME} 🌩️\n\n"
            "📝 /register – Konto erstellen\n"
            "🎮 /menu – Funktionen ansehen\n"
            "❓ /help – Hilfe\n\n"
            "Registriere dich, um alle Funktionen zu nutzen."
        )

    await update.effective_message.reply_text(text)


async def myid_command(update: Update, context):
    user = update.effective_user
    if user:
        await update.effective_message.reply_text(
            f"🆔 Deine Telegram-ID: {user.id}"
        )


async def error_handler(update: object, context):
    logger.error(
        "Fehler bei der Update-Verarbeitung",
        exc_info=context.error,
    )


def main():
    if not BOT_TOKEN:
        raise RuntimeError(
            "BOT_TOKEN fehlt. Lege ihn als Umgebungsvariable bei FadeHost fest."
        )

    if not isinstance(OWNER_ID, int) or OWNER_ID <= 0:
        raise RuntimeError("OWNER_ID in config.py ist ungültig.")

    database.init_db()

    application = Application.builder().token(BOT_TOKEN).build()

    application.add_handler(
        TypeHandler(Update, registration_gate),
        group=-1,
    )

    application.add_handler(build_registration_handler(), group=0)
    application.add_handler(CommandHandler("profile", profile_command), group=0)
    application.add_handler(CommandHandler("me", profile_command), group=0)

    application.add_handler(CommandHandler("start", start_command), group=1)
    application.add_handler(CommandHandler("myid", myid_command), group=1)
    application.add_handler(CommandHandler("id", myid_command), group=1)

    register_feature_handlers(application)
    register_admin_handlers(application)

    application.add_error_handler(error_handler)

    logger.info("%s v%s startet", BOT_NAME, BOT_VERSION)
    application.run_polling()


if __name__ == "__main__":
    main()
