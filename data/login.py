from django.urls import path
import polars as pl
from decouple import config
from adlfs import AzureBlobFileSystem

class Auth:
    def __init__(self):
        self.account_name =config("PATH_SECRET_NAME")
        self.account_key =config("PATH_SECRET_KEY")
        self.fs = AzureBlobFileSystem(
            account_name=self.account_name,
            account_key=self.account_key
        )

    def reading(self, azpath: str) -> pl.DataFrame:
        with self.fs.open(azpath, mode='rb') as f:
            df = pl.read_parquet(f)
        return df

reader = Auth()

def azul_travas() -> pl.DataFrame:return reader.reading(config("AZL_DASH_COLHEITA")+"/Extracao_saldo_contratos.parquet")
def azul_colhido() -> pl.DataFrame:return reader.reading(config("AZL_DASH_COLHEITA")+"/Extracao_Hectares_Colhidos.parquet")
def azul_hectares() -> pl.DataFrame:return reader.reading(config("AZL_DASH_COLHEITA")+"/Extracao_Hectares_Cultura.parquet")
def azul_romaneios() -> pl.DataFrame:return reader.reading(config("AZL_DASH_COLHEITA")+"/Extracao_Romaneio_Entrada.parquet")
def azul_talhao() -> pl.DataFrame:return reader.reading(config("AZL_DASH_COLHEITA")+"/Extracao_Cad_Talhao.parquet")



def azul_doc_a_pagar() -> pl.DataFrame:return reader.reading(config("AZL_DASG_FINAN")+"/Extracao_contas_a_pagar.parquet")
def azul_contas_bancarias() -> pl.DataFrame:return reader.reading(config("AZL_DASG_FINAN")+"/Extracao_contas_bancarias.parquet")
def azul_doc_pagos() -> pl.DataFrame:return reader.reading(config("AZL_DASG_FINAN")+"/Extracao_documentos_pagos.parquet")




