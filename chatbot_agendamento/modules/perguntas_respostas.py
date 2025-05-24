# modules/perguntas_respostas.py

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext, CallbackQueryHandler
from utils.database import obter_perguntas_respostas_por_tag
from utils.menu import voltar_ao_menu

# Cache para perguntas/respostas por tag
PERGUNTAS = {}

def criar_handler(tag):
    """
    Cria um handler para uma categoria (tag), lidando com:
    - Listagem de perguntas
    - Exibição de resposta ao clicar
    """

    async def mostrar_perguntas(update: Update, context: CallbackContext):
        query = update.callback_query
        await query.answer()
        perguntas_respostas = obter_perguntas_respostas_por_tag(tag)

        if not perguntas_respostas:
            await query.edit_message_text(f"❗ Nenhuma pergunta disponível para *{tag.replace('_', ' ').title()}*.",
                                          parse_mode="Markdown")
            return

        keyboard = [
            [InlineKeyboardButton(pergunta, callback_data=f"{tag}|{idx}")]
            for idx, (pergunta, _) in enumerate(perguntas_respostas)
        ]
        keyboard.append([InlineKeyboardButton("🔙 Voltar", callback_data="voltar_menu")])

        PERGUNTAS[tag] = perguntas_respostas

        await query.edit_message_text(
            f"🧾 Escolha uma pergunta da categoria *{tag.replace('_', ' ').title()}*:",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )

    async def mostrar_resposta(update: Update, context: CallbackContext):
        query = update.callback_query
        await query.answer()
        data = query.data.split("|")
        if len(data) != 2:
            return

        tag, idx = data
        idx = int(idx)
        pergunta, resposta = PERGUNTAS.get(tag, [(None, None)])[idx]

        keyboard = [[InlineKeyboardButton("🔙 Voltar", callback_data=tag)]]

        await query.edit_message_text(
            f"❓ *{pergunta}*\n\n💬 {resposta}",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )

    return CallbackQueryHandler(
        lambda update, context: mostrar_resposta(update, context)
        if "|" in update.callback_query.data
        else mostrar_perguntas(update, context),
        pattern=f"^{tag}(\\|\\d+)?$"
    )
