import polars as pl
from datetime import datetime, timedelta, date
from decimal import Decimal
from .utilitarios import date_func
from .azure_financial import azul_contas_bancarias, azul_doc_a_pagar, azul_doc_pagos, azul_doc_recebidos, azul_doc_a_receber, azul_doc_partner
import calendar
import locale


# Constantes
DECIMAL_15_2 = pl.Decimal(15, 2)
ZERO_DECIMAL = pl.lit("0.00").cast(DECIMAL_15_2)



def azul_fornecedores_lazy() -> pl.LazyFrame:
    azul_df_partner =azul_doc_partner().lazy()
    return azul_df_partner

def a_receber_setup_lazy() -> pl.LazyFrame:
    # A variável aqui dentro deve ser local, usando a_receber do escopo global.
    df_a_receber = azul_doc_a_receber().lazy() 
    return df_a_receber.select([
        pl.col("Codigo_PN").cast(pl.String),
        pl.col("Razao_Social").cast(pl.String),
        pl.col("Num_Docto").cast(pl.String),
        pl.col("Parcela").cast(pl.Int32),
        pl.col("Tipo_Docto").cast(pl.String),
        pl.col("DocEntry").cast(pl.Int64),
        pl.col("Doc_Origem").cast(pl.String),
        pl.col("Emissao").cast(pl.Date),
        pl.col("Vencimento").cast(pl.Date),
        pl.col("Valor_Original").cast(DECIMAL_15_2),
        pl.col("Valor_Aberto").cast(DECIMAL_15_2),
        pl.col("Forma_Pagamento").cast(pl.String),
        pl.col("Status").cast(pl.String),
        pl.col("BPLId").cast(pl.String),
        pl.col("BPLName").cast(pl.String),
        pl.col("Obs").cast(pl.String),
        pl.col("TaxId0").cast(pl.String),
        pl.col("Conta_Contabil").cast(pl.String),
        pl.col("Valor_Multa").cast(DECIMAL_15_2),
        pl.col("Valor_Juros").cast(DECIMAL_15_2),
        pl.col("Total_Previsto").cast(DECIMAL_15_2)
    ])

def recebidos_setup_lazy() -> pl.LazyFrame:
    recebidos = azul_doc_recebidos().lazy()
    return recebidos.select([
        pl.col("Codigo_PN").cast(pl.String),
        pl.col("Razao_Social").cast(pl.String),
        pl.col("Num_Docto").cast(pl.String), # Alterado para String para consistência
        pl.col("Prest").cast(pl.String),
        pl.col("Emissao").cast(pl.Date),
        pl.col("Vencimento").cast(pl.Date),
        pl.col("Valor_Original").cast(DECIMAL_15_2),  
        pl.col("Docto_Origem").cast(pl.String),
        pl.col("Tipo_Docto").cast(pl.String),        
        pl.col("Desconto").cast(DECIMAL_15_2),
        pl.col("Juros").cast(DECIMAL_15_2),
        pl.col("Banco_Recebedor").cast(pl.String),
        pl.col("TaxId0").cast(pl.String),
        pl.col("Valor_Recebido").cast(DECIMAL_15_2),
        pl.col("Data_Recebimento").cast(pl.Date),
        pl.col("Dias_Atraso").cast(pl.Int64),
        pl.col("Docto_Baixa").cast(pl.String),
        pl.col("Num_Boleto").cast(pl.String),
        pl.col("Forma_Receb").cast(pl.String),
        pl.col("BPLId").cast(pl.String),
        pl.col("BPLName").cast(pl.String),
        pl.col("Tipo_Docto2").cast(pl.String),
        pl.col("docentry").cast(pl.String)
    ])

