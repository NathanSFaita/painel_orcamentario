import requests
import pandas as pd
from itertools import product
import time
from datetime import datetime, timedelta
from googleapiclient.discovery import build
from google.oauth2 import service_account
from googleapiclient.http import MediaFileUpload
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive

inicio = time.time()
horario_inicio = datetime.now().strftime("%H:%M:%S")
print("Início da execução:", horario_inicio)

dt_inicio = datetime.fromtimestamp(inicio)
ano = str(dt_inicio.year)
mes = str(dt_inicio.month)

# Configurações iniciais
TOKEN = "b9c10754-7b28-3aee-b0bc-4f6785f9c6bd"
BASE_URL = "https://gateway.apilib.prefeitura.sp.gov.br/sf/sof/v4/"

# Headers para autenticação
headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

if dt_inicio.month < 10:
    mes = "0" + mes  # Adiciona zero à esquerda se o mês for menor que 10

URL_ORC = (f"https://orcamento.sf.prefeitura.sp.gov.br/orcamento/uploads/{ano}/basedadosexecucao_{mes}{ano[2:]}.xlsx")
print(URL_ORC)

orcamento = pd.read_excel(URL_ORC)
orcamento_smdhc = orcamento[orcamento["Cd_Orgao"].isin([8, 34, 78, 90])]

nome_arquivo = f"despesas_painel_{mes}{ano[2:]}.xlsx"

procv = pd.read_excel("procv.xlsx")
procv_dict_coord = dict(zip(procv["acao"], procv["coordenadoria"]))
procv_dict_politicas = dict(zip(procv["acao"], procv["politicas_para"]))

def emenda_se_menor_8000(proj_ativ):
    if proj_ativ > 8000:
        return "Emenda"
    return procv_dict_coord.get(proj_ativ, "Emenda")

def emenda_se_menor_8000_politicas(proj_ativ):
    if proj_ativ > 8000:
        return "Emenda"
    return procv_dict_politicas.get(proj_ativ, "Emenda")

orcamento_smdhc["coordenadoria"] = orcamento_smdhc["ProjetoAtividade"].map(emenda_se_menor_8000)
orcamento_smdhc["politicas_para"] = orcamento_smdhc["ProjetoAtividade"].map(emenda_se_menor_8000_politicas)

orcamento_smdhc.to_excel(nome_arquivo, index=False)

# Upload automático para o Google Drive usando OAuth (PyDrive)
gauth = GoogleAuth()
gauth.LocalWebserverAuth()  # Abre navegador para login e autorização

drive = GoogleDrive(gauth)

# Envia o arquivo para o Meu Drive
file_drive = drive.CreateFile({'title': nome_arquivo})
file_drive.SetContentFile(nome_arquivo)
file_drive.Upload()

print("✅ Arquivo enviado com sucesso ao Meu Drive!")