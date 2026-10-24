
import os
import logging

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    TypeHandler,
)

import database
from config import OWNER_ID
from permissions import registration_gate
from accounts import (
    build_registration_handler,
    profile_command,
)
from admin_panel import register_admin_handlers


# ------------------------------
# LOL STUDIOS MANAGER
# ------------------------------

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()

logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    level=logging.INFO,
)

logger = logging.getLogger("LOLStudiosManager")


# ------------------------------
# BASIC COMMANDS
# ------------------------------

async def start_command(
    update: Update,
    context,
):
    user = update.effective_user

    if not user:
        return

    await update.effective_message.reply_text(
        f"👋 Moin {user.first_name}!\n\n"
        "Willkommen beim LOL Studios Manager 🚀\n\n"
        "📝 /register – Konto erstellen\n"
        "🆔 /myid – Deine Telegram-ID anzeigen\n"
        "❓ /help – Hilfe anzeigen\n"
        "👤 /profile – Dein Profil\n"
        "🎮 /menu – Bot-Menü\n\n"
        "Registriere dich, um die Funktionen zu nutzen."
    )


async def myid_command(
    update: Update,
    context,
):
    user = update.effective_user

    if not user:
        return

    await update.effective_message.reply_text(
        f"🆔 Deine Telegram-ID:\n\n"
        f"`{user.id}`\n\n"
        "Du kannst diese ID als OWNER_ID in config.py eintragen.",
        parse_mode="Markdown",
    )


async def help_command(
    update: Update,
    context,
):
    await update.effective_message.reply_text(
        "📚 LOL STUDIOS MANAGER — HILFE\n\n"
        "👤 ACCOUNT\n"
        "/register – Registrieren\n"
        "/profile – Profil ansehen\n"
        "/myid – Telegram-ID anzeigen\n\n"
        "🎮 SPIELE & MENÜ\n"
        "/menu – Hauptmenü\n\n"
        "🛡️ ADMIN\n"
        "/admin – Owner-Admin-Panel\n"
        "/adminsearch Name – Account suchen\n\n"
        "Moderations- und weitere Funktionen sind verfügbar, "
        "wenn ihre Handler im Projekt registriert sind."
    )


async def menu_command(
    update: Update,
    context,
):
    await update.effective_message.reply_text(
        "🎮 LOL STUDIOS MANAGER — HAUPTMENÜ\n\n"
        "👤 /profile – Profil\n"
        "🎲 /games – Spiele\n"
        "💰 /daily – Tägliche Belohnung\n"
        "🏆 /leaderboard – Rangliste\n\n"
        "🛡️ /admin – Admin-Panel (nur Owner)\n\n"
        "Hinweis: Nicht alle Menüpunkte sind aktiv, "
        "solange ihre jeweiligen Handler nicht registriert sind."
    )


# ------------------------------
# ERROR HANDLER
# ------------------------------

async def error_handler(
    update: object,
    context,
):
    logger.error(
        "Fehler bei der Verarbeitung eines Updates",
        exc_info=context.error,
    )


# ------------------------------
# MAIN
# ------------------------------

def main():
    if not BOT_TOKEN:
        raise RuntimeError(
            "BOT_TOKEN fehlt! Setze ihn in Render unter "
            "Environment als BOT_TOKEN."
        )

    if not isinstance(OWNER_ID, int) or OWNER_ID <= 0:
        raise RuntimeError(
            "Bitte eine gültige numerische OWNER_ID in config.py eintragen."
        )

    database.init_db()

    application = (
        Application.builder()
        .token(BOT_TOKEN)
        .build()
    )

    # Gruppe -1: Registrierungspflicht vor normalen Commands.
    application.add_handler(
        TypeHandler(Update, registration_gate),
        group=-1,
    )

    # Registrierung und Profil.
    application.add_handler(
        build_registration_handler(),
        group=0,
    )

    application.add_handler(
        CommandHandler("profile", profile_command),
        group=0,
    )

    # Basis-Commands.
    application.add_handler(
        CommandHandler("start", start_command),
        group=1,
    )

    application.add_handler(
        CommandHandler("myid", myid_command),
        group=1,
    )

    application.add_handler(
        CommandHandler("help", help_command),
        group=1,
    )

    application.add_handler(
        CommandHandler("menu", menu_command),
        group=1,
    )

    # Owner-only Admin-Panel.
    register_admin_handlers(application)

    # Fehlerprotokollierung.
    application.add_error_handler(error_handler)

    logger.info("LOL Studios Manager startet ...")
    application.run_polling()


if __name__ == "__main__":
    main()
