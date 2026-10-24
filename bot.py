from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ChatPermissions
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
from http.server import BaseHTTPRequestHandler, HTTPServer
import threading
import os
import time

TOKEN = "8511282233:AAF05ySHJNJyHxi5ctZbvHhUhSB4fMrrlzc"

# LISTE DER BOT-ADMINS (Trage hier deine Telegram-ID oder deinen Usernamen ein)
# Wenn du deine ID nicht weißt, lassen wir es erst für alle Admins der Gruppe offen
def run_health_server():
    class HealthCheckHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"Bot is alive")
    server = HTTPServer(('0.0.0.0', int(os.environ.get('PORT', 8080))), HealthCheckHandler)
    server.serve_forever()

# --- BEFEHLE FÜR GRUPPEN (MODERATION) ---

# Befehl: /kick
async def kick_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    user_id = update.effective_user.id

    # Prüfen, ob der Befehl in einer Gruppe genutzt wird
    if chat.type == "private":
        await update.message.reply_text("❌ Dieser Befehl funktioniert nur in Gruppen!")
        return

    # Prüfen, ob eine Nachricht beantwortet wurde (derjenige soll gekickt werden)
    if not update.message.reply_to_message:
        await update.message.reply_text("❌ Bitte antworte auf die Nachricht des Nutzers, den du kicken willst.")
        return

    target_user = update.message.reply_to_message.from_user

    try:
        # Nutzer kicken
        await chat.ban_member(user_id=target_user.id)
        # Sofort wieder entbannen, damit er nicht auf der permanenten Blacklist steht, sondern nur fliegt
        await chat.unban_member(user_id=target_user.id)
        await update.message.reply_text(f"🎯 **{target_user.first_name}** wurde erfolgreich gekickt!")
    except Exception as e:
        await update.message.reply_text(f"❌ Fehler: Ich benötige Admin-Rechte zum Kicken! ({e})")

# Befehl: /mute
async def mute_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    if chat.type == "private" or not update.message.reply_to_message:
        await update.message.reply_text("❌ Antworte in einer Gruppe auf eine Nachricht, um den Nutzer stummzuschalten.")
        return

    target_user = update.message.reply_to_message.from_user

    # Rechte einschränken (keine Nachrichten mehr senden)
    permissions = ChatPermissions(can_send_messages=False)
    
    try:
        # Für 10 Minuten stummschalten (Beispiel)
        until_time = int(time.time() + 600)
        await chat.restrict_member(user_id=target_user.id, permissions=permissions, until_date=until_time)
        await update.message.reply_text(f"🤫 **{target_user.first_name}** wurde für 10 Minuten stummgeschaltet!")
    except Exception as e:
        await update.message.reply_text("❌ Fehler: Mir fehlen die Admin-Rechte für diese Aktion.")

# --- BEFEHLE MIT KNÖPFEN & ADMIN PANEL ---

# Befehl: /start (Privatjetzt mit Menü-Knöpfen)
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("Admin Panel 🛠️", callback_data="admin_panel")],
        [InlineKeyboardButton("Hilfe & Befehle 📜", callback_data="help_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("🤖 Willkommen beim LOL Studios Manager! Wähle eine Option:", reply_markup=reply_markup)

# Auswertung der Knopf-Klicks (Callback Queries)
async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer() # Signalisiert Telegram, dass der Klick angekommen ist

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
        await query.edit_message_text(text="🔒 Funktion angefordert: Gruppe wird für normale User geschlossen. (Feature in Arbeit!)", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("➔ Zurück", callback_data="admin_panel")]]))
    elif query.data == "unlock_group":
        await query.edit_message_text(text="🔓 Funktion angefordert: Gruppe wird wieder geöffnet. (Feature in Arbeit!)", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("➔ Zurück", callback_data="admin_panel")]]))

if __name__ == "__main__":
    print("Krassere Bot-Version wird gestartet...")
    threading.Thread(target=run_health_server, daemon=True).start()
    
    app = Application.builder().token(TOKEN).build()

    # Handlers registrieren
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("kick", kick_user))
    app.add_handler(CommandHandler("mute", mute_user))
    app.add_handler(CallbackQueryHandler(button_click)) # Für die Klicks auf die Buttons

    app.run_polling()
