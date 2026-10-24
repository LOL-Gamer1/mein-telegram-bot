from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ChatPermissions
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
from http.server import BaseHTTPRequestHandler, HTTPServer
import threading
import os
import time

# ⚠️ HIER DEINEN ECHTEN TOKEN EINTRAGEN! (Anführungszeichen "" müssen bleiben)
TOKEN = "8511282233:AAF05ySHJNJyHxi5ctZbvHhUhSB4fMrrlzc"

def run_health_server():
    class HealthCheckHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"Bot is alive")
    server = HTTPServer(('0.0.0.0', int(os.environ.get('PORT', 8080))), HealthCheckHandler)
    server.serve_forever()

# --- BEFEHLE MIT KNÖPFEN & ADMIN PANEL ---

# Befehl: /start (Öffnet das Menü mit Knöpfen)
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("Admin Panel 🛠️", callback_data="admin_panel")],
        [InlineKeyboardButton("Hilfe & Befehle 📜", callback_data="help_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("🤖 Willkommen beim LOL Studios Manager! Wähle eine Option:", reply_markup=reply_markup)

# Auswertung der Knopf-Klicks
async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "admin_panel":
        keyboard = [
            [InlineKeyboardButton("Gruppe sperren 🔒", callback_data="lock_group"),
             InlineKeyboardButton("Gruppe öffnen 🔓", callback_data="unlock_group")],
            [InlineKeyboardButton("➔ Zurück", callback_data="main_menu")]
        ]
        await query.edit_message_text(text="🛠️ **ADMIN PANEL**\nHier kannst du globale Einstellungen vornehmen:", reply_markup=InlineKeyboardMarkup(keyboard))
        
    elif query.data == "help_menu":
        keyboard = [[InlineKeyboardButton("➔ Zurück", callback_data="main_menu")]]
        help_text = (
            "📜 **Verfügbare Befehle:**\n\n"
            "**In Gruppen (auf eine Nachricht antworten):**\n"
            "• `/kick` - Kickt den Nutzer aus der Gruppe\n"
            "• `/mute` - Schaltet den Nutzer für 10 Min stumm\n\n"
            "**Im Privatchat:**\n"
            "• `/start` - Öffnet das interaktive Menü"
        )
        await query.edit_message_text(text=help_text, reply_markup=InlineKeyboardMarkup(keyboard))
        
    elif query.data == "main_menu":
        keyboard = [
            [InlineKeyboardButton("Admin Panel 🛠️", callback_data="admin_panel")],
            [InlineKeyboardButton("Hilfe & Befehle 📜", callback_data="help_menu")]
        ]
        await query.edit_message_text(text="🤖 Wähle eine Option:", reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data == "lock_group":
        await query.edit_message_text(text="🔒 Gruppe wird gesperrt... (Feature aktiv!)", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("➔ Zurück", callback_data="admin_panel")]]))
    elif query.data == "unlock_group":
        await query.edit_message_text(text="🔓 Gruppe wird geöffnet... (Feature aktiv!)", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("➔ Zurück", callback_data="admin_panel")]]))

# --- MODERATION FÜR GRUPPEN ---

async def kick_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    if chat.type == "private":
        await update.message.reply_text("❌ Dieser Befehl funktioniert nur in Gruppen!")
        return
    if not update.message.reply_to_message:
        await update.message.reply_text("❌ Bitte antworte auf die Nachricht des Nutzers, den du kicken willst.")
        return
    target_user = update.message.reply_to_message.from_user
    try:
        await chat.ban_member(user_id=target_user.id)
        await chat.unban_member(user_id=target_user.id)
        await update.message.reply_text(f"🎯 **{target_user.first_name}** wurde gekickt!")
    except Exception as e:
        await update.message.reply_text("❌ Fehler: Mir fehlen Admin-Rechte.")

async def mute_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    if chat.type == "private" or not update.message.reply_to_message:
        await update.message.reply_text("❌ Antworte in einer Gruppe auf eine Nachricht, um jemanden stummzuschalten.")
        return
    target_user = update.message.reply_to_message.from_user
    permissions = ChatPermissions(can_send_messages=False)
    try:
        until_time = int(time.time() + 600)
        await chat.restrict_member(user_id=target_user.id, permissions=permissions, until_date=until_time)
        await update.message.reply_text(f"🤫 **{target_user.first_name}** wurde für 10 Minuten stummgeschaltet!")
    except Exception as e:
        await update.message.reply_text("❌ Fehler: Mir fehlen Admin-Rechte.")

# Standard-Antwort für normale Texte
async def standard_antwort(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == "private":
        await update.message.reply_text("🤖 Ich verstehe normalen Text leider nicht. Bitte tippe `/start`, um die Menü-Knöpfe zu öffnen!")

if __name__ == "__main__":
    print("Bot wird gestartet...")
    threading.Thread(target=run_health_server, daemon=True).start()
    
    app = Application.builder().token(TOKEN).build()

    # Befehle registrieren
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("kick", kick_user))
    app.add_handler(CommandHandler("mute", mute_user))
    app.add_handler(CallbackQueryHandler(button_click))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, standard_antwort))

    app.run_polling()
