# group_moderation.py — LOL Studios Manager
# Gruppenmoderation für python-telegram-bot v20+

import re
import time
from collections import defaultdict, deque

import database
from telegram import Update, ChatPermissions
from telegram.error import TelegramError
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ChatMemberHandler,
    ContextTypes,
    filters,
)

GROUP_TYPES = ("group", "supergroup")

# Anti-Spam: Nachrichten der letzten Sekunden pro Nutzer
SPAM_TIMES = defaultdict(deque)
SPAM_WINDOW = 8
SPAM_LIMIT = 5

# Einfache Wortliste für den Beleidigungsfilter.
# Bei Bedarf kannst du sie später erweitern.
INSULT_WORDS = {
    "idiot", "idioten", "dummkopf", "depp", "deppen",
    "arschloch", "arschlöcher", "hurensohn", "hurensöhne",
    "wichser", "mistkerl", "blödmann", "vollidiot",
}


# --------------------------------------------------
# HILFSFUNKTIONEN
# --------------------------------------------------

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
            await msg.reply_text(
                "⛔ Diesen Befehl dürfen nur Gruppenadmins verwenden."
            )
            return False

        bot_member = await context.bot.get_chat_member(
            msg.chat_id, context.bot.id
        )

        if bot_member.status != "administrator":
            await msg.reply_text(
                "⚠️ Bitte mache mich zuerst zum Gruppenadmin."
            )
            return False

        return True

    except TelegramError:
        await msg.reply_text(
            "Ich konnte deine Gruppenrechte nicht prüfen. "
            "Bitte kontrolliere meine Adminrechte."
        )
        return False


async def _find_target(update, context):
    """Nutzer per Antwort auf eine Nachricht oder per Telegram-ID finden."""
    msg = update.effective_message

    if not msg:
        return None

    if msg.reply_to_message and msg.reply_to_message.from_user:
        return msg.reply_to_message.from_user

    if context.args:
        value = context.args[0].strip()

        if value.startswith("@"):
            return None

        try:
            member = await context.bot.get_chat_member(
                msg.chat_id, int(value)
            )
            return member.user
        except (ValueError, TelegramError):
            return None

    return None


async def _target_help(msg, command):
    await msg.reply_text(
        f"Antworte auf eine Nachricht der Person und schreibe /{command}.\n\n"
        f"Alternativ: /{command} TELEGRAM_ID\n"
        "Ein @username lässt sich nicht immer auflösen."
    )


# --------------------------------------------------
# GRUPPENINFORMATIONEN
# --------------------------------------------------

async def admins_command(update, context):
    msg = update.effective_message
    if not msg or msg.chat.type not in GROUP_TYPES:
        if msg:
            await msg.reply_text("Das funktioniert nur in Gruppen.")
        return

    try:
        admins = await context.bot.get_chat_administrators(msg.chat_id)
        lines = ["🛡️ Gruppenadmins"]

        for item in admins:
            user = item.user
            suffix = f" (@{user.username})" if user.username else ""
            lines.append(f"• {user.full_name}{suffix}")

        await msg.reply_text("\n".join(lines))

    except TelegramError:
        await msg.reply_text("Die Adminliste konnte nicht geladen werden.")


async def groupinfo_command(update, context):
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


async def grouplink_command(update, context):
    msg = update.effective_message
    if not await _is_group_admin(update, context):
        return

    try:
        chat = await context.bot.get_chat(msg.chat_id)
        link = chat.invite_link

        if not link:
            link = await context.bot.export_chat_invite_link(msg.chat_id)

        await msg.reply_text(f"🔗 Gruppenlink:\n{link}")

    except TelegramError:
        await msg.reply_text(
            "Ich brauche die Adminberechtigung zum Verwalten von Einladungslinks."
        )


# --------------------------------------------------
# MITGLIEDER VERWALTEN
# --------------------------------------------------

async def kick_command(update, context):
    msg = update.effective_message
    if not await _is_group_admin(update, context):
        return

    target = await _find_target(update, context)
    if not target:
        await _target_help(msg, "kick")
        return

    if target.id in (update.effective_user.id, context.bot.id):
        await msg.reply_text("Du kannst dich selbst oder den Bot nicht so entfernen.")
        return

    try:
        await context.bot.ban_chat_member(msg.chat_id, target.id)
        await context.bot.unban_chat_member(
            msg.chat_id, target.id, only_if_banned=True
        )
        await msg.reply_text(f"👢 {target.full_name} wurde entfernt.")

    except TelegramError:
        await msg.reply_text(
            "Entfernen fehlgeschlagen. Prüfe meine Rechte und die Admin-Rangfolge."
        )


