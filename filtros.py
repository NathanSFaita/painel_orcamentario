import dash_bootstrap_components as dbc
from dash import dcc, html
import os
from utils import BASE_DIR

# Descobre anos disponíveis ao iniciar
despesas_dir = os.path.join(BASE_DIR, "base_despesas")
anos_disponiveis = []
if os.path.exists(despesas_dir):
    anos_disponiveis = sorted([
        p for p in os.listdir(despesas_dir)
        if os.path.isdir(os.path.join(despesas_dir, p))
    ])

ano_padrao = anos_disponiveis[-1] if anos_disponiveis else None

def layout_filtros_padrao(prefixo):
    """
    Gera o Grid de filtros padrão.
    prefixo: 'exe' ou 'emp' para diferenciar IDs na página.
    """
    return html.Div([
        dbc.Row([
            # Linha 1
            dbc.Col([
                html.Label("Ano", className="fw-bold"),
                dcc.Dropdown(
                    id=f"{prefixo}-ano",
                    options=[{"label": a, "value": a} for a in anos_disponiveis],
                    value=ano_padrao, clearable=False
                ),
            ], md=1),
            dbc.Col([
                html.Label("Órgão", className="fw-bold"),
                dcc.Dropdown(id=f"{prefixo}-orgao", multi=True)
            ], md=1),
            dbc.Col([
                html.Label("Coordenação", className="fw-bold"),
                dcc.Dropdown(id=f"{prefixo}-coordenacao", multi=True)
            ], md=2),
            dbc.Col([
                html.Label("Ação", className="fw-bold"),
                dcc.Dropdown(id=f"{prefixo}-projeto", multi=True)
            ], md=2),
            dbc.Col([
                html.Label("Atividade", className="fw-bold"),
                dcc.Dropdown(id=f"{prefixo}-acao", multi=True)
            ], md=3),
        ], className="mb-2", justify="center"),
        
        dbc.Row([
            # Linha 2
            dbc.Col([
                html.Label("Despesa (Código)", className="fw-bold"),
                dcc.Dropdown(id=f"{prefixo}-despesa", multi=True)
            ], md=2),
            dbc.Col([
                html.Label("Elemento de Despesa", className="fw-bold"),
                dcc.Dropdown(id=f"{prefixo}-elemento", multi=True)
            ], md=7),            
        ], className="mb-2", justify="center"),
        
        dbc.Row([
            # Linha 3
            dbc.Col([
                html.Label("Vinculação", className="fw-bold"),
                dcc.Dropdown(id=f"{prefixo}-vinculacao", multi=True)
            ], md=2),
            dbc.Col([
                html.Label("Fonte", className="fw-bold"),
                dcc.Dropdown(id=f"{prefixo}-fonte", multi=True)
            ], md=7)
            ,
        ], className="mb-4", justify="center")
    ])
