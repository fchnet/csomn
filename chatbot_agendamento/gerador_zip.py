import shutil
import os
import zipfile

# Caminho base do projeto
base_dir = os.getcwd()
pasta_projeto = os.path.join(base_dir, "chatgpt_news_zip")

# Arquivos e pastas para incluir no ZIP
arquivos_para_incluir = [
    ".env",
    "chatbot_unificado.py",
    "menu.py",
    "messages.py",
    "strings.py",
    "requirements.txt",
    os.path.join("data", "messages.json"),
    os.path.join("database", "banco.db"),
    os.path.join("json", "memory.json"),
    os.path.join("json", "service_account.json"),
    os.path.join("image", "maria_de_nazare.png"),
    os.path.join("txt", "conteudo.txt"),
]

# Cria uma pasta temporária para montar a estrutura
if os.path.exists(pasta_projeto):
    shutil.rmtree(pasta_projeto)
os.makedirs(pasta_projeto)

# Copia os arquivos para a pasta temporária mantendo a estrutura
for item in arquivos_para_incluir:
    destino = os.path.join(pasta_projeto, item)
    os.makedirs(os.path.dirname(destino), exist_ok=True)
    shutil.copy(item, destino)

# Cria o arquivo ZIP
zip_path = os.path.join(base_dir, "chatbot_atualizado.zip")
with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
    for root, _, files in os.walk(pasta_projeto):
        for file in files:
            caminho_completo = os.path.join(root, file)
            caminho_relativo = os.path.relpath(caminho_completo, pasta_projeto)
            zipf.write(caminho_completo, caminho_relativo)

print(f"Arquivo ZIP criado com sucesso: {zip_path}")
