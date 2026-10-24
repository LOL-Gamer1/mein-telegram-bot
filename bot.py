from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ChatPermissions
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
from http.server import BaseHTTPRequestHandler, HTTPServer
import threading
import os
import time

# ⚠️ TRAGE HIER DEINEN ECHTEN TOKEN EIN! (Die Anführungszeichen "" müssen bleiben)
TOKEN = "DEIN_NEUER_TOKEN_VOM_BOTFATHER"

# Speicher für Verwarnungen
verwarnungen = {}

def run_health_server():
    class HealthCheckHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"Bot is alive")
    server = HTTPServer(('0.0.0.0', int(os.environ.get('PORT', 8080))), HealthCheckHandler)
    server.serve_forever()

# Hilfsfunktion: Prüft, ob der Absender Admin oder Ersteller ist
async def is_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    chat = update.effective_chat
    user_id = update.effective_user.id
    if chat.type == "private":
        return True
    member = await context.bot.get_chat_member(chat_id=chat.id, user_id=user_id)
    return member.status in ["administrator", "creator"]

# --- MODERATIONS COMMANDS ---

# Kick-Funktion (Hier war zuvor der Namensfehler behoben)
async def kick_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    if chat.type == "private":
        await update.message.reply_text("❌ Dieser Befehl funktioniert nur in Gruppen!")
        return
    if not await is_admin(update, context):
        await update.message.reply_text("❌ Du bist kein Admin in dieser Gruppe!")
        return
    if not update.message.reply_to_message:
        await update.message.reply_text("❌ Bitte antworte direkt auf die Nachricht des Nutzers, den du kicken willst.")
        return
    target_user = update.message.reply_to_message.from_user
    try:
        await chat.ban_member(user_id=target_user.id)
        await chat.unban_member(user_id=target_user.id)
        await update.message.reply_text(f"🎯 **{target_user.first_name}** wurde erfolgreich gekickt!")
    except Exception:
        await update.message.reply_text("❌ Fehler: Mir fehlen Admin-Rechte zum Kicken.")

# Befehl: /mute
async def mute_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    if chat.type == "private" or not await is_admin(update, context): return
    if not update.message.reply_to_message:
        await update.message.reply_text("❌ Bitte antworte auf die Nachricht des Nutzers, den du stummschalten willst.")
        return
    target_user = update.message.reply_to_message.from_user
    permissions = ChatPermissions(can_send_messages=False)
    try:
        until_time = int(time.time() + 600)
        await chat.restrict_member(user_id=target_user.id, permissions=permissions, until_date=until_time)
        await update.message.reply_text(f"🤫 **{target_user.first_name}** wurde für 10 Minuten stummgeschaltet!")
    except Exception:
        await update.message.reply_text("❌ Fehler: Mir fehlen Admin-Rechte.")

# Befehl: /unmute
async def unmute_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    if chat.type == "private" or not await is_admin(update, context): return
    if not update.message.reply_to_message:
        await update.message.reply_text("❌ Antworte auf die Nachricht des Nutzers, den du entstummen willst.")
        return
    target_user = update.message.reply_to_message.from_user
    full_permissions = ChatPermissions(
        can_send_messages=True, can_send_audios=True, can_send_documents=True,
        can_send_photos=True, can_send_videos=True, can_send_video_notes=True,
        can_send_voice_notes=True, can_send_polls=True, can_send_other_messages=True,
        can_add_web_page_previews=True, can_change_info=True, can_invite_users=True,
        can_pin_messages=True
    )
    try:
        await chat.restrict_member(user_id=target_user.id, permissions=full_permissions)
        await update.message.reply_text(f"🔊 **{target_user.first_name}** darf wieder schreiben!")
    except Exception:
        await update.message.reply_text("❌ Fehler: Mir fehlen Admin-Rechte.")

# Befehl: /warn
async def warn_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    if chat.type == "private" or not await is_admin(update, context): return
    if not update.message.reply_to_message:
        await update.message.reply_text("❌ Antworte auf eine Nachricht, um eine Verwarnung auszusprechen.")
        return
    target_user = update.message.reply_to_message.from_user
    u_id = target_user.id
    verwarnungen[u_id] = verwarnungen.get(u_id, 0) + 1
    anzahl = verwarnungen[u_id]
    if anzahl >= 3:
        try:
            await chat.ban_member(user_id=u_id)
            await chat.unban_member(user_id=u_id)
            verwarnungen[u_id] = 0
            await update.message.reply_text(f"🚨 **{target_user.first_name}** hat 3 Verwarnungen erreicht und wurde gekickt!")
        except Exception:
            await update.message.reply_text("❌ Fehler beim Kicken nach der 3. Verwarnung.")
    else:
        await update.message.reply_text(f"⚠️ **{target_user.first_name}** wurde verwarnt! Stand: [{anzahl}/3]")

