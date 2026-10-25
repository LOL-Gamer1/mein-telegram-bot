# group_moderation.py — LOL Studios Manager
# Gruppenmoderation für python-telegram-bot v20+

from telegram import Update, ChatPermissions
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
)
from telegram.error import TelegramError


GROUP_TYPES = ("group", "supergroup")


async def _is_group_admin(update, context):
    msg = update.effective_message
    user = update.effective_user

    if not msg or not user or msg.chat.type not in GROUP_TYPES:
        if msg:
            await msg.reply_text("Dieser Befehl funktioniert nur in Gruppen.")
        return False

    try:
        member = await context.bot.get_chat_member(msg.chat_id, user.id)
        if member.status not in ("administrator", "creator"):
            await msg.reply_text("⛔ Diesen Befehl dürfen nur Gruppenadmins verwenden.")
            return False

        bot_member = await context.bot.get_chat_member(msg.chat_id, context.bot.id)
        if bot_member.status != "administrator":
            await msg.reply_text("⚠️ Bitte mache mich zuerst zum Gruppenadmin.")
            return False

        return True
    except TelegramError:
        await msg.reply_text("Ich konnte deine Gruppenrechte nicht prüfen. Bitte kontrolliere meine Adminrechte.")
        return False


async def _find_target(update, context):
    """Sucht eine Person per Antwort oder numerischer Telegram-ID."""
    msg = update.effective_message
    if not msg:
        return None

    if msg.reply_to_message and msg.reply_to_message.from_user:
        return msg.reply_to_message.from_user

    if context.args:
        value = context.args[0].strip()

        # Telegrams Bot API kann einen beliebigen @username nicht zuverlässig
        # in eine User-ID umwandeln. IDs funktionieren dagegen zuverlässig.
        if value.startswith("@"):
            return None

        try:
            user_id = int(value)
            member = await context.bot.get_chat_member(msg.chat_id, user_id)
            return member.user
        except (ValueError, TelegramError):
            return None

    return None


async def _target_help(msg, command):
    await msg.reply_text(
        f"Markiere die Person am einfachsten, indem du auf ihre Nachricht antwortest und "
        f"/{command} schreibst.\n\n"
        f"Alternativ: /{command} TELEGRAM_ID\n"
        f"Ein beliebiger @username lässt sich von Telegram-Bots nicht immer auflösen."
    )


async def admins_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    if not msg or msg.chat.type not in GROUP_TYPES:
        if msg:
            await msg.reply_text("Das funktioniert nur in Gruppen.")
        return

    try:
        admins = await context.bot.get_chat_administrators(msg.chat_id)
        lines = ["🛡️ **Gruppenadmins**"]
        for item in admins:
            u = item.user
            suffix = f" (@{u.username})" if u.username else ""
            lines.append(f"• {u.full_name}{suffix}")
        await msg.reply_text("\n".join(lines), parse_mode="Markdown")
    except TelegramError:
        await msg.reply_text("Die Adminliste konnte ich gerade nicht laden.")


async def groupinfo_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    if not msg or msg.chat.type not in GROUP_TYPES:
        if msg:
            await msg.reply_text("Das funktioniert nur in Gruppen.")
        return

    try:
        count = await context.bot.get_chat_member_count(msg.chat_id)
        await msg.reply_text(
            "ℹ️ Gruppeninfo\n\n"
            f"Name: {msg.chat.title or '—'}\n"
            f"Chat-ID: {msg.chat_id}\n"
            f"Typ: {msg.chat.type}\n"
            f"Mitglieder: {count}"
        )
    except TelegramError:
        await msg.reply_text("Die Gruppeninfos konnten nicht geladen werden.")


async def grouplink_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    if not await _is_group_admin(update, context):
        return

    try:
        chat = await context.bot.get_chat(msg.chat_id)
        link = chat.invite_link or await context.bot.export_chat_invite_link(msg.chat_id)
        await msg.reply_text(f"🔗 Gruppenlink:\n{link}")
    except TelegramError:
        await msg.reply_text("Ich brauche die Adminberechtigung zum Verwalten von Einladungslinks.")