def abertos_setup_lazy() -> pl.LazyFrame:  
    abertos = azul_doc_a_pagar().lazy() 
    return abertos.select([
        pl.col('Codigo_PN').cast(pl.String),
        pl.col('Razao_Social').cast(pl.String),
        pl.col('ID_Fiscal').cast(pl.String),
        pl.col('Num_Docto').cast(pl.Int64),
        pl.col('Parcela').cast(pl.Int32),
        pl.col('Total_Parcelas').cast(pl.Int32),
        pl.col('Tipo_Docto').cast(pl.String),
        pl.col('DocEntry_Lancamento').cast(pl.Int64),
        pl.col('Emissao').cast(pl.Date),
        pl.col('Vencimento').cast(pl.Date),
        pl.col('Valor_Original').cast(DECIMAL_15_2),
        pl.col('Valor_Pago').cast(DECIMAL_15_2),
        pl.col('Valor_em_Aberto').cast(DECIMAL_15_2),
        pl.col('Status').cast(pl.String),
        pl.col('Dias_Atraso').cast(pl.Int32),
        pl.col('Observacoes').cast(pl.String),
        pl.col('BPLId').cast(pl.Int64),
        pl.col('BPLName').cast(pl.String),
        pl.col('Cod_Custo').cast(pl.Int64),

    ])

def pagos_setup_lazy() -> pl.LazyFrame:
    pagos = azul_doc_pagos().lazy()
    return pagos.select([
        pl.col('Tipo_Documento_Origem').cast(pl.String),
        pl.col('Codigo_PN').cast(pl.String),
        pl.col('Razao_Social').cast(pl.String),
        pl.col('ID_Fiscal').cast(pl.String),
        pl.col('Num_Docto').cast(pl.String),
        pl.col('Prest').cast(pl.Int64),
        pl.col('Parcelas').cast(pl.Int64),
        pl.col('Docto_Origem').cast(pl.Int64),
        pl.col('Tipo_Docto').cast(pl.String),
        pl.col('Emissao_NF').cast(pl.Date),
        pl.col('Vencimento').cast(pl.Date),
        pl.col('Valor_Original').cast(DECIMAL_15_2),
        pl.col('Valor_Pago').cast(DECIMAL_15_2),
        pl.when(pl.col('Data_Pagamento').is_null())
            .then(pl.col('Emissao_NF'))
            .otherwise(pl.col('Data_Pagamento'))
            .alias('Data_Pagamento').cast(pl.Date),
        pl.col('Dias_Atraso').cast(pl.Int64),
        pl.col('Docto_Baixa').cast(pl.String).alias('Docto_Baixa'),
        pl.col('Num_Boleto'),
        pl.col('Forma_Pagto').cast(pl.String),
        pl.col('BPLId').cast(pl.Int64),
        pl.col('BPLName').cast(pl.String),
        pl.col('Observacoes').cast(pl.String),
        pl.col('PrimaryKey').cast(pl.Int64),
        pl.col('U_CenterCoast').cast(pl.String),
        pl.col('U_IV_IB_CentroDeCusto1').cast(pl.String),
        pl.col('PrcCode').cast(pl.String),
        pl.col('Centro_Custo').cast(pl.String),
    ])

def contas_setup_lazy() -> pl.LazyFrame:
    contas = azul_contas_bancarias().lazy()
    return contas.select([
        pl.col('DocNum').cast(pl.String).alias('Docto_Baixa'),
        pl.col('DataPagamento'),
        pl.col('Pagamento_DocEntry').cast(pl.Int64),
        pl.col('CashAcct').cast(pl.String),
        pl.col('CheckAcct').cast(pl.String),
        pl.col('TrsfrAcct').cast(pl.String),
        pl.col('DocCurr').cast(pl.String),
        pl.col('DocTotal').cast(DECIMAL_15_2),
        pl.col('CreditAcct').cast(pl.String),
        pl.col('Caixa').cast(pl.String),
        pl.col('Transferencias').cast(pl.String),
        pl.col('Credito').cast(pl.String),
        pl.col('CodConta').cast(pl.String),
        pl.col('NomeConta').cast(pl.String),
        pl.col('Finanse').cast(pl.String),
        pl.col('Details').cast(pl.String),
        pl.col('U_IB_ItemFluxo').cast(pl.String),
        pl.col('CashBox').cast(pl.String),
    ])

