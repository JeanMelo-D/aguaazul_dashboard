# pipeline.py
from django.http import JsonResponse
from django.shortcuts import render
from .login import azul_colhido, azul_hectares, azul_romaneios, azul_talhao, azul_travas
import polars as pl

# --- Funções de carregamento de dados (Melhor prática para evitar dados "stale") ---
# ALTERAÇÃO 1: O carregamento dos dados foi movido para dentro das funções lazy.
# Isso garante que você busque os dados mais recentes a cada execução do pipeline.
# Para performance em produção, considere adicionar uma camada de cache aqui.
def aguaazul_colhido_lazy() -> pl.LazyFrame:
    return azul_colhido().lazy().select(
        pl.col('PeriodoProd').cast(pl.String),
        pl.col('CodSetor').cast(pl.String),
        pl.col('CodTalhao').cast(pl.String),
        pl.col('Talhao').cast(pl.String),
        pl.col('HectaresColhidos').cast(pl.Float64).round(2),
    )

def aguaazul_hectares_lazy() -> pl.LazyFrame:
    return azul_hectares().lazy().select(
        pl.col('PeriodoProd').cast(pl.String),
        pl.col('Safra').cast(pl.String),
        pl.col('CodTalhao').cast(pl.String),
        pl.col('Cultura').cast(pl.String),
        pl.col('HectaresPlantado').cast(pl.Float64).round(2),
        pl.col('Replantio').cast(pl.Float64).round(2),
        pl.col('Hectares').cast(pl.Float64).round(2),
    )

def aguaazul_rom_entradas_lazy() -> pl.LazyFrame:
    # ALTERAÇÃO 2: Adicionada a conversão de Peso para Sacas (assumindo 60kg/saca).
    # Este é o ponto crítico que estava faltando.
    return (
        azul_romaneios().lazy()
        .select(
            pl.col('PeriodoProd').cast(pl.String),
            pl.col('CodTalhao').cast(pl.String),
            pl.col('PesoCarga').cast(pl.Float64).round(2),
            pl.col('PesoTara').cast(pl.Float64).round(2),
            pl.col('PesoBruto').cast(pl.Float64).round(2),
            pl.col('PesoLiquido').cast(pl.Float64).round(2),
        )
        .with_columns(
            (pl.col('PesoBruto') - pl.col('PesoLiquido')).cast(pl.Float64).alias("Desconto"),
            (pl.col('PesoBruto') / 60).cast(pl.Float64).round(2).alias("PesoBrutoSacas"),
            (pl.col('PesoLiquido') / 60).cast(pl.Float64).round(2).alias("PesoLiquidoSacas"),
        )
    )

def aguaazul_talhao_lazy() -> pl.LazyFrame:
    return azul_talhao().lazy().select(
        pl.col('CodTalhao').cast(pl.String),
        pl.col('Talhao').cast(pl.String),
        pl.col('CodFazenda').cast(pl.String),
        pl.col('Fazenda').cast(pl.String),
        pl.col('CodSetor').cast(pl.String),
        pl.col('Setor').cast(pl.String),
        pl.col('HectaresTotais').cast(pl.Float64).round(2),
        pl.col('U_CooX').cast(pl.String),
        pl.col('U_CooY').cast(pl.String),
        pl.col('U_CooZ').cast(pl.String),
        pl.col('SVG').cast(pl.String),
    )
    

def aguaazul_travas_lazy() -> pl.LazyFrame:
    """Carrega e prepara os dados brutos de contratos (travas) de forma lazy."""
    return azul_travas().lazy().select(
        pl.col('Code').alias('CodeSap'), # Mantendo o nome original para clareza
        pl.col('U_CodPeriodoProducao').alias('PeriodoProd'),
        pl.col('Safra'),
        pl.col('NumeroContrato'),
        pl.col('Commoditie'),
        pl.col('Fixado'),
        pl.col('PN').alias('Cliente'), # Renomeia a coluna chave aqui
        pl.col('Cargas'),
        pl.col('Romaneios').alias('QuantEntregue'),
        pl.col('UnidadeMedida').alias('Fator'),
        pl.col('Saldo'),
        pl.col('ValorUN'),
        pl.col('ValorTotal'),
    )

