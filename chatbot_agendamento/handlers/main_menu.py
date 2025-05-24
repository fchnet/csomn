# handlers/main_menu.py

from telegram import Update
from telegram.ext import CallbackContext
from messages import (
    CANCELAMENTO_EM_DESENVOLVIMENTO,
    CONSULTA_EM_DESENVOLVIMENTO,
    AGENDAMENTO_EM_DESENVOLVIMENTO,
    COMO_UTILIZAR,
    MENU_INICIAL,
)
from telegram import InlineKeyboardMarkup, InlineKeyboardButton

def exibir_menu(update: Update, context: CallbackContext) -> None:
    keyboard = [
        [
            InlineKeyboardButton("📅 Agendar atendimento", callback_data="menu_agendar"),
            InlineKeyboardButton("📖 Ver meus agendamentos", callback_data="menu_ver_agendamentos")
        ],
        [
            InlineKeyboardButton("❌ Cancelar atendimento", callback_data="menu_cancelar"),
            InlineKeyboardButton("ℹ️ Como utilizar", callback_data="menu_como_utilizar")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text(MENU_INICIAL, reply_markup=reply_markup)

def tratar_clique_menu(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    query.answer()

    if query.data == "menu_agendar":
        query.edit_message_text(text=AGENDAMENTO_EM_DESENVOLVIMENTO)
    elif query.data == "menu_ver_agendamentos":
        query.edit_message_text(text=CONSULTA_EM_DESENVOLVIMENTO)
    elif query.data == "menu_cancelar":
        query.edit_message_text(text=CANCELAMENTO_EM_DESENVOLVIMENTO)
    elif query.data == "menu_como_utilizar":
        query.edit_message_text(text=COMO_UTILIZAR)
