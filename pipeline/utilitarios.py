from datetime import datetime, date, timedelta
import calendar
from django.urls import path

def date_func(dt_obj: datetime, formato: str = "relativo") -> str:
    if not isinstance(dt_obj, datetime):
        raise TypeError("O primeiro argumento deve ser um objeto datetime.")
    meses_pt = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho","Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]
    meses_pt_abr = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"]
    dias_semana_pt = ["Segunda-feira", "Terça-feira", "Quarta-feira", "Quinta-feira", "Sexta-feira", "Sábado", "Domingo"]
    dias_semana_pt_abr = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"]
    agora = datetime.now()
    if formato.lower() == "relativo":
        delta = agora - dt_obj
        segundos_atras = delta.total_seconds()
        if segundos_atras < 0:
            delta = dt_obj - agora
            segundos_frente = delta.total_seconds()
            dias_frente = delta.days
            if dt_obj.date() == agora.date():
                return f"hoje às {dt_obj.strftime('%H:%M')}"
            if dt_obj.date() == (agora + timedelta(days=1)).date():
                return f"amanhã às {dt_obj.strftime('%H:%M')}"
            if dias_frente < 7:
                return f"daqui a {dias_frente} dias"
            return f"em {dt_obj.strftime('%d/%m/%Y')}"
        if dt_obj.date() == agora.date():
            if segundos_atras < 60:
                return "agora mesmo"
            if segundos_atras < 3600:
                minutos = int(segundos_atras / 60)
                return f"há {minutos} minuto{'s' if minutos > 1 else ''}"
            return f"hoje às {dt_obj.strftime('%H:%M')}"
        if dt_obj.date() == (agora - timedelta(days=1)).date():
            return f"ontem às {dt_obj.strftime('%H:%M')}"
        if segundos_atras < 604800:
            dias = delta.days
            return f"há {dias} dia{'s' if dias > 1 else ''}"
        return f"em {dt_obj.strftime('%d/%m/%Y')}"
    else:
        substituicoes = {"AAAA": str(dt_obj.year),"AA": dt_obj.strftime("%y"),"MM": dt_obj.strftime("%m"),"M": str(dt_obj.month),"B": meses_pt[dt_obj.month - 1],"b": meses_pt_abr[dt_obj.month - 1],"DD": dt_obj.strftime("%d"),"D": str(dt_obj.day),"A": dias_semana_pt[dt_obj.weekday()],"a": dias_semana_pt_abr[dt_obj.weekday()],"HH": dt_obj.strftime("%H"),"mm": dt_obj.strftime("%M"),"ss": dt_obj.strftime("%S"),}
        resultado = formato
        for codigo, valor in substituicoes.items():
            resultado = resultado.replace(codigo, valor)
        return resultado

def pdt(dt_obj: datetime) -> str:
    return date_func(dt_obj, "DD/MM/AAAA")


from datetime import date, datetime, timedelta
import polars as pl

def fluxodatas (data_para_checar: date) -> pl.DataFrame:

    dia = data_para_checar.day
    mes = date_func(data_para_checar, 'b')
    ano = data_para_checar.year

    if 11 <= dia <= 20:
        return {
            "periodo": "1st_Período",
            "Mes_ref": mes,
            "ano_ref": ano
        }

    # Caso 2: A data está entre o dia 21 e o fim do mês.
    # Pertence ao início do "Segundo Período" do mês da própria data.
    elif dia >= 21:
        return {
            "periodo": "Segundo Período",
            "Mes_ref": mes,
            "ano_ref": ano
        }
        
    # Caso 3 (o mais complexo): A data está entre o dia 1 e 10.
    # Pertence ao final do "Segundo Período" que começou no MÊS ANTERIOR.
    elif 1 <= dia <= 10:
        # Precisamos calcular qual era o mês/ano anterior
        data_mes_anterior = data_para_checar - timedelta(days=dia + 1) # Forma segura de voltar para o mês anterior
        
        return {
            "periodo": "Segundo Período",
            "Mes_ref": data_mes_anterior.month,
            "ano_ref": data_mes_anterior.year
        }


def dates(mes_alvo: int) -> pl.DataFrame:
    
    if not 1 <= mes_alvo <= 12:
        raise ValueError("O mês deve ser um número entre 1 e 12.")

    hoje = date.today()
    ano_alvo = hoje.year

    if mes_alvo < hoje.month:

        ano_alvo = hoje.year 
    
    data_inicio = date(ano_alvo, mes_alvo, 1)

    _, ultimo_dia = calendar.monthrange(ano_alvo, mes_alvo)
    data_fim = date(ano_alvo, mes_alvo, ultimo_dia)

 
    return {
        "data_inicio": data_inicio,
        "data_fim": data_fim
    }