import dash
from dash import html, dcc, Input, Output
import dash_bootstrap_components as dbc
import os

from dash_execucao import layout_execucao, registrar_callbacks_execucao
from dash_empenhos import layout_empenhos, registrar_callbacks_empenhos
from dash_sobre import layout_sobre, registrar_callbacks_sobre
from filtros import ano_padrao

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
    dcc.Location(id="url", refresh=False),
    
    # STORE GLOBAL - Gerencia o estado dos filtros entre as páginas
    dcc.Store(id="store_filtros", storage_type="session", data={ # Session mantém enquanto a aba estiver aberta
        "ano": ano_padrao, "mes": None,
        "orgao": ["Todos"], "coordenacao": ["Todos"], "acao": ["Todos"],
        "projeto": ["Todos"], "descricao": ["Todos"], "elemento": ["Todos"], "vinculacao": ["Todos"],
        "fonte": ["Todos"], "despesa": ["Todos"], "fonte_descricao": ["Todos"],
        "data_inicio": None, "data_fim": None
    }),
    
    html.Div(id="page-content")
])

@app.callback(Output("page-content", "children"), Input("url", "pathname"))
def render_page(pathname):
    if pathname == "/empenhos":
        return layout_empenhos()
    elif pathname == "/sobre":
        return layout_sobre()
    elif pathname == "/health":
        return html.Div("OK") # Retorna uma página simples para o health check
    return layout_execucao()

# Registra os callbacks de todas as páginas
registrar_callbacks_execucao(app)
registrar_callbacks_empenhos(app)
registrar_callbacks_sobre(app)

if __name__ == "__main__":
    if os.environ.get("PORT"):   # Heroku
        port = int(os.environ.get("PORT", 8050))
        app.run(host="0.0.0.0", port=port, debug=False)
    else:                        # Local
        app.run(host="127.0.0.1", port=8050, debug=True)
