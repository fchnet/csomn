import os
import json
import re
import calendar
import smtplib
import logging
import traceback
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from dotenv import load_dotenv
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
    CallbackQueryHandler,
)
from telegram.error import TimedOut, BadRequest
from google.oauth2 import service_account
from googleapiclient.discovery import build
from sentence_transformers import SentenceTransformer, util
import numpy as np
from cachetools import TTLCache
import threading
import redis

# --- CONFIGURAÇÃO DE LOGS ---
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.DEBUG
)
logger = logging.getLogger(__name__)

# --- CONFIGURAÇÕES ---
load_dotenv(encoding='utf-8')
TOKEN = os.getenv("TELEGRAM_TOKEN")
MEMORY_FILE = "json/memory.json"
SERVICE_ACCOUNT_FILE = "json/service_account.json"
CALENDAR_ID = os.getenv("GOOGLE_CALENDAR_ID")
EMAIL_HOST = os.getenv("EMAIL_HOST", "smtp.gmail.com")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", 587))
EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
FEEDBACK_FILE = "feedback.txt"
IMAGE_PATH = os.getenv("IMAGE_PATH", "image/maria_de_nazare.png")
START_HOUR = int(os.getenv("START_HOUR", 8))
END_HOUR = int(os.getenv("END_HOUR", 17))
APPOINTMENT_DURATION_MINUTES = int(os.getenv("APPOINTMENT_DURATION_MINUTES", 60))
MAX_CONCURRENT_APPOINTMENTS = int(os.getenv("MAX_CONCURRENT_APPOINTMENTS", 1))
MAX_APPOINTMENTS_PER_DAY = int(os.getenv("MAX_APPOINTMENTS_PER_DAY", 5))

# Cache e Redis
busy_info_cache = TTLCache(maxsize=100, ttl=120)  # Cache com TTL de 2 minutos
cache_lock = threading.Lock()
redis_client = redis.Redis(host='localhost', port=6379, db=0)

# Mapeamento dos textos dos botões do menu principal para as tags das categorias
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
    "🚪 Sair": "sair",
}

FEEDBACK_LEVELS = {
    "muito_insatisfeito": {"emoji": "💔", "value": 1},
    "insatisfeito": {"emoji": "😥", "value": 2},
    "neutro": {"emoji": "✨", "value": 3},
    "satisfeito": {"emoji": "🙏", "value": 4},
    "muito_satisfeito": {"emoji": "⭐", "value": 5},
}

# --- INICIALIZAÇÃO DO MODELO DE EMBEDDINGS ---
model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
question_embeddings = None
questions_list = []
category_questions = {}

def initialize_embeddings():
    global question_embeddings, questions_list, category_questions
    memory = load_memory()
    questions_list = []
    category_questions = {}
    for intent in memory.get("intents", []):
        category = intent["tag"]
        patterns = intent["patterns"]
        responses = intent["responses"]
        if not patterns or len(patterns) != len(responses):
            logger.warning(f"Categoria '{category}' tem padrões ou respostas inválidos")
            continue
        category_questions[category] = patterns
        questions_list.extend([(q, category) for q in patterns])
    if questions_list:
        question_embeddings = model.encode([q[0] for q in questions_list], convert_to_tensor=True)
    else:
        logger.warning("Nenhuma pergunta válida encontrada no memory.json")
        question_embeddings = None
    if "paz_interior" not in category_questions or not category_questions["paz_interior"]:
        logger.warning("Categoria 'paz_interior' não encontrada ou sem perguntas válidas")

# --- INICIALIZAÇÃO DO GOOGLE CALENDAR ---
def get_calendar_service():
    try:
        credentials = service_account.Credentials.from_service_account_file(
            SERVICE_ACCOUNT_FILE,
            scopes=["https://www.googleapis.com/auth/calendar"],
        )
        service = build("calendar", "v3", credentials=credentials, cache_discovery=False)
        logger.info("Serviço do Google Calendar inicializado com sucesso")
        return service
    except FileNotFoundError:
        logger.error(f"Arquivo de conta de serviço não encontrado: {SERVICE_ACCOUNT_FILE}")
        return None
    except Exception as e:
        logger.error(f"Erro ao inicializar serviço do Google Calendar: {e}")
        return None

