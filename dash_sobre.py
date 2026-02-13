import dash_bootstrap_components as dbc
from dash import html, Input, Output, State, dash_table
import pandas as pd
import os
from utils import cabecalho_padrao, descrição_cards, BASE_DIR

def layout_sobre():
    # Gera os itens do glossário dinamicamente a partir do dicionário existente
    itens_glossario = []
    for termo, definicao in descrição_cards.items():
        item = dbc.ListGroupItem([
            html.Div([
                html.H5(termo, className="mb-1 text-primary"),
                html.P(definicao, className="mb-1 text-muted")
            ], className="d-flex w-100 justify-content-between flex-column")
        ])
        itens_glossario.append(item)

    # Carregamento das tabelas auxiliares
    try:
        df_acoes = pd.read_excel(os.path.join(BASE_DIR, "dados_auxiliares", "procv_acoes.xlsx"))
    except Exception:
        df_acoes = pd.DataFrame()

    try:
        df_elementos = pd.read_excel(os.path.join(BASE_DIR, "dados_auxiliares", "procv_elemento.xlsx"))
    except Exception:
        df_elementos = pd.DataFrame()

    # Mapas para renomear as colunas (ID do Excel -> Nome na Tela)
    mapa_acoes = {
        "acao": "Cód. Ação",
        "coordenadoria": "Coordenação",
        "politicas_para": "Descrição da Coordenação",
        "acao_programatica": "Atividade"
    }

    mapa_elementos = {
        "num_elemento": "Cód. Elemento",
        "elemento_despesa": "Descrição do Elemento"
    }

    return dbc.Container([
        cabecalho_padrao("📚 Informações e Glossário", "Entenda os termos do Orçamento"),
        
        dbc.Row([
            dbc.Col([
                dbc.Button("⬅️ Voltar para Execução", href="/", color="secondary", className="mb-4 me-2"),
                dbc.Button("Ir para Empenhos ➡️", href="/empenhos", color="primary", className="mb-4"),
            ], width=12, className="d-flex justify-content-center gap-2")
        ]),

        html.Hr(),

        dbc.Card([
            dbc.CardHeader(
                html.Div([
                    html.H5("Sobre este Painel", className="m-0"),
                    dbc.Button("➖/➕", id="btn-collapse-sobre", color="link", size="sm", className="text-decoration-none ms-2", n_clicks=1)
                ], className="d-flex align-items-center")
            ),
            dbc.Collapse(
                dbc.CardBody([
                    html.P(
                        "Este painel foi desenvolvido para fornecer uma visão clara e acessível sobre a" \
                        " execução orçamentária da Secretaria Municipal de Direitos Humanos e Cidadania (SMDHC). "
                        "Aqui você pode explorar os dados de despesas, empenhos e entender os " \
                        "termos técnicos utilizados no contexto orçamentário.",
                        className="card-text"
                    ),
                    html.P(
                        "Os dados apresentados são atualizados diariamente, refletindo as informações mais recentes disponíveis. ",
                        className="card-text"
                    )
                ]),
                id="collapse-sobre", is_open=True
            )
        ], className="shadow-sm mb-5"),

        dbc.Card([
            dbc.CardHeader(
                html.Div([
                    html.H5("Sobre o Orçamento", className="m-0"),
                    dbc.Button("➖/➕", id="btn-collapse-orcamento", color="link", size="sm", className="text-decoration-none ms-2", n_clicks=1)
                ], className="d-flex align-items-center")
            ),
            dbc.Collapse(
                dbc.CardBody([
                    html.P(
                        "O Orçamento Municipal",
                        className="card-text"
                    ),
                ]),
                id="collapse-orcamento", is_open=True
            )
        ], className="shadow-sm mb-5"),

        dbc.Card([
            dbc.CardHeader(
                html.Div([
                    html.H5("Códigos Orçamentários (Dotação)", className="m-0"),
                    dbc.Button("➖/➕", id="btn-collapse-dotacao", color="link", size="sm", className="text-decoration-none ms-2", n_clicks=1)
                ], className="d-flex align-items-center")
            ),
            dbc.Collapse(
                dbc.CardBody([
                    html.P(
                        "Os códigos orçamentários são utilizados para classificar e organizar as despesas públicas. " \
                        "Eles seguem uma lógica que permite fácilmente identificar o objetivo, natureza e origem de cada gasto público, " \
                        "além de outros detalhes importantes para a gestão financeira do município.",
                        className="card-text"),
                    html.H5("Estrutura da dotação orçamentária", className="mt-4"),
                    html.Img(src="/assets/estrutura_dotacao.png", className="img-fluid", alt="Estrutura da Dotação Orçamentária")
                ]),
                id="collapse-codigos", is_open=True
            )
        ], className="shadow-sm mb-5"),

        dbc.Card([
            dbc.CardHeader(
                html.Div([
                    html.H5("Descrição dos códigos e siglas", className="m-0"),
                    dbc.Button("➖/➕", id="btn-collapse-codigos", color="link", size="sm", className="text-decoration-none ms-2", n_clicks=1)
                ], className="d-flex align-items-center")
            ),
            dbc.Collapse(
                dbc.CardBody([
                    html.H5("Tabela de Ações", className="mb-3"),
                    dash_table.DataTable(
                        data=df_acoes.to_dict('records'),
                        columns=[{"name": mapa_acoes[col], "id": col} for col in mapa_acoes if col in df_acoes.columns],
                        style_table={'overflowX': 'auto'},
                        style_header={'backgroundColor': "#0f69c9", 'fontWeight': 'bold', "fontSize": "14px", 
                                      "fontFamily": "Calibri, sans-serif", "color": "#FFFFFF"},
                        style_cell={'textAlign': 'left', 'fontSize': '12px', "fontFamily": "Calibri, sans-serif", "color": "#333333"},
                        page_size=10,
                        sort_action="native"
                    ),
                    html.Hr(className="my-4"),
                    html.H5("Tabela de Elementos", className="mb-3"),
                    dash_table.DataTable(
                        data=df_elementos.to_dict('records'),
                        columns=[{"name": mapa_elementos[col], "id": col} for col in mapa_elementos if col in df_elementos.columns],
                        style_table={'overflowX': 'auto'},
                        style_header={'backgroundColor': "#0f69c9", 'fontWeight': 'bold', "fontSize": "14px", 
                                      "fontFamily": "Calibri, sans-serif", "color": "#FFFFFF"},
                        style_cell={'textAlign': 'left', 'fontSize': '12px', "fontFamily": "Calibri, sans-serif", "color": "#333333"},
                        page_size=10,
                        sort_action="native"
                    ),
                ]),
                id="collapse-codigos-siglas", is_open=True
            )
        ], className="shadow-sm mb-5"),

        dbc.Card([
            dbc.CardHeader(
                html.Div([
                    html.H5("Glossário de Termos Orçamentários", className="m-0"),
                    dbc.Button("➖/➕", id="btn-collapse-glossario", color="link", size="sm", className="text-decoration-none ms-2", n_clicks=1)
                ], className="d-flex align-items-center")
            ),
            dbc.Collapse(
                dbc.CardBody([
                    html.P("Abaixo você encontra a definição de cada termo utilizado nos cards e tabelas deste painel.", className="card-text"),
                    dbc.ListGroup(itens_glossario, flush=True)
                ]),
                id="collapse-glossario", is_open=True
            )
        ], className="shadow-sm mb-5"),

        html.Footer([
            html.P("Painel Orçamentário SMDHC - Desenvolvido em Python/Dash | "
            "(11) 2833-4832 - nsfaita@prefeitura.sp.gov.br", className="text-center text-muted mt-4")
        ])
        
    ], fluid=True, style={"backgroundColor": "#f8f9fa", "padding": "20px"})

