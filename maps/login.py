import polars as pl
from decouple import config
from adlfs import AzureBlobFileSystem

class Auth:
    def __init__(self):
        self.account_name = config("MAP_SECRET_NAME")
        self.account_key = config("MAP_SECRET_KEY")
        self.fs = AzureBlobFileSystem(
            account_name=self.account_name,
            account_key=self.account_key
        )
    def get_public_url(self, azpath: str) -> str:

        base_url = f"https://{self.account_name}.blob.core.windows.net"
        
        # Junta a base com o caminho do arquivo
        return f"{base_url}/{azpath}"

# --- Exemplo de Uso ---

# Instância da classe
auth = Auth()

# 1. Caminho para o SVG no Azure (container/caminho/arquivo)
svg_path = "mapeamentoaguaazul/Teste_deploy/LAGOA_DOS_PATOS_2_SEMFUNDO.svg"

# 2. Obter a URL pública
public_url = auth.get_public_url(svg_path)

# 3. Imprimir o resultado
print(public_url)

# Saída esperada:
# https://samapeamento.blob.core.windows.net/aguaazul/static/mapas_svg/LAGOA_DOS_PATOS_2_SEMFUNDO.svg