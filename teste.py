# ...existing code...
import requests
import pandas as pd
from itertools import product
import time
from datetime import datetime, timedelta
from pathlib import Path
import math

inicio = time.time()
horario_inicio = datetime.now().strftime("%H:%M:%S")
print("Início da execução:", horario_inicio)
# -----------------------------
# CONFIGURAÇÃO
# -----------------------------

dt_inicio = datetime.fromtimestamp(inicio)
ANO = str(dt_inicio.year)
MES = str(dt_inicio.month)

BASE = "https://gateway.apilib.prefeitura.sp.gov.br/sf/sof/v4"
ORGAO = 34
UNIDADE = 10
LIMIT = 500
TOKEN = "b9c10754-7b28-3aee-b0bc-4f6785f9c6bd"
SAIDA = "execucao_org34_uo10.csv"
headers = {
    "Authorization": f"Bearer {TOKEN}"
}

def fetch_all(endpoint, params=None, list_=None):
    """Busca todos os registros paginados de um endpoint."""
    all_items = []
    while True:
        p = params.copy() if params else {}
        r = requests.get(f"{BASE}/{endpoint}", params=p, headers=headers)
        r.raise_for_status()
        data = r.json() or []
        if not data:
            break
        df = pd.json_normalize(data[list_])
        if endpoint == "modalidades":
            l = df.iloc[:, 1].tolist()
        else: 
            l = df.iloc[:, 0].tolist()
        all_items.extend(l)
        time.sleep(0.05)  # respeitar limites da API
        break
    return all_items

p = {
    "anoExercicio": ANO
}

v = fetch_all("fonteRecursos", p, "lstFonteRecurso")
print(v)