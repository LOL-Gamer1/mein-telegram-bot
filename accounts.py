# accounts.py

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
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

    context.user_data["registration_active"] = True
    context.user_data["registration"] = {
        "name": "",
        "bio": "",
        "avatar": "",
        "agegroup": "",
    }

    await update.effective_message.reply_text(
        "👋 Willkommen bei der Registrierung des LOL Studios Manager!\n\n"
        "Schritt 1 von 4: Wie möchtest du im Bot heißen?\n"
        "Bitte gib einen Namen mit 2–40 Zeichen ein."
    )
    return NAME


async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = (update.effective_message.text or "").strip()

    if not 2 <= len(name) <= 40:
        await update.effective_message.reply_text(
            "Bitte gib einen Namen mit 2–40 Zeichen ein."
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
        "Schritt 2 von 4: Wähle deine Altersgruppe.",
        reply_markup=InlineKeyboardMarkup(buttons),
    )
    return AGEGROUP


async def get_agegroup(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    query = update.callback_query
    await query.answer()

    data = query.data or ""
    if not data.startswith("reg:age:"):
        return AGEGROUP

    value = data.split(":", 2)[2]
    allowed = {age_value for _, age_value in AGE_GROUPS}

    context.user_data["registration"]["agegroup"] = (
        "" if value == "skip" else value if value in allowed else ""
    )

    await query.edit_message_text(
        "Schritt 3 von 4: Schreibe eine kurze Bio über dich.\n"
        "Du kannst auch /skip senden."
    )
    return BIO


async def get_bio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    bio = (update.effective_message.text or "").strip()

    if len(bio) > 250:
        await update.effective_message.reply_text(
            "Die Bio darf maximal 250 Zeichen lang sein. "
            "Bitte kürze sie oder sende /skip."
        )
        return BIO

    context.user_data["registration"]["bio"] = bio
    await ask_for_avatar(update, context)
    return AVATAR


async def skip_bio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["registration"]["bio"] = ""
    await ask_for_avatar(update, context)
    return AVATAR


async def ask_for_avatar(update, context):
    await update.effective_message.reply_text(
        "Schritt 4 von 4: Sende ein Foto als Avatar.\n"
        "Das Foto wird als Telegram-Datei-ID gespeichert. "
        "Alternativ kannst du /skip senden."
    )


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


async def skip_not_allowed(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    await update.effective_message.reply_text(
        "Diesen Schritt kannst du nicht überspringen. "
        "Bitte beantworte die aktuelle Frage oder nutze /cancel."
    )
    return ConversationHandler.END if False else context.user_data.get(
        "registration_state", NAME
    )


async def finish_registration(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
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
        "✅ **Registrierung abgeschlossen!**\n\n"
        "Du kannst jetzt die Commands des LOL Studios Manager verwenden.\n"
        "Öffne /menu, um die verfügbaren Funktionen zu sehen.",
        parse_mode="Markdown",
    )


async def cancel_registration(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    context.user_data["registration_active"] = False
    context.user_data.pop("registration", None)

    await update.effective_message.reply_text(
        "Registrierung abgebrochen. Du kannst jederzeit wieder /register nutzen."
    )
    return ConversationHandler.END


async def profile_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    user = update.effective_user
    account = database.get_account(user.id)

    if not account:
        await update.effective_message.reply_text(
            "Du hast noch kein Konto. Starte mit /register."
        )
        return

    username = (
        f"@{account['username']}" if account["username"] else "Nicht gesetzt"
    )
    agegroup = account["agegroup"] or "Nicht angegeben"
    bio = account["bio"] or "Keine Bio"

    caption = (
        f"👤 Profil: {account['name']}\n"
        f"🆔 Telegram-ID: {account['user_id']}\n"
        f"🔗 Username: {username}\n"
        f"🎂 Altersgruppe: {agegroup}\n"
        f"📝 Bio: {bio}"
    )

    if account["avatar"]:
        await update.effective_message.reply_photo(
            photo=account["avatar"],
            caption=caption,
        )
    else:
        await update.effective_message.reply_text(caption)


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
        fallbacks=[
            CommandHandler("cancel", cancel_registration),
        ],
        allow_reentry=True,
        name="registration",
        persistent=False,
    )
