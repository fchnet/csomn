from datetime import datetime, timedelta
from telegram import InlineKeyboardButton
import os

START_HOUR = int(os.getenv("START_HOUR", 8))
END_HOUR = int(os.getenv("END_HOUR", 17))
MAX_APPOINTMENTS_PER_DAY = int(os.getenv("MAX_APPOINTMENTS_PER_DAY", 90))
MAX_CONCURRENT_APPOINTMENTS = int(os.getenv("MAX_CONCURRENT_APPOINTMENTS", 5))

# Mock: Disponibilidade do banco
agenda_ocupada = {
    "2025-05-22": ["09:00", "10:00", "10:00", "10:00", "10:00", "10:00"]
}

def gerar_grade_calendario():
    hoje = datetime.now().date()
    botoes = []
    for i in range(7):
        dia = hoje + timedelta(days=i)
        dia_str = dia.strftime("%Y-%m-%d")

        if dia < hoje:
            label = f"({dia.strftime('%d/%m')})"
            botao = InlineKeyboardButton(label, callback_data="-1")
        else:
            total_agendados = len(agenda_ocupada.get(dia_str, []))
            if total_agendados >= MAX_APPOINTMENTS_PER_DAY:
                label = f"❌ {dia.strftime('%d/%m')}"
                botao = InlineKeyboardButton(label, callback_data="-1")
            else:
                label = dia.strftime('%d/%m')
                botao = InlineKeyboardButton(label, callback_data=dia_str)

        botoes.append([botao])

    return botoes

def gerar_grade_horarios(dia_str):
    horarios = []
    ocupados = agenda_ocupada.get(dia_str, [])
    for hora in range(START_HOUR, END_HOUR):
        hora_str = f"{hora:02d}:00"
        count = ocupados.count(hora_str)
        if count >= MAX_CONCURRENT_APPOINTMENTS:
            label = f"❌ {hora_str}"
            botao = InlineKeyboardButton(label, callback_data="-1")
        else:
            label = hora_str
            botao = InlineKeyboardButton(label, callback_data=hora_str)
        horarios.append([botao])

    return horarios
