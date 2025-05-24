# utils/email_service.py
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
import os
from utils.ics_generator import gerar_arquivo_ics

def enviar_email_confirmacao(dados):
    remetente = os.getenv("EMAIL_USER")
    senha = os.getenv("EMAIL_PASSWORD")
    destinatario = dados["email"]

    # Gera arquivo .ics
    caminho_ics = gerar_arquivo_ics(dados)

    msg = MIMEMultipart()
    msg["From"] = remetente
    msg["To"] = destinatario
    msg["Subject"] = "Confirmação de Agendamento"

    corpo = (
        f"Olá, {dados['nome']}!\n\n"
        f"Seu atendimento está agendado para {dados['dia']} às {dados['horario']}.\n"
        f"Telefone informado: {dados['telefone']}\n"
        f"E-mail: {dados['email']}\n\n"
        "Se desejar, adicione o compromisso ao seu calendário com o arquivo em anexo."
    )
    msg.attach(MIMEText(corpo, "plain"))

    # Anexar arquivo ICS
    with open(caminho_ics, "rb") as file:
        parte_ics = MIMEApplication(file.read(), _subtype="ics")
        parte_ics.add_header("Content-Disposition", "attachment", filename="agendamento.ics")
        msg.attach(parte_ics)

    try:
        with smtplib.SMTP(os.getenv("EMAIL_HOST"), int(os.getenv("EMAIL_PORT"))) as server:
            server.starttls()
            server.login(remetente, senha)
            server.send_message(msg)
        print(f"✅ Confirmação enviada para {destinatario}")
    except Exception as e:
        print(f"❌ Erro ao enviar e-mail: {e}")
