# modules/entrada.py

import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext
from utils.menu import construir_menu_principal
from utils.database import obter_categorias_unicas

async def start_cmd(update: Update, context: CallbackContext):
    imagem_path = os.getenv("IMAGE_PATH", "image/maria_de_nazare.png")

    if not os.path.exists(imagem_path) or os.path.getsize(imagem_path) == 0:
        await update.message.reply_text("Imagem de apresentação não encontrada ou está vazia.")
        return

    with open(imagem_path, "rb") as img:
        await update.message.reply_photo(
            photo=img,
            caption="📄 *Termo de Consentimento LGPD:*\n\nEste bot é utilizado para agendamentos filantrópicos. Seus dados serão utilizados apenas para essa finalidade.",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("✅ Estou de acordo", callback_data="aceitar_termos")]
            ])
        )

async def aceitar_termos(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()

    categorias = obter_categorias_unicas()
    nomes_formatados = []
    for cat in categorias:
        tag = cat[0] if isinstance(cat, tuple) else cat
        nome = tag.replace("_", " ").title()
        nomes_formatados.append((nome, tag))

    keyboard = construir_menu_principal(nomes_formatados)

    await query.edit_message_text(
        "✅ Obrigado! Escolha uma opção abaixo:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
