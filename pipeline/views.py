# fluxo_caixa/views.py
from django.http import JsonResponse, HttpRequest
from django.shortcuts import render
from datetime import datetime
import polars as pl
from django.contrib.auth.decorators import login_required




# Importe suas funções de lógica/serviços
from .financeiro_pipe import (
    timeline_financeiro_v2_eficiente,
    financeiro_kpis,
    abertos_setup_lazy,
    pagos_setup_lazy,
    contas_setup_lazy,
    recebidos_setup_lazy,
    a_receber_setup_lazy,
    get_fluxo_caixa,
    
    )

lazy_abertos = abertos_setup_lazy()
lazy_pagos = pagos_setup_lazy()
lazy_contas = contas_setup_lazy()
lazy_recebidos = recebidos_setup_lazy() 
lazy_a_receber = a_receber_setup_lazy()




def painel_financeiro_api(request: HttpRequest):
    
    start_date_str = request.GET.get('startdate', None)
    final_date_str = request.GET.get('finaldate', None)
    granularity = request.GET.get('granularity', 'month')

    kpis_dict = financeiro_kpis(lazy_abertos)

    report_lazy = timeline_financeiro_v2_eficiente(
        lazy_abertos=lazy_abertos,
        lazy_pagos=lazy_pagos,
        lazy_contas=lazy_contas,
        lazy_recebidos=lazy_recebidos,  
        lazy_a_receber=lazy_a_receber,
        startdate=start_date_str,
        finaldate=final_date_str,
        granularity=granularity
    )
    report_df = report_lazy.collect()

    timestamps_ms = report_df["Periodo"].dt.timestamp("ms").to_list()
    
    timeline_series = [
        {
            "name": "Pagos",
            "data": list(zip(timestamps_ms, report_df["Total_Pago_Periodo"]))
        },
        {
            "name": "Em Aberto",
            "data": list(zip(timestamps_ms, report_df["Total_Aberto_Periodo"]))
        },
        {
            "name": "A Receber",
            "data": list(zip(timestamps_ms, report_df["Total_A_Receber_Periodo"]))
        },
        {
            "name": "Recebidos",
            "data": list(zip(timestamps_ms, report_df["Total_Recebido_Periodo"]))
        }
    ]
    contexto = {
        "kpis": kpis_dict,
        "timeline_series": timeline_series
    }
    
    return JsonResponse(contexto)

def fluxo_caixa_api_view(request: HttpRequest):
    start_date_str = request.GET.get("startdate")
    final_date_str = request.GET.get("finaldate")
    granularity = request.GET.get("granularity", "month")
    tabela_fluxo = get_fluxo_caixa(
        start_date=start_date_str,
        final_date=final_date_str,
        granularity=granularity,
    )
        
    if tabela_fluxo.is_empty():
        dados_formatados = []
        kpis = {"saldo_final": 0, "total_receitas": 0, "total_despesas": 0}
    else:
        dados_formatados = tabela_fluxo.to_dicts()
        
        total_receitas = tabela_fluxo["Recebidos"].sum() + tabela_fluxo["Areceber"].sum()
        total_despesas = abs(tabela_fluxo["Pagamentos"].sum() + tabela_fluxo["Apagar"].sum())
        
        kpis = {
            "saldo_final": tabela_fluxo["SaldoAcumulado"].last(),
            "total_receitas": total_receitas,
            "total_despesas": total_despesas,
        }
    context = {
        "data": dados_formatados,
        "kpis": kpis,
        "filters_applied": {
            "start_date": start_date_str,
            "final_date": final_date_str,
            "granularity": granularity,
        },
    }
    return JsonResponse(context)


@login_required
def dashboard_financeiro_view(request):
    return render(request, 'fluxo_caixa/financeiro.html')