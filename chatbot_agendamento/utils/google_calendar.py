# utils/google_calendar.py
from datetime import datetime, timedelta
from googleapiclient.discovery import build
from google.oauth2 import service_account
import os

SCOPES = ['https://www.googleapis.com/auth/calendar']
SERVICE_ACCOUNT_FILE = 'json/service_account.json'
CALENDAR_ID = os.getenv('GOOGLE_CALENDAR_ID')

credentials = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES)
service = build('calendar', 'v3', credentials=credentials)

def obter_dias_disponiveis(numero_dias=7):
    hoje = datetime.utcnow().date()
    return [(hoje + timedelta(days=i)).isoformat() for i in range(numero_dias)]

def obter_horarios_disponiveis(dia):
    inicio_dia = datetime.strptime(dia, '%Y-%m-%d').isoformat() + 'Z'
    fim_dia = (datetime.strptime(dia, '%Y-%m-%d') + timedelta(days=1)).isoformat() + 'Z'

    eventos = service.events().list(
        calendarId=CALENDAR_ID,
        timeMin=inicio_dia,
        timeMax=fim_dia,
        singleEvents=True,
        orderBy="startTime"
    ).execute()

    horarios_ocupados = []
    for evento in eventos.get('items', []):
        start = evento['start'].get('dateTime', evento['start'].get('date'))
        horarios_ocupados.append(start)

    return horarios_ocupados

def salvar_evento_google(nome, telefone, email, dia, hora):
    evento = {
        'summary': f'Atendimento: {nome}',
        'description': f'Telefone: {telefone}, E-mail: {email}',
        'start': {
            'dateTime': f'{dia}T{hora}:00',
            'timeZone': 'America/Sao_Paulo',
        },
        'end': {
            'dateTime': f'{dia}T{int(hora[:2]) + 1:02d}:{hora[3:]}:00',
            'timeZone': 'America/Sao_Paulo',
        },
    }
    criado = service.events().insert(calendarId=CALENDAR_ID, body=evento).execute()
    return criado