# --- CARREGAR MEMÓRIA ---
def load_memory():
    try:
        with open(MEMORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        logger.error(f"Arquivo de memória não encontrado: {MEMORY_FILE}")
        return {"intents": []}
    except json.JSONDecodeError as e:
        logger.error(f"Erro ao decodificar JSON do memory.json: {e}")
        return {"intents": []}
    except Exception as e:
        logger.error(f"Erro inesperado ao carregar memory.json: {e}")
        return {"intents": []}

# --- SALVAR FEEDBACK ---
def save_feedback(feedback_level, feedback_text, user_id):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    feedback_line = f"[{timestamp}] User ID: {user_id} - Nível: {feedback_level}!Texto: {feedback_text}\n"
    try:
        with open(FEEDBACK_FILE, "a", encoding="utf-8") as f:
            f.write(feedback_line)
        logger.info(f"Feedback salvo de User ID {user_id} (Nível: {feedback_level})")
    except IOError as e:
        logger.error(f"Erro ao salvar feedback no arquivo {FEEDBACK_FILE}: {e}")
    except Exception as e:
        logger.error(f"Erro inesperado ao salvar feedback: {e}")

# --- VALIDAÇÃO DE E-MAIL ---
def is_valid_email(email):
    pattern = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    if not re.match(pattern, email):
        return False
    common_domains = ['.com', '.org', '.net', '.br']
    return any(email.lower().endswith(domain) for domain in common_domains)

# --- TELAS DO BOT ---
def get_main_menu():
    return ReplyKeyboardMarkup(
        [
            ["🧘 Meditação", "💖 Emoções"],
            ["🌟 Cura", "🕊️ Paz Interior"],
            ["📬 Mensagem", "📝 Feedback"],
            ["📅 Agendar Atendimento", "❌ Cancelar Agendamento"],
            ["❓ Ajuda", "ℹ️ Como funciona"],
            ["🚪 Sair"],
        ],
        resize_keyboard=True,
        one_time_keyboard=False
    )

def get_main_menu_inline():
    buttons = [
        [
            InlineKeyboardButton("🧘 Meditação", callback_data="submenu_meditacao_0"),
            InlineKeyboardButton("💖 Emoções", callback_data="submenu_emocao_0"),
        ],
        [
            InlineKeyboardButton("🌟 Cura", callback_data="submenu_cura_0"),
            InlineKeyboardButton("🕊️ Paz Interior", callback_data="submenu_paz_interior_0"),
        ],
        [
            InlineKeyboardButton("❓ Ajuda", callback_data="submenu_ajuda_0"),
            InlineKeyboardButton("📬 Mensagem", callback_data="submenu_mensagem_0"),
        ],
        [
            InlineKeyboardButton("📅 Agendar Atendimento", callback_data="start_scheduling"),
            InlineKeyboardButton("📝 Feedback", callback_data="start_feedback"),
        ],
        [
            InlineKeyboardButton("❌ Cancelar Agendamento", callback_data="start_cancel_appointment"),
            InlineKeyboardButton("ℹ️ Como funciona", callback_data="how_it_works"),
        ],
        [
            InlineKeyboardButton("🚪 Sair", callback_data="exit"),
        ],
    ]
    return InlineKeyboardMarkup(buttons)

def get_submenu(category, page=0, items_per_page=10):
    memory = load_memory()
    intent = next((i for i in memory.get("intents", []) if i["tag"] == category), None)
    questions = intent["patterns"] if intent else []
    if not questions:
        logger.warning(f"Categoria '{category}' não possui perguntas no memory.json")
        return InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Voltar", callback_data="main_menu")]]), \
               f"⚠️ Nenhuma pergunta disponível para {category.replace('_', ' ').capitalize()}."
    total_pages = (len(questions) + items_per_page - 1) // items_per_page
    page = max(0, min(page, total_pages - 1 if total_pages > 0 else 0))
    start_idx = page * items_per_page
    end_idx = min(start_idx + items_per_page, len(questions))
    page_questions = questions[start_idx:end_idx]
    buttons = []
    for i in range(0, len(page_questions)):
        idx = start_idx + i
        q = page_questions[i]
        safe_category = category.replace("_", "__")
        callback_data = f"answer_{safe_category}_{idx}"
        buttons.append([InlineKeyboardButton(q, callback_data=callback_data)])
    nav_buttons = []
    if page > 0:
        nav_buttons.append(InlineKeyboardButton("◀ Anterior", callback_data=f"submenu_{category}_{page-1}"))
    if page < total_pages - 1:
        nav_buttons.append(InlineKeyboardButton("Próximo ▶", callback_data=f"submenu_{category}_{page+1}"))
    if nav_buttons:
        buttons.append(nav_buttons)
    buttons.append([InlineKeyboardButton("🔙 Voltar ao Menu", callback_data="main_menu")])
    return InlineKeyboardMarkup(buttons), None

# --- SISTEMA DE AGENDAMENTO ---
async def start_scheduling(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        context.user_data.pop("agendamento", None)
        context.user_data.pop("current_month", None)
        keyboard = [[InlineKeyboardButton("🔙 Voltar ao Menu", callback_data="main_menu")]]
        await update.effective_message.reply_text(
            "📅 **Vamos agendar seu atendimento!**\n\nPor favor, digite seu **nome completo**:",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown",
        )
        context.user_data["agendamento"] = {"etapa": "nome"}
        logger.info(f"Iniciando agendamento - Etapa: nome")
    except Exception as e:
        logger.error(f"Erro em start_scheduling: {str(e)}\n{traceback.format_exc()}")
        await send_error_message(update, context, "ao iniciar o agendamento")

async def collect_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        agendamento = context.user_data.get("agendamento", {})
        if not agendamento or "etapa" not in agendamento:
            logger.error("Estado de agendamento inválido")
            await send_error_message(update, context, "estado de agendamento perdido")
            context.user_data.pop("agendamento", None)
            return
        keyboard = [[InlineKeyboardButton("🔙 Voltar ao Menu", callback_data="main_menu")]]
        if agendamento.get("etapa") == "nome":
            nome = update.effective_message.text.strip()
            if not nome:
                await update.effective_message.reply_text(
                    "❌ Por favor, digite um nome válido.",
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    parse_mode="Markdown",
                )
                return
            context.user_data["agendamento"]["nome"] = nome
            context.user_data["agendamento"]["etapa"] = "telefone"
            await update.effective_message.reply_text(
                f"Ótimo, **{nome}**! Agora seu **telefone** no formato:\n\n👉 *(DD)NNNNN-NNNN*\nExemplo: (99)99999-9999",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="Markdown",
            )
            logger.info(f"Agendamento - Etapa: telefone")
        elif agendamento.get("etapa") == "telefone":
            telefone = update.effective_message.text.strip()
            if not re.match(r"^\(\d{2}\)9\d{4}-\d{4}$", telefone):
                await update.effective_message.reply_text(
                    "❌ **Formato inválido!** Use: *(DD)9XXXX-XXXX*",
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    parse_mode="Markdown",
                )
                return
            context.user_data["agendamento"]["telefone"] = telefone
            context.user_data["agendamento"]["etapa"] = "calendario"
            await show_month_calendar(update, context)
            logger.info(f"Agendamento - Etapa: calendario")
    except Exception as e:
        logger.error(f"Erro em collect_info: {str(e)}\n{traceback.format_exc()}")
        await send_error_message(update, context, "ao coletar informações")

async def show_month_calendar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        now = datetime.now()
        current_date = now.date()
        current_year, current_month = now.year, now.month
        if "current_month" in context.user_data:
            year = context.user_data["current_month"]["year"]
            month = context.user_data["current_month"]["month"]
            if year < current_year or (year == current_year and month < current_month):
                year, month = current_year, current_month
                context.user_data["current_month"] = {"year": year, "month": month}
        else:
            year = current_year
            month = current_month
            context.user_data["current_month"] = {"year": year, "month": month}
        start_date = datetime(year, month, 1).date()
        if month == 12:
            end_date = datetime(year + 1, 1, 1).date()
        else:
            end_date = datetime(year, month + 1, 1).date()
        busy_info = get_busy_info(start_date, end_date)
        busy_days_total = busy_info["total"]
        month_name = calendar.month_name[month]
        keyboard = [
            [
                InlineKeyboardButton("◀", callback_data="cal_prev_month" if year > current_year or month > current_month else "ignore"),
                InlineKeyboardButton(f"{month_name} {year}", callback_data="ignore"),
                InlineKeyboardButton("▶", callback_data="cal_next_month")
            ],
            [InlineKeyboardButton(day, callback_data="ignore") for day in ["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"]]
        ]
        cal = calendar.monthcalendar(year, month)
        for week in cal:
            week_buttons = []
            for day in week:
                if day == 0:
                    week_buttons.append(InlineKeyboardButton(" ", callback_data="ignore"))
                else:
                    is_past_day = datetime(year, month, day).date() < current_date
                    is_day_full = busy_days_total.get(day, 0) >= MAX_APPOINTMENTS_PER_DAY
                    if is_past_day:
                        btn_text = f"({day})"
                        callback = "ignore"
                    elif is_day_full:
                        btn_text = f"{day}X"
                        callback = "ignore"
                    else:
                        btn_text = str(day)
                        callback = f"cal_day_{year}_{month}_{day}"
                    week_buttons.append(InlineKeyboardButton(btn_text, callback_data=callback))
            keyboard.append(week_buttons)
        keyboard.append([InlineKeyboardButton("🔙 Voltar ao Menu", callback_data="main_menu")])
        message_text = (
            "📅 **Selecione um dia disponível:**\n"
            "(X indica agenda cheia, () indica data passada)"
        )
        if update.callback_query:
            await update.callback_query.message.edit_text(
                message_text,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="Markdown"
            )
        else:
            await update.effective_message.reply_text(
                message_text,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="Markdown"
            )
        if context.user_data.get("agendamento"):
            context.user_data["agendamento"]["etapa"] = "calendario"
        logger.info(f"Agendamento - Etapa: calendario")
    except Exception as e:
        logger.error(f"Erro em show_month_calendar: {str(e)}\n{traceback.format_exc()}")
        await send_error_message(update, context, "ao mostrar o calendário")

def get_busy_info(start_date, end_date):
    cache_key = f"{start_date.isoformat()}_{end_date.isoformat()}"
    with cache_lock:
        if cache_key in busy_info_cache:
            logger.debug(f"Cache hit para {cache_key}")
            return busy_info_cache[cache_key]
    try:
        service = get_calendar_service()
        if not service:
            logger.warning("Serviço do Google Calendar não disponível")
            return {"hourly": {}, "total": {}}
        start_time_search = datetime.combine(start_date, datetime.min.time()).isoformat() + "Z"
        end_time_search = datetime.combine(end_date, datetime.min.time()).isoformat() + "Z"
        events_result = service.events().list(
            calendarId=CALENDAR_ID,
            timeMin=start_time_search,
            timeMax=end_time_search,
            singleEvents=True,
            orderBy="startTime"
        ).execute()
        busy_days_slots = {}
        busy_days_total = {}
        possible_slots = []
        current_time = datetime.min.replace(hour=START_HOUR).time()
        end_time_limit = datetime.min.replace(hour=END_HOUR).time()
        while current_time <= end_time_limit:
            possible_slots.append(current_time.strftime("%H:%M"))
            current_datetime = datetime.combine(datetime.min.date(), current_time) + timedelta(minutes=APPOINTMENT_DURATION_MINUTES)
            current_time = current_datetime.time()
        for event in events_result.get("items", []):
            logger.debug(f"Processando evento: {event.get('summary', 'Sem título')} - Início: {event.get('start', {}).get('dateTime', 'Sem data')}")
            start = event["start"].get("dateTime")
            if start:
                try:
                    event_datetime = datetime.fromisoformat(start.replace("Z", "+00:00")).astimezone()
                    event_date = event_datetime.date()
                    day = event_date.day
                    event_start_time = event_datetime.time()
                    if day not in busy_days_slots:
                        busy_days_slots[day] = {slot: 0 for slot in possible_slots}
                    if day not in busy_days_total:
                        busy_days_total[day] = 0
                    busy_days_total[day] += 1
                    for slot_str in possible_slots:
                        slot_time = datetime.strptime(slot_str, "%H:%M").time()
                        slot_end_time = (datetime.combine(datetime.min.date(), slot_time) + timedelta(minutes=APPOINTMENT_DURATION_MINUTES)).time()
                        if slot_time <= event_start_time < slot_end_time or (
                            slot_end_time <= slot_time and (event_start_time >= slot_time or event_start_time < slot_end_time)
                        ):
                            busy_days_slots[day][slot_str] += 1
                            break
                except ValueError:
                    logger.warning(f"Formato de data/hora inválido em evento: {start}")
                    continue
        full_slots_per_day = {day: [slot for slot, count in slots.items() if count >= MAX_CONCURRENT_APPOINTMENTS]
                            for day, slots in busy_days_slots.items()}
        result = {"hourly": full_slots_per_day, "total": busy_days_total}
        logger.debug(f"Eventos processados: {len(events_result.get('items', []))}")
        logger.debug(f"Dias com eventos: {busy_days_total}")
        logger.debug(f"Slots ocupados por dia: {busy_days_slots}")
        with cache_lock:
            busy_info_cache[cache_key] = result
        logger.info(f"Cache atualizado para {cache_key}")
        return result
    except Exception as e:
        logger.error(f"Erro em get_busy_info: {str(e)}\n{traceback.format_exc()}")
        return {"hourly": {}, "total": {}}

async def show_day_schedule(update: Update, context: ContextTypes.DEFAULT_TYPE, year, month, day):
    try:
        logger.info(f"Mostrando horários para {day}/{month}/{year}")
        selected_date = datetime(year, month, day).date()
        current_datetime = datetime.now()
        current_date = current_datetime.date()
        current_time = current_datetime.time()
        if selected_date < current_date:
            await update.callback_query.message.edit_text(
                f"❌ **{day}/{month}/{year} é uma data passada.**\nPor favor, escolha uma data futura.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 Voltar ao Calendário", callback_data="cal_back")],
                    [InlineKeyboardButton("🔙 Voltar ao Menu", callback_data="main_menu")]
                ]),
                parse_mode="Markdown",
            )
            return
        start_date = selected_date
        end_date = selected_date + timedelta(days=1)
        busy_info = get_busy_info(start_date, end_date)
        busy_slots_for_day = busy_info["hourly"].get(day, [])
        busy_total_for_day = busy_info["total"].get(day, 0)
        if busy_info is None:
            await send_error_message(update, context, "ao carregar os horários disponíveis")
            return
        if busy_total_for_day >= MAX_APPOINTMENTS_PER_DAY:
            await update.callback_query.message.edit_text(
                f"❌ **O dia {day}/{month}/{year} está totalmente ocupado.**\nEscolha outra data:",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 Voltar ao Calendário", callback_data="cal_back")],
                    [InlineKeyboardButton("🔙 Voltar ao Menu", callback_data="main_menu")]
                ]),
                parse_mode="Markdown",
            )
            return
        possible_slots = []
        current_slot_time = datetime.min.replace(hour=START_HOUR, minute=0, second=0, microsecond=0)
        end_time_limit = datetime.min.replace(hour=END_HOUR, minute=0, second=0, microsecond=0)
        while current_slot_time.time() <= end_time_limit.time():
            possible_slots.append(current_slot_time.strftime("%H:%M"))
            current_slot_time += timedelta(minutes=APPOINTMENT_DURATION_MINUTES)
        keyboard = []
        current_row = []
        buttons_per_row = 3
        for slot_str in possible_slots:
            slot_time = datetime.strptime(slot_str, "%H:%M").time()
            btn_text = slot_str
            callback = f"cal_time_{year}_{month}_{day}_{slot_str.replace(':', '')}"
            is_past_slot = (selected_date == current_date and slot_time < current_time)
            is_busy = slot_str in busy_slots_for_day
            if is_past_slot or is_busy:
                btn_text = f"{slot_str}X"
                callback = "ignore"
            current_row.append(InlineKeyboardButton(btn_text, callback_data=callback))
            if len(current_row) == buttons_per_row or slot_str == possible_slots[-1]:
                keyboard.append(current_row)
                current_row = []
        nav_buttons = [
            InlineKeyboardButton("🔙 Voltar ao Calendário", callback_data="cal_back"),
            InlineKeyboardButton("🔙 Voltar ao Menu", callback_data="main_menu")
        ]
        keyboard.append(nav_buttons)
        available_slots_count = sum(1 for row in keyboard[:-1] for button in row if button.callback_data != "ignore")
        if available_slots_count == 0:
            await update.callback_query.message.edit_text(
                f"❌ **{day}/{month}/{year} totalmente ocupado**\nEscolha outra data:",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 Voltar ao Calendário", callback_data="cal_back")],
                    [InlineKeyboardButton("🔙 Voltar ao Menu", callback_data="main_menu")]
                ]),
                parse_mode="Markdown",
            )
        else:
            await update.callback_query.message.edit_text(
                f"⏰ **Horários disponíveis para {day}/{month}/{year}:**\n(X indica horário ocupado ou passado)",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="Markdown",
            )
            context.user_data["agendamento"]["etapa"] = "horario"
            context.user_data["agendamento"]["data"] = f"{day}/{month}/{year}"
            logger.info(f"Agendamento - Etapa: horario")
    except Exception as e:
        logger.error(f"Erro em show_day_schedule: {str(e)}\n{traceback.format_exc()}")
        await send_error_message(update, context, "ao mostrar horários disponíveis")