# Befehl: /pin
async def pin_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    if chat.type == "private" or not await is_admin(update, context): return
    if not update.message.reply_to_message:
        await update.message.reply_text("❌ Antworte auf die Nachricht, die angeheftet werden soll.")
        return
    try:
        await context.bot.pin_chat_message(chat_id=chat.id, message_id=update.message.reply_to_message.message_id)
        await update.message.reply_text("📌 Nachricht wurde oben angeheftet!")
    except Exception:
        await update.message.reply_text("❌ Fehler: Ich darf keine Nachrichten anheften.")

# Befehl: /say
async def say_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context): return
    if not context.args:
        await update.message.reply_text("❌ Bitte schreibe einen Text hinter den Befehl. Beispiel: `/say Hallo`")
        return
    nachricht = " ".join(context.args)
    try:
        await update.message.delete()
    except Exception:
        pass
    await context.bot.send_message(chat_id=update.effective_chat.id, text=nachricht)

# Befehl: /info
async def info_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    user = update.effective_user
    info_text = (
        "📊 **INFO-BOARD**\n\n"
        f"👤 **Dein Name:** {user.first_name}\n"
        f"🆔 **Deine User-ID:** `{user.id}`\n"
        f"🌐 **Chat-Typ:** {chat.type.capitalize()}\n"
    )
    if chat.type != "private":
        info_text += f"👥 **Gruppen-Name:** {chat.title}\n🆔 **Gruppen-ID:** `{chat.id}`"
    await update.message.reply_text(info_text, parse_mode="Markdown")

# --- MENÜ LOGIK ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("Admin Panel 🛠️", callback_data="admin_panel")],
        [InlineKeyboardButton("Hilfe & Befehle 📜", callback_data="help_menu")]
    ]
    await update.message.reply_text("🤖 Willkommen beim LOL Studios Manager! Wähle eine Option:", reply_markup=InlineKeyboardMarkup(keyboard))

async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "admin_panel":
        if not await is_admin(update, context):
            await query.edit_message_text(text="❌ **Zugriff verweigert!** Nur für Gruppen-Admins.")
            return
        keyboard = [
            [InlineKeyboardButton("Gruppe sperren 🔒", callback_data="lock_group"),
             InlineKeyboardButton("Gruppe öffnen 🔓", callback_data="unlock_group")],
            [InlineKeyboardButton("➔ Zurück", callback_data="main_menu")]
        ]
        await query.edit_message_text(text="🛠️ **ADMIN PANEL**\nHier kannst du Einstellungen vornehmen:", reply_markup=InlineKeyboardMarkup(keyboard))
    elif query.data == "help_menu":
        keyboard = [[InlineKeyboardButton("➔ Zurück", callback_data="main_menu")]]
        help_text = (
            "📜 **Verfügbare Befehle:**\n\n"
            "**Moderation (auf Nachrichten antworten):**\n"
            "• `/kick` - Nutzer kicken\n"
            "• `/mute` - Nutzer stummschalten (10 Min)\n"
            "• `/unmute` - Stummschaltung aufheben\n"
            "• `/warn` - Nutzer verwarnen\n"
            "• `/pin` - Nachricht anheften\n\n"
            "**Nützliches:**\n"
            "• `/info` - Zeigt IDs an\n"
            "• `/say [Text]` - Bot spricht"
        )
        await query.edit_message_text(text=help_text, reply_markup=InlineKeyboardMarkup(keyboard))
    elif query.data == "main_menu":
        keyboard = [
            [InlineKeyboardButton("Admin Panel 🛠️", callback_data="admin_panel")],
            [InlineKeyboardButton("Hilfe & Befehle 📜", callback_data="help_menu")]
        ]
        await query.edit_message_text(text="🤖 Wähle eine Option:", reply_markup=InlineKeyboardMarkup(keyboard))
    elif query.data == "lock_group":
        if not await is_admin(update, context): return
        await query.edit_message_text(text="🔒 Gruppe gesperrt.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("➔ Zurück", callback_data="admin_panel")]]))
    elif query.data == "unlock_group":
        if not await is_admin(update, context): return
        await query.edit_message_text(text="🔓 Gruppe geöffnet.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("➔ Zurück", callback_data="admin_panel")]]))

async def standard_antwort(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == "private":
await update.message.reply_text("🤖 Bitte tippe /start, um die Menü-Knöpfe zu öffnen!")
if name == "main":
print("Reparierte Bot-Version wird gestartet...")
threading.Thread(target=run_health_server, daemon=True).start()
app = Application.builder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("kick", kick_user))
app.add_handler(CommandHandler("mute", mute_user))
app.add_handler(CommandHandler("unmute", unmute_user))
app.add_handler(CommandHandler("warn", warn_user))
app.add_handler(CommandHandler("pin", pin_message))
app.add_handler(CommandHandler("say", say_command))
app.add_handler(CommandHandler("info", info_command))
app.add_handler(CallbackQueryHandler(button_click))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, standard_antwort))
app.run_polling()
