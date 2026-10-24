# group_moderation.py — Gruppenmoderation für LOL Studios Manager

from telegram import Update, ChatPermissions
from telegram.ext import CommandHandler, ContextTypes
from telegram.error import TelegramError


async def _is_group_admin(update, context):
    msg = update.effective_message
    user = update.effective_user

    if not msg or not user or msg.chat.type not in ("group", "supergroup"):
        if msg:
            await msg.reply_text("Dieser Befehl funktioniert nur in Gruppen.")
        return False

    try:
        member = await context.bot.get_chat_member(msg.chat_id, user.id)

        if member.status not in ("administrator", "creator"):
            await msg.reply_text(
                "⛔ Nur Gruppenadmins dürfen diesen Befehl verwenden."
            )
            return False

        bot_member = await context.bot.get_chat_member(
            msg.chat_id,
            context.bot.id,
        )

        if bot_member.status != "administrator":
            await msg.reply_text(
                "⚠️ Bitte mache den Bot zuerst zum Gruppenadmin."
            )
            return False

        return True

    except TelegramError:
        await msg.reply_text(
            "Konnte Gruppenrechte nicht prüfen. "
            "Bitte kontrolliere die Adminrechte des Bots."
        )
        return False


async def admins_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message

    if not msg or msg.chat.type not in ("group", "supergroup"):
        if msg:
            await msg.reply_text("Nur in Gruppen verfügbar.")
        return

    try:
        admins = await context.bot.get_chat_administrators(msg.chat_id)
        lines = ["🛡️ Gruppenadmins:"]

        for member in admins:
            user = member.user
            if user.username:
                lines.append(f"• {user.full_name} (@{user.username})")
            else:
                lines.append(f"• {user.full_name} (ID {user.id})")

        await msg.reply_text("\n".join(lines))

    except TelegramError:
        await msg.reply_text("Admins konnten nicht geladen werden.")


async def groupinfo_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message

    if not msg or msg.chat.type not in ("group", "supergroup"):
        if msg:
            await msg.reply_text("Nur in Gruppen verfügbar.")
        return

    chat = msg.chat

    try:
        count = await context.bot.get_chat_member_count(chat.id)
        await msg.reply_text(
            "ℹ️ GRUPPENINFO\n"
            f"Name: {chat.title or '—'}\n"
            f"Chat-ID: {chat.id}\n"
            f"Typ: {chat.type}\n"
            f"Mitglieder: {count}"
        )
    except TelegramError:
        await msg.reply_text("Gruppeninformationen konnten nicht geladen werden.")


async def grouplink_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message

    if not await _is_group_admin(update, context):
        return

    try:
        chat = await context.bot.get_chat(msg.chat_id)
        link = chat.invite_link

        if not link:
            link = await context.bot.export_chat_invite_link(msg.chat_id)

        await msg.reply_text(f"🔗 Gruppenlink: {link}")

    except TelegramError:
        await msg.reply_text(
            "Der Bot benötigt die Berechtigung, Einladungslinks zu verwalten."
        )


async def _find_target(update, context):
    msg = update.effective_message

    if msg.reply_to_message and msg.reply_to_message.from_user:
        return msg.reply_to_message.from_user

    if context.args:
        try:
            member = await context.bot.get_chat_member(
                msg.chat_id,
                int(context.args[0]),
            )
            return member.user
        except (ValueError, TelegramError):
            return None

    return None


async def kick_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message

    if not await _is_group_admin(update, context):
        return

    target = await _find_target(update, context)

    if not target:
        await msg.reply_text(
            "Antworte auf eine Nachricht oder nutze /kick TELEGRAM_ID."
        )
        return

    if target.id in (update.effective_user.id, context.bot.id):
        await msg.reply_text(
            "Diese Person kann mit diesem Befehl nicht entfernt werden."
        )
        return

    try:
        await context.bot.ban_chat_member(msg.chat_id, target.id)
        await context.bot.unban_chat_member(
            msg.chat_id,
            target.id,
            only_if_banned=True,
        )
        await msg.reply_text(
            f"👢 {target.full_name} wurde aus der Gruppe entfernt."
        )
    except TelegramError:
        await msg.reply_text(
            "Entfernen fehlgeschlagen. Prüfe Adminrechte und Admin-Rangfolge."
        )


async def promote_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message

    if not await _is_group_admin(update, context):
        return

    target = await _find_target(update, context)

    if not target:
        await msg.reply_text(
            "Antworte auf eine Nachricht oder nutze /promote TELEGRAM_ID."
        )
        return

    try:
        await context.bot.promote_chat_member(
            msg.chat_id,
            target.id,
            can_manage_chat=True,
            can_delete_messages=True,
            can_restrict_members=True,
            can_invite_users=True,
            can_pin_messages=True,
            can_promote_members=False,
        )
        await msg.reply_text(
            f"⬆️ {target.full_name} wurde zum Gruppenadmin befördert."
        )
    except TelegramError:
        await msg.reply_text(
            "Beförderung fehlgeschlagen. Prüfe die Bot-Rechte."
        )