def cp_em_abertos(
    start_date: str = None,
    final_date: str = None,
    fornecedores: list = None,  # 1. Alterado de 'fornecedor: str' para 'fornecedores: list'
) -> pl.DataFrame:              # 2. Alterado o tipo de retorno para DataFrame, pois .collect() é usado
    
    meses_pt = {
        1: "Janeiro", 2: "Fevereiro", 3: "Março", 4: "Abril",
        5: "Maio", 6: "Junho", 7: "Julho", 8: "Agosto",
        9: "Setembro", 10: "Outubro", 11: "Novembro", 12: "Dezembro"
    }
    
    df = azul_doc_a_pagar().lazy()
    
    # 3. A lógica de filtro agora usa a lista 'fornecedores' e o método .is_in()
    if fornecedores: 
        df = df.filter(
            pl.col("Razao_Social").is_in(fornecedores)
        )
        
    if start_date:
        dt_inicial = datetime.strptime(start_date, "%Y-%m-%d")
        df = df.filter(pl.col('Vencimento') >= dt_inicial)

    if final_date:
        dt_final = datetime.strptime(final_date, "%Y-%m-%d")
        df = df.filter(pl.col('Vencimento') <= dt_final)

    df = df.select(
        pl.col('Vencimento').dt.strftime("%d/%m/%Y").alias('Vencto'),
        pl.col('Vencimento').dt.month().cast(pl.String).replace(meses_pt).alias('Mes'),
        pl.col('Vencimento').dt.year().cast(pl.String).alias('Ano'),
        pl.col('Razao_Social').cast(pl.String),
        pl.col('Tipo_Docto').cast(pl.String),
        pl.col('Num_Docto'),
        pl.col('Emissao').dt.strftime("%d/%m/%Y").alias('Emissao'),
        pl.concat_str(
            [pl.col('Parcela').cast(pl.String), pl.col('Total_Parcelas').cast(pl.String)],
            separator="/"
        ).alias('Parcelas'),
        pl.col('Valor_em_Aberto').cast(DECIMAL_15_2),
        pl.col('Observacoes'),
        pl.col('BPLName'),
        pl.col('Vencimento'), 
    )
    df = df.sort('Vencimento')
   
    return df.collect()

def timeline_financeiro_v2_eficiente(
    lazy_abertos: pl.LazyFrame,
    lazy_pagos: pl.LazyFrame,
    lazy_contas: pl.LazyFrame,
    lazy_recebidos: pl.LazyFrame,
    lazy_a_receber: pl.LazyFrame, 
    startdate: str = None,
    finaldate: str = None,
    granularity: str = 'month'
) -> pl.LazyFrame:

    lazy_pagos = lazy_pagos.join(lazy_contas, on='Docto_Baixa', how='left')
    
    lazy_pagos = lazy_pagos
    decimal_type = pl.Decimal(15, 2)

    # Prepara Saídas Futuras
    abertos_prep = lazy_abertos.select(
        pl.col("Vencimento").alias("Data"),
        pl.col("Valor_em_Aberto"),
        pl.lit(0).cast(decimal_type).alias("Valor_Pago"),
        pl.lit(0).cast(decimal_type).alias("Valor_Recebido"),
        pl.lit(0).cast(decimal_type).alias("Valor_A_Receber") # <-- Coluna zerada
    )

    # Prepara Saídas Realizadas
    pagos_prep = lazy_pagos.select(
        pl.col("Data_Pagamento").alias("Data"),
        pl.lit(0).cast(decimal_type).alias("Valor_em_Aberto"),
        pl.col("Valor_Pago"),
        pl.lit(0).cast(decimal_type).alias("Valor_Recebido"),
        pl.lit(0).cast(decimal_type).alias("Valor_A_Receber") 
    )

    # Prepara Entradas Realizadas
    recebidos_prep = lazy_recebidos.select(
        pl.col("Data_Recebimento").alias("Data"),
        pl.lit(0).cast(decimal_type).alias("Valor_em_Aberto"),
        pl.lit(0).cast(decimal_type).alias("Valor_Pago"),
        pl.col("Valor_Recebido"),
        pl.lit(0).cast(decimal_type).alias("Valor_A_Receber") # <-- Coluna zerada
    )
    
    # --- NOVO BLOCO PARA ENTRADAS FUTURAS ---
    a_receber_prep = lazy_a_receber.select(
        pl.col("Vencimento").alias("Data"),
        pl.lit(0).cast(decimal_type).alias("Valor_em_Aberto"),
        pl.lit(0).cast(decimal_type).alias("Valor_Pago"),
        pl.lit(0).cast(decimal_type).alias("Valor_Recebido"),
        pl.col("Total_Previsto").alias("Valor_A_Receber") # <-- 2. Usamos o valor real aqui
    )

    timeline_lazy = pl.concat([
        abertos_prep,
        pagos_prep,
        recebidos_prep,
        a_receber_prep # <-- 3. Adicionado à concatenação
    ])

    granularity_map = {
        'day': '1d', 'week': '1w', 'month': '1mo', 'year': '1y'
    }
    polars_granularity = granularity_map.get(granularity, '1mo')

    report_lazy = timeline_lazy.group_by(
        pl.col("Data").dt.truncate(every=polars_granularity).alias("Periodo")
    ).agg([
        pl.sum("Valor_Pago").alias("Total_Pago_Periodo"),
        pl.sum("Valor_em_Aberto").alias("Total_Aberto_Periodo"),
        pl.sum("Valor_Recebido").alias("Total_Recebido_Periodo"),
        pl.sum("Valor_A_Receber").alias("Total_A_Receber_Periodo") # <-- 4. Adicionada agregação
    ]).sort("Periodo")

    # Filtros de data permanecem os mesmos
    if startdate:
        start_date_lit = pl.lit(startdate).cast(pl.Date).dt.truncate(every=polars_granularity)
        report_lazy = report_lazy.filter(pl.col('Periodo') >= start_date_lit)
    if finaldate:
        final_date_lit = pl.lit(finaldate).cast(pl.Date).dt.truncate(every=polars_granularity)
        report_lazy = report_lazy.filter(pl.col('Periodo') <= final_date_lit)

    return report_lazy

