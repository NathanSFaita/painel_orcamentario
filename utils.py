import os
import pandas as pd
import dash_bootstrap_components as dbc
from dash import html
from datetime import datetime
import pytz

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ======================================================
# CONFIGURAÇÃO DE EXIBIÇÃO (MAPA EXATO DAS SUAS COLUNAS)
# ======================================================
# Esquerda: Nome exato na sua base | Direita: Nome para exibir na tela
# Dicionário para colunas de índice (categorias)
DE_PARA_INDICES_EXECUCAO = {
    "orgao": "Órgão",
    "coordenação": "Coordenação",
    "acao_programatica": "Atividade",
    "projeto_atividade": "Ação",
    "nome_elemento": "Elemento de Despesa",
    "ds_fonte": "Fonte"
}

# Dicionário para colunas de valores
DE_PARA_EXECUCAO = {
    "valOrcadoInicial": "Orçado Inicial",
    "valOrcadoAtualizado": "Orçado Atualizado",
    "valCongelado": "Congelado",
    "valDisponivel": "Disponível",
    "valReservadoLiquido": "Reservado",
    "valEmpenhadoLiquido": "Empenhado",
    "valLiquidado": "Liquidado",
    "valPagoExercicio": "Pago",
    "Saldo de Dotação": "Saldo de Dotação",  # Campo calculado manualmente no dash
    "Saldo de Reserva": "Saldo de Reserva"  # Campo calculado manualmente no dash
}

DE_PARA_INDICES_EMPENHOS = {
    "orgao": "Órgão",
    "codEmpenho": "Nº Empenho",
    "codProcesso": "Processo SEI",
    "coordenacao": "Coordenação",
    "acao_programatica": "Atividade",
    "codVinculacaoRecurso": "Vinculação",
    "codDespesa": "Despesa",
    "nome_elemento": "Elemento de Despesa",
    "txDescricaoFonteRecurso": "Fonte",
    "txtRazaoSocial": "Credor",
    "anexo_descricaoAnexo": "Objeto do Empenho"
}

DE_PARA_EMPENHOS = {
    "valEmpenhadoLiquido": "Empenhado",
    "valLiquidado": "Liquidado",
    "valPagoExercicio": "Pago"
}

# ======================================================
# TRATAMENTO DE DADOS
# ======================================================
def tratar_selecao_todos(valores_novos, valores_antigos):
    """
    Lógica para o comportamento do filtro 'Todos':
    1. Se a lista estiver vazia -> Retorna ["Todos"]
    2. Se selecionou "Todos" (e não estava antes) -> Limpa os outros e deixa só ["Todos"]
    3. Se "Todos" estava selecionado e selecionou outro -> Remove "Todos"
    """
    if valores_antigos is None: valores_antigos = ["Todos"]
    if not valores_novos: return ["Todos"]
    
    if "Todos" in valores_novos:
        if "Todos" not in valores_antigos: # Usuário acabou de clicar em Todos
            return ["Todos"]
        if len(valores_novos) > 1: # Usuário tinha Todos e clicou em outro
            return [x for x in valores_novos if x != "Todos"]
            
    return valores_novos

def formata_moeda(valor):
    try:
        return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except:
        return "R$ 0,00"

# ======================================================
# GERAÇÃO DE COMPONENTES VISUAIS
# ======================================================

