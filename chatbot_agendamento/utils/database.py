# utils/database.py

import sqlite3
import os
from dotenv import load_dotenv

load_dotenv()
DB_PATH = os.getenv("DB_PATH", "database/banco.db")

def salvar_agendamento(nome, telefone, email, data, hora):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO agendamentos (nome, telefone, email, data, hora)
        VALUES (?, ?, ?, ?, ?)
    """, (nome, telefone, email, data, hora))
    conn.commit()
    conn.close()

def verificar_disponibilidade(data, hora):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT COUNT(*) FROM agendamentos
        WHERE data = ? AND hora = ?
    """, (data, hora))
    resultado = cursor.fetchone()[0]
    conn.close()
    return resultado == 0

def obter_perguntas_respostas_por_tag(tag):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT question, response FROM intents
        WHERE tag = ?
    """, (tag,))
    resultados = cursor.fetchall()
    conn.close()
    return resultados

def obter_categorias_unicas():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT tag FROM intents ORDER BY tag")
    resultados = cursor.fetchall()
    conn.close()
    return resultados

def obter_categorias_disponiveis():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT tag FROM intents ORDER BY tag")
    resultados = cursor.fetchall()
    conn.close()
    return [linha[0] for linha in resultados]
