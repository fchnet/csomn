import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CallbackContext, CallbackQueryHandler
from telegram.constants import ParseMode

# Caminho da imagem de fundo do termo LGPD
IMAGE_PATH = "image/maria_de_nazare.png"

# Menu principal com botões 2 por linha
MAIN_MENU = [
    ["👍 Agendar atendimento", "🔎 Ver meus agendamentos"],
    ["❌ Cancelar agendamento", "ℹ️ Como utilizar"]
]

async def mostrar_termo_lgpd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    termo_resumido = (
        "\U0001F4AC *Termo de Consentimento (LGPD)*\n"
        "Este bot coleta apenas o nome, telefone e e-mail para fins de agendamento *filantrópico*.
        Nenhuma informação é compartilhada.\n\n"
        "Deseja prosseguir?"
    )
    botoes = [
        [InlineKeyboardButton("🔍 Ver Termo Completo", callback_data="ver_termo")],
        [InlineKeyboardButton("☑️ Aceito os termos", callback_data="aceitar_termos")]
    ]
    with open(IMAGE_PATH, "rb") as img:
        await update.message.reply_photo(
            photo=img,
            caption=termo_resumido,
            reply_markup=InlineKeyboardMarkup(botoes),
            parse_mode=ParseMode.MARKDOWN
        )

async def ver_termo_completo(update: Update, context: CallbackContext):
    termo_completo = (
        "*Termo completo de consentimento:*
        \n\nEste bot tem por objetivo facilitar o agendamento de atendimentos filantrópicos.\n\n"
        "Os dados coletados (nome, telefone e e-mail) são usados exclusivamente para esta finalidade."
        "\nVocê pode solicitar a remoção definitiva dos seus dados a qualquer momento."
    )
    await update.callback_query.answer()
    await update.callback_query.message.reply_text(termo_completo, parse_mode=ParseMode.MARKDOWN)

async def aceitar_termos(update: Update, context: CallbackContext):
    await update.callback_query.answer()
    botoes_menu = [
        [InlineKeyboardButton(text, callback_data=text)] for linha in MAIN_MENU for text in linha
    ]
    menu_organizado = []
    for i in range(0, len(botoes_menu), 2):
        menu_organizado.append(botoes_menu[i:i+2])
    await update.callback_query.message.reply_text(
        "✅ Obrigado! Escolha uma opção:",
        reply_markup=InlineKeyboardMarkup(menu_organizado)
    )

TERMO_HANDLERS = [
    CallbackQueryHandler(ver_termo_completo, pattern="^ver_termo$"),
    CallbackQueryHandler(aceitar_termos, pattern="^aceitar_termos$")
]