descrição_cards = {
    "Orçado Inicial": "Valor aprovado na Lei Orçamentária Anual (LOA).",
    "Orçado Atualizado": "Orçamento inicial ajustado por créditos adicionais, suplementações e reduções.",
    "Disponível": "Saldo livre para empenhos (Disponível = Orçado Atualizado - Reservado - Congelado).",
    "Congelado": "Parcela do orçamento bloqueada pela Secretaria da Fazenda (SF).",
    "Reservado": "Valor reservado para futura contratação.",
    "Empenhado": "Valor comprometido com credores para entrega de bens ou serviços.",
    "Liquidado": "O bem foi entregue ou o serviço foi prestado, e o credor poderá receber o pagamento.",
    "Pago": "Pagamento foi efetivamente realizado ao credor.",
    "Saldo de Dotação": "Diferença entre o valor Disponível e o Reservado.",
    "Saldo de Reserva": "Valor que ainda precisa ser empenhado (Saldo de Reserva = Reservado - Empenhado).",
    "Órgão": "Unidade orçamentária responsável pela despesa.",
    "Coordenação": "Coordenação gestora pela despesa.",
    "Atividade": "Atividade continuada de cada coordenação",
    "Ação": "Código numérico da atividade.",
    "Despesa (Código)": "Código numérico da despesa (ex: 339000 - Serviços de Terceiros - Pessoa Jurídica).",
    "Elemento de Despesa": "Classificação do objeto do gasto orçamentário (ex: material de consumo, serviços de terceiros, etc).",
    "Vinculação": "Código numérico da vinculação.",
    "Fonte": "Indica se a despesa possui ou não alguma vinculação específica (Orçamento Cidadão, Emendas etc.).",
    "Credor": "Nome do fornecedor ou prestador de serviço do empenho.",
    "Nº Empenho": "Número identificador do empenho.",
    "Processo SEI": "Número do processo no Sistema Eletrônico de Informações (SEI) relacionado ao empenho.",
    "Objeto do Empenho": "Descrição do objeto ou serviço contratado no empenho."
}

def monta_cards_resumo(dados_totais, mapa_colunas):
    cards = []

    # Função auxiliar para criar card personalizado
    def criar_card(titulo, valor, cor_fundo="#FFFFFF", cor_texto="#212529", descricao=None):
        elementos_titulo = [
            html.Span(titulo, style={"verticalAlign": "middle"})
        ]

        if descricao:
            # Gera ID único para o tooltip baseado no título
            id_tooltip = f"tooltip-{titulo.replace(' ', '').replace('/', '').lower()}"
            elementos_titulo.append(html.Span(" ℹ️", id=id_tooltip, 
                                              style={"cursor": "help", "fontSize": "0.8em", "marginLeft": "5px", "verticalAlign": "middle", "opacity": "0.7"}))
            elementos_titulo.append(dbc.Tooltip(descricao, target=id_tooltip, placement="top"))

        return dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H6(elementos_titulo, className="card-subtitle mb-2", style={"color": cor_texto, "opacity": "0.9"}),
                    html.H4(formata_moeda(valor), className="card-title", style={"color": cor_texto, "fontWeight": "bold"})
                ])
            ], className="h-100 shadow-sm", style={"backgroundColor": cor_fundo, "border": "none"})
        ], md=3, className="mb-3")

    # Verifica contexto Execução (baseado nas chaves do mapa)
    if "valOrcadoInicial" in mapa_colunas:
        # --- EXECUÇÃO: Definição Manual dos Cards ---
        cards.append(criar_card("Orçado Inicial", dados_totais.get("valOrcadoInicial", 0), 
                                cor_fundo="#6c757d", cor_texto="#FFFFFF", descricao=descrição_cards["Orçado Inicial"]))
        cards.append(criar_card("Orçado Atualizado", dados_totais.get("valOrcadoAtualizado", 0), 
                                cor_fundo="#28a745", cor_texto="#FFFFFF", descricao=descrição_cards["Orçado Atualizado"]))
        cards.append(criar_card("Disponível", dados_totais.get("valDisponivel", 0), 
                                cor_fundo="#007bff", cor_texto="#FFFFFF", descricao=descrição_cards["Disponível"]))
        cards.append(criar_card("Congelado", dados_totais.get("valCongelado", 0), 
                                cor_fundo="#17a2b8", cor_texto="#FFFFFF", descricao=descrição_cards["Congelado"]))
        
        cards.append(criar_card("Reservado", dados_totais.get("valReservadoLiquido", 0), 
                                cor_fundo="#dabd18e2", cor_texto="#FFFFFF", descricao=descrição_cards["Reservado"]))
        cards.append(criar_card("Empenhado", dados_totais.get("valEmpenhadoLiquido", 0), 
                                cor_fundo="#fd7e14", cor_texto="#FFFFFF", descricao=descrição_cards["Empenhado"]))
        cards.append(criar_card("Liquidado", dados_totais.get("valLiquidado", 0), 
                                cor_fundo="#b82e2e", cor_texto="#FFFFFF", descricao=descrição_cards["Liquidado"]))
        cards.append(criar_card("Pago", dados_totais.get("valPagoExercicio", 0), 
                                cor_fundo="#871987", cor_texto="#FFFFFF", descricao=descrição_cards["Pago"]))        
        
        cards.append(criar_card("Saldo de Reserva", dados_totais.get("Saldo de Reserva", 0), 
                                cor_fundo="#af865a", cor_texto="#FFFFFF", descricao=descrição_cards["Saldo de Reserva"]))
        cards.append(criar_card("Saldo de Dotação", dados_totais.get("Saldo de Dotação", 0), 
                                cor_fundo="#198754", cor_texto="#FFFFFF", descricao=descrição_cards["Saldo de Dotação"]))
        
    # Verifica contexto Empenhos
    elif "valEmpenhadoLiquido" in mapa_colunas:
        cards.append(criar_card("Empenhado", dados_totais.get("valEmpenhadoLiquido", 0), 
                                cor_fundo="#fd7e14", cor_texto="#FFFFFF", descricao=descrição_cards["Empenhado"]))
        cards.append(criar_card("Liquidado", dados_totais.get("valLiquidado", 0), 
                                cor_fundo="#b82e2e", cor_texto="#FFFFFF", descricao=descrição_cards["Liquidado"]))
        cards.append(criar_card("Pago", dados_totais.get("valPagoExercicio", 0), 
                                cor_fundo="#871987", cor_texto="#FFFFFF", descricao=descrição_cards["Pago"]))

    else:
        # Fallback para outros casos
        for col, nome in mapa_colunas.items():
            cards.append(criar_card(nome, dados_totais.get(col, 0), cor_fundo="#f8f9fa", cor_texto="#212529", descricao=f"Total acumulado de {nome}"))
            
    return dbc.Row(cards, justify="center")

