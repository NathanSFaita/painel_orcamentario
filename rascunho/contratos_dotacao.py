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
        print(f"Resposta inválida da API para {url} com params {params}:")
        print(response.text)
        return None

df_empenhos = pd.read_excel("empenhos_2025.xlsx")

pivot = pd.pivot_table(
    df_empenhos,
    index=["anoContrato", "codProcesso", "dotacao_completa"],
    values=["valEmpenhadoLiquido"],
    aggfunc="sum",
    fill_value=0
).reset_index()

# Calcula o total por dotacao_completa
totais_dotacao = pivot.groupby("codProcesso")["valEmpenhadoLiquido"].sum()
totais_dotacao.index = totais_dotacao.index.astype(str)

# Calcula o total por codProcesso (o "pai")
totais_codprocesso = pivot.groupby("codProcesso")["valEmpenhadoLiquido"].sum()

# Calcula o percentual de cada dotacao_completa dentro do seu codProcesso
pivot["percentual"] = (
    pivot["valEmpenhadoLiquido"] /
    pivot["codProcesso"].map(totais_codprocesso)
)

pivot["percentual"] = pivot["percentual"].round(2)

# Crie um dicionário para mapear (codProcesso, dotacao_completa) -> percentual
pivot["chave"] = pivot["codProcesso"].astype(str) + "|" + pivot["dotacao_completa"].astype(str)
percentual_dict = pivot.set_index("chave")["percentual"].to_dict()

# Indo para as requisições de contratos

requisicao = 0
requisicoes = df_empenhos.shape[0]
print("Total de requisições:", requisicoes)

params_contratos = {
    "anoContrato": "",
    "codContrato": "",
    "numProcesso": "",
    "codOrgao": "",

}

colunas_iniciais = [
    "UO",
    "Funcao",
    "SubFuncao",
    "Programa",
    "ProjAtiv",
    "Despesa",
    "VigenciaMeses",
    "datExtracao",
    "situacaoContrato",
    "valTotal",
    "valMensal",
    "valAnual",
    "valTotal_proporcional",
    "valMensal_proporcional",
    "valAnual_proporcional",
]
df_contratos = pd.DataFrame(columns=colunas_iniciais)

for index, row in df_empenhos.iterrows():
    requisicao += 1
    print("Requisição:", requisicao, "de", requisicoes)
    ano_contrato = row["anoContrato"]
    num_contrato = row["numContrato"]
    cod_empenho = row["codEmpenho"]
    processo = row["codProcesso"]
    dotacao_completa = row["dotacao_completa"]

    funcao = row["codFuncao"]
    subfuncao = row["codSubFuncao"]
    programa = row["codPrograma"]
    proj_ativ = row["codProjetoAtividade"]
    despesa = "".join([
        str(row["codCategoria"]), 
        str(row["codGrupo"]), 
        str(row["codElemento"]), 
        str(row["codModalidade"]),
        "00"
        ])
    
    print("34", "10", funcao, subfuncao, programa, proj_ativ, despesa)

    params_contratos["anoContrato"] = ano_contrato
    #params_contratos["codContrato"] = num_contrato
    params_contratos["numProcesso"] = processo
    print(ano_contrato, num_contrato, cod_empenho)
    if num_contrato == 1378:
        print("Processo 6074202200005773")
        print("\x1b[F" * 2, end="")  # Move o cursor para cima uma linha]
        continue

    contratos = fazer_requisicao("contratos", params=params_contratos)

    print("\x1b[F" * 3, end="")  # Move o cursor para cima uma linha]

    if contratos is None:
        print("Nenhum contrato encontrado para o empenho:", cod_empenho)
        continue
    else:
        df_parcial = pd.json_normalize(contratos["lstContratos"])

        # Adiciona as colunas extras em cada linha retornada

        df_parcial["UO"] = "10"
        df_parcial["Funcao"] = funcao
        df_parcial["SubFuncao"] = subfuncao
        df_parcial["Programa"] = programa
        df_parcial["ProjAtiv"] = proj_ativ
        df_parcial["Despesa"] = despesa
        df_parcial["dotacao_completa"] = dotacao_completa
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

            # Calculo de valores proporcionais
            df_parcial["chave"] = df_parcial["codProcesso"].astype(str) + "|" + df_parcial["dotacao_completa"].astype(str)
            df_parcial["percentual_pivot"] = df_parcial["chave"].map(percentual_dict).fillna(0)  # transforma em fração
            df_parcial["valTotal_proporcional"] = df_parcial["valTotal"] * df_parcial["percentual_pivot"]
            df_parcial["valMensal_proporcional"] = df_parcial["valMensal"] * df_parcial["percentual_pivot"]
            df_parcial["valAnual_proporcional"] = df_parcial["valAnual"] * df_parcial["percentual_pivot"]
            
            df_contratos = pd.concat([df_contratos, df_parcial], ignore_index=True)
            continue

ordem_colunas = [
    "codEmpresa",
    "txtDescricaoOrgao",
    "codOrgao",
    "UO",
    "Funcao",
    "SubFuncao",
    "Programa",
    "ProjAtiv",
    "Despesa",
    "dotacao_completa",
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
    "valTotal_proporcional",
    "valMensal_proporcional",
    "valAnual_proporcional",
    "valTotalEmpenhado",
    "valAnuladoEmpenho",
    "valEmpenhadoLiquido",
    "valLiquidado",
    "valPago",
    "datExtracao"
]

df_contratos = df_contratos.drop_duplicates()
df_contratos = df_contratos[ordem_colunas + [col for col in df_contratos.columns if col not in ordem_colunas]]
df_contratos.to_excel("contratos_dotacao_2025.xlsx", index=False)

print("prontinho")