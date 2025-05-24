# utils/email.py
import smtplib
import os
from email.message import EmailMessage

def enviar_email_confirmacao(destinatario, assunto, corpo, anexo=None):
    EMAIL_USER = os.getenv("EMAIL_USER")
    EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
    EMAIL_HOST = os.getenv("EMAIL_HOST", "smtp.gmail.com")
    EMAIL_PORT = int(os.getenv("EMAIL_PORT", 587))

    msg = EmailMessage()
    msg["Subject"] = assunto
    msg["From"] = EMAIL_USER
    msg["To"] = destinatario
    msg.set_content(corpo)

    if anexo:
        with open(anexo, "rb") as f:
            file_data = f.read()
            file_name = os.path.basename(anexo)
            msg.add_attachment(file_data, maintype="application", subtype="octet-stream", filename=file_name)

    with smtplib.SMTP(EMAIL_HOST, EMAIL_PORT) as server:
        server.starttls()
        server.login(EMAIL_USER, EMAIL_PASSWORD)
        server.send_message(msg)
