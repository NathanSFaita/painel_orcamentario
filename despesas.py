import requests
import pandas as pd
from io import BytesIO
from itertools import product
import time
from datetime import datetime, timedelta, timezone
import pytz
import os
import sys

from relatorio_mensal import gerar_pdf_resumo
from utils import tratar_dotacao_rigoroso


def baixar_excel_com_retry(url, tentativas=5, espera=10):
    """
    Baixa um arquivo Excel por HTTP com tentativas automáticas
    para erros temporários do servidor.
    """

    headers_download = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/131.0 Safari/537.36"
        )
    }

    for tentativa in range(1, tentativas + 1):

        print(
            f"Baixando arquivo de orçamento "
            f"(tentativa {tentativa}/{tentativas})..."
        )

        try:
            response = requests.get(
                url,
                headers=headers_download,
                timeout=120
            )

            print(
                f"Resposta do servidor: "
                f"{response.status_code}"
            )

            if response.status_code == 200:

                if not response.content:
                    raise RuntimeError(
                        "O servidor respondeu 200, "
                        "mas o arquivo está vazio."
                    )

                print(
                    f"Arquivo baixado: "
                    f"{len(response.content) / 1024 / 1024:.2f} MB"
                )

                return pd.read_excel(
                    BytesIO(response.content)
                )

            # Erros temporários
            if response.status_code in (502, 503, 504):

                if tentativa < tentativas:
                    print(
                        f"Erro temporário HTTP "
                        f"{response.status_code}. "
                        f"Tentando novamente em {espera}s..."
                    )

                    time.sleep(espera)
                    continue

                raise RuntimeError(
                    f"Servidor retornou HTTP "
                    f"{response.status_code} após "
                    f"{tentativas} tentativas."
                )

            # Outros erros HTTP
            response.raise_for_status()

        except requests.RequestException as e:

            print(
                f"Erro de conexão ao baixar "
                f"o arquivo: {e}"
            )

            if tentativa < tentativas:

                print(
                    f"Tentando novamente em {espera}s..."
                )

                time.sleep(espera)

            else:
                raise

    raise RuntimeError(
        "Falha inesperada ao baixar o arquivo."
    )


