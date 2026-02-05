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

        nome_orgao = procv_orgao.loc[procv_orgao["cod_orgao"] == int(orgao), "orgao"].values
        df_empenhos["orgao"] = nome_orgao[0]
        if uo == "20":
            df_empenhos["orgao"] = "FUMCAF"

        if int(proj_ativ) < 8000:
            coordenacao = procv_acao.loc[procv_acao["acao"] == proj_ativ, "coordenadoria"].values
            politicas_para = procv_acao.loc[procv_acao["acao"] == proj_ativ, "politicas_para"].values
            acao = procv_acao.loc[procv_acao["acao"] == proj_ativ, "acao_programatica"].values
            # Corrige para garantir valor padrão
            if len(coordenacao) > 0:
                coordenacao_val = coordenacao[0]
            else:
                coordenacao_val = "Não encontrado"

            if len(politicas_para) > 0:
                politicas_para_val = politicas_para[0]
            else:
                politicas_para_val = "Não encontrado"

            if len(acao) > 0:
                acao_val = acao[0]
            else:
                acao_val = "Não encontrado"
                
            df_empenhos["coordenacao"] = coordenacao_val
            df_empenhos["politicas_para"] = politicas_para_val
            df_empenhos["acao_programatica"] = acao_val

        else:
            coordenacao_val = "Emenda"
            politicas_para_val = "Emenda"
            acao_val = "Emenda"

        df_parcial = pd.concat([df_parcial, df_empenhos], ignore_index=True)
        continue

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

# Cria um DataFrame só com os dados extraídos
anexos_expandido = df_parcial["anexos"].apply(extrai_anexo).apply(pd.Series)

# Renomeia as colunas para evitar conflitos
anexos_expandido = anexos_expandido.add_prefix("anexo_")

# Junta ao DataFrame original (removendo a coluna "anexos" se quiser)
df_parcial = pd.concat([df_parcial.drop(columns=["anexos"]), anexos_expandido], axis=1)

caminho_arquivo = os.path.join("base_empenhos", f"empenhos_{ano}.xlsx")
df_parcial.to_excel(caminho_arquivo, index=False)
print("feitos os empenhos")