def gera_card_atualizacao(data_extracao_df):
    # Função ajustada para receber apenas a data do dataframe
    """Gera um card informativo com as datas de atualização."""
    data_exibicao = data_extracao_df if data_extracao_df and data_extracao_df != "-" else "Dados não encontrados"

    return dbc.Card(
        dbc.CardBody([
            dbc.Row([
                dbc.Col(
                    html.Div([
                        html.H6("Data de Atualização", 
                                className="card-subtitle text-muted", 
                                style={"fontSize": "0.9rem"}),
                        html.H5(data_exibicao, 
                                className="card-title", 
                                style={"fontSize": "1.1rem"}),
                        html.H6("Fonte: API-SOF", className="card-subtitle text-muted mt-2")
                    ]),
                    width="auto"
                ),
                dbc.Col(
                    html.Div([
                        html.H5("Desenvolvido pela Coordenadoria de Planejamento e Informação (CPI)", 
                                className="card-title text-end"),
                        html.H6("Dúvidas: (11) 2833-4832 | nsfaita@prefeitura.sp.gov.br", 
                                className="text-muted text-end")
                    ]),
                    width="auto",
                    className="text-end" # Alinha à direita
                )
            ], justify="between", align="center")
        ]),
        className="mb-4",
        color="light",
    )

def gera_tabela_pivot(df, tipo):
    if df.empty: return pd.DataFrame()
    
    # Normaliza nomes de colunas (remove espaços nas pontas)
    df.columns = [c.strip() for c in df.columns]


    if tipo == "execucao":
        # Colunas de Agrupamento (Linhas da Tabela)
        cols_index = list(DE_PARA_INDICES_EXECUCAO.keys())
        # Colunas de Valor
        cols_values = [k for k in DE_PARA_EXECUCAO.keys() if k != "Saldo de Dotação"]
    else:
        # Colunas de Agrupamento Empenhos
        cols_index = list(DE_PARA_INDICES_EMPENHOS.keys())
        cols_values = list(DE_PARA_EMPENHOS.keys())

    # Filtra colunas que realmente existem para evitar erro
    index_validos = [c for c in cols_index if c in df.columns]
    values_validos = [c for c in cols_values if c in df.columns]
    
    if not index_validos: return pd.DataFrame()

    pivot = df.pivot_table(index=index_validos, values=values_validos, aggfunc="sum", fill_value=0).reset_index()
    return pivot

