import sqlite3
import json
import os

DB_PATH = os.path.join("database", "banco.db")
JSON_PATH = os.path.join("json", "memory.json")

# Cria a base de dados e tabela, se não existirem
def criar_tabela():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tag TEXT,
            question TEXT,
            response TEXT
        )
    ''')
    conn.commit()
    conn.close()

# Popula a tabela com dados do memory.json
def importar_dados():
    if not os.path.exists(JSON_PATH):
        print(f"Arquivo {JSON_PATH} não encontrado.")
        return

    with open(JSON_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    intents = data.get("intents", [])
    if not intents:
        print("Nenhum dado encontrado no arquivo JSON.")
        return

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    for intent in intents:
        tag = intent.get("tag")
        responses = intent.get("responses", [])
        questions = intent.get("patterns", [])

        for question in questions:
            for response in responses:
                c.execute("INSERT INTO feedback (tag, question, response) VALUES (?, ?, ?)", (tag, question, response))

    conn.commit()
    conn.close()
    print("Base de dados populada com sucesso!")

if __name__ == "__main__":
    criar_tabela()
    importar_dados()
