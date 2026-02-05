import pandas as pd
import requests
from datetime import datetime
import time
import os

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

baseaux_path = os.path.dirname(__file__)
procv_acao = pd.read_excel(os.path.join(baseaux_path, "dados_auxiliares", "procv_acoes.xlsx"))
procv_orgao = pd.read_excel(os.path.join(baseaux_path, "dados_auxiliares", "procv_orgao.xlsx"))

params_emp = {
    "anoEmpenho": "",
    "mesEmpenho": "",
    "numPagina": "",
}	

df_parcial = pd.DataFrame()
requisicoes = 0
requisicao = 0
lista_orgaos = ["08", "34", "78", "90"]

params_emp["anoEmpenho"] = ano
params_emp["mesEmpenho"] = mes
#params_emp["codOrgao"] = 34

for orgao in lista_orgaos:
    params_emp["codOrgao"] = orgao
    num_pagina = fazer_requisicao("empenhos", params=params_emp)
    df_paginas = pd.json_normalize(num_pagina["metaDados"])
    requisicoes += df_paginas["qtdPaginas"][0]
    #print("ORG", orgao, "metaDados:", num_pagina.get("metaDados"))


print("Total de requisições:", requisicoes)

for orgao_api in lista_orgaos:
    params_emp["codOrgao"] = orgao_api
    params_emp["numPagina"] = ""
    num_pagina = fazer_requisicao("empenhos", params=params_emp)
    df_paginas = pd.json_normalize(num_pagina["metaDados"])
    paginas = df_paginas["qtdPaginas"][0]
    pagina = 0

    for p in range(paginas):
        pagina += 1
        requisicao += 1
        print("Requisição:", requisicao, "de", requisicoes)

        print(f"Órgão: {orgao_api} - Página: {pagina}/{paginas}")
# for i in range(requisicoes):
#     pagina = 0
#     for orgao in lista_orgaos:
#         pagina += 1
#         requisicao += 1
#         print("Requisição:", requisicao, "de", requisicoes)
        
#         params_emp["codOrgao"] = orgao
#         num_pagina = fazer_requisicao("empenhos", params=params_emp)
#         df_paginas = pd.json_normalize(num_pagina["metaDados"])
#         paginas = df_paginas["qtdPaginas"][0]

        #params_emp["codOrgao"] = orgao
        params_emp["anoEmpenho"] = ano
        params_emp["mesEmpenho"] = mes
        params_emp["numPagina"] = pagina

        empenhos = fazer_requisicao("empenhos", params=params_emp)

        print("\x1b[F" * 2, end="") # Mover o cursor duas linhas para cima

        if empenhos is None:
            continue

        else:
            df_empenhos = pd.json_normalize(empenhos["lstEmpenhos"])

            orgao_api = df_empenhos["codOrgao"][0]
            uo = df_empenhos["codUnidade"][0]
            funcao = df_empenhos["codFuncao"][0]
            subfuncao = df_empenhos["codSubFuncao"][0]
            programa = df_empenhos["codPrograma"][0]
            proj_ativ = str(df_empenhos["codProjetoAtividade"][0])
            despesa = "".join([
                str(df_empenhos["codCategoria"][0]), 
                str(df_empenhos["codGrupo"][0]), 
                str(df_empenhos["codModalidade"][0]), 
                str(df_empenhos["codElemento"][0]),
                "00"
            ])
            df_empenhos["dotacao_completa"] = "".join([
                str(orgao_api),
                ".", 
                str(uo),
                ".", 
                str(funcao),
                ".", 
                str(subfuncao),
                ".", 
                str(programa), 
                ".",
                str(proj_ativ),
                ".", 
                str(despesa)
            ])

        df_parcial = pd.concat([df_parcial, df_empenhos], ignore_index=True)
        continue

