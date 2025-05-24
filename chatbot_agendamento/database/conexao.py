# database/conexao.py
import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join("database", "banco.db")

def gravar_resposta_feedback(respostas: dict):
    conexao = sqlite3.connect(DB_PATH)
    cursor = conexao.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pergunta TEXT,
            resposta TEXT,
            data_hora TEXT
        )
    """)

    for pergunta, resposta in respostas.items():
        cursor.execute(
            "INSERT INTO feedback (pergunta, resposta, data_hora) VALUES (?, ?, ?)",
            (pergunta, resposta, datetime.now().isoformat())
        )

    conexao.commit()
    conexao.close()
