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

        start_date = request.GET.get('start_date') or None
        final_date = request.GET.get('final_date') or None
        fornecedores_selecionados = request.GET.getlist('fornecedor')

        
        df_raw = cp_em_abertos(
            start_date=start_date,
            final_date=final_date,
            fornecedores=fornecedores_selecionados
        ).rename({
            'Razao_Social': 'Fornecedor',
            'Num_Docto': 'Nº Documento',
            'Parcelas': 'Nº Parcelas',
            'Emissao': 'Data de Emissão',
            'Vencto': 'Data de Vencimento',
            'Valor_em_Aberto': 'Valor a Pagar (R$)',
            'Cod_Custo': 'Regra de Distribuição',
            'Modalidade': 'Pgto',
            'BPLName': 'Filial',
            'Observacoes': 'Observações',
        })
        

        df_raw = df_raw.with_columns(
    pl.when(pl.col("Regra de Distribuição") == "Centr_z").then(pl.lit("Centro de custos geral"))
      .when(pl.col("Regra de Distribuição") == "1").then(pl.lit("ADMINISTRATIVO"))
      .when(pl.col("Regra de Distribuição") == "2").then(pl.lit("AGRICULTURA"))
      .when(pl.col("Regra de Distribuição") == "3").then(pl.lit("PECUÁRIA"))
      .when(pl.col("Regra de Distribuição") == "4").then(pl.lit("CONSTRUÇÃO CIVIL"))
      .when(pl.col("Regra de Distribuição") == "5").then(pl.lit("SILO"))
      .when(pl.col("Regra de Distribuição") == "6").then(pl.lit("MANUTENÇÃO"))
      .when(pl.col("Regra de Distribuição") == "7").then(pl.lit("ARRENDAMENTOS"))
      .when(pl.col("Regra de Distribuição") == "8").then(pl.lit("FUNCIONARIOS"))
      .when(pl.col("Regra de Distribuição") == "9").then(pl.lit("FINANCEIRO"))
      .when(pl.col("Regra de Distribuição") == "10").then(pl.lit("COMBUSTÍVEIS"))
      .when(pl.col("Regra de Distribuição") == "11").then(pl.lit("COMPRA DE ATIVO"))
      .when(pl.col("Regra de Distribuição") == "12").then(pl.lit("ENERGIA ELETRICA"))
      .when(pl.col("Regra de Distribuição") == "13").then(pl.lit("INSUMOS"))
      .when(pl.col("Regra de Distribuição") == "14").then(pl.lit("SEGUROS"))
      .when(pl.col("Regra de Distribuição") == "15").then(pl.lit("INVESTIMENTOS"))
      .when(pl.col("Regra de Distribuição") == "16").then(pl.lit("FINANCEIRO"))
      .when(pl.col("Regra de Distribuição") == "0").then(pl.lit("NÃO DEFINIDO"))
      
      .otherwise(pl.col("Regra de Distribuição")).cast(pl.String) # Mantém o código original se não for encontrado
      .alias("Centro de Custo") # Cria/substitui por uma coluna com nome claro
)

