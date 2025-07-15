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

    def reading(self, azpath: str) -> pl.LazyFrame:
        with self.fs.open(azpath, mode='rb') as f:
            df = pl.read_parquet(f)
        return df


# Instância do leitor
reader = Auth()

def azul_doc_a_pagar() -> pl.LazyFrame:return reader.reading(config("AZL_DASG_FINAN")+"/Extracao_contas_a_pagar.parquet")
def azul_contas_bancarias() -> pl.LazyFrame:return reader.reading(config("AZL_DASG_FINAN")+"/Extracao_contas_bancarias.parquet")
def azul_doc_pagos() -> pl.LazyFrame:return reader.reading(config("AZL_DASG_FINAN")+"/Extracao_documentos_pagos.parquet")
def azul_doc_recebidos() -> pl.LazyFrame:return reader.reading(config("AZL_DASG_FINAN")+"/Extracao_documentos_recebidos.parquet")
def azul_doc_a_receber() -> pl.LazyFrame:return reader.reading(config("AZL_DASG_FINAN")+"/Extracao_documentos_a_receber.parquet")