def _get_periodos_meses_futuros(num_meses: int) -> list:

    data_base = date.today()
    meses_futuros = []
    
    mes_atual = data_base.month
    ano_atual = data_base.year

    for i in range(1, num_meses + 1):
        mes_calculado = mes_atual + i
        ano_calculado = ano_atual
        if mes_calculado > 12:
            ano_calculado += (mes_calculado - 1) // 12
            mes_calculado = (mes_calculado - 1) % 12 + 1
            
        data_inicio = date(ano_calculado, mes_calculado, 1)
        _, ultimo_dia = calendar.monthrange(ano_calculado, mes_calculado)
        data_fim = date(ano_calculado, mes_calculado, ultimo_dia)
        
        meses_futuros.append({"inicio": data_inicio, "fim": data_fim})
        
    return meses_futuros

def _formatar_moeda_brl(valor: float | Decimal | None) -> str:
    if valor is None or not isinstance(valor, (int, float, Decimal)):
        return "0,00"
    
    s = "{:,.2f}".format(valor)
    s = s.replace(",", "X").replace(".", ",").replace("X", ".")
    return s

def financeiro_kpis(lazy_abertos: pl.LazyFrame) -> dict:
    periodos = _get_periodos_meses_futuros(num_meses=6)
    
    if not periodos:
        return {} # Retorna vazio se não houver períodos

    data_inicio_geral = periodos[0]["inicio"]
    data_fim_geral = periodos[-1]["fim"]

    vencimentos_futuros = (
        lazy_abertos
        .filter(pl.col("Vencimento").is_between(data_inicio_geral, data_fim_geral))
        .group_by(pl.col("Vencimento").dt.truncate("1mo").alias("Mes"))
        .agg(pl.sum("Valor_em_Aberto").alias("Total")) 
        .collect()
    )

    kpis = {}
    chaves_kpi = ["next_one", "next_two", "next_three", "next_four", "next_five", "next_six"]
    
    mapa_resultados = {row["Mes"]: row["Total"] for row in vencimentos_futuros.to_dicts()}

    for i, periodo in enumerate(periodos):
        total_mes = mapa_resultados.get(periodo["inicio"], 0.0)
        
        kpis[chaves_kpi[i]] = total_mes

            
    return kpis

