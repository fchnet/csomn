import logging
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
import strings
from handlers import menu
import os

logger = logging.getLogger(__name__)

# Conversation state for feedback text input
FEEDBACK_TEXT = 7

# Define feedback levels mapping (satisfação) com emojis e valores
FEEDBACK_LEVELS = {
    "muito_insatisfeito": {"emoji": "💔", "value": 1},
    "insatisfeito": {"emoji": "😥", "value": 2},
    "neutro": {"emoji": "😐", "value": 3},
    "satisfeito": {"emoji": "😊", "value": 4},
    "muito_satisfeito": {"emoji": "🤩", "value": 5}
}

async def start_feedback(update, context):
    """Initiate feedback collection by asking for satisfaction level."""
    # Reset any existing feedback state
    context.user_data.pop("feedback", None)
    # Construct inline buttons for feedback levels
    level_buttons = [InlineKeyboardButton(level["emoji"], callback_data=f"feedback_level_{name}") 
                     for name, level in FEEDBACK_LEVELS.items()]
    keyboard = [level_buttons, [InlineKeyboardButton("🔙 Voltar ao Menu", callback_data="main_menu")]]
    await update.effective_message.reply_text(
        "📝 **Deixe seu feedback!**\\n\\nPor favor, selecione seu nível de satisfação geral:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )
    context.user_data["feedback"] = {"stage": "select_level"}
    logger.info(f"Iniciando feedback - seleção de nível de satisfação.")
    # Transition to waiting for level selection (handled via callback)
    return None  # remain in current state (handled by callback query)

async def handle_feedback_level_callback(update, context):
    """Handle feedback level selection (callback)."""
    query = update.callback_query
    data = query.data
    level_name = data.replace("feedback_level_", "")
    try:
        query.answer()
    except Exception as e:
        logger.warning(f"Erro ao responder feedback callback: {e}")
    if level_name not in FEEDBACK_LEVELS:
        logger.warning(f"Nível de feedback inválido: {level_name}")
        return None
    # Store selected level
    context.user_data["feedback"] = {
        "stage": "writing_text",
        "level": FEEDBACK_LEVELS[level_name]["value"],
        "emoji": FEEDBACK_LEVELS[level_name]["emoji"]
    }
    # Ask for feedback text
    query.edit_message_text(
        f"Você selecionou: {context.user_data['feedback']['emoji']}\\n\\nAgora, por favor, digite seu feedback:",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Voltar ao Menu", callback_data="main_menu")]]),
        parse_mode="Markdown"
    )
    logger.info(f"Nível de feedback selecionado: {level_name}. Aguardando texto do feedback.")
    # Move to state waiting for feedback text
    return FEEDBACK_TEXT

async def handle_feedback_text(update, context):
    """Handle the feedback text entered by the user."""
    feedback_state = context.user_data.get("feedback", {})
    if feedback_state.get("stage") == "writing_text":
        user_feedback_text = update.effective_message.text.strip()
        if not user_feedback_text:
            await update.effective_message.reply_text(
                "❌ Por favor, digite um feedback válido.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Voltar ao Menu", callback_data="main_menu")]]),
                parse_mode="Markdown"
            )
            return None
        # Save feedback to file
        user_id = update.effective_user.id
        level_value = feedback_state.get("level")
        if level_value is None:
            logger.error("Nível de feedback não encontrado.")
            await update.effective_message.reply_text("❌ Ocorreu um erro ao registrar seu feedback.", reply_markup=strings.main_menu_keyboard(), parse_mode="Markdown")
            context.user_data.pop("feedback", None)
            return 1
        save_feedback(level_value, user_feedback_text, user_id)
        await update.effective_message.reply_text(
            "✅ **Obrigado pelo seu feedback!** Ele foi registrado com sucesso.\\n\\nVolte ao menu principal:",
            reply_markup=strings.main_menu_keyboard(),
            parse_mode="Markdown"
        )
        context.user_data.pop("feedback", None)
        logger.info(f"Feedback recebido de user {user_id}, nível {level_value}.")
        return 1
    # If feedback stage not as expected, end or return to menu
    return 1

def save_feedback(level, text, user_id):
    """Append feedback to a local file for record."""
    try:
        timestamp = __import__('datetime').datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        line = f"[{timestamp}] User ID: {user_id} - Nível: {level} - Texto: {text}\\n"
        with open("feedback.txt", "a", encoding="utf-8") as f:
            f.write(line)
        logger.info("Feedback salvo com sucesso.")
    except Exception as e:
        logger.error(f"Erro ao salvar feedback: {e}")