async def promote_command(update, context):
    msg = update.effective_message
    if not await _is_group_admin(update, context):
        return

    target = await _find_target(update, context)
    if not target:
        await _target_help(msg, "promote")
        return

    if target.id == context.bot.id:
        await msg.reply_text("Ändere meine Rechte direkt in den Telegram-Gruppeneinstellungen.")
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
            f"⬆️ Adminrechte für {target.full_name} wurden angefordert."
        )

    except TelegramError:
        await msg.reply_text(
            "Befördern fehlgeschlagen. Prüfe deine Rechte und die Admin-Rangfolge."
        )


async def demote_command(update, context):
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
        await msg.reply_text("Zurückstufen fehlgeschlagen. Prüfe die Admin-Rangfolge.")


async def pin_command(update, context):
    msg = update.effective_message
    if not await _is_group_admin(update, context):
        return

    if not msg.reply_to_message:
        await msg.reply_text(
            "Antworte auf die Nachricht, die angepinnt werden soll, und schreibe /pin."
        )
        return

    try:
        await msg.reply_to_message.pin()
        await msg.reply_text("📌 Nachricht angepinnt.")
    except TelegramError:
        await msg.reply_text("Anpinnen fehlgeschlagen. Prüfe meine Rechte.")


async def del_command(update, context):
    msg = update.effective_message
    if not await _is_group_admin(update, context):
        return

    if not msg.reply_to_message:
        await msg.reply_text(
            "Antworte auf die zu löschende Nachricht und schreibe /del."
        )
        return

    try:
        await msg.reply_to_message.delete()
        await msg.delete()
    except TelegramError:
        await msg.reply_text("Löschen fehlgeschlagen. Prüfe meine Rechte.")


async def usermute_command(update, context):
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
        await msg.reply_text(f"🔇 {target.full_name} wurde stummgeschaltet.")

    except TelegramError:
        await msg.reply_text("Stummschalten fehlgeschlagen. Prüfe meine Rechte.")


async def userunmute_command(update, context):
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
        await msg.reply_text("Entstummen fehlgeschlagen. Prüfe meine Rechte.")


async def mute_command(update, context):
    msg = update.effective_message
    if not await _is_group_admin(update, context):
        return

    try:
        await context.bot.set_chat_permissions(
            msg.chat_id,
            ChatPermissions(can_send_messages=False),
        )
        await msg.reply_text(
            "🔇 Normale Mitglieder können nicht mehr schreiben.\n"
            "Mit /unmute kannst du die Schreibrechte wieder aktivieren."
        )
    except TelegramError:
        await msg.reply_text("Gruppen-Stummschaltung fehlgeschlagen.")


async def unmute_command(update, context):
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
        await msg.reply_text("Schreibrechte konnten nicht wiederhergestellt werden.")


# --------------------------------------------------
# DAUERHAFTE REGELN UND BEGRÜSSUNGSTEXT
# --------------------------------------------------

async def rules_command(update, context):
    msg = update.effective_message
    if not msg:
        return

    rules = " ".join(context.args).strip()

    if rules:
        if not await _is_group_admin(update, context):
            return

        database.set_group_setting(msg.chat_id, "rules", rules[:3500])
        await msg.reply_text("📜 Gruppenregeln dauerhaft gespeichert.")
    else:
        saved = database.get_group_settings(msg.chat_id).get("rules")
        await msg.reply_text(
            "📜 Gruppenregeln:\n"
            + (saved or "Für diese Gruppe wurden noch keine Regeln festgelegt.")
        )


async def grouprules_command(update, context):
    await rules_command(update, context)


async def welcome_command(update, context):
    msg = update.effective_message
    if not await _is_group_admin(update, context):
        return

    text = " ".join(context.args).strip()

    if not text:
        settings = database.get_group_settings(msg.chat_id)
        await msg.reply_text(
            "Aktueller Begrüßungstext:\n"
            + settings.get("welcome_text", "Willkommen {name}!")
            + "\n\nBeispiel: /welcome Willkommen {name}!"
        )
        return

    database.set_group_setting(msg.chat_id, "welcome_text", text[:1000])
    await msg.reply_text(
        "✅ Begrüßungstext gespeichert.\n"
        "Aktiviere die automatische Begrüßung mit /welcometoggle an."
    )


# --------------------------------------------------
# MODERATION EIN- UND AUSSCHALTEN
# --------------------------------------------------

