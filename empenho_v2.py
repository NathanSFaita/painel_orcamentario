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


params_emp = {
    "anoEmpenho": "",
    "mesEmpenho": "",
    "numPagina": "",
}	

df_parcial = pd.DataFrame()
requisicao = 0

params_emp["anoEmpenho"] = ano
params_emp["mesEmpenho"] = mes
#params_emp["codOrgao"] = 34
#params_emp["codUnidade"] = 10
ano = "2025"
mes = "12"
num_pagina = fazer_requisicao("empenhos", params=params_emp)
df_paginas = pd.json_normalize(num_pagina["metaDados"])
requisicoes = df_paginas["qtdPaginas"][0]

print("Total de requisições:", requisicoes)

for i in range(requisicoes):
    requisicao += 1
    print("Requisição:", requisicao, "de", requisicoes)
    
    params_emp["anoEmpenho"] = ano
    params_emp["mesEmpenho"] = mes
    params_emp["numPagina"] = requisicao

    empenhos = fazer_requisicao("empenhos", params=params_emp)

    print("\x1b[F" * 1, end="") # Mover o cursor duas linhas para cima

    if empenhos is None:
        continue

    else:
        df_empenhos = pd.json_normalize(empenhos["lstEmpenhos"])

        orgao = df_empenhos["codOrgao"][0]
        uo = df_empenhos["codUnidade"][0]
        funcao = df_empenhos["codFuncao"][0]
        subfuncao = df_empenhos["codSubFuncao"][0]
        programa = df_empenhos["codPrograma"][0]
        proj_ativ = df_empenhos["codProjetoAtividade"][0]
        despesa = "".join([
            str(df_empenhos["codCategoria"][0]), 
            str(df_empenhos["codGrupo"][0]), 
            str(df_empenhos["codModalidade"][0]), 
            str(df_empenhos["codElemento"][0]),
            "00"
        ])
        df_empenhos["dotacao_completa"] = "".join([
            str(orgao),
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

df_parcial = df_parcial[ordem_colunas + [col for col in df_parcial.columns if col not in ordem_colunas]]

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

df_parcial.to_excel(f"empenhos_{ano}.xlsx", index=False)
print("feitos os empenhos")