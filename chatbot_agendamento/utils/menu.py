# utils/menu.py

from telegram import InlineKeyboardButton

# Itens fixos do menu que não são categorias
ITENS_FIXOS = [
    ("📅 Agendar atendimento", "agendar"),
    ("🔎 Ver meus agendamentos", "ver_agendamentos"),
    ("❌ Cancelar atendimento", "cancelar_agendamento"),
    ("🛈 Como utilizar", "como_utilizar"),
    ("🚪 Sair", "sair"),
]

def construir_menu_principal(categorias=[]):
    botoes = []

    # Categorias dinâmicas da base de dados
    for tag in categorias:
        nome = tag.replace("_", " ").title()
        botoes.append(InlineKeyboardButton(f"📂 {nome}", callback_data=tag))

    # Itens fixos
    for nome, data in ITENS_FIXOS:
        botoes.append(InlineKeyboardButton(nome, callback_data=data))

    # Divide os botões em linhas de 2
    linhas = [botoes[i:i + 2] for i in range(0, len(botoes), 2)]
    return linhas

async def voltar_ao_menu(update, context):
    from utils.database import obter_categorias_unicas
    from telegram import InlineKeyboardMarkup

    query = update.callback_query
    await query.answer()

    categorias = obter_categorias_unicas()
    botoes_menu = construir_menu_principal(categorias)

    await query.edit_message_text(
        "✅ Menu principal. Escolha uma opção:",
        reply_markup=InlineKeyboardMarkup(botoes_menu)
    )
