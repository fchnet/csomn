import logging
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
import strings

logger = logging.getLogger(__name__)

# Conversation state for consent
CONSENT = 0

def start(update, context):
    """Send LGPD consent message with Accept button when /start is invoked."""
    # Create inline keyboard for consent
    buttons = [
        [InlineKeyboardButton("✅ Aceito", callback_data="consent_agree")],
        [InlineKeyboardButton("❌ Não aceito", callback_data="consent_decline")]
    ]
    reply_markup = InlineKeyboardMarkup(buttons)
    update.message.reply_text(strings.CONSENT_MSG, reply_markup=reply_markup, parse_mode="Markdown")
    return CONSENT

def consent_response(update, context):
    """Handle user's response to consent prompt."""
    query = update.callback_query
    data = query.data
    if data == "consent_agree":
        # User accepted terms
        try:
            query.answer()
        except Exception as e:
            logger.warning(f"Error answering callback: {e}")
        # Edit original message to remove buttons
        query.edit_message_text("✅ *Consentimento LGPD confirmado.*", parse_mode="Markdown")
        # Send welcome message with main menu
        query.message.reply_text(strings.WELCOME_MSG, reply_markup= strings.main_menu_keyboard(), parse_mode="Markdown")
        logger.info(f"Usuário {update.effective_user.id} aceitou o consentimento LGPD.")
        # Proceed to main menu state
        return 1
    else:
        # User declined consent
        try:
            query.answer()
        except Exception as e:
            logger.warning(f"Error answering callback: {e}")
        query.edit_message_text("❌ Você optou por *não aceitar* os termos. Se mudar de ideia, envie /start novamente.", parse_mode="Markdown")
        logger.info(f"Usuário {update.effective_user.id} recusou o consentimento LGPD.")
        # End conversation
        return -1  # ConversationHandler.END

def prompt_delete(update, context):
    """Command /apagar_dados - ask user to confirm data deletion."""
    buttons = [
        [InlineKeyboardButton("✅ Sim, apagar", callback_data="confirm_delete"),
         InlineKeyboardButton("❌ Não, cancelar", callback_data="cancel_delete")]
    ]
    reply_markup = InlineKeyboardMarkup(buttons)
    update.effective_message.reply_text("⚠️ *Deseja realmente apagar todos os seus dados pessoais?* Esta ação é irreversível.", reply_markup=reply_markup, parse_mode="Markdown")
    return None  # stay in current state

def handle_delete_choice(update, context):
    """Handle confirmation or cancellation of data deletion."""
    query = update.callback_query
    data = query.data
    if data == "confirm_delete":
        try:
            query.answer()
        except Exception as e:
            logger.warning(f"Error answering callback: {e}")
        # Perform data deletion: clear user data and cancel any appointments
        user_id = update.effective_user.id
        email = context.user_data.get("last_email")
        if email:
            # Cancel all future events for this email
            from handlers import agendamento
            events, total = agendamento.get_user_events(email, page=0, page_size=1000)
            for event in events:
                try:
                    service = agendamento.get_calendar_service()
                    if service:
                        service.events().delete(calendarId=agendamento.CALENDAR_ID, eventId=event['id']).execute()
                except Exception as e:
                    logger.error(f"Erro ao deletar evento {event.get('summary')} do usuário {user_id}: {e}")
        # Clear context user data
        context.user_data.clear()
        # Confirm deletion to user
        query.edit_message_text("✅ *Seus dados pessoais foram apagados.*", parse_mode="Markdown")
        logger.info(f"Dados pessoais do usuário {user_id} apagados.")
        # Optionally, remain in menu state (user can continue using bot)
        query.message.reply_text(strings.WELCOME_MSG, reply_markup=strings.main_menu_keyboard(), parse_mode="Markdown")
        return 1
    else:
        # cancel_delete
        try:
            query.answer()
        except Exception as e:
            logger.warning(f"Error answering callback: {e}")
        # Just remove the confirmation prompt
        query.edit_message_text("Operação cancelada.", parse_mode="Markdown")
        return None  # remain in current state (likely main menu)
