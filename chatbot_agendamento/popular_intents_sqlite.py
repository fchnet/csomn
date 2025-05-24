# popular_intents_sqlite.py

import sqlite3
import json
import os

DB_PATH = "database/banco.db"
MEMORY_PATH = "json/memory.json"

def popular_tabela_intents():
    if not os.path.exists(MEMORY_PATH):
        print("Arquivo memory.json não encontrado.")
        return

    with open(MEMORY_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS intents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tag TEXT NOT NULL,
            patterns TEXT NOT NULL,
            responses TEXT NOT NULL
        );
    """)

    cursor.execute("DELETE FROM intents")  # Limpa os dados antes de repopular

    for item in data.get("intents", []):
        tag = item.get("tag", "")
        patterns = json.dumps(item.get("patterns", []), ensure_ascii=False)
        responses = json.dumps(item.get("responses", []), ensure_ascii=False)
        cursor.execute("INSERT INTO intents (tag, patterns, responses) VALUES (?, ?, ?)", (tag, patterns, responses))

    conn.commit()
    conn.close()
    print("✅ Dados da tabela 'intents' foram inseridos com sucesso.")

if __name__ == "__main__":
    popular_tabela_intents()
