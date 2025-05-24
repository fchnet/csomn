import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from datetime import datetime, timedelta
import os
import logging

logger = logging.getLogger(__name__)

# Email configuration from environment
EMAIL_HOST = os.getenv("EMAIL_HOST", "smtp.gmail.com")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", 587))
EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
# Appointment duration needed for ICS
APPOINTMENT_DURATION_MINUTES = int(os.getenv("APPOINTMENT_DURATION_MINUTES", 60))

def send_confirmation_email(to_email, name, appointment_time):
    """Send a confirmation email with an .ics calendar invite for the appointment."""
    try:
        msg = MIMEMultipart()
        msg['From'] = EMAIL_USER
        msg['To'] = to_email
        msg['Subject'] = "✅ Confirmação de Agendamento"
        body = f"""
        <h2>Seu agendamento foi confirmado!</h2>
        <p><strong>Nome:</strong> {name}</p>
        <p><strong>Data/Horário:</strong> {appointment_time}</p>
        <p>Por favor, se prepare com 15 minutos de antecedência,<br>
        procure relaxar e, <strong>CALMAMENTE</strong>, inspire o ar pelo nariz e expire pelo nariz, pelo menos 3 vezes.</p>
        <p>Segue em anexo o convite do evento (.ics) para adicionar ao seu calendário.</p>
        <p>Agradecemos sua confiança!</p>
        """
        msg.attach(MIMEText(body, 'html'))
        # Create ICS calendar invite
        try:
            date_part, time_part = appointment_time.split(" às ")
            day, month, year = map(int, date_part.split("/"))
            hour, minute = map(int, time_part.split(":"))
        except Exception as e:
            logger.error(f"Erro ao parsear appointment_time: {appointment_time} -> {e}")
            day = month = year = hour = minute = None
        if year and month and day and hour is not None:
            start_dt = datetime(year, month, day, hour, minute)
            end_dt = start_dt + timedelta(minutes=APPOINTMENT_DURATION_MINUTES)
            dtstart = start_dt.strftime("%Y%m%dT%H%M%SZ")
            dtend = end_dt.strftime("%Y%m%dT%H%M%SZ")
            safe_name = ''.join(c for c in name if c.isalnum() or c in (' ', '_')).strip().replace(' ', '_')
            safe_email_user = EMAIL_USER or ''
            ics_content = f"""BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//GuiaEspiritual Bot//EN
BEGIN:VEVENT
UID:{datetime.now().strftime('%Y%m%d%H%M%S')}-{safe_name}@guiaespiritual
DTSTAMP:{datetime.now().strftime('%Y%m%dT%H%M%SZ')}
DTSTART:{dtstart}
DTEND:{dtend}
SUMMARY:Atendimento - {name}
DESCRIPTION:Atendimento confirmado com Guia Espiritual.
ORGANIZER;CN={safe_email_user}:MAILTO:{safe_email_user}
LOCATION:Casa Socorrista e Orfanato Maria de Nazaré
END:VEVENT
END:VCALENDAR"""
            part = MIMEApplication(ics_content.encode('utf-8'), _subtype="calendar")
            part.add_header('Content-Disposition', 'attachment; filename="convite.ics"')
            msg.attach(part)
        # Send email via SMTP
        with smtplib.SMTP(EMAIL_HOST, EMAIL_PORT) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            if EMAIL_USER and EMAIL_PASSWORD:
                server.login(EMAIL_USER, EMAIL_PASSWORD)
            server.send_message(msg)
        logger.info(f"E-mail de confirmação enviado para {to_email}")
    except Exception as e:
        logger.error(f"Erro ao enviar e-mail para {to_email}: {e}")
        raise
