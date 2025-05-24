from telegram import ReplyKeyboardMarkup

# Interface text constants
WELCOME_MSG = "✨ **Bem-vindo ao Guia Espiritual!**\\n\\nEscolha uma opção abaixo:"
CONSENT_MSG = ("⚖️ *Consentimento LGPD*\n"
              "Este bot coletará seu nome, telefone e e-mail para agendamento e envio de confirmações. "
              "Seus dados serão utilizados apenas para essa finalidade e poderão ser apagados mediante solicitação. "
              "Ao prosseguir, você concorda com o uso dos seus dados pessoais conforme a LGPD.\n\n"
              "Você aceita os termos?")
HOW_IT_WORKS = ("ℹ️ *Como funciona o agendamento*\n\n"
               "1. Clique em 'Agendar Atendimento' para escolher uma data e horário.\n"
               "2. No calendário, selecione um dia disponível:\n"
               "   - Dias disponíveis aparecem com o número (ex.: 23).\n"
               "   - Dias lotados são marcados com X (ex.: 19X).\n"
               "   - Dias passados são marcados com () (ex.: (18)).\n"
               "3. Escolha um horário disponível e confirme seus dados.\n"
               "4. Para cancelar, use 'Cancelar Agendamento' e selecione o atendimento.\n\n"
               "Selecione um dia disponível: (X indica agenda cheia, () indica data passada)")
CONTINUE_MSG = "✨ *Posso ajudar em algo mais?* Se desejar, escolha outra opção abaixo:"
DID_NOT_UNDERSTAND = ("🤔 **Não entendi.** Tente:\n"
                      "- Usar os botões do menu\n"
                      "- Reformular sua pergunta\n"
                      "- Agendar um atendimento 📅")

# Main menu categories mapping (button text to category tag)
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
    "🚪 Sair": "sair"
}

# Main menu keyboard layout
MAIN_MENU_BUTTONS = [
    ["🧘 Meditação", "💖 Emoções"],
    ["🌟 Cura", "🕊️ Paz Interior"],
    ["📬 Mensagem", "📝 Feedback"],
    ["📅 Agendar Atendimento", "❌ Cancelar Agendamento"],
    ["❓ Ajuda", "ℹ️ Como funciona"],
    ["🚪 Sair"]
]

def main_menu_keyboard():
    """Return the ReplyKeyboardMarkup for the main menu."""
    return ReplyKeyboardMarkup(MAIN_MENU_BUTTONS, resize_keyboard=True, one_time_keyboard=False)
