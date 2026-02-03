import requests
import pandas as pd
from itertools import product
import time
from datetime import datetime, timedelta

inicio = time.time()

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

orcamento = pd.read_excel(URL_ORC)
orcamento_smdhc = orcamento[orcamento["Cd_Orgao"].isin([34, 8, 78, 90])]

procv = pd.read_excel("C:\\Users\\x526325\\OneDrive - rede.sp\\painel orçamentário\\python\\procv.xlsx")
procv_orgao = pd.read_excel("C:\\Users\\x526325\OneDrive - rede.sp\\painel orçamentário\\python\\procv_orgao.xlsx")

# Função para fazer requisições à API
def fazer_requisicao(endpoint, params=None):
    url = f"{BASE_URL}/{endpoint}"
    response = requests.get(url, headers=headers, params=params)
    return response.json()

params_dp = {
    "anoDotacao": "",
    "mesDotacao": "",
    "codOrgao": "",
    "codUnidade": "",
    "codFuncao": "",
    "codSubFuncao": "",
    "codPrograma": "",
    "codProjetoAtividade": "",
    "codCategoria": "",
    "codGrupo": "", 
    "codModalidade": "",
    "codElemento": "",
    "codVinculacaoRecurso": ""  
    # Outros parâmetros podem ser adicionados para filtrar
}

colunas_iniciais = ["cd_orgao", "orgao", "uo", "funcao", "subfuncao", "programa", "projeto_atividade", "coordenadoria", "despesa", "vinculacao"]
df_final = pd.DataFrame(columns=colunas_iniciais)

for index, row in orcamento_smdhc.iterrows():
    orgao = str(row["Cd_Orgao"])
    if orgao == "8":
        orgao = "08"
    uo = str(row["Cd_Unidade"])
    funcao = str(row["Cd_Funcao"])
    if funcao == "8":
        funcao = "08"  # Padroniza a função para dois dígitos
    subfuncao = row["Cd_SubFuncao"]
    programa = row["Cd_Programa"]
    proj_ativ = int(row["ProjetoAtividade"])
    categoria = str(row["Categoria_Despesa"])
    grupo = str(row["Grupo_Despesa"])
    modalidade = str(row["Cd_Modalidade"])
    elemento = str(row["Cd_Elemento"])
    vinculacao = str(row["COD_VINC_REC_PMSP"])
    if vinculacao == "0" or vinculacao == "4":
        vinculacao = "000" + vinculacao
    params_dp["anoDotacao"] = ano
    params_dp["mesDotacao"] = mes
    params_dp["codOrgao"] = orgao
    params_dp["codUnidade"] = uo
    params_dp["codFuncao"] = funcao
    params_dp["codSubFuncao"] = subfuncao
    params_dp["codPrograma"] = programa
    params_dp["codProjetoAtividade"] = proj_ativ
    params_dp["codCategoria"] = categoria
    params_dp["codGrupo"] = grupo
    params_dp["codModalidade"] = modalidade
    params_dp["codElemento"] = elemento
    params_dp["codVinculacaoRecurso"] = vinculacao

    despesas = fazer_requisicao("despesas", params=params_dp)
    df_despesas = pd.json_normalize(despesas["lstDespesas"])
      
    if proj_ativ < 8000:
        coordenadoria = procv.loc[procv["acao"] == proj_ativ, "coordenadoria"].values
    else:
        coordenadoria = "Emenda"

    df_despesas["cd_orgao"] = orgao
    
    nome_orgao = procv_orgao.loc[procv_orgao["cod_orgao"] == int(orgao), "orgao"].values
    df_despesas["orgao"] = nome_orgao[0]
    if uo == "20":
        df_despesas["uo"] = "FUMCAF"
    df_despesas["uo"] = uo
    df_despesas["funcao"] = funcao
    df_despesas["subfuncao"] = subfuncao
    df_despesas["programa"] = programa
    df_despesas["projeto_atividade"] = proj_ativ
    df_despesas["coordenadoria"] = str(proj_ativ) + " - " + coordenadoria[0]
    df_despesas["despesa"] = categoria + grupo + modalidade + elemento + "00"
    df_despesas["vinculacao"] = vinculacao

    df_final = pd.concat([df_final, df_despesas], ignore_index=True)

df_final = df_final.drop_duplicates()
df_final.to_csv(f"despesas_{ano}{mes}.xlsx", index=True, encoding="utf-8")