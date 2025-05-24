# modules/como_utilizar.py
from telegram import Update
from telegram.ext import ContextTypes, CommandHandler
from utils.menu import voltar_ao_menu

async def como_utilizar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texto = (
        "\u2139\ufe0f *Como utilizar este bot:*\n\n"
        "- Use os botões do menu para agendar, cancelar ou consultar atendimentos.\n"
        "- Você também pode acessar conteúdos por categorias como Meditação, Emoções etc.\n"
        "- Os comandos especiais iniciam com '/'. Exemplo: /menu, /apagar_dados, /indicadores.\n"
        "- Ao agendar, você receberá um e-mail com o resumo e um convite em formato `.ics`.\n"
        "- Você pode retornar ao menu principal a qualquer momento digitando `/menu`.\n"
    )
    await update.message.reply_text(texto, parse_mode="Markdown")
    return await voltar_ao_menu(update, context)

handler = CommandHandler("como_utilizar", como_utilizar)
