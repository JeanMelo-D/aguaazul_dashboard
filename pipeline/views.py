# fluxo_caixa/views.py
import io
from django.http import JsonResponse, HttpRequest, HttpResponse
from django.contrib.auth.decorators import login_required
from polars.exceptions import ColumnNotFoundError
from django.shortcuts import render
from django.utils import timezone
from datetime import datetime
import xlsxwriter
from django.core.paginator import Paginator
import polars as pl
from .financeiro_pipe import (
    timeline_financeiro_v2_eficiente,
    financeiro_kpis,
    abertos_setup_lazy,
    pagos_setup_lazy,
    contas_setup_lazy,
    recebidos_setup_lazy,
    a_receber_setup_lazy,
    get_fluxo_caixa,
    cp_em_abertos,
    azul_fornecedores_lazy,
    
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

def contas_em_aberto_api(request):
    if request.method != 'GET':
        return JsonResponse({'error': 'Método não permitido'}, status=405)

    try:
        start_date = request.GET.get('start_date', None)
        final_date = request.GET.get('final_date', None)
        
        fornecedores_selecionados = request.GET.getlist('fornecedor')

        df = cp_em_abertos(
            start_date=start_date,
            final_date=final_date,
            fornecedores=fornecedores_selecionados
        )
        
        payload_list = df.drop('Vencimento').to_dicts()
        page_number = request.GET.get('page', 1)
        paginator = Paginator(payload_list, 50)
        page_obj = paginator.get_page(page_number)
        
        response_payload = {
            'count': paginator.count,
            'num_pages': paginator.num_pages,
            'current_page': page_obj.number,
            'results': page_obj.object_list
        }
        
        # O seu uso de safe=False está correto aqui, pois o payload é um dicionário.
        return JsonResponse(response_payload)

    except Exception as e:
        return JsonResponse({'error': f'Ocorreu um erro inesperado: {e}'}, status=500)
    
def api_fornecedores_view(request):
    try:
        termo_busca = request.GET.get('term', '').strip()
        
        # [CORREÇÃO] Usar a função correta para buscar todos os fornecedores
        df = azul_fornecedores_lazy().collect()
        
        fornecedores = df.get_column("Razao_Social").unique(maintain_order=True)

        if termo_busca:
            fornecedores_filtrados = fornecedores.filter(
                fornecedores.str.contains(f"(?i){termo_busca}")
            )
        else:
            fornecedores_filtrados = fornecedores

        return JsonResponse({"fornecedores": fornecedores_filtrados.to_list()[:20]})
    except Exception as e:
        return JsonResponse({'error': f'Erro ao buscar fornecedores: {e}'}, status=500)
    
    
def download_contas_em_aberto_xlsx(request: HttpRequest):

    try:
        # --- Coleta os filtros da URL ---
        start_date = request.GET.get('start_date') or ''
        final_date = request.GET.get('final_date') or ''
        fornecedores_selecionados = request.GET.getlist('fornecedor')

        # --- Carrega os dados (Polars Lazy ou Eager) ---
        df_abertos = cp_em_abertos(
            start_date=start_date,
            final_date=final_date,
            fornecedores=fornecedores_selecionados
        ).rename({
            'Razao_Social': 'Fornecedor',
            'Valor_em_Aberto': 'Valor Aberto (R$)',
            'Num_Docto': 'Nº Documento',
            'Tipo_Docto': 'Tipo',
            'BPLName': 'Filial'
        })

        if df_abertos.is_empty():
            return HttpResponse("Nenhum dado encontrado para os filtros selecionados.", status=404)

        # --- Converte para pandas para exportar com formatação ---
        df_pandas = df_abertos.to_pandas()

        output_buffer = io.BytesIO()
        workbook = xlsxwriter.Workbook(output_buffer, {'in_memory': True})
        worksheet = workbook.add_worksheet('Contas em Aberto')

        # --- Estilos ---
        header_format = workbook.add_format({
            'bold': True, 'text_wrap': True, 'valign': 'top',
            'fg_color': '#33CCF5', 'border': 1
        })
        currency_format = workbook.add_format({'num_format': 'R$ #,##0.00'})
        date_format = workbook.add_format({'num_format': 'dd/mm/yyyy'})
        default_format = workbook.add_format({'border': 1})

        # --- Escreve cabeçalhos ---
        for col_num, col_name in enumerate(df_pandas.columns):
            worksheet.write(0, col_num, col_name, header_format)

        # --- Escreve dados linha a linha ---
        for row_idx, row in enumerate(df_pandas.itertuples(index=False), start=1):
            for col_idx, value in enumerate(row):
                if isinstance(value, (int, float)) and df_pandas.columns[col_idx] == 'Valor Aberto (R$)':
                    worksheet.write_number(row_idx, col_idx, value, currency_format)
                else:
                    worksheet.write(row_idx, col_idx, value, default_format)

        # --- Ajusta colunas ---
        worksheet.set_column('A:A', 40)  # Fornecedor
        worksheet.set_column('B:B', 18, currency_format)  # Valor Aberto
        worksheet.set_column('C:C', 15)  # Nº Documento
        worksheet.set_column('D:D', 8)   # Tipo
        worksheet.set_column('E:E', 25)  # Filial
        # Se tiver coluna de data, ajuste com date_format, exemplo:
        # worksheet.set_column('F:F', 15, date_format)

        worksheet.freeze_panes(1, 0)

        # --- Finaliza ---
        workbook.close()
        output_buffer.seek(0)

        filename = f"Relatorio_Contas_Aberto_{timezone.now().strftime('%Y-%m-%d')}.xlsx"
        response = HttpResponse(
            output_buffer.read(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response

    except Exception as e:
        print(f"Erro ao gerar XLSX: {e}")
        return HttpResponse(f"Ocorreu um erro ao gerar o arquivo: {e}", status=500)


@login_required
def dashboard_financeiro_view(request):
    return render(request, 'fluxo_caixa/financeiro.html')