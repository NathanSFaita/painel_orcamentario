import pandas as pd
import requests
from datetime import datetime
import time

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

inicio = time.time()
dt_inicio = datetime.fromtimestamp(inicio)
ano = str(dt_inicio.year)
mes = str(dt_inicio.month)
if dt_inicio.month < 10:
    mes = "0" + mes  # Adiciona zero à esquerda se o mês for menor que 10

URL_ORC = (f"https://orcamento.sf.prefeitura.sp.gov.br/orcamento/uploads/{ano}/basedadosexecucao_{mes}{ano[2:]}.xlsx")
# url = "https://orcamento.sf.prefeitura.sp.gov.br/orcamento/uploads/2024/OrcamentoAprovado_2024.xlsx"
loa = pd.read_excel(URL_ORC)

loa_smdhc = loa.loc[loa["Cd_Orgao"] == 34]

params_emp = {
    "anoEmpenho": "",
    "mesEmpenho": "",
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
}	

df_parcial = pd.DataFrame()
requisicao = 0
requisicoes = loa_smdhc.shape[0]

print("Total de requisições:", requisicoes)

for index, row in loa_smdhc.iterrows():
    requisicao += 1
    print("Requisição:", requisicao, "de", requisicoes)
    orgao = row["Cd_Orgao"]
    uo = row["Cd_Unidade"]
    funcao = row["Cd_Funcao"]
    subfuncao = row["Cd_SubFuncao"]
    programa = row["Cd_Programa"]
    proj_ativ = row["ProjetoAtividade"]
    categoria = str(row["Categoria_Despesa"])
    grupo = str(row["Grupo_Despesa"])
    modalidade = str(row["Cd_Modalidade"])
    elemento = str(row["Cd_Elemento"])
    vinculacao = str(row["COD_VINC_REC_PMSP"])
    if vinculacao == "0" or vinculacao == "4":
        vinculacao = "000" + vinculacao

    print(orgao, uo, funcao, subfuncao, programa, proj_ativ, categoria, grupo, modalidade, elemento)
    
    params_emp["anoEmpenho"] = ano
    params_emp["mesEmpenho"] = mes
    params_emp["codOrgao"] = orgao
    params_emp["codUnidade"] = uo
    params_emp["codFuncao"] = funcao
    params_emp["codSubFuncao"] = subfuncao
    params_emp["codPrograma"] = programa
    params_emp["codProjetoAtividade"] = proj_ativ
    params_emp["codCategoria"] = categoria
    params_emp["codGrupo"] = grupo
    params_emp["codModalidade"] = modalidade
    params_emp["codElemento"] = elemento
    params_emp["codVinculacaoRecurso"] = vinculacao

    empenhos = fazer_requisicao("empenhos", params=params_emp)

    print("\x1b[F" * 2, end="") # Mover o cursor duas linhas para cima

    if empenhos is None:
        continue

    else:
        df_empenhos = pd.json_normalize(empenhos["lstEmpenhos"])
        df_parcial = pd.concat([df_parcial, df_empenhos], ignore_index=True)
        continue

df_parcial.to_excel("empenhos_2025.xlsx", index=False)
print("feitos os empenhos")