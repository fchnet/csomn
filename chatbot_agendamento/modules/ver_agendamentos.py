# modules/ver_agendamentos.py
from telegram import Update
from telegram.ext import ContextTypes, CommandHandler
from utils.menu import voltar_ao_menu

async def ver_agendamentos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔎 Consulta de agendamentos em desenvolvimento.")
    return await voltar_ao_menu(update, context)

handler = CommandHandler("ver_agendamentos", ver_agendamentos)