async def demote_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message

    if not await _is_group_admin(update, context):
        return

    target = await _find_target(update, context)

    if not target:
        await msg.reply_text(
            "Antworte auf eine Nachricht oder nutze /demote TELEGRAM_ID."
        )
        return

    try:
        await context.bot.promote_chat_member(
            msg.chat_id,
            target.id,
            can_manage_chat=False,
            can_delete_messages=False,
            can_manage_video_chats=False,
            can_restrict_members=False,
            can_promote_members=False,
            can_change_info=False,
            can_invite_users=False,
            can_pin_messages=False,
            can_post_messages=False,
            can_edit_messages=False,
        )
        await msg.reply_text(
            f"⬇️ Adminrechte von {target.full_name} wurden entfernt."
        )
    except TelegramError:
        await msg.reply_text(
            "Zurückstufen fehlgeschlagen. Prüfe die Bot-Rechte."
        )


async def pin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message

    if not await _is_group_admin(update, context):
        return

    if not msg.reply_to_message:
        await msg.reply_text(
            "Antworte auf die Nachricht, die angepinnt werden soll."
        )
        return

    try:
        await msg.reply_to_message.pin()
        await msg.reply_text("📌 Nachricht angepinnt.")
    except TelegramError:
        await msg.reply_text("Anpinnen fehlgeschlagen. Prüfe die Bot-Rechte.")


async def del_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message

    if not await _is_group_admin(update, context):
        return

    if not msg.reply_to_message:
        await msg.reply_text(
            "Antworte auf die Nachricht, die gelöscht werden soll."
        )
        return

    try:
        await msg.reply_to_message.delete()
        await msg.delete()
    except TelegramError:
        await msg.reply_text("Löschen fehlgeschlagen. Prüfe die Bot-Rechte.")


async def mute_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message

    if not await _is_group_admin(update, context):
        return

    target = await _find_target(update, context)

    if not target:
        await msg.reply_text(
            "Antworte auf eine Nachricht oder nutze /usermute TELEGRAM_ID."
        )
        return

    try:
        await context.bot.restrict_chat_member(
            msg.chat_id,
            target.id,
            ChatPermissions(can_send_messages=False),
        )
        await msg.reply_text(f"🔇 {target.full_name} wurde stummgeschaltet.")
    except TelegramError:
        await msg.reply_text("Stummschalten fehlgeschlagen. Prüfe die Bot-Rechte.")


async def unmute_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message

    if not await _is_group_admin(update, context):
        return

    target = await _find_target(update, context)

    if not target:
        await msg.reply_text(
            "Antworte auf eine Nachricht oder nutze /userunmute TELEGRAM_ID."
        )
        return

    try:
        await context.bot.restrict_chat_member(
            msg.chat_id,
            target.id,
            ChatPermissions(
                can_send_messages=True,
                can_send_audios=True,
                can_send_documents=True,
                can_send_photos=True,
                can_send_videos=True,
                can_send_video_notes=True,
                can_send_voice_notes=True,
                can_send_polls=True,
                can_send_other_messages=True,
                can_add_web_page_previews=True,
            ),
        )
        await msg.reply_text(f"🔊 {target.full_name} darf wieder schreiben.")
    except TelegramError:
        await msg.reply_text("Entstummen fehlgeschlagen. Prüfe die Bot-Rechte.")


async def rules_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    rules = " ".join(context.args).strip()

    if rules:
        if not await _is_group_admin(update, context):
            return

        context.chat_data["group_rules"] = rules[:3500]
        await msg.reply_text(
            "📜 Gruppenregeln gespeichert, solange der Bot läuft."
        )
    else:
        saved = context.chat_data.get(
            "group_rules",
            "Noch keine Regeln gesetzt. Admins können /grouprules REGELN senden.",
        )
        await msg.reply_text(f"📜 Gruppenregeln:\n{saved}")


async def welcome_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message

    if not await _is_group_admin(update, context):
        return

    text = " ".join(context.args).strip()

    if not text:
        await msg.reply_text("Verwendung: /welcome Willkommen {name}!")
        return

    context.chat_data["welcome_text"] = text[:1000]
    await msg.reply_text(
        "✅ Begrüßungstext gespeichert. Automatische Begrüßungen müssen separat aktiviert werden."
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.effective_message.reply_text(
        "🛡️ GRUPPENMODERATION\n\n"
        "/admins – Admins anzeigen\n"
        "/groupinfo – Gruppeninfos\n"
        "/grouplink – Einladungslink (Admin)\n"
        "/grouprules TEXT – Regeln setzen\n"
        "/kick – auf Nachricht antworten oder ID angeben\n"
        "/promote – Adminrechte vergeben\n"
        "/demote – Adminrechte entfernen\n"
        "/pin – Nachricht anpinnen\n"
        "/del – Nachricht löschen\n"
        "/usermute – Mitglied stummschalten\n"
        "/userunmute – Mitglied entstummen\n\n"
        "Massen-Kick und massenhaftes Markieren sind absichtlich nicht enthalten."
    )


def register_group_handlers(application):
    handlers = [
        ("admins", admins_command),
        ("admin", admins_command),
        ("groupinfo", groupinfo_command),
        ("gi", groupinfo_command),
        ("grouplink", grouplink_command),
        ("grouplid", grouplink_command),
        ("kick", kick_command),
        ("promote", promote_command),
        ("demote", demote_command),
        ("pin", pin_command),
        ("del", del_command),
        ("usermute", mute_command),
        ("muteuser", mute_command),
        ("userunmute", unmute_command),
        ("unmuteuser", unmute_command),
        ("grouprules", rules_command),
        ("welcome", welcome_command),
        ("modhelp", help_command),
    ]

    for name, callback in handlers:
        application.add_handler(
            CommandHandler(name, callback),
            group=1,
        )
