# modules/sair.py

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackQueryHandler, ContextTypes

async def sair(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text(
        "👋 Agradecemos pela sua visita!\nVocê pode voltar a qualquer momento enviando /start.",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔁 Voltar ao início", callback_data="voltar_menu")]
        ])
    )

handler = CallbackQueryHandler(sair, pattern="^sair$")
