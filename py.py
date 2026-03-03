import sys

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

def fazer_requisicao(endpoint, params):
        url = f"{BASE_URL}/{endpoint}"
        try:
            response = requests.get(
                url,
                params=params,
                headers=headers,
                timeout=60
            )
        except Exception as e:
            print(f"Erro na requisição HTTP: {e}")
            sys.exit(1)

        print(f"[{endpoint}] Status code:", response.status_code)

        if response.status_code != 200:
            print("Resposta não-200 da API:")
            print(response.status_code, response.text[:1000])
            sys.exit(1)

        if not response.text or response.text.strip() == "":
            print("Resposta vazia da API")
            sys.exit(1)

        try:
            payload = response.json()
        except Exception:
            print("Falha ao converter resposta em JSON")
            print(response.text[:1000])
            sys.exit(1)
        return payload

params_proj = {
     "anoExercicio": "2026",
}

proj_atividades = fazer_requisicao("projetosAtividades", params_proj)
df_proj = pd.json_normalize(proj_atividades["lstProjetosAtividades"])

print(df_proj)