def _build_fluxo_caixa_base_lazy() -> pl.LazyFrame:
    pagos_fmt = pagos_setup_lazy().select(
        pl.col("Data_Pagamento").alias("Data"),
        (pl.col("Valor_Pago") * -1).alias("Valor"),
        pl.lit("Pagamentos").alias("Tipo"),
    )
    recebidos_fmt = recebidos_setup_lazy().select(
        pl.col("Data_Recebimento").alias("Data"),
        pl.col("Valor_Recebido").alias("Valor"),
        pl.lit("Recebidos").alias("Tipo"),
    )
    a_pagar_fmt = abertos_setup_lazy().select(
        pl.col("Vencimento").alias("Data"),
        (pl.col("Valor_em_Aberto") * -1).alias("Valor"),
        pl.lit("A Pagar").alias("Tipo"),
    )
    a_receber_fmt = a_receber_setup_lazy().select(
        pl.col("Vencimento").alias("Data"),
        pl.col("Total_Previsto").alias("Valor"),
        pl.lit("A Receber").alias("Tipo"),
    )

    transacoes_lazy = pl.concat([pagos_fmt, recebidos_fmt, a_pagar_fmt, a_receber_fmt])

    return transacoes_lazy

def get_fluxo_caixa(start_date: str = None, final_date: str = None, granularity: str = "month") -> pl.DataFrame:

    try:
        locale.setlocale(locale.LC_TIME, "pt_BR.UTF-8")
    except locale.Error:
        pass

    transacoes_lazy = _build_fluxo_caixa_base_lazy()

    if start_date:
        transacoes_lazy = transacoes_lazy.filter(pl.col("Data") >= pl.lit(start_date).cast(pl.Date))
    if final_date:
        transacoes_lazy = transacoes_lazy.filter(pl.col("Data") <= pl.lit(final_date).cast(pl.Date))

    # Realiza a primeira agregação diária
    daily_summary = (
        transacoes_lazy.group_by("Data")
        .agg(
            # CORREÇÃO APLICADA AQUI: O .sum() vai para o final da expressão
            pl.when(pl.col("Tipo") == "Pagamentos").then(pl.col("Valor")).otherwise(0).sum().alias("Pagamentos"),
            pl.when(pl.col("Tipo") == "A Pagar").then(pl.col("Valor")).otherwise(0).sum().alias("Apagar"),
            pl.when(pl.col("Tipo") == "Recebidos").then(pl.col("Valor")).otherwise(0).sum().alias("Recebidos"),
            pl.when(pl.col("Tipo") == "A Receber").then(pl.col("Valor")).otherwise(0).sum().alias("Areceber"),
        )
        .sort("Data")
        .fill_null(0)
    )

    # O resto da função continua igual
    daily_with_cumsum = daily_summary.with_columns(
        (pl.col("Recebidos") + pl.col("Areceber") + pl.col("Pagamentos") + pl.col("Apagar")).alias("MovimentoDia")
    ).with_columns(
        pl.col("MovimentoDia").cum_sum().alias("SaldoAcumulado")
    )

    if granularity == "day":
        return daily_with_cumsum.with_columns(
            pl.col("Data").dt.strftime("%d/%m/%Y").alias("Periodo")
        ).collect()

    granularity_map = {"week": "1w", "month": "1mo", "year": "1y"}
    date_format_map = {
        "week": "%d/%m/%Y",
        "month": "%b/%Y",
        "year": "%Y",
    }
    
    polars_granularity = granularity_map.get(granularity, "1mo")
    date_format = date_format_map.get(granularity, "%b/%Y")

    aggregated_df = (
        daily_with_cumsum.lazy()
        .group_by_dynamic("Data", every=polars_granularity)
        .agg(
            pl.sum("Recebidos"),
            pl.sum("Areceber"),
            pl.sum("Pagamentos"),
            pl.sum("Apagar"),
            pl.sum("MovimentoDia"),
            pl.col("SaldoAcumulado").last().alias("SaldoFinal"),
        )
        .with_columns(
            pl.col("Data").dt.strftime(date_format).str.to_titlecase().alias("Periodo"),
            pl.col("SaldoFinal").alias("SaldoAcumulado")
        )
        .sort("Data")
    )

    return aggregated_df.collect()