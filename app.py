import dash
from dash import html, dcc, Input, Output, State
import dash_bootstrap_components as dbc
import os

from dash_execucao import layout_execucao, registrar_callbacks_execucao
from dash_empenhos import layout_empenhos, registrar_callbacks_empenhos
from dash_sobre import layout_sobre, registrar_callbacks_sobre
from dash_pressao import layout_pressao, registrar_callbacks_pressao
from dash_planejamento import layout_planejamento, registrar_callbacks_planejamento
from filtros import ano_padrao
from utils import cabecalho_padrao

# Inicialização do App
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP], suppress_callback_exceptions=True, title="Painel Orçamentário")
app._favicon = "pmsp_logo.png"
server = app.server

@server.route('/health')
def health_check():
    """
    Endpoint leve para monitoramento de atividade (UptimeRobot).
    Retorna uma resposta simples para manter o servidor ativo sem carregar o app Dash.
    """
    return "OK", 200

app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    # STORE GLOBAL - Gerencia o estado dos filtros entre as páginas
    dcc.Store(id="store_filtros", storage_type="session", data={
        "ano": ano_padrao, "mes": None,
        "orgao": ["Todos"], "coordenacao": ["Todos"], "acao": ["Todos"],
        "projeto": ["Todos"], "descricao": ["Todos"], "elemento": ["Todos"], "vinculacao": ["Todos"],
        "fonte": ["Todos"], "despesa": ["Todos"], "fonte_descricao": ["Todos"],
        "processo": ["Todos"], "credor": ["Todos"], "objeto": ["Todos"], "origem": ["Todos"], "fase": ["Todos"],
        "status_empenho": ["Todos"], "situacao_orcamentaria": ["Todos"], "descricao_generica": ["Todos"], "numero_termo": ["Todos"], "tem_pressao": ["Todos"],
        "data_inicio": None, "data_fim": None
    }),
    html.Div(id='page-content')
])


homepage_layout = html.Div([
    cabecalho_padrao("Painel Orçamentário SMDHC", "🏢Bem-vindo ao Painel Orçamentário"),
    
    dbc.Row([
        dbc.Col(dbc.Button("Planejamento", id="btn-open-planejamento", color="primary", className="me-2"), md=4, style={'textAlign': 'center'}),
        dbc.Col(dbc.Button("Execução", id="btn-open-execucao", color="success", className="me-2"), md=4, style={'textAlign': 'center'}),
        dbc.Col(dbc.Button("Saiba Mais", href="/sobre", color="info"), md=4, style={'textAlign': 'center'}),
    ], className="d-flex justify-content-center", style={'marginBottom': '30px'}),
    
    html.P("Selecione a seção que deseja acessar.", style={'textAlign': 'center'}),

    # Modal de Planejamento
    dbc.Modal([
        dbc.ModalHeader(dbc.ModalTitle("Seção de Planejamento")),
        dbc.ModalBody([
            dbc.Row([
                dbc.Col(dbc.Button("Planejamento de Pagamentos", href="/planejamento", color="primary", className="w-100 mb-2"), width=12),
                dbc.Col(dbc.Button("Pressão Orçamentária", href="/pressao", color="danger", className="w-100"), width=12),
            ])
        ]),
        dbc.ModalFooter(dbc.Button("Fechar", id="btn-close-planejamento", className="ms-auto", n_clicks=0))
    ], id="modal-planejamento", is_open=False, centered=True),

    # Modal de Execução
    dbc.Modal([
        dbc.ModalHeader(dbc.ModalTitle("Seção de Execução")),
        dbc.ModalBody([
            dbc.Row([
                dbc.Col(dbc.Button("Execução Orçamentária", href="/execucao", color="success", className="w-100 mb-2"), width=12),
                dbc.Col(dbc.Button("Consulta de Empenhos", href="/empenhos", color="primary", className="w-100"), width=12),
            ])
        ]),
        dbc.ModalFooter(dbc.Button("Fechar", id="btn-close-execucao", className="ms-auto", n_clicks=0))
    ], id="modal-execucao", is_open=False, centered=True),

], style={'padding': '20px'})


@app.callback(
    Output('page-content', 'children'),
    Input('url', 'pathname'),
)
def render_page(pathname):
    # if pathname == "/":
    #     return homepage_layout

    if pathname == "/":
        return layout_execucao()  # Redireciona para a página de execução como homepage
    elif pathname == "/execucao":
        return layout_execucao()
    elif pathname == "/empenhos":
        return layout_empenhos()
    elif pathname == "/sobre":
        return layout_sobre()
    elif pathname == "/pressao":
        return layout_pressao()
    elif pathname == "/planejamento":
        return layout_planejamento()
    elif pathname == '/health':
        return html.Div("OK") # Retorna uma página simples para o health check
    return layout_execucao()

# Callbacks para abrir/fechar modais na homepage
@app.callback(
    Output("modal-planejamento", "is_open"),
    [Input("btn-open-planejamento", "n_clicks"), Input("btn-close-planejamento", "n_clicks")],
    [State("modal-planejamento", "is_open")],
)
def toggle_modal_planejamento(n1, n2, is_open):
    if n1 or n2: return not is_open
    return is_open

@app.callback(
    Output("modal-execucao", "is_open"),
    [Input("btn-open-execucao", "n_clicks"), Input("btn-close-execucao", "n_clicks")],
    [State("modal-execucao", "is_open")],
)
def toggle_modal_execucao(n1, n2, is_open):
    if n1 or n2: return not is_open
    return is_open

# Registra os callbacks de todas as páginas
registrar_callbacks_execucao(app)
registrar_callbacks_empenhos(app)
registrar_callbacks_sobre(app)
registrar_callbacks_pressao(app)
registrar_callbacks_planejamento(app)

if __name__ == "__main__":
    if os.environ.get("PORT"):   # Heroku
        port = int(os.environ.get("PORT",8050))
        app.run(host="0.0.0.0", port=port, debug=False)
    else:                        # Local
        app.run(host="127.0.0.1", port=8050, debug=True)
