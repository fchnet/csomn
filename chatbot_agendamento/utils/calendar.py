# utils/calendar.py
import datetime

def gerar_grade_calendario(start_hour, end_hour, duracao_min, max_por_hora, max_por_dia, agendamentos):
    hoje = datetime.date.today()
    dias_disponiveis = []
    for i in range(7):
        dia = hoje + datetime.timedelta(days=i)
        if dia < hoje:
            continue
        dia_str = dia.strftime("%Y-%m-%d")
        agendamentos_dia = agendamentos.get(dia_str, {})
        total_dia = sum(agendamentos_dia.values())
        if total_dia >= max_por_dia:
            continue
        horas_disponiveis = []
        for h in range(start_hour, end_hour):
            slot = f"{h:02d}:00"
            count = agendamentos_dia.get(slot, 0)
            if count < max_por_hora:
                horas_disponiveis.append(slot)
        if horas_disponiveis:
            dias_disponiveis.append((dia_str, horas_disponiveis))
    return dias_disponiveis
