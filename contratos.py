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

print("inicio do script")

# Função para fazer requisições à API
def fazer_requisicao(endpoint, params=None):
    url = f"{BASE_URL}/{endpoint}"
    response = requests.get(url, headers=headers, params=params)
    try:
        return response.json()
    except Exception:
        print(f"Resposta inválida da API para {url} com params {params}:")
        print(response.text)
        return None

params_contratos = {
    "anoContrato": "2025",
    "codContrato": "",
    "numProcesso": "",
    "codOrgao": "34 ",
    "numPagina": ""
}

df_empenhos = pd.read_excel("empenhos_2025.xlsx")

# Agrupamento dos anoContrato e codProcesso
anos_contrato = df_empenhos["anoContrato"].unique()
anos_contrato = anos_contrato[anos_contrato != -1]
processos = df_empenhos["codProcesso"].unique()
processos = processos[processos != -1]
anos_problema = []

requisicoes = 0
requisicao = 0

for ano in anos_contrato:
    if ano == 2022:
        continue
    params_contratos["anoContrato"] = ano
    num_pagina = fazer_requisicao("contratos", params=params_contratos)
    if num_pagina is None:
        anos_problema.append(ano)
        continue
    df_paginas = pd.json_normalize(num_pagina["metaDados"])
    requisicoes += df_paginas["qtdPaginas"][0]

print("Total de requisições:", requisicoes)


colunas_iniciais = [
    "VigenciaMeses",
    "datExtracao",
    "situacaoContrato",
    "valTotal",
    "valMensal",
    "valAnual",
]
df_contratos = pd.DataFrame(columns=colunas_iniciais)

anos_contrato = [2025]

for ano in anos_contrato:
    if ano == 2022:
        continue
    requisicao += 1
    print("Requisição:", requisicao, "de", requisicoes)
    ano_contrato = ano
    
    params_contratos["anoContrato"] = ano_contrato
    contratos = fazer_requisicao("contratos", params=params_contratos)
    df_paginas = pd.json_normalize(contratos["metaDados"])
    qtd_paginas = df_paginas["qtdPaginas"][0]

    for pagina in range(1, qtd_paginas + 1):
        params_contratos["numPagina"] = pagina
        params_contratos["anoContrato"] = ano_contrato
        contratos = fazer_requisicao("contratos", params=params_contratos)

        if contratos is None:
            continue

        print("\x1b[F" * 3, end="")
        df_parcial = pd.json_normalize(contratos["lstContratos"])
        
        print("\x1b[F" * 3, end="")  # Move o cursor para cima uma linha]
        # Adiciona as colunas extras em cada linha retornada
        df_parcial["datExtracao"] = datetime.now().strftime("%d-%m-%Y")

        # Verifica se o valor principal é igual ao anulado e exclui a linha se for o caso
        if "valPrincipal" in df_parcial.columns and "valAnulacao" in df_parcial.columns:
            df_parcial = df_parcial[df_parcial["valPrincipal"] != df_parcial["valAnulacao"]]

        # Só prossiga se df_parcial não estiver vazio
        if not df_parcial.empty:
            # Calcula a vigência em meses e situação do contrato
            if (
                "datVigencia" in df_parcial.columns and
                "datAssinaturaContrato" in df_parcial.columns and
                pd.notna(df_parcial["datVigencia"].iloc[0]) and
                pd.notna(df_parcial["datAssinaturaContrato"].iloc[0])
            ):
                vigencia = df_parcial["datVigencia"].iloc[0]
                assinatura = df_parcial["datAssinaturaContrato"].iloc[0]
                vigencia = datetime.strptime(str(vigencia), "%d/%m/%Y %H:%M:%S")
                assinatura = datetime.strptime(str(assinatura), "%d/%m/%Y %H:%M:%S")
                meses = int((vigencia - assinatura).days / 30)
                df_parcial["VigenciaMeses"] = meses

                # Situação do contrato
                data_extracao = datetime.strptime(df_parcial["datExtracao"].iloc[0], "%d-%m-%Y")
                if vigencia > data_extracao:
                    df_parcial["situacaoContrato"] = "Vigente"
                else:
                    df_parcial["situacaoContrato"] = "Encerrado"
            else:
                df_parcial["VigenciaMeses"] = 12
                df_parcial["situacaoContrato"] = "Desconhecida"

            # Calculo de valores
            df_parcial["valTotal"] = (
                df_parcial.get("valPrincipal", 0)
                + df_parcial.get("valReajustes", 0)
                + df_parcial.get("valAditamentos", 0)
                - df_parcial.get("valAnulacao", 0)
            )

            if df_parcial["VigenciaMeses"].iloc[0] < 12:
                df_parcial["valMensal"] = df_parcial["valTotal"] / 12
                df_parcial["valAnual"] = df_parcial["valMensal"] * 12
            else:
                df_parcial["valMensal"] = df_parcial["valTotal"] / df_parcial["VigenciaMeses"]
                df_parcial["valAnual"] = df_parcial["valMensal"] * 12
            
            if ano != 2025:
                # Filtra os contratos que possuem o código do processo presente na lista de processos
                df_parcial = df_parcial[df_parcial["codProcesso"].isin(processos)]
            df_contratos = pd.concat([df_contratos, df_parcial], ignore_index=True)

ordem_colunas = [
    "codEmpresa",
    "codOrgao",
    "txtDescricaoOrgao",
    "codTipoContratacao",
    "txtTipoContratacao",
    "codModalidade",
    "txtDescricaoModalidade",
    "anoContrato",
    "codContrato",
    "numOriginalContrato",
    "codProcesso",
    "txtObjetoContrato",
    "datAssinaturaContrato",
    "datPublicacaoContrato",
    "datVigencia",
    "VigenciaMeses",
    "situacaoContrato",
    "valPrincipal",
    "valReajustes",
    "valAditamentos",
    "valAnulacao",
    "valTotal",
    "valMensal",
    "valAnual",
    "valTotalEmpenhado",
    "valAnuladoEmpenho",
    "valEmpenhadoLiquido",
    "valLiquidado",
    "valPago",
    "datExtracao"
]

#df_contratos = df_contratos.drop_duplicates()
df_contratos = df_contratos[ordem_colunas + [col for col in df_contratos.columns if col not in ordem_colunas]]
df_contratos.to_excel("contratos_2025.xlsx", index=False)

print("prontinho")