async def _toggle(update, context, setting, label):
    msg = update.effective_message
    if not await _is_group_admin(update, context):
        return

    if not context.args or context.args[0].lower() not in ("an", "aus", "on", "off"):
        enabled = bool(
            database.get_group_settings(msg.chat_id).get(setting, 0)
        )
        await msg.reply_text(
            f"{label}: {'AN' if enabled else 'AUS'}\n"
            "Verwende an oder aus, zum Beispiel /antispam an."
        )
        return

    enabled = context.args[0].lower() in ("an", "on")
    database.set_group_setting(msg.chat_id, setting, int(enabled))
    await msg.reply_text(
        f"✅ {label} ist jetzt {'AN' if enabled else 'AUS'}."
    )


async def antispam_command(update, context):
    await _toggle(update, context, "anti_spam", "Anti-Spam")


async def antiinsult_command(update, context):
    await _toggle(update, context, "anti_insult", "Beleidigungsfilter")


async def antisticker_command(update, context):
    await _toggle(update, context, "anti_sticker", "Anti-Sticker")


async def welcometoggle_command(update, context):
    await _toggle(
        update, context, "welcome_enabled", "Automatische Begrüßung"
    )


# --------------------------------------------------
# VERWARNUNGSSYSTEM
# --------------------------------------------------

async def warn_command(update, context):
    msg = update.effective_message
    if not await _is_group_admin(update, context):
        return

    target = await _find_target(update, context)
    if not target:
        await _target_help(msg, "warn")
        return

    if target.id == context.bot.id:
        await msg.reply_text("Ich kann mich nicht selbst verwarnen.")
        return

    count = database.add_group_warning(msg.chat_id, target.id)
    settings = database.get_group_settings(msg.chat_id)
    limit = max(1, int(settings.get("warning_limit", 3)))

    if count >= limit:
        try:
            await context.bot.ban_chat_member(msg.chat_id, target.id)
            await msg.reply_text(
                f"⛔ {target.full_name} hat {count} Verwarnungen erreicht "
                "und wurde aus der Gruppe entfernt."
            )
        except TelegramError:
            await msg.reply_text(
                f"⚠️ {target.full_name}: {count}/{limit} Verwarnungen. "
                "Entfernen fehlgeschlagen; prüfe meine Rechte."
            )
    else:
        await msg.reply_text(
            f"⚠️ {target.full_name} wurde verwarnt ({count}/{limit})."
        )


async def warnings_command(update, context):
    msg = update.effective_message
    if not await _is_group_admin(update, context):
        return

    target = await _find_target(update, context)
    if not target:
        await _target_help(msg, "warnings")
        return

    count = database.get_group_warnings(msg.chat_id, target.id)
    await msg.reply_text(
        f"⚠️ {target.full_name} hat {count} Verwarnung(en)."
    )


async def resetwarnings_command(update, context):
    msg = update.effective_message
    if not await _is_group_admin(update, context):
        return

    target = await _find_target(update, context)
    if not target:
        await _target_help(msg, "resetwarnings")
        return

    database.reset_group_warnings(msg.chat_id, target.id)
    await msg.reply_text(
        f"✅ Verwarnungen von {target.full_name} wurden zurückgesetzt."
    )


# --------------------------------------------------
# AUTOMATISCHE MODERATION
# --------------------------------------------------

async def _moderation_filter(update, context):
    msg = update.effective_message
    user = update.effective_user

    if not msg or not user or msg.chat.type not in GROUP_TYPES or user.is_bot:
        return

    try:
        member = await context.bot.get_chat_member(msg.chat_id, user.id)

        # Gruppenadmins nicht automatisch moderieren
        if member.status in ("administrator", "creator"):
            return

        settings = database.get_group_settings(msg.chat_id)

        # Sticker blockieren
        if msg.sticker and settings.get("anti_sticker"):
            await msg.delete()
            return

        # Beleidigungsfilter
        if settings.get("anti_insult") and msg.text:
            words = set(
                re.findall(r"[^\W_]+", msg.text.lower(), flags=re.UNICODE)
            )

            if words & INSULT_WORDS:
                await msg.delete()
                await msg.reply_text(
                    "🚫 Bitte bleib respektvoll. Beleidigungen sind hier nicht erlaubt."
                )
                return

        # Anti-Spam: mindestens 5 Textnachrichten innerhalb von 8 Sekunden
        if settings.get("anti_spam") and msg.text:
            key = (msg.chat_id, user.id)
            now = time.monotonic()
            history = SPAM_TIMES[key]

            while history and now - history[0] > SPAM_WINDOW:
                history.popleft()

            history.append(now)

            if len(history) >= SPAM_LIMIT:
                await msg.delete()
                history.clear()
                await msg.reply_text("🚫 Bitte nicht spammen.")

    except TelegramError:
        # Fehlende Telegram-Rechte können die Moderation verhindern.
        return
    except Exception:
        # Ein vorübergehender Datenbankfehler soll den Bot nicht abstürzen lassen.
        return