async def kick_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    if not await _is_group_admin(update, context):
        return

    target = await _find_target(update, context)
    if not target:
        await _target_help(msg, "kick")
        return

    if target.id in (update.effective_user.id, context.bot.id):
        await msg.reply_text("Das geht nicht: Du kannst dich selbst oder mich nicht damit entfernen.")
        return

    try:
        await context.bot.ban_chat_member(msg.chat_id, target.id)
        await context.bot.unban_chat_member(msg.chat_id, target.id, only_if_banned=True)
        await msg.reply_text(f"👢 {target.full_name} wurde aus der Gruppe entfernt.")
    except TelegramError:
        await msg.reply_text("Das Entfernen ist fehlgeschlagen. Prüfe meine Rechte und die Admin-Rangfolge.")


async def promote_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    if not await _is_group_admin(update, context):
        return

    target = await _find_target(update, context)
    if not target:
        await _target_help(msg, "promote")
        return

    if target.id == context.bot.id:
        await msg.reply_text("Ich bin bereits in der Gruppe – bitte ändere meine Rechte direkt in Telegram.")
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
        await msg.reply_text(f"⬆️ {target.full_name} wurde zum Admin befördert, soweit es meine Rechte erlauben.")
    except TelegramError:
        await msg.reply_text("Das Befördern ist fehlgeschlagen. Prüfe meine Rechte und deine Admin-Rangfolge.")


async def demote_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    if not await _is_group_admin(update, context):
        return

    target = await _find_target(update, context)
    if not target:
        await _target_help(msg, "demote")
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
        await msg.reply_text(f"⬇️ Adminrechte von {target.full_name} wurden entfernt.")
    except TelegramError:
        await msg.reply_text("Das Zurückstufen ist fehlgeschlagen. Prüfe die Admin-Rangfolge.")


async def pin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    if not await _is_group_admin(update, context):
        return
    if not msg.reply_to_message:
        await msg.reply_text("Antworte auf die Nachricht, die angepinnt werden soll, und schreibe /pin.")
        return

    try:
        await msg.reply_to_message.pin()
        await msg.reply_text("📌 Nachricht angepinnt.")
    except TelegramError:
        await msg.reply_text("Das Anpinnen ist fehlgeschlagen. Prüfe meine Rechte.")


async def del_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    if not await _is_group_admin(update, context):
        return
    if not msg.reply_to_message:
        await msg.reply_text("Antworte auf die Nachricht, die gelöscht werden soll, und schreibe /del.")
        return

    try:
        await msg.reply_to_message.delete()
        await msg.delete()
    except TelegramError:
        await msg.reply_text("Das Löschen ist fehlgeschlagen. Prüfe meine Rechte.")


async def usermute_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    if not await _is_group_admin(update, context):
        return

    target = await _find_target(update, context)
    if not target:
        await _target_help(msg, "usermute")
        return

    if target.id == context.bot.id:
        await msg.reply_text("Ich kann mich nicht selbst stummschalten.")
        return

    try:
        await context.bot.restrict_chat_member(
            msg.chat_id,
            target.id,
            ChatPermissions(can_send_messages=False),
        )
        await msg.reply_text(f"🔇 {target.full_name} kann vorerst nicht mehr schreiben.")
    except TelegramError:
        await msg.reply_text("Das Stummschalten ist fehlgeschlagen. Prüfe meine Rechte.")


async def userunmute_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    if not await _is_group_admin(update, context):
        return

    target = await _find_target(update, context)
    if not target:
        await _target_help(msg, "userunmute")
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
        await msg.reply_text("Das Entstummen ist fehlgeschlagen. Prüfe meine Rechte.")


