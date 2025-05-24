# modules/consultar_agendamentos.py
from telegram import Update
from telegram.ext import ContextTypes
import sqlite3
import os

DB_PATH = os.path.join("database", "database/banco.db")

def consultar_agendamentos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT nome, telefone, email, data, hora
            FROM agendamentos
            WHERE telegram_id = ?
            ORDER BY data, hora
        """, (user_id,))

        resultados = cursor.fetchall()
        conn.close()

        if not resultados:
            await update.message.reply_text("🔍 Você ainda não possui agendamentos registrados.")
            return

        resposta = "📅 Seus agendamentos:\n"
        for nome, telefone, email, data, hora in resultados:
            resposta += f"\n🧑 Nome: {nome}\n📞 Telefone: {telefone}\n📧 E-mail: {email}\n📅 Data: {data}\n🕒 Hora: {hora}\n{'-'*30}"

        await update.message.reply_text(resposta)

    except Exception as e:
        await update.message.reply_text("⚠️ Ocorreu um erro ao consultar seus agendamentos. Tente novamente mais tarde.")
        print(f"Erro ao consultar agendamentos: {e}")
