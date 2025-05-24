# scripts/carregar_perguntas_feedback.py
import sqlite3

PERGUNTAS = [
    "Sinto que meu trabalho é reconhecido pela equipe.",
    "Tenho os recursos necessários para desempenhar bem minhas funções.",
    "O ambiente de trabalho é acolhedor e respeitoso.",
    "Recebo feedbacks construtivos com regularidade.",
    "Consigo manter um bom equilíbrio entre vida pessoal e profissional.",
    "Sinto-me motivado para realizar minhas atividades diárias.",
    "A liderança da equipe está presente e acessível.",
    "Percebo oportunidades de crescimento profissional aqui.",
    "As metas da equipe são claras e alcançáveis.",
    "Recomendaria esta organização como um bom lugar para trabalhar."
]

OPCOES = [
    "a) Concordo totalmente",
    "b) Concordo parcialmente",
    "c) Neutro",
    "d) Discordo parcialmente",
    "e) Discordo totalmente"
]

def carregar_perguntas():
    conn = sqlite3.connect("database/banco.db")
    cursor = conn.cursor()

    for texto in PERGUNTAS:
        cursor.execute("INSERT INTO perguntas (texto) VALUES (?)", (texto,))
        pergunta_id = cursor.lastrowid
        for opcao in OPCOES:
            cursor.execute("INSERT INTO opcoes_resposta (pergunta_id, texto) VALUES (?, ?)", (pergunta_id, opcao))

    conn.commit()
    conn.close()
    print("Perguntas e opções carregadas com sucesso.")

if __name__ == "__main__":
    carregar_perguntas()
