
# accounts.py

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ContextTypes,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ConversationHandler,
    filters,
)

import database
from config import AGE_GROUPS

NAME, AGEGROUP, BIO, AVATAR = range(4)


async def register_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not user:
        return ConversationHandler.END

    if database.is_registered(user.id):
        await update.effective_message.reply_text(
            "Du bist bereits registriert! Nutze /me für dein Profil."
        )
        return ConversationHandler.END

    context.user_data["registration_active"] = True
    context.user_data["registration"] = {
        "name": "",
        "bio": "",
        "avatar": "",
        "agegroup": "",
    }

    await update.effective_message.reply_text(
        "🌩️ LOL Studios Manager – Registrierung\n\n"
        "Schritt 1/4: Wie möchtest du im Bot heißen?\n"
        "Gib einen Namen mit 2–40 Zeichen ein."
    )
    return NAME


async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = (update.effective_message.text or "").strip()

    if not 2 <= len(name) <= 40:
        await update.effective_message.reply_text(
            "Der Name muss zwischen 2 und 40 Zeichen lang sein."
        )
        return NAME

    context.user_data["registration"]["name"] = name

    buttons = [
        [InlineKeyboardButton(label, callback_data=f"reg:age:{value}")]
        for label, value in AGE_GROUPS
    ]
    buttons.append([
        InlineKeyboardButton("Überspringen", callback_data="reg:age:skip")
    ])

    await update.effective_message.reply_text(
        "Schritt 2/4: Wähle deine Altersgruppe.",
        reply_markup=InlineKeyboardMarkup(buttons),
    )
    return AGEGROUP


async def get_agegroup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    value = (query.data or "").split(":", 2)[-1]
    allowed = {age_value for _, age_value in AGE_GROUPS}

    context.user_data["registration"]["agegroup"] = (
        value if value in allowed else ""
    )

    await query.edit_message_text(
        "Schritt 3/4: Schreibe eine kurze Bio oder sende /skip."
    )
    return BIO


async def get_bio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    bio = (update.effective_message.text or "").strip()

    if len(bio) > 250:
        await update.effective_message.reply_text(
            "Deine Bio darf höchstens 250 Zeichen enthalten."
        )
        return BIO

    context.user_data["registration"]["bio"] = bio
    await update.effective_message.reply_text(
        "Schritt 4/4: Sende ein Foto als Avatar oder nutze /skip."
    )
    return AVATAR


async def skip_bio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["registration"]["bio"] = ""
    await update.effective_message.reply_text(
        "Schritt 4/4: Sende ein Foto als Avatar oder nutze /skip."
    )
    return AVATAR


async def get_avatar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    photo = update.effective_message.photo
    if not photo:
        await update.effective_message.reply_text(
            "Bitte sende ein Foto oder nutze /skip."
        )
        return AVATAR

    context.user_data["registration"]["avatar"] = photo[-1].file_id
    await finish_registration(update, context)
    return ConversationHandler.END


async def skip_avatar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["registration"]["avatar"] = ""
    await finish_registration(update, context)
    return ConversationHandler.END


async def finish_registration(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    user = update.effective_user
    form = context.user_data.get("registration", {})

    database.save_account(
        user_id=user.id,
        username=user.username or "",
        name=form.get("name", ""),
        bio=form.get("bio", ""),
        avatar=form.get("avatar", ""),
        agegroup=form.get("agegroup", ""),
    )

    context.user_data["registration_active"] = False
    context.user_data.pop("registration", None)

    await update.effective_message.reply_text(
        "✅ Registrierung abgeschlossen!\n\n"
        "Dein Profil ist eingerichtet. Öffne /menu für alle Funktionen."
    )


async def cancel_registration(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    context.user_data["registration_active"] = False
    context.user_data.pop("registration", None)
    await update.effective_message.reply_text(
        "Registrierung abgebrochen. Du kannst es mit /register erneut versuchen."
    )
    return ConversationHandler.END


async def profile_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    account = database.get_account(user.id)

    if not account:
        await update.effective_message.reply_text(
            "Du hast noch kein Konto. Starte mit /register."
        )
        return

    username = (
        f"@{account['username']}" if account.get("username")
        else "Nicht gesetzt"
    )

    text = (
        f"👤 Profil: {account.get('name') or user.first_name}\n"
        f"🆔 Telegram-ID: {account['user_id']}\n"
        f"🔗 Username: {username}\n"
        f"🎂 Altersgruppe: {account.get('agegroup') or 'Nicht angegeben'}\n"
        f"📝 Bio: {account.get('bio') or 'Keine Bio'}\n"
        f"⭐ Punkte: {database.get_points(user.id)}"
    )

    avatar = account.get("avatar")
    if avatar:
        await update.effective_message.reply_photo(photo=avatar, caption=text)
    else:
        await update.effective_message.reply_text(text)


def build_registration_handler():
    return ConversationHandler(
        entry_points=[CommandHandler("register", register_start)],
        states={
            NAME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, get_name),
            ],
            AGEGROUP: [
                CallbackQueryHandler(get_agegroup, pattern=r"^reg:age:"),
            ],
            BIO: [
                CommandHandler("skip", skip_bio),
                MessageHandler(filters.TEXT & ~filters.COMMAND, get_bio),
            ],
            AVATAR: [
                CommandHandler("skip", skip_avatar),
                MessageHandler(filters.PHOTO, get_avatar),
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel_registration)],
        allow_reentry=True,
        name="registration",
        persistent=False,
    )