def reserve_slot(year, month, day, hour):
    slot_key = f"slot:{year}:{month}:{day}:{hour}"
    ttl_seconds = 300
    try:
        reserved = redis_client.setnx(slot_key, "reserved")
        if reserved:
            redis_client.expire(slot_key, ttl_seconds)
            logger.info(f"Slot {slot_key} reservado por {ttl_seconds} segundos")
            return True
        else:
            logger.info(f"Slot {slot_key} já reservado")
            return False
    except Exception as e:
        logger.error(f"Erro ao reservar slot {slot_key}: {str(e)}\n{traceback.format_exc()}")
        return False

def release_slot(year, month, day, hour):
    slot_key = f"slot:{year}:{month}:{day}:{hour}"
    try:
        redis_client.delete(slot_key)
        logger.info(f"Slot {slot_key} liberado")
    except Exception as e:
        logger.error(f"Erro ao liberar slot {slot_key}: {str(e)}\n{traceback.format_exc()}")

async def confirm_appointment(update: Update, context: ContextTypes.DEFAULT_TYPE, year, month, day, hour):
    try:
        agendamento = context.user_data.get("agendamento", {})
        if not agendamento or "etapa" not in agendamento:
            await send_error_message(update, context, "estado de agendamento perdido")
            return
        hora_formatada = f"{hour[:2]}:{hour[2:]}"
        if agendamento.get("etapa") == "horario":
            if not reserve_slot(year, month, day, hora_formatada):
                await update.callback_query.message.edit_text(
                    f"❌ **Horário {hora_formatada} em {day}/{month}/{year} foi reservado por outro usuário.**\nEscolha outro horário:",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("🔙 Voltar ao Calendário", callback_data="cal_back")],
                        [InlineKeyboardButton("🔙 Voltar ao Menu", callback_data="main_menu")]
                    ]),
                    parse_mode="Markdown",
                )
                return
            context.user_data["agendamento"]["etapa"] = "email"
            context.user_data["agendamento"]["horario"] = f"{day}/{month}/{year} {hora_formatada}"
            await update.callback_query.message.edit_text(
                "📧 Por favor, digite seu e-mail para confirmação:",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Voltar ao Menu", callback_data="main_menu")]]),
                parse_mode="Markdown"
            )
            logger.info(f"Agendamento - Etapa: email")
            return
        if agendamento.get("etapa") != "confirmacao":
            release_slot(year, month, day, hora_formatada)
            await send_error_message(update, context, f"etapa de agendamento inválida")
            return
        if "email" not in agendamento:
            release_slot(year, month, day, hora_formatada)
            await send_error_message(update, context, "e-mail não fornecido")
            return
        selected_date = datetime(year, month, day).date()
        busy_info_check = get_busy_info(selected_date, selected_date + timedelta(days=1))
        if hora_formatada in busy_info_check["hourly"].get(day, []) or busy_info_check["total"].get(day, 0) >= MAX_APPOINTMENTS_PER_DAY:
            release_slot(year, month, day, hora_formatada)
            await update.effective_message.reply_text(
                f"❌ **Horário {hora_formatada} em {day}/{month}/{year} não está mais disponível.**\nEscolha outro horário:",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 Voltar ao Calendário", callback_data="cal_back")],
                    [InlineKeyboardButton("🔙 Voltar ao Menu", callback_data="main_menu")]
                ]),
                parse_mode="Markdown",
            )
            return
        start_time = datetime(year, month, day, int(hour[:2]), int(hour[2:]))
        end_time = start_time + timedelta(minutes=APPOINTMENT_DURATION_MINUTES)
        service = get_calendar_service()
        if not service:
            release_slot(year, month, day, hora_formatada)
            raise Exception("Serviço do Google Calendar não disponível")
        event = {
            "summary": f"Atendimento - {agendamento['nome']}",
            "description": f"Nome: {agendamento['nome']}\nTelefone: {agendamento['telefone']}\nE-mail: {agendamento['email'].lower()}",
            "start": {"dateTime": start_time.isoformat(), "timeZone": "America/Sao_Paulo"},
            "end": {"dateTime": end_time.isoformat(), "timeZone": "America/Sao_Paulo"},
        }
        created_event = service.events().insert(calendarId=CALENDAR_ID, body=event).execute()
        logger.info(f"Evento criado: {created_event.get('htmlLink')}")
        release_slot(year, month, day, hora_formatada)
        context.user_data["last_email"] = agendamento['email'].lower()
        email_sent = True
        try:
            send_confirmation_email(agendamento['email'], agendamento['nome'], f"{day}/{month}/{year} às {hora_formatada}")
        except Exception as e:
            logger.error(f"Erro ao enviar e-mail: {str(e)}\n{traceback.format_exc()}")
            email_sent = False
        confirmation_msg = (
            f"✅ **Agendamento Confirmado!**\n\n"
            f"📅 Data: {day}/{month}/{year} às {hora_formatada}\n"
            f"👤 Nome: {agendamento['nome']}\n"
            f"📞 Telefone: {agendamento['telefone']}\n"
            f"📧 E-mail: {agendamento['email']}\n\n"
        )
        if not email_sent:
            confirmation_msg += "⚠️ O e-mail de confirmação não pôde ser enviado, mas o agendamento foi registrado.\n"
        await update.effective_message.reply_text(
            confirmation_msg,
            reply_markup=get_main_menu(),
            parse_mode="Markdown"
        )
        context.user_data.pop("agendamento", None)
        logger.info("Agendamento concluído")
    except Exception as e:
        logger.error(f"Erro em confirm_appointment: {str(e)}\n{traceback.format_exc()}")
        release_slot(year, month, day, hora_formatada)
        await send_error_message(update, context, "ao confirmar o agendamento")
        context.user_data.pop("agendamento", None)

