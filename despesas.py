import requests
import pandas as pd
from itertools import product
import time
from datetime import datetime, timedelta, timezone
import pytz
import os


def main():
    BASE_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    BASE_DESPESAS = os.path.join(BASE_PATH, "base_despesas")

    # Defina o timezone de Brasília
    tz_brasilia = pytz.timezone('America/Sao_Paulo')
    
    inicio = time.time()
    horario_inicio = datetime.now(tz=tz_brasilia).strftime("%H:%M:%S")
    print("Início da execução:", horario_inicio)

    dt_inicio = datetime.fromtimestamp(inicio, tz=tz_brasilia)
    ano = str(dt_inicio.year)
    mes = str(dt_inicio.month)

    # Configurações iniciais
    #TOKEN = ""
    TOKEN = os.getenv("API_TOKEN_SF")
    print("TOKEN carregado?", bool(TOKEN))
    print("Primeiros 6 chars do token:", TOKEN[:6] if TOKEN else "NULO")

    BASE_URL = "https://gateway.apilib.prefeitura.sp.gov.br/sf/sof/v4/"

    # Headers para autenticação
    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "Content-Type": "application/json"
    }

    if dt_inicio.month < 10:
        mes = "0" + mes  # Adiciona zero à esquerda se o mês for menor que 10

    URL_ORC = (f"https://orcamento.sf.prefeitura.sp.gov.br/orcamento/uploads/{ano}/basedadosexecucao_{mes}{ano[2:]}.xlsx")

    orgaos_list = [8, 34, 78, 90]

    orcamento = pd.read_excel(URL_ORC)
    orcamento_smdhc = orcamento[orcamento["Cd_Orgao"].isin(orgaos_list)]
    num_linhas = orcamento_smdhc.shape[0]

    baseaux_path = os.path.dirname(__file__)
    procv_acao = pd.read_excel(os.path.join(baseaux_path, "dados_auxiliares", "procv_acoes.xlsx"))
    procv_orgao = pd.read_excel(os.path.join(baseaux_path, "dados_auxiliares", "procv_orgao.xlsx"))
    procv_elemento = pd.read_excel(os.path.join(baseaux_path, "dados_auxiliares", "procv_elemento.xlsx"))

    # Função para fazer requisições à API
    def fazer_requisicao(endpoint, params):
        url = f"{BASE_URL}/{endpoint}"

        response = requests.get(
            url,
            params=params,
            headers=headers,
            timeout=60
        )

        print(f"[{endpoint}] Status code:", response.status_code)

        if response.status_code != 200:
            print("Resposta não-200 da API:")
            print(response.text[:1000])
            raise Exception(f"Erro HTTP {response.status_code}")

        # Proteção TOTAL contra resposta vazia ou não-JSON
        if not response.text or response.text.strip() == "":
            print("Resposta vazia da API")
            raise Exception("Resposta vazia da API")

        try:
            return response.json()
        except Exception:
            print("Falha ao converter resposta em JSON")
            print(response.text[:1000])
            raise



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

    colunas_iniciais = ["cd_orgao", "orgao", "uo", "funcao", "subfuncao", "programa", "projeto_atividade", "coordenação", "despesa", "vinculacao"]
    df_final = pd.DataFrame(columns=colunas_iniciais)
    requisicoes = 0

    for index, row in orcamento_smdhc.iterrows():
        orgao = str(row["Cd_Orgao"])
        if len(orgao) == 1:
            orgao = "0" + str(orgao)  # Padroniza o órgão para dois dígitos
        uo = str(row["Cd_Unidade"])
        funcao = str(row["Cd_Funcao"])
        if len(funcao) == 1:
            funcao = "0" + str(funcao)  # Padroniza a função para dois dígitos
        subfuncao = row["Cd_SubFuncao"]
        programa = row["Cd_Programa"]
        proj_ativ = int(row["ProjetoAtividade"])
        categoria = str(row["Categoria_Despesa"])
        grupo = str(row["Grupo_Despesa"])
        modalidade = str(row["Cd_Modalidade"])
        elemento = str(row["Cd_Elemento"])
        fonte = str(row["Cd_Fonte"])
        ds_vinculacao = str(row["TXT_VINC_PMSP"])
        if len(fonte) < 2:
            fonte = ("0" * (2 - len(fonte))) + fonte
        referencia = str(row["COD_EX_FONT_REC"])
        destinacao = str(row["COD_DSTN_REC"])
        if len(destinacao) < 3:
            destinacao = ("0" * (3 - len(destinacao))) + destinacao    
        vinculacao = str(row["COD_VINC_REC_PMSP"])
        if len(vinculacao) < 4:
            vinculacao = ("0" * (4 - len(vinculacao))) + vinculacao
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
        params_dp["codFonteRecurso"] = fonte
        params_dp["codReferencia"] = referencia
        params_dp["codDestinacaoRecurso"] = destinacao
        params_dp["codVinculacaoRecurso"] = vinculacao

        inicio_requisicao = time.time()
        despesas = fazer_requisicao("despesas", params=params_dp)
        requisicoes += 1
        fim_requisicao = time.time()

        tempo_medio = (fim_requisicao - inicio) / requisicoes

        df_despesas = pd.json_normalize(despesas["lstDespesas"])
        
        porcentagem = (requisicoes / num_linhas) * 100
        requisicoes_restantes = num_linhas - requisicoes
        
        tempo_restante = (tempo_medio * requisicoes_restantes)
        horas_restantes, resto = divmod(tempo_restante, 3600)
        minutos, segundos = divmod(resto, 60)

        horario_termino = datetime.now(tz=tz_brasilia) + timedelta(seconds=tempo_restante)
        horario_termino_str = horario_termino.strftime("%H:%M:%S")
        
        print(
            f"Requisição {requisicoes} de {num_linhas} - {porcentagem:.2f}% concluído ")
        print(
            f"Tempo restante estimado: {int(horas_restantes)} horas, {int(minutos)} minutos e {int(segundos)} segundos ")
        print(
            f"Previsão de término: {horario_termino_str} ", end=""
        )
        print("\x1b[F" * 2, end="")  # Move o cursor para cima uma linha]
        
        if proj_ativ < 8000:
            coordenacao = procv_acao.loc[procv_acao["acao"] == proj_ativ, "coordenadoria"].values
            politicas_para = procv_acao.loc[procv_acao["acao"] == proj_ativ, "politicas_para"].values
            # Corrige para garantir valor padrão
            if len(coordenacao) > 0:
                coordenacao_val = coordenacao[0]
            else:
                coordenacao_val = "Não encontrado"
            if len(politicas_para) > 0:
                politicas_para_val = politicas_para[0]
            else:
                politicas_para_val = "Não encontrado"
        else:
            coordenacao_val = "Emenda"
            politicas_para_val = "Emenda"

        elemento_despesa = categoria + grupo + modalidade + elemento + "00"
        nome_elemento = procv_elemento.loc[procv_elemento["num_elemento"] == int(elemento_despesa), "elemento_despesa"].values

        df_despesas["cd_orgao"] = orgao
        
        nome_orgao = procv_orgao.loc[procv_orgao["cod_orgao"] == int(orgao), "orgao"].values
        df_despesas["orgao"] = nome_orgao[0]
        if uo == "20":
            df_despesas["orgao"] = "FUMCAF"
        df_despesas["uo"] = uo
        df_despesas["funcao"] = funcao
        df_despesas["subfuncao"] = subfuncao
        df_despesas["programa"] = programa
        df_despesas["projeto_atividade"] = proj_ativ
        df_despesas["coordenação"] = coordenacao_val
        df_despesas["politicas_para"] = politicas_para_val
        df_despesas["despesa"] = elemento_despesa
        df_despesas["vinculacao"] = vinculacao
        df_despesas["ds_fonte"] = ds_vinculacao

        # Corrige o erro de atribuição
        if len(nome_elemento) > 0:
            df_despesas["nome_elemento"] = nome_elemento[0]
        else:
            df_despesas["nome_elemento"] = "Não encontrado"


    # busca da fonte de recursos
        
        # fonte_recursos = f"{fonte}.{referencia}.{destinacao}.{vinculacao}"

        # if fonte_recursos == "00.1.500.9001":
        #     df_despesas["ds_fonte"] = "Recursos não vinculados de Impostos"
        # else:
        #     params_fonte = {
        #         "anoExercicio": ano,
        #         "codFonteRecurso": fonte,
        #         "codReferencia": referencia,
        #         "codDestinacaoRecurso": destinacao,
        #         "codVinculacaoRecurso": vinculacao
        #     }
        #     fonte_recursos_response = fazer_requisicao("fonteRecursos", params=params_fonte)
        #     df_fonte = pd.json_normalize(fonte_recursos_response["lstFonteRecurso"])
            
        #     # Validação e tratamento de erro
        #     if df_fonte.empty:
        #         print(f"Aviso: Resposta vazia para fonte_recursos={fonte_recursos}")
        #         df_despesas["ds_fonte"] = "Não encontrado"
        #     elif "txtDescricaoFonteRecurso" not in df_fonte.columns:
        #         print(f"Aviso: Coluna 'txtDescricaoFonteRecurso' não encontrada")
        #         print(f"Colunas disponíveis: {list(df_fonte.columns)}")
        #         df_despesas["ds_fonte"] = "Não encontrado"
        #     else:
        #         df_despesas["ds_fonte"] = df_fonte["txtDescricaoFonteRecurso"].iloc[0]


        df_final = pd.concat([df_final, df_despesas], ignore_index=True)

    ordem_colunas =     [
        "orgao",
        "cd_orgao",
        "uo",
        "funcao",
        "subfuncao",
        "programa",
        "projeto_atividade",
        "despesa",
        "vinculacao",
        "ds_fonte",
        "coordenação",
        "politicas_para",
        "nome_elemento",
        "valOrcadoInicial",
        "valSuplementado",
        "valReduzido",
        "valOrcadoAtualizado",
        "valCongelado",
        "valDescongelado",
        "valDisponivel",
        "valReservado",
        "valCanceladoReserva",
        "valReservadoLiquido",
        "valTotalEmpenhado",
        "valAnuladoEmpenho",
        "valEmpenhadoLiquido",
        "valLiquidado",
        "valPagoExercicio",
        "valPagoRestos",
        "modifiedMode",
        "usuarioOperacao"    
    ]

    # Adiciona a coluna com data e hora da extração
    df_final["data_hora_extracao"] = str(datetime.now(tz=tz_brasilia).strftime("%d/%m/%Y %H:%M:%S"))
   
    # ✅ CORRIGIDO: Filtra apenas colunas que existem
    colunas_existentes = [col for col in ordem_colunas if col in df_final.columns]
    colunas_existentes.append("data_hora_extracao")
    
    df_final = df_final.drop_duplicates()

    # Antes de salvar, crie a pasta do ano se não existir
    pasta_ano = os.path.join(BASE_DESPESAS, ano)
    os.makedirs(pasta_ano, exist_ok=True)

    # Agora salve o arquivo normalmente
    df_final.to_excel(
    os.path.join(pasta_ano, f"despesas_{ano}{mes}.xlsx"),
    index=False
    )

    print(f"Dados salvos em despesas_{ano}{mes}.xlsx")

    fim = time.time()
    horario_fim = datetime.now(tz=tz_brasilia).strftime("%H:%M:%S")
    print("Fim da execução:", horario_fim)
    tempo_total = fim - inicio
    minutos, segundos = divmod(tempo_total, 60)

    print(f"Total de requisições: {requisicoes}")
    print(f"Tempo total de execução: {int(minutos)} minutos e {int(segundos)} segundos")
    pass

if __name__ == "__main__":
    main()