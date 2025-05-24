# main.py

import os
from dotenv import load_dotenv
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler, ConversationHandler
)
from modules.entrada import start_cmd, aceitar_termos

load_dotenv()
TOKEN = os.getenv("TELEGRAM_TOKEN")

app = ApplicationBuilder().token(TOKEN).build()

conv_handler = ConversationHandler(
    entry_points=[CommandHandler("start", start_cmd)],
    states={
        1: [CallbackQueryHandler(aceitar_termos, pattern="^aceitar_termos$")],
    },
    fallbacks=[],
    per_message=True,
)

app.add_handler(conv_handler)

print("🤖 Bot está em execução...")
app.run_polling()