def send_confirmation_email(to_email, name, appointment_time):
    try:
        msg = MIMEMultipart()
        msg['From'] = EMAIL_USER
        msg['To'] = to_email
        msg['Subject'] = "✅ Confirmação de Agendamento"
        body = f"""
        <h2>Seu agendamento foi confirmado!</h2>
        <p><strong>Nome:</strong> {name}</p>
        <p><strong>Data/Horário:</strong> {appointment_time}</p>
        <p>Por favor, se prepare com 15 minutos de antecedência, <br>procure relaxar e, <strong>(CALMAMENTE)</strong> inspire o ar pelo nariz e, expire pelo nariz, pelo menos 3 vezes.</p>
        <p>Segue em anexo o convite do evento (.ics) para adicionar ao seu calendário.</p>
        <p>Agradecemos sua confiança!</p>
        """
        msg.attach(MIMEText(body, 'html'))
        date_part, time_part = appointment_time.split(" às ")
        day, month, year = map(int, date_part.split("/"))
        hour, minute = map(int, time_part.split(":"))
        start_time = datetime(year, month, day, hour, minute)
        end_time = start_time + timedelta(minutes=APPOINTMENT_DURATION_MINUTES)
        dtstart = start_time.strftime("%Y%m%dT%H%M%SZ")
        dtend = end_time.strftime("%Y%m%dT%H%M%SZ")
        safe_name = name.encode('ascii', 'ignore').decode('ascii').replace(' ', '_')
        safe_email_user = EMAIL_USER.encode('ascii', 'ignore').decode('ascii')
        ics_content = f"""BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//xAI//Grok Bot//EN
BEGIN:VEVENT
UID:{datetime.now().strftime('%Y%m%d%H%M%S')}-{safe_name}@xai.com
DTSTART:{dtstart}
DTEND:{dtend}
SUMMARY:Atendimento - {safe_name}
DESCRIPTION:Por favor, se prepare com 15 minutos de antecedência, <br>procure relaxar e, CALMAMENTE, inspire o ar pelo nariz e, expire pelo nariz, pelo menos 3 vezes.
ORGANIZER;CN={safe_email_user}:MAILTO:{safe_email_user}
LOCATION:CSOMN - Casa Socorrista e Orfanato Maria de Nazaré
END:VEVENT
END:VCALENDAR
"""
        ics_part = MIMEApplication(ics_content.encode('utf-8'), _subtype="calendar; charset=utf-8")
        ics_part.add_header('Content-Disposition', 'attachment; filename="invite.ics"')
        msg.attach(ics_part)
        with smtplib.SMTP(EMAIL_HOST, EMAIL_PORT) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(EMAIL_USER, EMAIL_PASSWORD)
            server.send_message(msg)
            logger.info(f"E-mail enviado para {to_email}")
    except Exception as e:
        logger.error(f"Erro ao enviar e-mail para {to_email}: {str(e)}\n{traceback.format_exc()}")
        raise

async def start_feedback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        context.user_data.pop("feedback", None)
        feedback_buttons = [
            InlineKeyboardButton(level["emoji"], callback_data=f"feedback_level_{name}")
            for name, level in FEEDBACK_LEVELS.items()
        ]
        keyboard = [feedback_buttons, [InlineKeyboardButton("🔙 Voltar ao Menu", callback_data="main_menu")]]
        await update.effective_message.reply_text(
            "📝 **Deixe seu feedback!**\n\nPor favor, selecione seu nível de satisfação geral:",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown",
        )
        context.user_data["feedback"] = {"etapa": "selecionar_nivel"}
        logger.info("Iniciando feedback - Etapa: selecionar_nivel")
    except Exception as e:
        logger.error(f"Erro em start_feedback: {str(e)}\n{traceback.format_exc()}")
        await send_error_message(update, context, "ao iniciar o feedback")

