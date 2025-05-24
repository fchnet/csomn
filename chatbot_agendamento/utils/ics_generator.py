# utils/ics_generator.py
from datetime import datetime, timedelta
import os

def gerar_arquivo_ics(dados):
    inicio = datetime.strptime(f"{dados['dia']} {dados['horario']}", "%d/%m/%Y %H:%M")
    fim = inicio + timedelta(minutes=60)
    conteudo = f"""BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Atendimento Bot//Agendamento//PT-BR
BEGIN:VEVENT
UID:{dados['email']}
DTSTAMP:{inicio.strftime('%Y%m%dT%H%M%S')}
DTSTART:{inicio.strftime('%Y%m%dT%H%M%S')}
DTEND:{fim.strftime('%Y%m%dT%H%M%S')}
SUMMARY:Atendimento Filantrópico
DESCRIPTION:Atendimento agendado via bot.
LOCATION:Online
END:VEVENT
END:VCALENDAR"""

    caminho = os.path.join("data", "agendamento.ics")
    with open(caminho, "w", encoding="utf-8") as file:
        file.write(conteudo)
    return caminho
