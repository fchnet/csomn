# modules/apagar_dados.py
import sqlite3
from telegram import Update
from telegram.ext import ContextTypes

DB_PATH = "database/banco.db"

async def apagar_dados(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = update.effective_user.id
    
    # Confirmação da exclusão
    texto_confirmacao = (
        "⚠️ *Confirmação de Exclusão de Dados*

"
        "Você está prestes a apagar todos os seus dados de agendamentos e feedbacks deste bot."
        "\nEsta ação é *irreversível* e não poderá ser desfeita.\n\n"
        "Se você tem certeza, envie a mensagem: `CONFIRMAR_APAGAR`"
    )
    await update.message.reply_text(texto_confirmacao, parse_mode="Markdown")

async def confirmar_apagar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text.strip().upper() == "CONFIRMAR_APAGAR":
        telegram_id = update.effective_user.id
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Apaga dados relacionados ao usuário
        cursor.execute("DELETE FROM agendamentos WHERE telegram_id = ?", (telegram_id,))
        cursor.execute("DELETE FROM feedback WHERE telegram_id = ?", (telegram_id,))
        conn.commit()
        conn.close()

        await update.message.reply_text("✅ Todos os seus dados foram apagados com sucesso.")
    else:
        await update.message.reply_text("❌ Código de confirmação incorreto. Nenhuma ação foi realizada.")
