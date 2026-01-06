import pandas as pd
import requests
from datetime import datetime
import time
import numpy as np

# Configurações iniciais
TOKEN = "b9c10754-7b28-3aee-b0bc-4f6785f9c6bd"
BASE_URL = "https://gateway.apilib.prefeitura.sp.gov.br/sf/sof/v4/"

# Headers para autenticação
headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

# Função para fazer requisições à API
def fazer_requisicao(endpoint, params=None):
    url = f"{BASE_URL}/{endpoint}"
    response = requests.get(url, headers=headers, params=params)
    try:
        return response.json()
    except Exception:
        print(f"Resposta inválida da API paraq {url} com params {params}")
        return None

df_empenhos = pd.read_excel("empenhos_2025.xlsx")

pivot = pd.pivot_table(
    df_empenhos,
    index=["codProcesso", "dotacao_completa", "anoContrato"],
    values=["valEmpenhadoLiquido"],
    aggfunc="sum",
    fill_value=0
).reset_index()

# Calcula o total por dotacao_completa
totais_dotacao = pivot.groupby("codProcesso")["valEmpenhadoLiquido"].sum()
totais_dotacao.index = totais_dotacao.index.astype(str)

#totais_dotacao = totais_dotacao.replace(0, np.nan)

# Calcula o total por codProcesso (o "pai")
totais_codprocesso = pivot.groupby("codProcesso")["valEmpenhadoLiquido"].sum()

# Calcula o percentual de cada dotacao_completa dentro do seu codProcesso
pivot["percentual"] = (
    pivot["valEmpenhadoLiquido"] /
    pivot["codProcesso"].map(totais_codprocesso)
) * 100

pivot["percentual"] = pivot["percentual"].round(2)

pivot.to_excel("pivot_empenhos_2025.xlsx", index=False)
print("Finalizado")