def main():

    BASE_PATH = os.path.dirname(
        os.path.abspath(__file__)
    )

    BASE_DESPESAS = os.path.join(
        BASE_PATH,
        "base_despesas"
    )

    print("BASE_DESPESAS:", BASE_DESPESAS)

    tz_brasilia = pytz.timezone(
        "America/Sao_Paulo"
    )

    inicio = time.time()

    horario_inicio = datetime.now(
        tz=tz_brasilia
    ).strftime("%H:%M:%S")

    print(
        "Início da execução:",
        horario_inicio
    )

    dt_inicio = datetime.now(
        tz=tz_brasilia
    )

    ano = str(dt_inicio.year)

    mes = str(dt_inicio.month).zfill(2)

    TOKEN = os.getenv("API_TOKEN_SF")

    print(
        "TOKEN carregado?",
        bool(TOKEN)
    )

    if not TOKEN:
        raise RuntimeError(
            "A variável de ambiente "
            "API_TOKEN_SF não está configurada."
        )

    BASE_URL = (
        "https://gateway.apilib.prefeitura.sp.gov.br/"
        "sf/sof/v4"
    )

    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "Content-Type": "application/json"
    }

    # ==========================================
    # ARQUIVO-BASE DO ORÇAMENTO
    # ==========================================

    URL_ORC = (
        f"https://prefeitura.sp.gov.br/"
        f"cidade/secretarias/upload/seplan/arquivos/"
        f"Exercicio_{ano}/"
        f"basedadosexecucao_{ano}.xlsx"
    )

    print(
        "Arquivo-base do orçamento:",
        URL_ORC
    )

    orcamento = baixar_excel_com_retry(
        URL_ORC
    )

    print(
        "Arquivo de orçamento carregado."
    )

    # ==========================================
    # FILTRO DOS ÓRGÃOS
    # ==========================================

    orgaos_list = [
        8,
        34,
        78,
        90
    ]

    orcamento_smdhc = orcamento[
        orcamento["Cd_Orgao"].isin(
            orgaos_list
        )
    ].copy()

    num_linhas = (
        orcamento_smdhc.shape[0]
    )

    print(
        f"Linhas de orçamento da SMDHC: "
        f"{num_linhas}"
    )

    # ==========================================
    # ARQUIVOS AUXILIARES
    # ==========================================

    baseaux_path = os.path.dirname(
        __file__
    )

    procv_acao = pd.read_excel(
        os.path.join(
            baseaux_path,
            "dados_auxiliares",
            "procv_acoes.xlsx"
        )
    )

    procv_orgao = pd.read_excel(
        os.path.join(
            baseaux_path,
            "dados_auxiliares",
            "procv_orgao.xlsx"
        )
    )

    procv_elemento = pd.read_excel(
        os.path.join(
            baseaux_path,
            "dados_auxiliares",
            "procv_elemento.xlsx"
        )
    )

    procv_fonte = pd.read_excel(
        os.path.join(
            baseaux_path,
            "dados_auxiliares",
            "procv_fonte.xlsx"
        )
    )

    # ==========================================
    # API
    # ==========================================

    def fazer_requisicao(endpoint, params):

        url = f"{BASE_URL}/{endpoint}"

        try:

            response = requests.get(
                url,
                params=params,
                headers=headers,
                timeout=60
            )

        except Exception as e:

            print(
                f"Erro na requisição HTTP: {e}"
            )

            sys.exit(1)

        print(
            f"[{endpoint}] Status code:",
            response.status_code
        )

        if response.status_code != 200:

            print(
                "Resposta não-200 da API:"
            )

            print(
                response.status_code,
                response.text[:1000]
            )

            sys.exit(1)

        if (
            not response.text
            or response.text.strip() == ""
        ):

            print(
                "Resposta vazia da API"
            )

            sys.exit(1)

        try:

            payload = response.json()

        except Exception:

            print(
                "Falha ao converter "
                "resposta em JSON"
            )

            print(
                response.text[:1000]
            )

            sys.exit(1)

        return payload

    # ==========================================
    # PROJETOS / ATIVIDADES
    # ==========================================

    params_proj = {
        "anoExercicio": ano
    }

    proj_atividades = fazer_requisicao(
        "projetosAtividades",
        params_proj
    )

    df_proj = pd.json_normalize(
        proj_atividades[
            "lstProjetosAtividades"
        ]
    )

    if (
        not df_proj.empty
        and "codProjetoAtividade"
        in df_proj.columns
    ):

        df_proj[
            "codProjetoAtividade"
        ] = pd.to_numeric(
            df_proj[
                "codProjetoAtividade"
            ],
            errors="coerce"
        )

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
        "codFonteRecurso": "",
        "codVinculacaoRecurso": "",  
        # Outros parâmetros podem ser adicionados para filtrar
    }

    colunas_iniciais = ["cd_orgao", "orgao", "uo", "funcao", "subfuncao", 
                        "programa", "projeto_atividade", "coordenação", "despesa", "fonte", "vinculacao"]
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
        print("\x1b[F" * 4, end="")  # Move o cursor para cima uma linha]
        
        if proj_ativ < 8000:
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
        else:
            coordenacao_val = "Emenda"
            politicas_para_val = "Emenda"
            # Busca segura para evitar erro de array vazio
            temp_acao = df_proj.loc[df_proj["codProjetoAtividade"] == proj_ativ, "txtDescricaoProjetoAtividade"].values
            if len(temp_acao) > 0:
                acao_val = temp_acao[0]
            else:
                acao_val = "Emenda Parlamentar"

        elemento_despesa = categoria + grupo + modalidade + elemento + "00"
        nome_elemento = procv_elemento.loc[procv_elemento["num_elemento"] == int(elemento_despesa), "elemento_despesa"].values

        desc_fonte = procv_fonte.loc[procv_fonte["cd_fonte"] == int(fonte), "ds_fonte"].values
        desc_fonte = fonte + " - " + (desc_fonte[0] if len(desc_fonte) > 0 else "Não encontrado")

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
        df_despesas["projeto_atividade"] = str(proj_ativ)
        df_despesas["coordenação"] = coordenacao_val
        df_despesas["politicas_para"] = politicas_para_val
        df_despesas["acao_programatica"] = acao_val
        df_despesas["despesa"] = elemento_despesa
        df_despesas["fonte"] = fonte
        df_despesas["fonte_descricao"] = desc_fonte
        df_despesas["vinculacao"] = vinculacao
        #df_despesas["ds_fonte"] = ds_vinculacao

        # Corrige o erro de atribuição
        if len(nome_elemento) > 0:
            df_despesas["nome_elemento"] = nome_elemento[0]
        else:
            df_despesas["nome_elemento"] = "Não encontrado"


    # busca da fonte de recursos
        
        fonte_recursos = f"{fonte}.{referencia}.{destinacao}.{vinculacao}"


        params_fonte = {
            "anoExercicio": ano,
            "codFonteRecurso": fonte,
            "codReferencia": referencia,
            "codDestinacaoRecurso": destinacao,
            "codVinculacaoRecurso": vinculacao
            }
        fonte_recursos_response = fazer_requisicao("fonteRecursos", params=params_fonte)
        df_fonte = pd.json_normalize(fonte_recursos_response["lstFonteRecurso"])
        
        # Validação e tratamento de erro
        if df_fonte.empty:
            df_despesas["ds_fonte"] = "Não encontrado"
        elif "txtDescricaoFonteRecurso" not in df_fonte.columns:
            df_despesas["ds_fonte"] = "Não encontrado"
        else:
            df_despesas["ds_fonte"] = df_fonte["txtDescricaoFonteRecurso"].iloc[0]

        # Cria a coluna de dotação completa para servir como chave
        df_despesas["dotacao_completa"] = (
            str(orgao) + "." +
            str(uo) + "." +
            str(funcao) + "." +
            str(subfuncao) + "." +
            str(programa) + "." +
            str(proj_ativ) + "." +
            str(elemento_despesa) + "." +
            str(fonte_recursos)
        )


        df_final = pd.concat([df_final, df_despesas], ignore_index=True)
        time.sleep(0.2)  # Pequena pausa para evitar sobrecarga na API

    # Garante que a dotação completa esteja no formato padrão
    if not df_final.empty and 'dotacao_completa' in df_final.columns:
        df_final['dotacao_completa'] = df_final['dotacao_completa'].apply(tratar_dotacao_rigoroso)

    ordem_colunas =     [
        "orgao",
        "dotacao_completa",
        "cd_orgao",
        "uo",
        "funcao",
        "subfuncao",
        "programa",
        "projeto_atividade",
        "despesa",
        "fonte",
        "fonte_descricao",
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
    
    # Define as colunas que identificam uma linha única para remover duplicatas
    colunas_chave = [
        "cd_orgao", "uo", "funcao", "subfuncao", "programa", 
        "projeto_atividade", "despesa", "vinculacao"
    ]
    # Remove duplicatas com base nas colunas que definem uma dotação orçamentária
    df_final = df_final.drop_duplicates()

    # Antes de salvar, crie a pasta do ano se não existir
    pasta_ano = os.path.join(BASE_DESPESAS, ano)
    os.makedirs(pasta_ano, exist_ok=True)

    # Agora salve o arquivo normalmente
    caminho_despesas = os.path.join(pasta_ano, f"despesas_{ano}{mes}.xlsx")
    df_final.to_excel(caminho_despesas, index=False)
    
    print(f"Dados salvos em {caminho_despesas}")

    # Gera o relatório resumido em PDF diariamente após a criação da base
    print("\nIniciando geração do relatório PDF resumido...")
    if not df_final.empty:
        gerar_pdf_resumo(df_final, ano, mes) # output_dest='F' (salvar em arquivo) é o padrão
    else:
        print("DataFrame final vazio, PDF resumido não gerado.")

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
