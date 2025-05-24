
from telegram import ReplyKeyboardMarkup

MAIN_MENU_CATEGORIES = {
    "🧘 Meditação": "meditacao",
    "💖 Emoções": "emocao",
    "🌟 Cura": "cura",
    "🕊️ Paz Interior": "paz_interior",
    "❓ Ajuda": "ajuda",
    "📬 Mensagem": "mensagem",
    "📅 Agendar Atendimento": "agendar",
    "📝 Feedback": "feedback",
    "❌ Cancelar Agendamento": "cancelar",
    "ℹ️ Como funciona": "como_funciona",
    "🚪 Sair": "sair",
}

def construir_menu():
    botoes = list(MAIN_MENU_CATEGORIES.keys())
    linhas = [botoes[i:i+2] for i in range(0, len(botoes), 2)]
    return ReplyKeyboardMarkup(linhas, resize_keyboard=True)