async def _welcome_new_members(update, context):
    change = update.chat_member
    if not change or not update.effective_chat:
        return

    old_status = change.old_chat_member.status
    new_status = change.new_chat_member.status

    if new_status not in ("member", "administrator"):
        return

    if old_status in ("member", "administrator", "creator"):
        return

    try:
        settings = database.get_group_settings(update.effective_chat.id)

        if not settings.get("welcome_enabled"):
            return

        user = change.new_chat_member.user
        template = settings.get("welcome_text") or "Willkommen {name}!"

        welcome = template.replace("{name}", user.full_name)
        welcome = welcome.replace(
            "{username}",
            "@" + user.username if user.username else user.full_name,
        )

        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=welcome[:1000],
        )

    except Exception:
        return


# --------------------------------------------------
# HILFE UND BOT VERLASSEN
# --------------------------------------------------

async def leave_command(update, context):
    msg = update.effective_message
    if not await _is_group_admin(update, context):
        return

    await msg.reply_text("Ich verlasse die Gruppe jetzt auf Admin-Anfrage.")
    await context.bot.leave_chat(msg.chat_id)


async def help_command(update, context):
    msg = update.effective_message
    if not msg:
        return

    await msg.reply_text(
        "🛡️ GRUPPENMODERATION\n\n"
        "/admins – Gruppenadmins anzeigen\n"
        "/groupinfo – Gruppeninfos\n"
        "/grouplink – Einladungslink\n"
        "/kick – Nutzer entfernen\n"
        "/promote – Adminrechte vergeben\n"
        "/demote – Adminrechte entfernen\n"
        "/pin – Nachricht anpinnen\n"
        "/del – Nachricht löschen\n"
        "/mute – normale Mitglieder stummschalten\n"
        "/unmute – Gruppen-Schreibrechte wiederherstellen\n"
        "/usermute – einzelne Person stummschalten\n"
        "/userunmute – einzelne Person entstummen\n\n"
        "AUTOMATISCHE MODERATION\n"
        "/antispam an|aus – Anti-Spam\n"
        "/antiinsult an|aus – Beleidigungsfilter\n"
        "/antisticker an|aus – Sticker blockieren\n"
        "/welcometoggle an|aus – automatische Begrüßung\n"
        "/welcome TEXT – Begrüßungstext setzen\n"
        "/rules TEXT – Regeln speichern\n"
        "/rules – Regeln anzeigen\n\n"
        "VERWARNUNGEN\n"
        "/warn – Nutzer verwarnen\n"
        "/warnings – Verwarnungen anzeigen\n"
        "/resetwarnings – Verwarnungen zurücksetzen\n\n"
        "/leave – Bot aus der Gruppe entfernen\n"
        "/modhelp – diese Hilfe anzeigen\n\n"
        "Bei Nutzerbefehlen antworte auf eine Nachricht oder verwende die Telegram-ID."
    )


# --------------------------------------------------
# HANDLER REGISTRIEREN
# --------------------------------------------------

def register_group_handlers(application: Application):
    commands = [
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
        ("rules", rules_command),
        ("grouprules", grouprules_command),
        ("welcome", welcome_command),
        ("leave", leave_command),
        ("modhelp", help_command),
        ("antispam", antispam_command),
        ("antiinsult", antiinsult_command),
        ("antibeleidigung", antiinsult_command),
        ("antisticker", antisticker_command),
        ("welcometoggle", welcometoggle_command),
        ("warn", warn_command),
        ("warnings", warnings_command),
        ("resetwarnings", resetwarnings_command),
    ]

    for name, callback in commands:
        application.add_handler(
            CommandHandler(name, callback),
            group=1,
        )

    # Textnachrichten und Sticker prüfen
    application.add_handler(
        MessageHandler(
            filters.ChatType.GROUPS
            & ~filters.COMMAND
            & (filters.TEXT | filters.Sticker.ALL),
            _moderation_filter,
        ),
        group=2,
    )

    # Automatische Begrüßung bei Änderungen des Mitgliedsstatus
    application.add_handler(
        ChatMemberHandler(
            _welcome_new_members,
            ChatMemberHandler.CHAT_MEMBER,
        ),
        group=2,
    )