# --- Pipeline Principal de Contratos ---
# CORREÇÃO 2: Nome da função corrigido para "pipeline" para diferenciar do carregador.
def aguaazul_travas_pipeline(
    Safra: str = None,
    Commoditie: str = None,
    Cliente: str = None,
) -> pl.LazyFrame:
    """Orquestra o pipeline de processamento e cálculo dos dados de contratos."""

    lazy_df = aguaazul_travas_lazy()

    # Aplica filtros, se fornecidos
    if Safra:
        lazy_df = lazy_df.filter(pl.col("Safra") == Safra)
    if Commoditie:
        lazy_df = lazy_df.filter(pl.col("Commoditie") == Commoditie)
    if Cliente:
        lazy_df = lazy_df.filter(pl.col("Cliente") == Cliente)

    lazy_df = lazy_df.fill_null(0)
    
    # Pipeline de transformações com as correções de tipo
    processed_df = (
        lazy_df
        .with_columns(
            # ✅ CORREÇÃO: Converte as colunas para Float64 ANTES de qualquer cálculo
            
            # Conversões para Sacas (SC) e Toneladas (TON)
            ((pl.col("Fixado").cast(pl.Float64) * pl.col("Fator").cast(pl.Float64)) / 60).round(2).alias('FixadoSC'),
            (pl.col("QuantEntregue").cast(pl.Float64) / 60).round(2).alias("EntregueSC"),
            (pl.col("QuantEntregue").cast(pl.Float64) / 1000).round(4).alias("EntregueTON"),
            ((pl.col("Fixado").cast(pl.Float64) * pl.col("Fator").cast(pl.Float64)) / 1000).round(2).alias("FixadoTON"),
            
            # Garante que Fator não seja zero para evitar erros de divisão
            pl.when(pl.col("Fator").cast(pl.Float64) > 0)
              .then(((pl.col("ValorUN").cast(pl.Float64) / pl.col("Fator").cast(pl.Float64)) * 60))
              .otherwise(0)
              .round(2)
              .alias("ValorSC"),
        )
        .with_columns(
            # Cálculos de Saldo (agora todos os campos de origem são floats)
            (pl.col("FixadoSC") - pl.col("EntregueSC")).round(2).alias("SaldoSC"),
            (pl.col("FixadoTON") - pl.col("EntregueTON")).round(4).alias("SaldoTON"),
        )
        .with_columns(
            # Porcentagens com proteção contra divisão por zero
            pl.when(pl.col("FixadoTON") != 0)
              .then(((pl.col("EntregueTON").cast(pl.Float64) / pl.col("FixadoTON").cast(pl.Float64)) * 100))
              .otherwise(0)
              .round(2)
              .alias("Perc_Entregue_Contrato"),

            pl.when(pl.sum("FixadoTON") != 0)
              .then(((pl.sum("EntregueTON") / pl.sum("FixadoTON")) * 100))
              .otherwise(0)
              .round(2)
              .alias("Perc_Entregue_Geral"),
        )
    )

    # Seleção final
    final_df = (
        processed_df
        .select(
            "Safra", "Commoditie", "CodeSap", "Cliente", "NumeroContrato",
            "FixadoTON", "EntregueTON", "SaldoTON",
            "FixadoSC", "EntregueSC", "SaldoSC",
            "ValorSC", "ValorTotal",
            "Perc_Entregue_Contrato", "Perc_Entregue_Geral"
        )
        .sort(['Safra', 'Cliente'])
    )

    return final_df

# --- Funções para Filtros de Dropdown (Otimizadas) ---
# CORREÇÃO 4: Apontam para o carregador de dados leve, não para a pipeline inteira.
def get_uniq_contrato_safra() -> pl.LazyFrame:
    return aguaazul_travas_lazy().select(pl.col('Safra')).unique().sort('Safra', descending=True)

def get_uniq_contrato_commoditie() -> pl.LazyFrame:
    return aguaazul_travas_lazy().select(pl.col('Commoditie')).unique().sort('Commoditie')

def get_uniq_contrato_cliente() -> pl.LazyFrame:
    return aguaazul_travas_lazy().select(pl.col('Cliente')).unique().sort('Cliente')


