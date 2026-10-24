from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from http.server import BaseHTTPRequestHandler, HTTPServer
import threading
import os

# TRAGE HIER DEINEN NEUEN TOKEN EIN (Die Anführungszeichen "" müssen bleiben!)
TOKEN = "8511282233:AAF05ySHJNJyHxi5ctZbvHhUhSB4fMrrlzc"

# Kleiner Webserver für Render.com, damit der Bot dauerhaft online bleibt
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is alive")

def run_health_server():
    # Der Server hört auf den Port, den Render ihm zuweist (Standard ist 8080)
    server = HTTPServer(('0.0.0.0', int(os.environ.get('PORT', 8080))), HealthCheckHandler)
    server.serve_forever()

# Das passiert, wenn jemand /start in Telegram drückt
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hallo! Dieser Bot läuft jetzt 24/7 in der Cloud! 🚀")

# Das passiert, wenn jemand dem Bot eine normale Textnachricht schreibt
async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text_vom_nutzer = update.message.text
    # Der Bot antwortet mit dem exakt gleichen Text
    await update.message.reply_text(f"Du hast geschrieben: {text_vom_nutzer}")

if __name__ == "__main__":
    print("Bot wird gestartet...")
    
    # Startet den Mini-Webserver in einem eigenen Thread im Hintergrund
    threading.Thread(target=run_health_server, daemon=True).start()
    
    # Verbindung zu Telegram aufbauen
    app = Application.builder().token(TOKEN).build()

    # Befehle und Text-Filter hinzufügen
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

    # Bot in den dauerhaften Abrufmodus versetzen
    app.run_polling()
  