def registrar_callbacks_sobre(app):
    @app.callback(
        Output("collapse-sobre", "is_open"),
        Input("btn-collapse-sobre", "n_clicks"),
        State("collapse-sobre", "is_open"),
    )
    def toggle_sobre(n, is_open):
        if n:
            return not is_open
        return is_open
    
    @app.callback(
        Output("collapse-orcamento", "is_open"),
        Input("btn-collapse-orcamento", "n_clicks"),
        State("collapse-orcamento", "is_open"),
    )
    def toggle_orcamento(n, is_open):
        if n:
            return not is_open
        return is_open

    @app.callback(
        Output("collapse-codigos", "is_open"),
        Input("btn-collapse-dotacao", "n_clicks"),
        State("collapse-codigos", "is_open"),
    )
    def toggle_dotacao(n, is_open):
        if n:
            return not is_open
        return is_open
    
    @app.callback(
        Output("collapse-codigos-siglas", "is_open"),
        Input("btn-collapse-codigos", "n_clicks"),
        State("collapse-codigos-siglas", "is_open"),
    )
    def toggle_codigos_siglas(n, is_open):
        if n:
            return not is_open
        return is_open

    @app.callback(
        Output("collapse-glossario", "is_open"),
        Input("btn-collapse-glossario", "n_clicks"),
        State("collapse-glossario", "is_open"),
    )
    def toggle_glossario(n, is_open):
        if n:
            return not is_open
        return is_open
    
