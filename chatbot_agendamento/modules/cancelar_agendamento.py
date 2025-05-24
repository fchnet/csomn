# modules/cancelar_agendamento.py
from telegram import Update
from telegram.ext import ContextTypes, CommandHandler
from utils.menu import voltar_ao_menu

async def cancelar_agendamento(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Cancelamento de agendamento em desenvolvimento.")
    return await voltar_ao_menu(update, context)

handler = CommandHandler("cancelar", cancelar_agendamento)