# --- Função de KPIs (Mais Robusta) ---
def kpis_contratos(df: pl.DataFrame) -> dict:

    if df.is_empty():
        return {
            "Total_Fixado": "0,00",
            "Total_Entregue": "0,00",
            "Total_Faturamento": "0,00",
            "Total_Saldo": "0,00",
            "Quantidade_Contratos": "0",
            "Preco_medio_sc": "0,00"
        }
    
    # Cálculos dos KPIs
    total_fixado = float(df['FixadoSC'].sum())
    total_entregue = float(df['EntregueSC'].sum())
    total_faturamento = float(df['ValorTotal'].sum())
    total_saldo = float(df['SaldoSC'].sum())
    quantidade_contratos = df['CodeSap'].n_unique() # Usa a coluna correta

    # CORREÇÃO 5: Proteção contra divisão por zero
    preco_medio_sc = (total_faturamento / total_fixado) if total_fixado > 0 else 0

    # Formatação para o front-end
    return {
        "Total_Fixado": f"{total_fixado:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
        "Total_Entregue": f"{total_entregue:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
        "Total_Faturamento": f"{total_faturamento:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
        "Total_Saldo": f"{total_saldo:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
        "Quantidade_Contratos": f"{quantidade_contratos:,}".replace(",", "."),
        "Preco_medio_sc": f"{preco_medio_sc:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    }
 
    ## Esse e o Bloco que cuida o Dashboard de Colheita com das Funções "aguaazul_pipeline_colheita", "aguaazul_cleanup"
def aguaazul_pipeline_colheita(
    Safra: str = None,
    cultura: str = None,
    Talhao: str = None
) -> pl.LazyFrame:
    """Orquestra a pipeline de processamento de dados de colheita de forma lazy."""
    df_colhido = aguaazul_colhido_lazy()
    df_hectares = aguaazul_hectares_lazy()
    df_entradas = aguaazul_rom_entradas_lazy()
    df_talhoes = aguaazul_talhao_lazy()

    # Agrupando entradas e colhido por talhão/período para evitar duplicação de dados nos joins
    df_entradas_grouped = df_entradas.group_by(['CodTalhao', 'PeriodoProd']).agg(
        pl.col('PesoBrutoSacas').sum(),
        pl.col('PesoLiquidoSacas').sum(),
    )
    
    df_colhido_grouped = df_colhido.group_by(['CodTalhao', 'PeriodoProd']).agg(
        pl.col('HectaresColhidos').sum()
    )

    df_hectares_grouped = df_hectares.group_by(['PeriodoProd', 'Cultura', 'Safra', 'CodTalhao']).agg(
        pl.col('Hectares').sum()
    )

    # ALTERAÇÃO 3: Usando 'left' join para incluir talhões mesmo que não tenham colheita ou romaneio.
    # A base agora é a informação de plantio (hectares).
    joinDf = df_hectares_grouped.join(
        df_colhido_grouped,
        on=['CodTalhao', 'PeriodoProd'],
        how='left'
    ).join(
        df_entradas_grouped,
        on=['CodTalhao', 'PeriodoProd'],
        how='left'
    )
    
    # ALTERAÇÃO 4: Adicionando o join com df_talhoes para enriquecer os dados.
    joinDf = joinDf.join(
        df_talhoes.select(['CodTalhao', 'Talhao', 'Fazenda', 'Setor']), # Seleciona só o que precisa
        on='CodTalhao',
        how='left'
    )

    # Aplicação de filtros
    if Safra:
        joinDf = joinDf.filter(pl.col('Safra') == Safra)
    if cultura:
        joinDf = joinDf.filter(pl.col('Cultura') == cultura)
    if Talhao:
        joinDf = joinDf.filter(pl.col('Talhao') == Talhao)

    return joinDf

def aguaazul_cleanup(lazy_df_input: pl.LazyFrame) -> pl.LazyFrame:
    """Realiza cálculos finais e seleciona as colunas para o DataFrame de saída."""
    # Preencher com 0 os valores nulos resultantes do left join antes dos cálculos
    lazy_df_filled = lazy_df_input.fill_null(0)

    # Aqui e pra calcular as Sacas
    lazy_df_output = lazy_df_filled.with_columns(
        # Evitar Zero Div, mas da pra simplificar se ficar pesada no django
        (pl.when(pl.col("HectaresColhidos") > 0)
         .then(pl.col("PesoLiquidoSacas") / pl.col("HectaresColhidos"))
         .otherwise(0))
        .cast(pl.Float64).round(2).alias("Liquido.Sc/Ha"),

        (pl.when(pl.col("HectaresColhidos") > 0)
         .then(pl.col("PesoBrutoSacas") / pl.col("HectaresColhidos"))
         .otherwise(0))
        .cast(pl.Float64).round(2).alias("Bruto.Sc/Ha")
    )
    
    # Selecionar e reordenar as colunas finais
    lazy_df_output = lazy_df_output.select(
        pl.col('Safra'),
        pl.col('Cultura'),
        pl.col('Setor'),
        pl.col('Talhao'),
        pl.col('Hectares').cast(pl.Float64).round(2),
        pl.col('HectaresColhidos').cast(pl.Float64).round(2),
        pl.col('PesoLiquidoSacas'),
        pl.col('Liquido.Sc/Ha'),
        pl.col('PesoBrutoSacas'),
        pl.col('Bruto.Sc/Ha'),
        
    ).sort(['Safra', 'Cultura', 'Setor', 'Talhao'])
    
    return lazy_df_output

# --- Funções para filtros (dropdowns) ---
# Nenhuma alteração necessária aqui, mas se o carregamento for pesado mudar e uma opção,
# a mesma lógica de cache poderia ser aplicada? estudar isso.
def get_unique_safra_lazy() -> pl.LazyFrame:
    return azul_hectares().lazy().select(pl.col('Safra')).unique().sort('Safra', descending=True)

def get_unique_cultura_lazy() -> pl.LazyFrame:
    return azul_hectares().lazy().select(pl.col('Cultura')).unique().sort('Cultura')

def get_unique_talhao_lazy() -> pl.LazyFrame:
    return azul_talhao().lazy().select(pl.col('Talhao')).unique().sort('Talhao')


# pipeline.py

def calculate_kpis(df: pl.DataFrame) -> dict:
    """
    Calcula os KPIs a partir de um LazyFrame de dados de colheita.
    Retorna um dicionário com os valores calculados.
    """
    if df.is_empty():
        return {
            "total_sacas_colhidas": "0",
            "total_sacas_brutas": "0",
            "media_liquida_sc_ha": "0,00",
            "media_bruta_sc_ha": "0,00", 
            "total_hectares_colhidos": "0",
            "numero_talhoes": 0,
        }

    # Calcula os KPIs
    total_sacas_liquidas = df["PesoLiquidoSacas"].sum()
    total_sacas_brutas = df["PesoBrutoSacas"].sum() 
    total_ha_colhidos = df["HectaresColhidos"].sum()
    num_talhoes = df["Talhao"].n_unique()
    
    # Média Líquida (Sc/Ha)
    media_liquida = (df["Liquido.Sc/Ha"] * df["HectaresColhidos"]).sum() / total_ha_colhidos if total_ha_colhidos > 0 else 0
    
    # Média Bruta (Sc/Ha)
    media_bruta = total_sacas_brutas / total_ha_colhidos if total_ha_colhidos > 0 else 0

    # Retorna um dicionário com os resultados formatados
    return {
    # Formatação antiga: f"{total_sacas_liquidas:,.0f}".replace(",", ".")
    # CORREÇÃO: Usar a formatação robusta para o padrão brasileiro
    "total_sacas_colhidas": f"{total_sacas_liquidas:,.0f}".replace(",", "X").replace(".", ",").replace("X", "."),
    "total_sacas_brutas": f"{total_sacas_brutas:,.0f}".replace(",", "X").replace(".", ",").replace("X", "."),
    "media_liquida_sc_ha": f"{media_liquida:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
    "media_bruta_sc_ha": f"{media_bruta:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
    "total_hectares_colhidos": f"{total_ha_colhidos:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."), # .2f para hectares
    "numero_talhoes": num_talhoes,
    }