if not df_parcial.empty:
    df_parcial["codOrgao"] = pd.to_numeric(df_parcial["codOrgao"], errors="coerce").astype("Int64")
    df_parcial["codUnidade"] = pd.to_numeric(df_parcial["codUnidade"], errors="coerce").astype("Int64")
    df_parcial["codProjetoAtividade"] = pd.to_numeric(
        df_parcial["codProjetoAtividade"], errors="coerce"
    ).astype("Int64")

    procv_orgao["cod_orgao"] = pd.to_numeric(procv_orgao["cod_orgao"], errors="coerce").astype("Int64")
    procv_acao["acao"] = pd.to_numeric(procv_acao["acao"], errors="coerce").astype("Int64")

    df_parcial = df_parcial.merge(
        procv_orgao[["cod_orgao", "orgao"]],
        left_on="codOrgao",
        right_on="cod_orgao",
        how="left"
    )

    df_parcial = df_parcial.merge(
        procv_acao[["acao", "coordenadoria", "politicas_para", "acao_programatica"]],
        left_on="codProjetoAtividade",
        right_on="acao",
        how="left"
    ).rename(columns={"coordenadoria": "coordenacao"})

    df_parcial.loc[df_parcial["codUnidade"] == 20, "orgao"] = "FUMCAF"

    mask_emenda = df_parcial["codProjetoAtividade"] >= 8000
    df_parcial.loc[mask_emenda, ["coordenacao", "politicas_para", "acao_programatica"]] = "Emenda"

    for col in ["orgao", "coordenacao", "politicas_para", "acao_programatica"]:
        df_parcial[col] = df_parcial[col].fillna("N?o encontrado")

ordem_colunas = [
    "codEmpresa",
    "nomEmpresa",
    "numReserva",
    "codEmpenho",
    "anoEmpenho",
    "mesEmpenho",
    "datEmpenho",
    "codProcesso",
    "numCpfCnpj",
    "txtRazaoSocial",
    "numContrato",
    "anoContrato",
    "codOrgao",
    "orgao",
    "txDescricaoOrgao",
    "codUnidade",
    "txDescricaoUnidade",
    "codFuncao",
    "txDescricaoFuncao",
    "codSubFuncao",
    "txDescricaoSubFuncao",
    "codPrograma",
    "txDescricaoPrograma",
    "codProjetoAtividade",
    "txDescricaoProjetoAtividade",
    "coordenacao",
    "politicas_para",
    "acao_programatica",
    "codCategoria",
    "txDescricaoCategoriaEconomica",
    "codGrupo",
    "txDescricaoGrupoDespesa",
    "codModalidade",
    "txDescricaoModalidade",
    "codElemento",
    "txDescricaoElemento",
    "codFonteRecurso",
    "txDescricaoFonteRecurso",
    "codItemDespesa",
    "txDescricaoItemDespesa",
    "codSubElemento",
    "txDescricaoSubElementoDespesa",
    "dotacao_completa",
    "valTotalEmpenhado",
    "valAnuladoEmpenho",
    "valEmpenhadoLiquido",
    "valLiquidado",
    "valPagoExercicio",
    "valPagoRestos",
    "anexos",
    "codReferencia",
    "codDestinacaoRecurso",
    "codVinculacaoRecurso",
    "codExeFonte"
]

if not df_parcial.empty:
    cols_existentes = [col for col in ordem_colunas if col in df_parcial.columns]
    df_parcial = df_parcial[cols_existentes + [col for col in df_parcial.columns if col not in cols_existentes]]

# Primeiro, expanda a coluna "anexos" para dicionários (pegando o primeiro item da lista)
def extrai_anexo(anexos):
    if isinstance(anexos, list) and len(anexos) > 0 and isinstance(anexos[0], dict):
        return anexos[0]
    return {}

# Cria um DataFrame s? com os dados extra?dos
if "anexos" in df_parcial.columns:
    anexos_expandido = df_parcial["anexos"].apply(extrai_anexo).apply(pd.Series)
    anexos_expandido = anexos_expandido.add_prefix("anexo_")
    df_parcial = pd.concat([df_parcial.drop(columns=["anexos"]), anexos_expandido], axis=1)


caminho_arquivo = os.path.join("base_empenhos", f"empenhos_{ano}.xlsx")
df_parcial.to_excel(caminho_arquivo, index=False)
print("feitos os empenhos")
