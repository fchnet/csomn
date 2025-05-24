# chatbot_unificado.py

import os
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    ContextTypes,
    filters
)
from dotenv import load_dotenv

# Variáveis de ambiente
load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

CONSENTIMENTO, MENU = range(2)

menu_principal = [
    ["Agendar atendimento", "Ver meus agendamentos"],
    ["Cancelar agendamento", "Como utilizar"]
]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    texto = (
        "🛡️ *Termo LGPD*\n"
        "Este bot utiliza seus dados para fins de agendamento filantrópico. "
        "Você consente em continuar?\n\n"
        "_Responda com 'sim' ou 'não'_"
    )
    await update.message.reply_text(texto, parse_mode="Markdown")
    return CONSENTIMENTO

async def receber_consentimento(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    texto = update.message.text.lower()
    if texto == "sim":
        await update.message.reply_text(
            "✅ Obrigado! Escolha uma opção:",
            reply_markup=ReplyKeyboardMarkup(menu_principal, resize_keyboard=True)
        )
        return MENU
    else:
        await update.message.reply_text("Você não consentiu. Digite /start para tentar novamente.")
        return ConversationHandler.END

async def tratar_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    texto = update.message.text.lower()
    if texto == "como utilizar":
        await update.message.reply_text("🛈 Este bot permite agendar, ver ou cancelar atendimentos.")
    elif texto == "agendar atendimento":
        await update.message.reply_text("📅 Agendamento em desenvolvimento.")
    elif texto == "ver meus agendamentos":
        await update.message.reply_text("🔎 Consulta de agendamentos em desenvolvimento.")
    elif texto == "cancelar agendamento":
        await update.message.reply_text("❌ Cancelamento em desenvolvimento.")
    else:
        await update.message.reply_text("Não entendi. Escolha uma opção do menu.")
    return MENU

async def cancelar(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Sessão encerrada. Digite /start para recomeçar.")
    return ConversationHandler.END

def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()

    conversa = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            CONSENTIMENTO: [MessageHandler(filters.TEXT & ~filters.COMMAND, receber_consentimento)],
            MENU: [MessageHandler(filters.TEXT & ~filters.COMMAND, tratar_menu)],
        },
        fallbacks=[CommandHandler("cancel", cancelar)]
    )

    app.add_handler(conversa)

    print("🤖 Bot em execução...")
    app.run_polling()

if __name__ == "__main__":
    main()
