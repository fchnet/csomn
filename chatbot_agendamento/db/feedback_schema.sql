# db/feedback_schema.sql

-- Tabela de perguntas do feedback
CREATE TABLE IF NOT EXISTS pergunta (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    texto TEXT NOT NULL,
    tipo TEXT CHECK(tipo IN ('likert', 'multipla', 'aberta')) NOT NULL
);

-- Tabela de opções de resposta (apenas para perguntas de múltipla escolha e likert)
CREATE TABLE IF NOT EXISTS opcao (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pergunta_id INTEGER NOT NULL,
    texto TEXT NOT NULL,
    valor INTEGER,
    FOREIGN KEY (pergunta_id) REFERENCES pergunta(id)
);

-- Tabela que representa cada submissão de feedback (sem vincular ao usuário)
CREATE TABLE IF NOT EXISTS feedback (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    data_hora DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Tabela que armazena as respostas por pergunta e por submissão
CREATE TABLE IF NOT EXISTS resposta (
    feedback_id INTEGER NOT NULL,
    pergunta_id INTEGER NOT NULL,
    valor_resposta TEXT NOT NULL,
    PRIMARY KEY (feedback_id, pergunta_id),
    FOREIGN KEY (feedback_id) REFERENCES feedback(id),
    FOREIGN KEY (pergunta_id) REFERENCES pergunta(id)
);