# 3. Aplicar o mapa para traduzir a modalidade
        df_raw = df_raw.with_columns(
    pl.when(pl.col("Pgto") == 0).then(pl.lit("Não Definido"))
      .when(pl.col("Pgto") == 1).then(pl.lit("TED"))
      .when(pl.col("Pgto") == 2).then(pl.lit("Cartão de Crédito"))
      .when(pl.col("Pgto") == 3).then(pl.lit("Pix"))
      .when(pl.col("Pgto") == 4).then(pl.lit("Dinheiro"))
      .when(pl.col("Pgto") == 5).then(pl.lit("Débito em Conta"))
      .when(pl.col("Pgto") == 6).then(pl.lit("Transferência Entre Contas"))
      .when(pl.col("Pgto") == 7).then(pl.lit("Boleto"))
      .when(pl.col("Pgto") == 8).then(pl.lit("Barter"))
      .otherwise(pl.col("Pgto"))  
      .alias("Pgto")
)
        df_abertos = df_raw.select([
            pl.col('Fornecedor'),
            pl.col('Data de Vencimento'),
            pl.col('Valor a Pagar (R$)').cast(pl.Decimal(15, 2), strict=False),
            pl.lit(0).alias('Receita'),
            pl.col('Nº Documento'),
            pl.col('Nº Parcelas'),
            pl.col('Data de Emissão'),
            pl.col('Centro de Custo'),
            pl.col('Pgto'),
            pl.col('Filial'),
            pl.col('Observações')
        ]).sort('Data de Vencimento')

        # 3. Limpar valores NaN/Inf que podem ter surgido
        df_abertos = df_abertos.with_columns([
        pl.col(col_name).fill_nan(0).fill_infinite(0)
        for col_name, dtype in df_abertos.schema.items()
        if dtype in (pl.Float32, pl.Float64)
])
        
        if df_abertos.is_empty():
            return HttpResponse("Nenhum dado encontrado para os filtros selecionados.", status=404)

        # 4. Converter para Pandas para a escrita manual com xlsxwriter
        df_pandas = df_abertos.to_pandas()

        # 5. Configurar o ficheiro Excel em memória
        output_buffer = io.BytesIO()
        workbook = xlsxwriter.Workbook(output_buffer, {'in_memory': True, 'default_date_format': 'dd/mm/yyyy', "nan_inf_to_errors": True})
        worksheet = workbook.add_worksheet('Contas em Aberto')


        # 6. Definir formatos
        header_format = workbook.add_format({
            'bold': True, 'valign': 'top', 'fg_color': '#D0D0D0', 'border': 1
        })
        currency_format = workbook.add_format({'num_format': 'R$ #,##0.00'})
        date_format = workbook.add_format({'num_format': 'dd/mm/yyyy'})
        default_format = workbook.add_format({'border': 1})

        # 7. Escrever o cabeçalho
        for col_num, col_name in enumerate(df_pandas.columns):
            worksheet.write(0, col_num, col_name, header_format)

        for row_idx, row in enumerate(df_pandas.itertuples(index=False), start=1):
            for col_idx, value in enumerate(row):
                if isinstance(value, (int, float)) and df_pandas.columns[col_idx] == 'Valor Aberto (R$)':
                    worksheet.write_number(row_idx, col_idx, value, currency_format)
                else:
                    worksheet.write(row_idx, col_idx, value, default_format)

        worksheet.set_column('A:A', 45)  # Fornecedor
        worksheet.set_column('B:B', 15)  # Data de Vencimento
        worksheet.set_column('C:C', 18)  # Valor a Pagar (R$)
        worksheet.set_column('D:D', 10)  # Receita
        worksheet.set_column('E:E', 15)  # Nº Documento
        worksheet.set_column('F:F', 10)  # Nº Parcelas
        worksheet.set_column('G:G', 15)  # Data de Emissão
        worksheet.set_column('H:H', 25)  # Pgto
        worksheet.set_column('I:I', 35)  # Filial
        worksheet.set_column('J:J', 40)  # Observações
        worksheet.set_column('K:K', 40)  # Regra de Distribuição

        worksheet.freeze_panes(1, 0) # Congela a primeira linha
        workbook.close()
        output_buffer.seek(0)

        # 10. Retornar a resposta HTTP com o ficheiro
        filename = f"Relatorio_Contas_Aberto_{timezone.now().strftime('%Y-%m-%d')}.xlsx"
        response = HttpResponse(
            output_buffer.read(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response

    except Exception as e:
        # É uma boa prática logar o erro completo no servidor para depuração
        print(f"Erro detalhado ao gerar XLSX: {e}")
        return HttpResponse(f"Ocorreu um erro ao gerar o arquivo. Por favor, contacte o suporte.", status=500)



@login_required
def dashboard_financeiro_view(request):
    return render(request, 'fluxo_caixa/financeiro.html')
