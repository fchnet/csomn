
from telegram import ReplyKeyboardMarkup, Update
from telegram.ext import CommandHandler, MessageHandler, filters, ConversationHandler, ContextTypes
from modules.menus import MAIN_MENU_CATEGORIES, construir_menu
from modules.responses import responder_tag

CONSENTIMENTO, MENU = range(2)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    termo = (
        "\U0001F4AC *Termo de Consentimento (LGPD)*\n"
        "Este bot coleta dados pessoais apenas para fins filantrópicos.\n"
        "Você aceita os termos? Marque 'Sim' para continuar."
    )
    await update.message.reply_text(termo)
    return CONSENTIMENTO

async def receber_consentimento(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.message.text.lower() == "sim":
        menu = construir_menu()
        await update.message.reply_text("Menu principal:", reply_markup=menu)
        return MENU
    await update.message.reply_text("Entendido. Digite /start se quiser tentar novamente.")
    return ConversationHandler.END

async def tratar_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    texto = update.message.text.strip()
    tag = MAIN_MENU_CATEGORIES.get(texto)
    if not tag:
        await update.message.reply_text("Ainda não entendi essa opção.")
        return MENU
    resposta = responder_tag(tag)
    await update.message.reply_text(resposta)
    return MENU

def criar_conversas():
    return ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            CONSENTIMENTO: [MessageHandler(filters.TEXT & ~filters.COMMAND, receber_consentimento)],
            MENU: [MessageHandler(filters.TEXT & ~filters.COMMAND, tratar_menu)],
        },
        fallbacks=[],
    )