def cabecalho_padrao(titulo, subtitulo):
    return dbc.Row([
        dbc.Col([
            html.Img(src="/assets/smdhc_logo.png", height="100px"),
            html.H2(titulo, className="text-center mb-2 mt-4", style={"color": "#1f77b4", "fontWeight": "bold"}),
            html.H4(subtitulo, className="text-center mb-4", style={"color": "#6c757d"}),
            html.Hr()
        ], className="text-center")
    ])

# ======================================================
# CARREGAMENTO DE ARQUIVOS
# ======================================================
def ler_info_versao():
    """Lê a data de última execução do arquivo version.txt."""
    try:
        version_path = os.path.join(BASE_DIR, "version.txt")
        with open(version_path, "r", encoding="utf-8") as f:
            content = f.read().strip() # ex: ultima_execucao=2026-02-03 13:42:18 UTC
            date_str_utc_full = content.split("=")[1]
            
            # Remove o " UTC" para um parse mais seguro e consistente
            date_str_utc = date_str_utc_full.replace(" UTC", "")
            
            # Converte a string para um objeto datetime "naive" (sem timezone)
            dt_naive = datetime.strptime(date_str_utc, "%Y-%m-%d %H:%M:%S")
            
            # Torna o objeto datetime ciente do seu timezone (UTC)
            dt_utc = pytz.utc.localize(dt_naive)
            
            # Converte para o timezone de Brasília
            tz_brasilia = pytz.timezone('America/Sao_Paulo')
            dt_brasilia = dt_utc.astimezone(tz_brasilia)
            
            # Formata para o padrão brasileiro
            return dt_brasilia.strftime("%d/%m/%Y %H:%M:%S")
    except Exception:
        return "Não disponível"

def lista_meses(base, ano):
    if not ano: return []
    try:
        # A função lista_meses é usada apenas para a base de execução
        pasta = os.path.join(BASE_DIR, "base_despesas", str(ano)) if base == "execucao" else os.path.join(BASE_DIR, "base_empenhos")
        if not os.path.exists(pasta): return []
        arquivos = [f for f in os.listdir(pasta) if f.endswith(".xlsx") and not f.startswith("~$")]
        return sorted([f.replace(f"despesas_{ano}", "").replace(".xlsx", "") for f in arquivos])
    except: return []

def carrega_base(base, ano, mes):
    try:
        if base == "execucao":
            caminho = os.path.join(BASE_DIR, "base_despesas", str(ano), f"despesas_{ano}{mes}.xlsx")
            # Colunas de filtro que podem ser lidas como números, mas devem ser tratadas como texto
            dtype_map = {
                'cd_orgao': str,
                'projeto_atividade': str,
                'despesa': str,
                'vinculacao': str
            }
            if os.path.exists(caminho):
                df = pd.read_excel(caminho, dtype=dtype_map)
            else: df = pd.DataFrame()
        else:
            caminho = os.path.join(BASE_DIR, "base_empenhos", f"empenhos_{ano}.csv")
            # Colunas de filtro que podem ser lidas como números, mas devem ser tratadas como texto
            dtype_map = {
                'codOrgao': str,
                'codUnidade': str,
                'codProjetoAtividade': str,
                'codDespesa': str,
                'codVinculacaoRecurso': str,
                'codEmpenho': str,
                'codProcesso': str,
                'numContrato': str,
                'anoContrato': str
            }
            if os.path.exists(caminho):
                df = pd.read_csv(caminho, sep=';', dtype=dtype_map, low_memory=False)
            else: df = pd.DataFrame()

        if not df.empty:
            # Ajuste de terminologia: Desaparecidas -> Desaparecidos
            for col in ["coordenação", "coordenacao", "acao_programatica"]:
                if col in df.columns:
                    df[col] = df[col].str.replace("Desaparecidas", "Desaparecidos", regex=False)
        
        return df
    except Exception as e:
        print(f"Erro ao carregar base '{base}': {e}")
        return pd.DataFrame()
