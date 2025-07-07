# Em seu_app/maps.py (ou onde suas funções de dados estão)

from .login import azul_talhao
import polars as pl

# Define a base da sua URL como uma constante para fácil manutenção
AZURE_BLOB_BASE_URL = "https://storagemapeamentos.blob.core.windows.net/mapeamentoaguaazul/"

def mapas_aguaazul() -> pl.LazyFrame:
    """
    Função base que carrega e prepara todos os dados dos talhões.
    """
    return azul_talhao().lazy().select(
        pl.col("CodTalhao").cast(pl.String),
        pl.col("Talhao").cast(pl.String),
        pl.col("CodFazenda").cast(pl.String),
        pl.col("Fazenda").cast(pl.String),
        pl.col("CodSetor").cast(pl.String),
        pl.col("Setor").cast(pl.String),
        pl.col("HectaresTotais").cast(pl.Float64).round(2),
        pl.col("U_CooX"),
        pl.col("U_CooY"),
        pl.col("U_CooZ"),
        pl.col("SVG").cast(pl.String), # O SVG aqui ainda é só o final do path
    )

def view_mapa_por_talhao(codigo_talhao: str) -> pl.DataFrame:
    """
    Retorna os dados de um talhão específico, com a URL do SVG completa.
    """
    lazy_df = mapas_aguaazul()

    lazy_df_filtrado = lazy_df.filter(
        pl.col("CodTalhao") == codigo_talhao
    )

    # ✅ CORREÇÃO: Monta a URL completa do SVG antes de selecionar as colunas
    lazy_df_com_url = lazy_df_filtrado.with_columns(
        pl.concat_str([
            pl.lit(AZURE_BLOB_BASE_URL),
            pl.col("SVG")
        ]).alias("SVG") # Sobrescreve a coluna SVG com a URL completa
    )

    lazy_df_final = lazy_df_com_url.select(
        "Talhao", "Setor", "HectaresTotais", "SVG" # Seleciona as colunas
    )

    return lazy_df_final.collect()

def listar_talhoes_disponiveis() -> pl.DataFrame:
    """
    ✅ NOVA FUNÇÃO: Retorna uma lista limpa de talhões disponíveis (código e nome).
    """
    lazy_df = mapas_aguaazul()

    # Seleciona apenas as colunas de código e nome, remove duplicados e ordena
    lista_talhoes = (
        lazy_df
        .select("CodTalhao", "Talhao")
        .unique(subset=["CodTalhao"])
        .sort("Talhao")
    )

    return lista_talhoes.collect()