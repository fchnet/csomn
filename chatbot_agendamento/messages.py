# messages.py

LGPD_MESSAGE = """
👋 Olá! Antes de começarmos, é importante que você leia e aceite o termo de consentimento LGPD.

🔐 *Termo de Consentimento*  
Este bot é usado para fins de agendamento filantrópico. Seus dados serão utilizados exclusivamente para essa finalidade e você pode solicitar a exclusão a qualquer momento.

✅ Para continuar, confirme que leu e aceita os termos clicando abaixo.
"""

TERMO_REJEITADO = "❌ Você precisa aceitar os termos para usar o bot."

MENU_INICIAL = "✅ Obrigado! Escolha uma opção:"
CANCELAMENTO_EM_DESENVOLVIMENTO = "❌ Cancelamento em desenvolvimento."
CONSULTA_EM_DESENVOLVIMENTO = "🔎 Consulta de agendamentos em desenvolvimento."
AGENDAMENTO_EM_DESENVOLVIMENTO = "📅 Agendamento em desenvolvimento."
COMO_UTILIZAR = "🛈 Este bot permite agendar, ver ou cancelar atendimentos."

SOLICITAR_NOME = "👤 Por favor, informe seu *nome completo*:"
SOLICITAR_TELEFONE = "📞 Agora, informe seu número de *telefone* com DDD:"
TELEFONE_INVALIDO = "❗ O número informado não parece válido. Tente novamente, por favor."

SELECIONE_DIA = "📆 Escolha um dia disponível para o agendamento:"
SELECIONE_HORARIO = "🕒 Agora selecione um *horário* disponível:"
DIA_INVALIDO = "❗ Dia inválido ou indisponível. Tente outro, por favor."
HORA_INVALIDA = "❗ Horário inválido ou indisponível. Tente outro, por favor."

SOLICITAR_EMAIL = "📧 Por fim, informe seu e-mail para que possamos enviar a confirmação:"
EMAIL_INVALIDO = "❗ O e-mail informado não parece válido. Tente novamente."

CONFIRMACAO_FINAL = "✅ Agendamento registrado com sucesso!\nVocê receberá a confirmação por e-mail."
ERRO_GERAL = "⚠️ Ocorreu um erro. Por favor, tente novamente."

EXCLUIR_DADOS_CONFIRMAR = (
    "⚠️ Você deseja realmente excluir *todos os seus dados* do sistema?\n"
    "Essa ação é *irreversível*. Envie *SIM* para confirmar ou *NÃO* para cancelar."
)
DADOS_EXCLUIDOS = "✅ Seus dados foram removidos com sucesso."
DADOS_NAO_EXCLUIDOS = "❎ Operação cancelada. Seus dados foram mantidos."

TERMO_RESUMIDO_LGPD = (
    "🔐 *Resumo da LGPD*: seus dados serão usados apenas para o agendamento filantrópico.\n"
    "Você pode apagá-los a qualquer momento enviando o comando */apagar_dados*."
)
