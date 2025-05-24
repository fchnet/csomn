import sqlite3

conn = sqlite3.connect("database/banco.db")
cursor = conn.cursor()
cursor.execute("SELECT tag, response FROM intents LIMIT 5")
dados = cursor.fetchall()
print(f"A tabela 'intents' contém {len(dados)} registros de exemplo:")
for tag, resp in dados:
    print(f"Tag: {tag} -> Resposta: {resp[:60]}...")
conn.close()
