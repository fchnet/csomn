# modules/indicadores_feedback.py
import sqlite3
from collections import defaultdict
from telegram import Update
from telegram.ext import CallbackContext

DB_PATH = 'database/banco.db'

def gerar_relatorio_estatistico():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT pergunta, resposta FROM feedback")
    dados = cursor.fetchall()
    conn.close()

    relatorio = defaultdict(lambda: defaultdict(int))

    for pergunta, resposta in dados:
        relatorio[pergunta][resposta] += 1

    texto = "\u2728 *Relat\u00f3rio de Feedbacks* \u2728\n"
    for pergunta, respostas in relatorio.items():
        texto += f"\n*{pergunta}*\n"
        total = sum(respostas.values())
        for resposta, qtd in respostas.items():
            percentual = (qtd / total) * 100
            texto += f"- {resposta}: {qtd} ({percentual:.1f}%)\n"
    return texto

def exibir_indicadores(update: Update, context: CallbackContext):
    relatorio = gerar_relatorio_estatistico()
    update.message.reply_text(relatorio, parse_mode='Markdown')
