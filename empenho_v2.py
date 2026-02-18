import pandas as pd
import requests
from datetime import datetime, timezone, timedelta
import pytz
import time
import os

# Configurações iniciais
TOKEN = os.getenv("API_TOKEN_SF")
# TOKEN = ""
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
procv_elemento = pd.read_excel(os.path.join(baseaux_path, "dados_auxiliares", "procv_elemento.xlsx"))

params_emp = {
    "anoEmpenho": "",
    "mesEmpenho": "",
    "numPagina": "",
}	

df_parcial = pd.DataFrame()
requisicoes = 0
requisicao = 0
lista_orgaos = ["08", "34", "78", "90"]

# ano = "2025"
# mes = "12"
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

        params_emp["anoEmpenho"] = ano
        params_emp["mesEmpenho"] = mes
        params_emp["numPagina"] = pagina

        empenhos = fazer_requisicao("empenhos", params=params_emp)

        print("\x1b[F" * 2, end="") # Mover o cursor duas linhas para cima

        if empenhos is None:
            continue

        else:
            df_empenhos = pd.json_normalize(empenhos["lstEmpenhos"])

            dotacao_cols = [
                "codOrgao",
                "codUnidade",
                "codFuncao",
                "codSubFuncao",
                "codPrograma",
                "codProjetoAtividade",
                "codCategoria",
                "codGrupo",
                "codModalidade",
                "codElemento",
            ]

            df_empenhos[dotacao_cols] = df_empenhos[dotacao_cols].apply(
                pd.to_numeric, errors="coerce"
            ).astype("Int64")

            def col_str(col):
                if orgao_api == "08":
                    return "0" + df_empenhos[col].astype("string").fillna("")
                return df_empenhos[col].astype("string").fillna("")

            despesa = (
                col_str("codCategoria")
                + col_str("codGrupo")
                + col_str("codModalidade")
                + col_str("codElemento")
                + "00"
            )

            df_empenhos["codDespesa"] = (despesa)
            
            df_empenhos["dotacao_completa"] = (
                col_str("codOrgao")
                + "."
                + col_str("codUnidade")
                + "."
                + col_str("codFuncao")
                + "."
                + col_str("codSubFuncao")
                + "."
                + col_str("codPrograma")
                + "."
                + col_str("codProjetoAtividade")
                + "."
                + despesa 
                + "."
                + col_str("codFonteRecurso")
            )
            
            fonte_str = df_empenhos["codFonteRecurso"].astype("string").fillna("")

            df_empenhos["Fonte"] = fonte_str.str.slice(0, 2)
            df_empenhos["codExeFonte"] = fonte_str.str.slice(3, 4)
            df_empenhos["codDestinacaoRecurso"] = fonte_str.str.slice(5, 8)
            df_empenhos["codVinculacaoRecurso"] = fonte_str.str.slice(9, 13)

            tz_brasilia = pytz.timezone('America/Sao_Paulo')
            df_empenhos["data_hora_extracao"] = str(datetime.now(tz=tz_brasilia).strftime("%d/%m/%Y %H:%M:%S"))

        df_parcial = pd.concat([df_parcial, df_empenhos], ignore_index=True)
        continue

if not df_parcial.empty:
    df_parcial["codOrgao"] = pd.to_numeric(df_parcial["codOrgao"], errors="coerce").astype("Int64")
    df_parcial["codUnidade"] = pd.to_numeric(df_parcial["codUnidade"], errors="coerce").astype("Int64")
    df_parcial["codProjetoAtividade"] = pd.to_numeric(df_parcial["codProjetoAtividade"], errors="coerce").astype("Int64")
    df_parcial["codDespesa"] = pd.to_numeric(df_parcial["codDespesa"], errors="coerce").astype("Int64")

    codproc = (
        df_parcial["codProcesso"]
        .astype("string")
        .fillna("")
        .str.replace(r"\D", "", regex=True)
    )
    codproc = codproc.str.zfill(16)
    has_codproc = codproc.str.len() == 16
    df_parcial.loc[has_codproc, "codProcesso"] = (
        codproc.str.slice(0, 4)
        + "."
        + codproc.str.slice(4, 8)
        + "/"
        + codproc.str.slice(8, 15)
        + "-"
        + codproc.str.slice(15)
    )

    procv_orgao["cod_orgao"] = pd.to_numeric(procv_orgao["cod_orgao"], errors="coerce").astype("Int64")
    procv_acao["acao"] = pd.to_numeric(procv_acao["acao"], errors="coerce").astype("Int64")
    procv_elemento["num_elemento"] = pd.to_numeric(procv_elemento["num_elemento"], errors="coerce").astype("Int64")

    df_parcial = df_parcial.merge(
        procv_orgao[["cod_orgao", "orgao"]],
        left_on="codOrgao",
        right_on="cod_orgao",
        how="left"
    )

    df_parcial = df_parcial.merge(
        procv_elemento[["num_elemento", "elemento_despesa"]],
        left_on="codDespesa",
        right_on="num_elemento",
        how="left"
    ).rename(columns={"elemento_despesa": "nome_elemento"})

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
    "codDespesa",
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
    "codExeFonte",
    "data_hora_extracao"
]

if not df_parcial.empty:
    cols_existentes = [col for col in ordem_colunas if col in df_parcial.columns]
    df_parcial = df_parcial[cols_existentes + [col for col in df_parcial.columns if col not in cols_existentes]]

# Primeiro, expanda a coluna "anexos" para dicionários (concatenando todos os itens da lista)
def extrai_anexo(anexos):
    if isinstance(anexos, list) and len(anexos) > 0:
        dados_concatenados = {}
        for item in anexos:
            if isinstance(item, dict):
                for k, v in item.items():
                    if v is not None:
                        val_str = str(v)
                        if k in dados_concatenados:
                            dados_concatenados[k] += " | " + val_str
                        else:
                            dados_concatenados[k] = val_str
        return dados_concatenados
    return {}

# Cria um DataFrame s? com os dados extra?dos
if "anexos" in df_parcial.columns:
    anexos_expandido = df_parcial["anexos"].apply(extrai_anexo).apply(pd.Series)
    anexos_expandido = anexos_expandido.add_prefix("anexo_")
    df_parcial = pd.concat([df_parcial.drop(columns=["anexos"]), anexos_expandido], axis=1)


pasta_destino = os.path.join(baseaux_path, "base_empenhos")
os.makedirs(pasta_destino, exist_ok=True)
caminho_arquivo = os.path.join(pasta_destino, f"empenhos_{ano}.csv")
df_parcial.to_csv(caminho_arquivo, index=False, sep=";", encoding="utf-8-sig")
print(f"Feitos os empenhos. Arquivo salvo em: {caminho_arquivo}")
