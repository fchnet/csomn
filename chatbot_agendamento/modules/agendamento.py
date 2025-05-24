# modules/agendamento.py
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ConversationHandler, ContextTypes, CallbackQueryHandler, MessageHandler, filters, CommandHandler
from utils.google_calendar import obter_dias_disponiveis, obter_horarios_disponiveis, salvar_evento_google
from utils.email_service import enviar_email_confirmacao
from utils.validadores import validar_telefone, validar_email
from utils.database import salvar_agendamento, verificar_disponibilidade
from utils.menu import voltar_ao_menu
import os

(ESCOLHER_DIA, ESCOLHER_HORARIO, CONFIRMAR_DADOS, INFORMAR_EMAIL) = range(4)

async def iniciar_agendamento(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Por favor, informe seu nome completo:")
    return ESCOLHER_DIA

async def receber_nome(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['nome'] = update.message.text
    await update.message.reply_text("Agora, informe seu telefone:")
    return ESCOLHER_HORARIO

async def receber_telefone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telefone = update.message.text
    if not validar_telefone(telefone):
        await update.message.reply_text("Telefone inválido. Tente novamente:")
        return ESCOLHER_HORARIO
    context.user_data['telefone'] = telefone

    dias = obter_dias_disponiveis()
    botoes = [[InlineKeyboardButton(dia, callback_data=dia)] for dia in dias]
    await update.message.reply_text("Escolha o dia do atendimento:", reply_markup=InlineKeyboardMarkup(botoes))
    return CONFIRMAR_DADOS

async def receber_dia(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    dia = query.data
    context.user_data['dia'] = dia

    horarios = obter_horarios_disponiveis(dia)
    botoes = [[InlineKeyboardButton(h, callback_data=h)] for h in horarios]
    await query.message.reply_text(f"Escolha o horário disponível para {dia}:", reply_markup=InlineKeyboardMarkup(botoes))
    return INFORMAR_EMAIL

async def receber_horario(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    horario = query.data
    context.user_data['horario'] = horario
    await query.message.reply_text("Informe seu e-mail:")
    return INFORMAR_EMAIL

async def receber_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    email = update.message.text
    if not validar_email(email):
        await update.message.reply_text("E-mail inválido. Tente novamente:")
        return INFORMAR_EMAIL
    context.user_data['email'] = email

    salvar_agendamento(context.user_data)
    salvar_evento_google(context.user_data)
    enviar_email_confirmacao(context.user_data)

    texto = (
        f"*Confirme suas informações:*\n"
        f"Nome: {context.user_data['nome']}\nTelefone: {context.user_data['telefone']}\n"
        f"Data: {context.user_data['dia']} às {context.user_data['horario']}\n"
        f"E-mail: {context.user_data['email']}"
    )
    await update.message.reply_text(texto, parse_mode="Markdown")
    return ConversationHandler.END

handler = ConversationHandler(
    entry_points=[
        MessageHandler(filters.Regex("(?i)agendar atendimento"), iniciar_agendamento)
    ],
    states={
        ESCOLHER_DIA: [MessageHandler(filters.TEXT & ~filters.COMMAND, receber_nome)],
        ESCOLHER_HORARIO: [MessageHandler(filters.TEXT & ~filters.COMMAND, receber_telefone)],
        CONFIRMAR_DADOS: [CallbackQueryHandler(receber_dia)],
        INFORMAR_EMAIL: [CallbackQueryHandler(receber_horario), MessageHandler(filters.TEXT & ~filters.COMMAND, receber_email)]
    },
    fallbacks=[CommandHandler("menu", voltar_ao_menu)]
)
