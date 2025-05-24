# modules/feedback.py
from telegram import Update
from telegram.ext import ContextTypes, CommandHandler

async def feedback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📝 Feedback em desenvolvimento.")

handler = CommandHandler("feedback", feedback)