async def mute_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Schaltet normale Mitglieder in der gesamten Gruppe stumm."""
    msg = update.effective_message
    if not await _is_group_admin(update, context):
        return

    try:
        await context.bot.set_chat_permissions(
            msg.chat_id,
            ChatPermissions(can_send_messages=False),
        )
        await msg.reply_text(
            "🔇 Schreibrechte für normale Mitglieder wurden deaktiviert.\n"
            "Gruppenadmins können weiterhin schreiben.\n"
            "Nutze /unmute, um die Gruppen-Schreibrechte wiederherzustellen."
        )
    except TelegramError:
        await msg.reply_text("Ich konnte die Gruppen-Schreibrechte nicht ändern. Prüfe meine Adminrechte.")


async def unmute_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Stellt allgemeine Schreibrechte der Gruppe wieder her."""
    msg = update.effective_message
    if not await _is_group_admin(update, context):
        return

    try:
        await context.bot.set_chat_permissions(
            msg.chat_id,
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
        await msg.reply_text("🔊 Gruppen-Schreibrechte wurden wieder aktiviert.")
    except TelegramError:
        await msg.reply_text("Ich konnte die Gruppen-Schreibrechte nicht wiederherstellen. Prüfe meine Adminrechte.")


async def rules_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    if not msg:
        return

    rules = " ".join(context.args).strip()
    if rules:
        if not await _is_group_admin(update, context):
            return
        context.chat_data["group_rules"] = rules[:3500]
        await msg.reply_text("📜 Regeln gespeichert. Hinweis: Diese Speicherung gilt nur, solange der Bot läuft.")
    else:
        saved = context.chat_data.get("group_rules", "Für diese Gruppe wurden noch keine Regeln festgelegt.")
        await msg.reply_text(f"📜 Gruppenregeln:\n{saved}")


async def grouprules_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await rules_command(update, context)


async def welcome_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    if not await _is_group_admin(update, context):
        return

    text = " ".join(context.args).strip()
    if not text:
        await msg.reply_text("Schreibe zum Beispiel: /welcome Willkommen {name}!")
        return

    context.chat_data["welcome_text"] = text[:1000]
    await msg.reply_text("✅ Begrüßungstext gespeichert. Automatische Begrüßungen sind damit noch nicht aktiviert.")


async def leave_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    if not await _is_group_admin(update, context):
        return
    await msg.reply_text("Ich verlasse die Gruppe jetzt auf Admin-Anfrage.")
    await context.bot.leave_chat(msg.chat_id)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.effective_message.reply_text(
        "🛡️ GRUPPENMODERATION\n\n"
        "/admins – Gruppenadmins anzeigen\n"
        "/groupinfo – Gruppeninfos\n"
        "/grouplink – Einladungslink\n"
        "/kick – auf Nachricht antworten oder ID angeben\n"
        "/promote – Adminrechte vergeben\n"
        "/demote – Adminrechte entfernen\n"
        "/pin – Nachricht anpinnen\n"
        "/del – beantwortete Nachricht löschen\n"
        "/mute – normale Mitglieder in der Gruppe stummschalten\n"
        "/unmute – Gruppen-Schreibrechte wieder aktivieren\n"
        "/usermute – einzelne Person stummschalten\n"
        "/userunmute – einzelne Person entstummen\n"
        "/grouprules TEXT – Gruppenregeln setzen\n"
        "/grouprules – Regeln anzeigen\n"
        "/welcome TEXT – Begrüßungstext speichern\n"
        "/leave – Bot aus der Gruppe entfernen\n"
        "/modhelp – diese Hilfe anzeigen\n\n"
        "Tipp: Bei Befehlen für einzelne Personen einfach auf ihre Nachricht antworten."
    )


def register_group_handlers(application: Application):
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
        ("mute", mute_command),
        ("unmute", unmute_command),
        ("usermute", usermute_command),
        ("muteuser", usermute_command),
        ("userunmute", userunmute_command),
        ("unmuteuser", userunmute_command),
        ("grouprules", grouprules_command),
        ("rules", rules_command),
        ("welcome", welcome_command),
        ("leave", leave_command),
        ("modhelp", help_command),
    ]

    for name, callback in handlers:
        application.add_handler(CommandHandler(name, callback), group=1)
