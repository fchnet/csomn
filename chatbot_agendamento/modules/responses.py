
import sqlite3
import random

def responder_tag(tag):
    try:
        conn = sqlite3.connect("database/banco.db")
        cursor = conn.cursor()
        cursor.execute("SELECT response FROM intents WHERE tag = ?", (tag,))
        respostas = [row[0] for row in cursor.fetchall()]
        conn.close()
        if respostas:
            return random.choice(respostas)
        return "Ainda não tenho uma resposta para isso."
    except Exception as e:
        return f"Erro ao buscar resposta: {e}"
