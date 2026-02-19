import dash_bootstrap_components as dbc
from dash import dcc, html
import os
from utils import BASE_DIR, descrição_cards

# Descobre anos disponíveis ao iniciar
despesas_dir = os.path.join(BASE_DIR, "base_despesas")
anos_disponiveis = []
if os.path.exists(despesas_dir):
    anos_disponiveis = sorted([
        p for p in os.listdir(despesas_dir)
        if os.path.isdir(os.path.join(despesas_dir, p))
    ])

ano_padrao = anos_disponiveis[-1] if anos_disponiveis else None

def criar_label_com_tooltip(texto, prefixo):
    """Cria um label com tooltip se houver descrição no dicionário."""
    descricao = descrição_cards.get(texto)
    elementos = [html.Span(texto, style={"verticalAlign": "middle"})]

    if descricao:
        # Gera ID único para o tooltip
        id_safe = texto.replace(" ", "").replace("(", "").replace(")", "").lower()
        id_tooltip = f"tooltip-{prefixo}-{id_safe}"
        
        elementos.append(html.Span(" ℹ️", id=id_tooltip, style={"cursor": "help", "fontSize": "0.8em", "marginLeft": "5px", "verticalAlign": "middle", "opacity": "0.7"}))
        elementos.append(dbc.Tooltip(descricao, target=id_tooltip, placement="top"))

    return html.Label(elementos, className="fw-bold")

def layout_filtros_padrao(prefixo):
    """
    Gera o Grid de filtros padrão.
    prefixo: 'exe' ou 'emp' para diferenciar IDs na página.
    """
    return html.Div([
        dbc.Button(
            "🔽 Filtros de Pesquisa (Clique para expandir/recolher)",
            id=f"{prefixo}-btn-toggle-filtros",
            className="mb-3 w-100",
            color="light",
            style={"textAlign": "left", "fontWeight": "bold", "border": "1px solid #ddd", "color": "#555"}
        ),
        dbc.Collapse(
            id=f"{prefixo}-collapse-filtros", 
            is_open=True,
            children=(
                [
                    dbc.Row([
                        # Linha 1
                        dbc.Col([
                            criar_label_com_tooltip("Ano", prefixo),
                            dcc.Dropdown(
                                id=f"{prefixo}-ano",
                                options=[{"label": a, "value": a} for a in anos_disponiveis],
                                value=ano_padrao, clearable=False,
                                style={"height": "38px", "width": "150px"}
                            ),
                        ], md=1),
                        dbc.Col([
                            criar_label_com_tooltip("Órgão", prefixo),
                            dcc.Dropdown(id=f"{prefixo}-orgao", multi=True, closeOnSelect=False,
                                         style={"maxHeight": "45px", "overflowY": "visible", "zIndex": 105})
                        ], md=2),
                        dbc.Col([
                            criar_label_com_tooltip("Coordenação", prefixo),
                            dcc.Dropdown(id=f"{prefixo}-coordenacao", multi=True, closeOnSelect=False,
                                         style={"maxHeight": "45px", "overflowY": "visible", "zIndex": 104})
                        ], md=2),
                        dbc.Col([
                            criar_label_com_tooltip("Descrição da Coordenação", prefixo),
                            dcc.Dropdown(id=f"{prefixo}-descricao", multi=True, closeOnSelect=False,
                                         style={"maxHeight": "45px", "overflowY": "visible", "zIndex": 103})
                        ], md=3),
                        dbc.Col([
                            criar_label_com_tooltip("Ação", prefixo),
                            dcc.Dropdown(id=f"{prefixo}-projeto", multi=True, closeOnSelect=False, 
                                         style={"maxHeight": "45px", "overflowY": "visible", "zIndex": 102})
                        ], md=1),
                        dbc.Col([
                            criar_label_com_tooltip("Atividade", prefixo),
                            dcc.Dropdown(id=f"{prefixo}-acao", multi=True, closeOnSelect=False, 
                                         style={"maxHeight": "45px", "overflowY": "visible", "zIndex": 101})
                        ], md=3),
                    ], className="mb-2", justify="center"),
                    
                    dbc.Row([
                        # Linha 2
                        dbc.Col([
                            criar_label_com_tooltip("Despesa (Código)", prefixo),
                            dcc.Dropdown(id=f"{prefixo}-despesa", multi=True, closeOnSelect=False, style={"maxHeight": "45px", "overflowY": "visible", "zIndex": 102})
                        ], md=3),
                        dbc.Col([
                            criar_label_com_tooltip("Elemento de Despesa", prefixo),
                            dcc.Dropdown(id=f"{prefixo}-elemento", multi=True, closeOnSelect=False, style={"maxHeight": "45px", "overflowY": "visible", "zIndex": 101})
                        ], md=9),            
                    ], className="mb-2", justify="center"),
                    
                    dbc.Row([
                        # Linha 3
                        dbc.Col([
                            criar_label_com_tooltip("Vinculação", prefixo),
                            dcc.Dropdown(id=f"{prefixo}-vinculacao", multi=True, closeOnSelect=False, style={"maxHeight": "45px", "overflowY": "visible", "zIndex": 102})
                        ], md=3),
                        dbc.Col([
                            criar_label_com_tooltip("Fonte", prefixo),
                            dcc.Dropdown(id=f"{prefixo}-fonte", multi=True, closeOnSelect=False, style={"maxHeight": "45px", "overflowY": "visible", "zIndex": 101})
                        ], md=9),
                    ], className="mb-2", justify="center"),
                ] + (
                    # Filtros específicos de Empenhos
                    [
                        html.Hr(className="my-3"),
                        dbc.Row([
                            dbc.Col([
                                criar_label_com_tooltip("Nº Empenho", prefixo),
                                dcc.Dropdown(id=f"{prefixo}-filtro-empenho", multi=True, closeOnSelect=False, 
                                             style={"maxHeight": "45px", "overflowY": "visible", "zIndex": 103})], md=3),
                            dbc.Col([
                                criar_label_com_tooltip("Objeto do Empenho", prefixo),
                                dcc.Dropdown(id=f"{prefixo}-filtro-objeto", multi=True, closeOnSelect=False, clearable=True, 
                                             style={"maxHeight": "45px", "overflowY": "visible", "zIndex": 102})], md=6),
                            dbc.Col([
                                html.Label("Período do Empenho", className="fw-bold"),
                                dcc.DatePickerRange(
                                    id=f"{prefixo}-date-picker",
                                    display_format="DD/MM/YYYY",
                                    start_date_placeholder_text="Data Início",
                                    end_date_placeholder_text="Data Fim",
                                    style={"zIndex": 101, "width": "100%"}
                                )
                            ], md=3),
                        ], className="mb-2", justify="center"),
                        dbc.Row([
                            dbc.Col([
                                criar_label_com_tooltip("Processo SEI", prefixo),
                                dcc.Dropdown(id=f"{prefixo}-filtro-processo", multi=True, closeOnSelect=False, 
                                             style={"maxHeight": "45px", "overflowY": "visible", "zIndex": 102})], md=3),
                            dbc.Col([
                                criar_label_com_tooltip("Credor", prefixo),
                                dcc.Dropdown(id=f"{prefixo}-filtro-credor", multi=True, closeOnSelect=False, 
                                             style={"maxHeight": "45px", "overflowY": "visible", "zIndex": 101})], md=9),
                        ], className="mb-4", justify="center"),
                    ] if prefixo == 'emp' else []
                )
            )
        )
    ])
