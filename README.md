# Chatbot de Agendamento Filantrópico

Este é um bot desenvolvido para Telegram, com foco em agendamentos filantrópicos, orientações de bem-estar, meditação e mensagens motivacionais. Ele utiliza Python 3.9+, SQLite e a API do Google Calendar.

## Funcionalidades
- Tela inicial com Termo LGPD e consentimento do usuário.
- Menu interativo com:
  - Agendamento de atendimento
  - Consulta e cancelamento de agendamento
  - Feedback
  - Categorias dinâmicas (como Meditação, Emoções, Paz Interior etc.) com perguntas/respostas
- Envio de e-mail com arquivo `.ics` para confirmação de agendamento.
- Integração com Google Calendar para checar disponibilidade.

## Requisitos
- Python 3.9+
- Conta do Google com agenda criada
- Conta de e-mail habilitada para SMTP (como Gmail com senha de aplicativo)
- Token do Telegram Bot

## Instalação

```bash
# Clonar o repositório
git clone https://github.com/fchnet/csomn.git
cd csomn

# Criar ambiente virtual
python -m venv venv
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate   # Windows

# Instalar dependências
pip install -r requirements.txt
```

## Configuração

1. Crie um arquivo `.env` com base no `.env.example`:

```bash
cp .env.example .env  # Linux/macOS
copy .env.example .env  # Windows
```

2. Edite o arquivo `.env` com os seus dados:

```
TELEGRAM_TOKEN=seu_token_do_bot
GOOGLE_CALENDAR_ID=id_da_sua_agenda_google
EMAIL_USER=seu_email@gmail.com
EMAIL_PASSWORD=sua_senha_de_aplicativo
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
IMAGE_PATH=image/maria_de_nazare.png
START_HOUR=8
END_HOUR=17
APPOINTMENT_DURATION_MINUTES=60
MAX_CONCURRENT_APPOINTMENTS=5
MAX_APPOINTMENTS_PER_DAY=90
```

3. Adicione o arquivo `service_account.json` gerado na conta de serviço da sua agenda do Google, dentro da pasta `json/`.

## Execução

```bash
python main.py
```

## Banco de Dados
O banco `banco.db` será criado e populado automaticamente com os dados iniciais.

## Estrutura de Pastas

```
chatbot_agendamento/
├── database/           # Contém banco SQLite
├── json/               # Arquivos auxiliares (service_account.json)
├── image/              # Imagens utilizadas
├── modules/            # Módulos do bot (agendamento, feedback, etc.)
├── utils/              # Funções auxiliares
├── data/               # JSON com intents e respostas
├── main.py             # Arquivo principal do bot
├── requirements.txt    # Dependências do projeto
└── .env                # Configuração (não versionar)
```

## Licença
Este projeto é livre para fins filantrópicos e não pode ser utilizado para fins comerciais sem autorização.

---
Desenvolvido com carinho para ajudar quem mais precisa. ✨