async def handle_feedback_level(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        query = update.callback_query
        data = query.data
        level_name = data.replace("feedback_level_", "")
        if level_name not in FEEDBACK_LEVELS:
            logger.warning(f"Nível de feedback inválido: {level_name}")
            await send_error_message(update, context, "ao processar seu nível de feedback")
            return
        context.user_data["feedback"] = {
            "etapa": "digitando_texto",
            "nivel": FEEDBACK_LEVELS[level_name]["value"],
            "emoji": FEEDBACK_LEVELS[level_name]["emoji"],
        }
        keyboard = [[InlineKeyboardButton("🔙 Voltar ao Menu", callback_data="main_menu")]]
        await query.message.edit_text(
            f"Você selecionou: {context.user_data['feedback']['emoji']}\n\nAgora, por favor, digite seu feedback (texto):",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
        logger.info(f"Feedback - Etapa: digitando_texto, Nível: {level_name}")
    except Exception as e:
        logger.error(f"Erro em handle_feedback_level: {str(e)}\n{traceback.format_exc()}")
        await send_error_message(update, context, "ao processar seu nível de feedback")
        context.user_data.pop("feedback", None)

async def handle_feedback_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        feedback_state = context.user_data.get("feedback", {})
        if feedback_state.get("etapa") == "digitando_texto":
            user_feedback_text = update.effective_message.text.strip()
            if not user_feedback_text:
                keyboard = [[InlineKeyboardButton("🔙 Voltar ao Menu", callback_data="main_menu")]]
                await update.effective_message.reply_text(
                    "❌ Por favor, digite um feedback válido.",
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    parse_mode="Markdown",
                )
                return
            user_id = update.effective_message.from_user.id
            feedback_level = feedback_state.get("nivel")
            if feedback_level is None:
                logger.error("Nível de feedback não encontrado")
                await send_error_message(update, context, "ao processar seu feedback")
                context.user_data.pop("feedback", None)
                return
            save_feedback(feedback_level, user_feedback_text, user_id)
            await update.effective_message.reply_text(
                "✅ **Obrigado pelo seu feedback!** Ele foi registrado com sucesso.\n\nVolte ao menu principal:",
                reply_markup=get_main_menu(),
                parse_mode="Markdown",
            )
            context.user_data.pop("feedback", None)
            logger.info("Feedback concluído")
    except Exception as e:
        logger.error(f"Erro em handle_feedback_text: {str(e)}\n{traceback.format_exc()}")
        await send_error_message(update, context, "ao processar seu feedback")
        context.user_data.pop("feedback", None)

async def start_cancel_appointment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        context.user_data.pop("cancelamento", None)
        keyboard = [[InlineKeyboardButton("🔙 Voltar ao Menu", callback_data="main_menu")]]
        last_email = context.user_data.get("last_email", "")
        prompt = (
            f"❌ **Cancelar Agendamento**\n\nPor favor, digite o **e-mail** usado no agendamento (ou digite 'Voltar' para cancelar):"
        )
        if last_email:
            prompt += f"\n\nSugestão: {last_email}"
        await update.effective_message.reply_text(
            prompt,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown",
        )
        context.user_data["cancelamento"] = {"etapa": "email", "page": 0}
    except Exception as e:
        logger.error(f"Erro em start_cancel_appointment: {str(e)}\n{traceback.format_exc()}")
        await send_error_message(update, context, "ao iniciar o cancelamento")

async def handle_cancel_appointment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        cancelamento = context.user_data.get("cancelamento", {})
        if cancelamento.get("etapa") != "email":
            logger.error("Estado de cancelamento inválido")
            await send_error_message(update, context, "estado de cancelamento perdido")
            context.user_data.pop("cancelamento", None)
            return
        email = update.effective_message.text.strip()
        logger.info(f"Tentativa de cancelamento com e-mail: {email}")
        if email.lower() == "voltar":
            await update.effective_message.reply_text(
                "🔙 Cancelamento abortado.",
                reply_markup=get_main_menu(),
                parse_mode="Markdown"
            )
            context.user_data.pop("cancelamento", None)
            return
        if not is_valid_email(email):
            keyboard = [[InlineKeyboardButton("🔙 Voltar ao Menu", callback_data="main_menu")]]
            last_email = context.user_data.get("last_email", "")
            prompt = "❌ E-mail inválido. Por favor, digite novamente (ou digite 'Voltar' para cancelar):"
            if last_email:
                prompt += f"\n\nSugestão: {last_email}"
            await update.effective_message.reply_text(
                prompt,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="Markdown"
            )
            return
        email_lower = email.lower()
        context.user_data["cancelamento"]["email"] = email_lower
        context.user_data["cancelamento"]["etapa"] = "listar_eventos"
        await list_user_events(update, context, page=0)
    except Exception as e:
        logger.error(f"Erro em handle_cancel_appointment: {str(e)}\n{traceback.format_exc()}")
        await send_error_message(update, context, "ao processar o cancelamento")
        context.user_data.pop("cancelamento", None)

def get_user_events(email, date=None, page=0, page_size=5):
    try:
        service = get_calendar_service()
        if not service:
            logger.warning("Serviço do Google Calendar não disponível")
            return [], 0
        now = datetime.now()
        end_date = now + timedelta(days=365)
        if date:
            start_date = datetime.strptime(date, '%Y-%m-%d').date()
            end_date = start_date + timedelta(days=1)
            time_min = datetime.combine(start_date, datetime.min.time()).isoformat() + "Z"
            time_max = datetime.combine(end_date, datetime.min.time()).isoformat() + "Z"
        else:
            time_min = now.isoformat() + "Z"
            time_max = end_date.isoformat() + "Z"
        events_result = service.events().list(
            calendarId=CALENDAR_ID,
            timeMin=time_min,
            timeMax=time_max,
            singleEvents=True,
            orderBy="startTime",
            q=email
        ).execute()
        user_events = [
            event for event in events_result.get("items", [])
            if 'description' in event and email in event['description'].lower()
            and 'start' in event and 'dateTime' in event['start']
        ]
        start_idx = page * page_size
        end_idx = start_idx + page_size
        return user_events[start_idx:end_idx], len(user_events)
    except Exception as e:
        logger.error(f"Erro em get_user_events: {str(e)}\n{traceback.format_exc()}")
        return [], 0

async def list_user_events(update: Update, context: ContextTypes.DEFAULT_TYPE, page=0):
    try:
        cancelamento = context.user_data.get("cancelamento", {})
        email = cancelamento.get("email")
        if not email:
            logger.error("E-mail não encontrado em context.user_data['cancelamento']")
            keyboard = [[InlineKeyboardButton("🔙 Voltar ao Menu", callback_data="main_menu")]]
            last_email = context.user_data.get("last_email", "")
            prompt = (
                f"❌ **E-mail não encontrado.**\n\nPor favor, digite o **e-mail** usado no agendamento (ou digite 'Voltar' para cancelar):"
            )
            if last_email:
                prompt += f"\n\nSugestão: {last_email}"
            if update.callback_query:
                await update.callback_query.message.edit_text(
                    prompt,
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    parse_mode="Markdown"
                )
            else:
                await update.effective_message.reply_text(
                    prompt,
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    parse_mode="Markdown"
                )
            context.user_data["cancelamento"] = {"etapa": "email", "page": page}
            return
        page_size = 5
        events, total_events = get_user_events(email, None, page, page_size)
        if not events:
            await update.effective_message.reply_text(
                f"❌ Nenhum agendamento encontrado para o e-mail **{email}**.",
                reply_markup=get_main_menu(),
                parse_mode="Markdown"
            )
            context.user_data.pop("cancelamento", None)
            return
        total_pages = (total_events + page_size - 1) // page_size
        page = max(0, min(page, total_pages - 1))
        keyboard = []
        for event in events:
            try:
                start_time = datetime.fromisoformat(event["start"]["dateTime"].replace("Z", "+00:00")).astimezone()
                event_str = f"{start_time.strftime('%d/%m/%Y %H:%M')} - {event.get('summary', 'Evento sem título')}"
                keyboard.append([InlineKeyboardButton(event_str, callback_data=f"confirm_cancel_{event['id']}")])
            except ValueError:
                logger.warning(f"Evento com formato de data/hora inválido: {event.get('summary', 'Sem título')}")
                continue
        nav_buttons = []
        if page > 0:
            nav_buttons.append(InlineKeyboardButton("◄ Anterior", callback_data=f"cancel_all_{page-1}"))
        if page < total_pages - 1:
            nav_buttons.append(InlineKeyboardButton("Próximo ▶", callback_data=f"cancel_all_{page+1}"))
        if nav_buttons:
            keyboard.append(nav_buttons)
        keyboard.append([InlineKeyboardButton("🔙 Voltar ao Menu", callback_data="main_menu")])
        text = f"📅 **Selecione o agendamento para cancelar (Página {page+1} de {total_pages}, mostrando {len(events)} de {total_events} registros):**"
        if update.callback_query:
            await update.callback_query.message.edit_text(
                text=text,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="Markdown"
            )
        else:
            await update.effective_message.reply_text(
                text=text,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="Markdown"
            )
        context.user_data["cancelamento"]["page"] = page
    except Exception as e:
        logger.error(f"Erro em list_user_events: {str(e)}\n{traceback.format_exc()}")
        await send_error_message(update, context, "ao listar os agendamentos")
        context.user_data.pop("cancelamento", None)

async def confirm_cancel_appointment(update: Update, context: ContextTypes.DEFAULT_TYPE, event_id):
    try:
        service = get_calendar_service()
        if not service:
            raise Exception("Serviço do Google Calendar não disponível")
        event = service.events().get(calendarId=CALENDAR_ID, eventId=event_id).execute()
        if 'start' in event and 'dateTime' in event['start']:
            start_time = datetime.fromisoformat(event["start"]["dateTime"].replace("Z", "+00:00")).astimezone()
            event_str = f"{start_time.strftime('%d/%m/%Y %H:%M')} - {event.get('summary', 'Evento sem título')}"
        else:
            event_str = f"Evento ID: {event_id} (Detalhes de data/hora não disponíveis)"
            logger.warning(f"Evento ID {event_id} sem detalhes de data/hora ao cancelar.")
        cancelamento = context.user_data.get("cancelamento", {})
        email = cancelamento.get("email")
        page = cancelamento.get("page", 0)
        context.user_data["cancelamento"] = {
            "etapa": "confirmar_cancelamento",
            "email": email,
            "page": page,
            "event_id": event_id
        }
        keyboard = [
            [InlineKeyboardButton("✅ Sim, cancelar", callback_data=f"execute_cancel_{event_id}")],
            [InlineKeyboardButton("❌ Não, voltar", callback_data=f"cancel_all_{page}")],
            [InlineKeyboardButton("🔙 Voltar ao Menu", callback_data="main_menu")]
        ]
        await update.effective_message.reply_text(
            f"⚠️ **Confirmar cancelamento**\n\nDeseja cancelar o seguinte agendamento?\n\n{event_str}",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
    except Exception as e:
        logger.error(f"Erro em confirm_cancel_appointment para evento ID {event_id}: {str(e)}\n{traceback.format_exc()}")
        await send_error_message(update, context, "ao confirmar o cancelamento")
        context.user_data.pop("cancelamento", None)

async def execute_cancel_appointment(update: Update, context: ContextTypes.DEFAULT_TYPE, event_id):
    try:
        service = get_calendar_service()
        if not service:
            raise Exception("Serviço do Google Calendar não disponível")
        event = service.events().get(calendarId=CALENDAR_ID, eventId=event_id).execute()
        if 'start' in event and 'dateTime' in event['start']:
            start_time = datetime.fromisoformat(event["start"]["dateTime"].replace("Z", "+00:00")).astimezone()
            event_str = f"{start_time.strftime('%d/%m/%Y %H:%M')} - {event.get('summary', 'Evento sem título')}"
        else:
            event_str = f"Evento ID: {event_id} (Detalhes de data/hora não disponíveis)"
            logger.warning(f"Evento ID {event_id} sem detalhes de data/hora ao cancelar.")
        service.events().delete(calendarId=CALENDAR_ID, eventId=event_id).execute()
        logger.info(f"Evento ID {event_id} cancelado com sucesso.")
        cancelamento = context.user_data.get("cancelamento", {})
        email = cancelamento.get("email", "desconhecido")
        page = cancelamento.get("page", 0)
        await update.effective_message.reply_text(
            f"❌ **Agendamento cancelado com sucesso!**\n\n{event_str}",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Voltar à lista", callback_data=f"cancel_all_{page}")],
                [InlineKeyboardButton("🔙 Voltar ao Menu", callback_data="main_menu")]
            ]),
            parse_mode="Markdown"
        )
        context.user_data["cancelamento"] = {"etapa": "listar_eventos", "email": email, "page": page}
    except Exception as e:
        logger.error(f"Erro em execute_cancel_appointment para evento ID {event_id}: {str(e)}\n{traceback.format_exc()}")
        await send_error_message(update, context, "ao cancelar o agendamento")
        context.user_data.pop("cancelamento", None)

async def send_error_message(update: Update, context: ContextTypes.DEFAULT_TYPE, error_detail: str):
    error_msg = f"❌ Ocorreu um erro {error_detail}. Por favor, tente novamente."
    try:
        await update.effective_message.reply_text(
            error_msg,
            reply_markup=get_main_menu(),
            parse_mode="Markdown"
        )
    except Exception as e:
        logger.error(f"Erro ao enviar mensagem de erro: {str(e)}\n{traceback.format_exc()}")

# --- HANDLERS PRINCIPAIS ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        context.user_data.clear()
        if os.path.exists(IMAGE_PATH):
            try:
                with open(IMAGE_PATH, 'rb') as photo:
                    await update.message.reply_photo(
                        photo=photo,
                        caption="🌟 **CSOMN - Casa Socorrista e Orfanato Maria de Nazaré**\n\n✨ **Bem-vindo ao Guia Espiritual!**\n\n",
                        reply_markup=None,
                        parse_mode="Markdown",
                    )
            except Exception as e:
                logger.error(f"Erro ao enviar a imagem {IMAGE_PATH}: {str(e)}\n{traceback.format_exc()}")
                await update.message.reply_text(
                    "🌟 **CSOMN - Casa Socorrista e Orfanato Maria de Nazaré**\n\n✨ **Bem-vindo ao Guia Espiritual!**\n\n",
                    reply_markup=None,
                    parse_mode="Markdown",
                )
        else:
            logger.warning(f"Imagem {IMAGE_PATH} não encontrada.")
            await update.message.reply_text(
                "🌟 **CSOMN - Casa Socorrista e Orfanato Maria de Nazaré**\n\n✨ **Bem-vindo ao Guia Espiritual!**\n\n",
                reply_markup=None,
                parse_mode="Markdown",
            )
        await update.message.reply_text(
            "Escolha uma opção abaixo:",
            reply_markup=get_main_menu(),
            parse_mode="Markdown",
        )
    except Exception as e:
        logger.error(f"Erro em start: {str(e)}\n{traceback.format_exc()}")
        await send_error_message(update, context, "ao iniciar o bot")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user_msg = update.message.text
        memory = load_memory()
        if user_msg in MAIN_MENU_CATEGORIES:
            logger.info(f"Comando de menu principal recebido: {user_msg}")
            context.user_data.pop("cancelamento", None)
            context.user_data.pop("agendamento", None)
            context.user_data.pop("feedback", None)
            context.user_data.pop("current_month", None)
            if user_msg == "🚪 Sair":
                await update.message.reply_text("Até logo! 🙏", reply_markup=ReplyKeyboardRemove())
                return
            if user_msg == "📅 Agendar Atendimento":
                await start_scheduling(update, context)
                return
            if user_msg == "📝 Feedback":
                await start_feedback(update, context)
                return
            if user_msg == "❌ Cancelar Agendamento":
                await start_cancel_appointment(update, context)
                return
            if user_msg == "ℹ️ Como funciona":
                message = (
                    "ℹ️ *Como funciona o agendamento*\n\n"
                    "1. Clique em 'Agendar Atendimento' para escolher uma data e horário.\n"
                    "2. No calendário, selecione um dia disponível:\n"
                    "   - Dias disponíveis aparecem com o número (ex.: 23).\n"
                    "   - Dias lotados são marcados com X (ex.: 19X).\n"
                    "   - Dias passados são marcados com () (ex.: (18)).\n"
                    "3. Escolha um horário disponível e confirme seus dados.\n"
                    "4. Para cancelar, use 'Cancelar Agendamento' e selecione o atendimento.\n\n"
                    "Selecione um dia disponível: (X indica agenda cheia, () indica data passada)"
                )
                await update.message.reply_text(
                    message,
                    reply_markup=get_main_menu(),
                    parse_mode="Markdown"
                )
                return
            category = MAIN_MENU_CATEGORIES[user_msg]
            keyboard, error_msg = get_submenu(category)
            reply_text = error_msg if error_msg else f"🔍 **{user_msg}** - Escolha um tópico:"
            await update.message.reply_text(
                reply_text,
                reply_markup=keyboard,
                parse_mode="Markdown",
            )
            return
        if context.user_data.get("agendamento", {}).get("etapa") == "email":
            if not is_valid_email(user_msg):
                keyboard = [[InlineKeyboardButton("🔙 Voltar ao Menu", callback_data="main_menu")]]
                last_email = context.user_data.get("last_email", "")
                prompt = "❌ E-mail inválido. Por favor, digite novamente:"
                if last_email:
                    prompt += f"\n\nSugestão: {last_email}"
                await update.message.reply_text(
                    prompt,
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    parse_mode="Markdown"
                )
                return
            context.user_data["agendamento"]["email"] = user_msg.lower()
            context.user_data["agendamento"]["etapa"] = "confirmacao"
            if "horario" not in context.user_data["agendamento"]:
                logger.error("Chave 'horario' não encontrada")
                await send_error_message(update, context, "ao processar o horário do agendamento")
                context.user_data.pop("agendamento", None)
                return
            data_str, hora_str = context.user_data["agendamento"]["horario"].split()
            try:
                day, month, year = map(int, data_str.split("/"))
            except ValueError:
                logger.error(f"Erro ao converter data: {data_str}")
                await send_error_message(update, context, "ao processar a data do agendamento")
                return
            hour = hora_str.replace(":", "")
            logger.info(f"Agendamento - Etapa: confirmacao")
            await confirm_appointment(update, context, year, month, day, hour)
            return
        if context.user_data.get("feedback", {}).get("etapa") == "digitando_texto":
            await handle_feedback_text(update, context)
            return
        if context.user_data.get("cancelamento", {}).get("etapa") == "email":
            await handle_cancel_appointment(update, context)
            return
        if context.user_data.get("agendamento"):
            await collect_info(update, context)
            return
        if question_embeddings is not None and questions_list:
            try:
                user_embedding = model.encode(user_msg, convert_to_tensor=True)
                cos_scores = util.cos_sim(user_embedding, question_embeddings)[0]
                max_idx = np.argmax(cos_scores)
                if cos_scores[max_idx] > 0.6:
                    question, category = questions_list[max_idx]
                    for intent in memory.get("intents", []):
                        if intent["tag"] == category:
                            try:
                                idx = intent["patterns"].index(question)
                                response = intent["responses"][idx]
                                await update.message.reply_text(
                                    response,
                                    reply_markup=get_main_menu(),
                                    parse_mode="Markdown"
                                )
                                logger.info(f"Resposta encontrada via embedding: {response[:50]}...")
                                return
                            except ValueError:
                                logger.error(f"Pergunta '{question}' não encontrada na categoria '{category}'")
                                continue
            except Exception as e:
                logger.error(f"Erro na busca de resposta via embedding: {str(e)}\n{traceback.format_exc()}")
        await update.message.reply_text(
            "🤔 **Não entendi.** Tente:\n- Usar os botões\n- Reformular sua pergunta\n- Agendar atendimento 📅",
            reply_markup=get_main_menu(),
            parse_mode="Markdown",
        )
        logger.info(f"Resposta padrão enviada para '{user_msg}'")
    except Exception as e:
        logger.error(f"Erro geral em handle_message: {str(e)}\n{traceback.format_exc()}")
        await send_error_message(update, context, "ao processar sua mensagem")

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    logger.debug(f"Callback query recebida: {data}")
    try:
        await query.answer()
    except (TimedOut, BadRequest) as e:
        logger.warning(f"Callback query expirado ou inválido: {str(e)}\n{traceback.format_exc()}")
        try:
            await query.message.edit_text(
                "⚠️ **Ação expirada.**\n\nOs botões desta mensagem expiraram. Por favor, reinicie o processo:",
                reply_markup=None,
                parse_mode="Markdown"
            )
            await query.message.reply_text(
                "✨ **Bem-vindo ao Guia Espiritual!**\n\nEscolha uma opção abaixo:",
                reply_markup=get_main_menu(),
                parse_mode="Markdown"
            )
        except Exception as edit_error:
            logger.error(f"Erro ao editar mensagem expirada: {str(edit_error)}\n{traceback.format_exc()}")
            try:
                await query.message.reply_text(
                    "⚠️ **Ação expirada.** Por favor, escolha uma opção no menu principal abaixo:",
                    reply_markup=get_main_menu(),
                    parse_mode="Markdown"
                )
            except Exception as reply_error:
                logger.error(f"Erro ao enviar mensagem de fallback: {str(reply_error)}\n{traceback.format_exc()}")
        return
    active_state = context.user_data.get("agendamento") or context.user_data.get("cancelamento") or context.user_data.get("feedback")
    is_main_menu_callback = data == "main_menu"
    is_scheduling_callback = data.startswith("cal_") or data == "start_scheduling"
    is_feedback_callback = data.startswith("feedback_level_") or data == "start_feedback"
    is_cancel_callback = data.startswith("cancel_") or data.startswith("execute_cancel_") or \
                         data.startswith("confirm_cancel_") or data == "start_cancel_appointment"
    is_answer_callback = data.startswith("answer_")
    is_part_of_active_flow = False
    if active_state:
        if "agendamento" in context.user_data and is_scheduling_callback:
            is_part_of_active_flow = True
        elif "cancelamento" in context.user_data and is_cancel_callback:
            is_part_of_active_flow = True
        elif "feedback" in context.user_data and is_feedback_callback:
            is_part_of_active_flow = True
        elif not active_state and is_answer_callback:
            is_part_of_active_flow = True
    if active_state and not is_part_of_active_flow and not is_main_menu_callback and not data.startswith("confirm_cancel_"):
        logger.info(f"Callback '{data}' durante fluxo ativo. Limpando estados.")
        context.user_data.pop("agendamento", None)
        context.user_data.pop("cancelamento", None)
        context.user_data.pop("feedback", None)
        context.user_data.pop("current_month", None)
        try:
            await query.message.edit_text(
                "⚠️ Ação anterior cancelada. Processando nova solicitação...",
                reply_markup=None,
                parse_mode="Markdown"
            )
        except Exception as edit_error:
            logger.warning(f"Não foi possível editar mensagem: {str(edit_error)}\n{traceback.format_exc()}")
    try:
        if data == "how_it_works":
            message = (
                "ℹ️ *Como funciona o agendamento*\n\n"
                "1. Clique em 'Agendar Atendimento' para escolher uma data e horário.\n"
                "2. No calendário, selecione um dia disponível:\n"
                "   - Dias disponíveis aparecem com o número (ex.: 23).\n"
                "   - Dias lotados são marcados com X (ex.: 19X).\n"
                "   - Dias passados são marcados com () (ex.: (18)).\n"
                "3. Escolha um horário disponível e confirme seus dados.\n"
                "4. Para cancelar, use 'Cancelar Agendamento' e selecione o atendimento.\n\n"
                "Selecione uma opção abaixo:"
            )
            await query.message.edit_text(
                message,
                reply_markup=get_main_menu_inline(),
                parse_mode="Markdown"
            )
        elif data == "cal_prev_month":
            current_month = context.user_data.get("current_month", {})
            year = current_month.get("year", datetime.now().year)
            month = current_month.get("month", datetime.now().month)
            month -= 1
            if month == 0:
                month = 12
                year -= 1
            context.user_data["current_month"] = {"year": year, "month": month}
            await show_month_calendar(update, context)
        elif data == "cal_next_month":
            current_month = context.user_data.get("current_month", {})
            year = current_month.get("year", datetime.now().year)
            month = current_month.get("month", datetime.now().month)
            month += 1
            if month == 13:
                month = 1
                year += 1
            context.user_data["current_month"] = {"year": year, "month": month}
            await show_month_calendar(update, context)
        elif data.startswith("cal_day_"):
            parts = data.split("_")
            if len(parts) == 5:
                _, _, year_str, month_str, day_str = parts
                try:
                    year = int(year_str)
                    month = int(month_str)
                    day = int(day_str)
                    await show_day_schedule(update, context, year, month, day)
                except ValueError:
                    logger.error(f"Erro ao converter data: {data}")
                    await send_error_message(update, context, "ao processar a data selecionada")
            else:
                logger.error(f"Formato inválido para cal_day: {data}")
                await send_error_message(update, context, "ao selecionar a data")
        elif data.startswith("cal_time_"):
            parts = data.split("_")
            if len(parts) == 6:
                _, _, year_str, month_str, day_str, hour = parts
                try:
                    year = int(year_str)
                    month = int(month_str)
                    day = int(day_str)
                    await confirm_appointment(update, context, year, month, day, hour)
                except ValueError:
                    logger.error(f"Erro ao converter data/hora: {data}")
                    await send_error_message(update, context, "ao processar o horário selecionado")
            else:
                logger.error(f"Formato inválido para cal_time: {data}")
                await send_error_message(update, context, "ao selecionar o horário")
        elif data == "cal_back":
            await show_month_calendar(update, context)
        elif data.startswith("confirm_cancel_"):
            parts = data.split("_")
            if len(parts) == 3:
                _, _, event_id = parts
                await confirm_cancel_appointment(update, context, event_id)
            else:
                logger.error(f"Formato inválido para confirm_cancel: {data}")
                await send_error_message(update, context, "ao selecionar o agendamento para cancelar")
        elif data.startswith("execute_cancel_"):
            parts = data.split("_")
            if len(parts) == 3:
                _, _, event_id = parts
                await execute_cancel_appointment(update, context, event_id)
            else:
                logger.error(f"Formato inválido para execute_cancel: {data}")
                await send_error_message(update, context, "ao cancelar o agendamento")
        elif data.startswith("cancel_all_"):
            page = int(data.split("_")[-1])
            await list_user_events(update, context, page)
        elif data.startswith("submenu_"):
            try:
                parts = data.rsplit("_", 1)
                if len(parts) != 2:
                    logger.error(f"Formato inválido para submenu: {data}")
                    await send_error_message(update, context, "ao navegar no submenu")
                    return
                prefix_and_encoded_category, page_str = parts
                encoded_category = prefix_and_encoded_category[len("submenu_"):]
                category = encoded_category.replace("__", "_")
                try:
                    page = int(page_str)
                except ValueError:
                    logger.error(f"Erro ao converter página: {page_str}")
                    await send_error_message(update, context, "ao navegar no submenu")
                    return
                keyboard, error_msg = get_submenu(category, page)
                reply_text = error_msg if error_msg else f"🔍 **{category.replace('_', ' ').title()}** - Escolha um tópico:"
                await query.message.edit_text(
                    reply_text,
                    reply_markup=keyboard,
                    parse_mode="Markdown"
                )
                logger.debug(f"Submenu gerado para categoria '{category}', página {page}")
            except Exception as e:
                logger.error(f"Erro ao processar submenu: {str(e)}\n{traceback.format_exc()}")
                await send_error_message(update, context, "ao navegar no submenu")
        elif data == "main_menu":
            logger.info("Callback 'main_menu' recebida.")
            context.user_data.pop("agendamento", None)
            context.user_data.pop("cancelamento", None)
            context.user_data.pop("feedback", None)
            context.user_data.pop("current_month", None)
            if query.message.reply_markup:
                await query.message.edit_reply_markup(reply_markup=None)
            await query.message.reply_text(
                "✨ **Bem-vindo ao Guia Espiritual!**\n\nEscolha uma opção abaixo:",
                reply_markup=get_main_menu(),
                parse_mode="Markdown"
            )
        elif data == "exit":
            await query.message.edit_text(
                "Até logo! 🙏",
                reply_markup=ReplyKeyboardRemove()
            )
            await query.message.edit_reply_markup(reply_markup=None)
        elif data.startswith("answer_"):
            try:
                parts = data.rsplit("_", 1)
                if len(parts) != 2:
                    logger.error(f"Formato inválido para answer: {data}")
                    await query.message.edit_text(
                        "⚠️ Erro técnico ao processar a resposta.",
                        reply_markup=get_main_menu(),
                        parse_mode="Markdown"
                    )
                    await query.message.edit_reply_markup(reply_markup=None)
                    return
                prefix_and_encoded_category, idx_str = parts
                encoded_category = prefix_and_encoded_category[len("answer_"):]
                category = encoded_category.replace("__", "_")
                try:
                    idx = int(idx_str)
                except ValueError:
                    logger.error(f"Índice inválido: {idx_str}")
                    await query.message.edit_text(
                        "⚠️ Erro técnico ao processar a resposta.",
                        reply_markup=get_main_menu(),
                        parse_mode="Markdown"
                    )
                    await query.message.edit_reply_markup(reply_markup=None)
                    return
                memory = load_memory()
                intent = next((i for i in memory.get("intents", []) if i["tag"] == category), None)
                if not intent:
                    logger.error(f"Categoria '{category}' não encontrada")
                    await query.message.edit_text(
                        "⚠️ Categoria não encontrada.",
                        reply_markup=get_main_menu(),
                        parse_mode="Markdown"
                    )
                    await query.message.edit_reply_markup(reply_markup=None)
                    return
                patterns = intent.get("patterns", [])
                responses = intent.get("responses", [])
                if idx < 0 or idx >= len(patterns):
                    logger.error(f"Índice de pergunta inválido: {idx}")
                    await query.message.edit_text(
                        "⚠️ Pergunta não encontrada.",
                        reply_markup=get_main_menu(),
                        parse_mode="Markdown"
                    )
                    await query.message.edit_reply_markup(reply_markup=None)
                    return
                if idx >= len(responses):
                    logger.error(f"Resposta não encontrada para índice {idx}")
                    await query.message.edit_text(
                        "⚠️ Resposta não encontrada.",
                        reply_markup=get_main_menu(),
                        parse_mode="Markdown"
                    )
                    await query.message.edit_reply_markup(reply_markup=None)
                    return
                answer = responses[idx]
                await query.message.edit_text(
                    answer,
                    reply_markup=None,
                    parse_mode="Markdown"
                )
                await query.message.reply_text(
                    "Escolha uma opção abaixo:",
                    reply_markup=get_main_menu(),
                    parse_mode="Markdown"
                )
            except Exception as e:
                logger.error(f"Erro ao processar answer: {str(e)}\n{traceback.format_exc()}")
                await query.message.edit_text(
                    "⚠️ Erro técnico ao processar a resposta.",
                    reply_markup=get_main_menu(),
                    parse_mode="Markdown"
                )
                await query.message.edit_reply_markup(reply_markup=None)
        elif data == "start_scheduling":
            await start_scheduling(update, context)
        elif data == "start_feedback":
            await start_feedback(update, context)
        elif data == "start_cancel_appointment":
            await start_cancel_appointment(update, context)
        elif data.startswith("feedback_level_"):
            await handle_feedback_level(update, context)
        elif data == "ignore":
            await query.message.reply_text(
                "⚠️ Ação não permitida. Escolha uma opção válida.",
                reply_markup=get_main_menu(),
                parse_mode="Markdown"
            )
    except Exception as e:
        logger.error(f"Erro em handle_callback para callback '{data}': {str(e)}\n{traceback.format_exc()}")
        try:
            await query.message.edit_text(
                "❌ Ocorreu um erro ao processar sua solicitação. Por favor, tente novamente.",
                reply_markup=get_main_menu(),
                parse_mode="Markdown"
            )
        except Exception as edit_error:
            logger.error(f"Erro ao editar mensagem de erro: {str(edit_error)}\n{traceback.format_exc()}")
            await query.message.reply_text(
                "❌ Ocorreu um erro. Volte ao menu principal:",
                reply_markup=get_main_menu(),
                parse_mode="Markdown"
            )

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.error(f"Update {update} causou erro: {context.error}\n{traceback.format_exc()}")
    try:
        if update and (update.message or update.callback_query):
            await send_error_message(update, context, "inesperado")
    except Exception as e:
        logger.error(f"Erro ao lidar com erro: {str(e)}\n{traceback.format_exc()}")

def main():
    try:
        initialize_embeddings()
        app = ApplicationBuilder().token(TOKEN).build()
        app.add_handler(CommandHandler("start", start))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        app.add_handler(CallbackQueryHandler(handle_callback))
        app.add_error_handler(error_handler)
        logger.info("Bot iniciado. Iniciando polling...")
        app.run_polling(allowed_updates=Update.ALL_TYPES)
    except Exception as e:
        logger.error(f"Erro ao iniciar o bot: {str(e)}\n{traceback.format_exc()}")

if __name__ == "__main__":
    main()