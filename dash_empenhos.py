import dash
from dash import html, dcc, Input, Output, State, callback_context, no_update
import dash_bootstrap_components as dbc
from dash import dash_table as dt
from dash.dash_table.Format import Format, Scheme, Symbol, Group
from filtros import layout_filtros_padrao, ano_padrao
from utils import (
    carrega_base, gera_tabela_pivot, cabecalho_padrao,
    tratar_selecao_todos, monta_cards_resumo, DE_PARA_EMPENHOS,
    DE_PARA_INDICES_EMPENHOS, ler_info_versao, gera_card_atualizacao,
)
from gerar_pdf import criar_relatorio_empenho_pdf

def layout_empenhos():
    return dbc.Container([
        cabecalho_padrao("📊 Painel Orçamentário", "💰 Consulta de Empenhos"),
        
        # CARDS + INFO ATUALIZAÇÃO
        html.Div(id="emp-cards-container", className="mb-4"),
        
        layout_filtros_padrao("emp"),
        
        dbc.Row([
            dbc.Col([html.Label("Nº Empenho", className="fw-bold"), dcc.Dropdown(id="emp-filtro-empenho", multi=True)], md=2),
            dbc.Col([html.Label("Processo", className="fw-bold"), dcc.Dropdown(id="emp-filtro-processo", multi=True)], md=2),
            dbc.Col([html.Label("Objeto do Empenho", className="fw-bold"), dcc.Dropdown(id="emp-filtro-objeto", multi=True)], md=5),
        ], className="mb-4", justify="center"),

        dbc.Row([
            dbc.Col([dbc.Button("🗑️ Limpar Filtros", id="emp-btn-limpar", color="warning", className="w-100 mt-4")], md=2),
            dbc.Col([dbc.Button("⬅️ Voltar para Execução", href="/", color="secondary", className="w-100 mt-4")], md=2),
        ], className="mb-4", justify="center"),           
        html.Div(id="emp-info-atualizacao"),
        
        # TABELA
        html.H5("Lista de Empenhos", className="fw-bold"),
        dt.DataTable(
            id="emp-tabela",
            style_table={"overflowX": "auto"},
            style_header={"backgroundColor": "#1f77b4", "color": "white", "fontWeight": "bold", "fontSize": "14px",  "fontFamily": "Arial, sans-serif"},
            style_cell={"textAlign": "left", "minWidth": "100px", "fontSize": "12px", "fontFamily": "Arial, sans-serif"},
            page_size=10, sort_action="native", #filter_action="native"
        ),
        dcc.Download(id="emp-download-xlsx"),
        dcc.Download(id="emp-download-pdf"),
        dbc.Button("📥 Download Excel", id="emp-btn-download", color="success", className="mt-3"),
        dbc.Button("📄 Download PDF", id="emp-btn-download-pdf", color="danger", className="mt-3", style={"marginLeft": "10px"})
    ], fluid=True, style={"backgroundColor": "#f8f9fa", "padding": "20px"})

def registrar_callbacks_empenhos(app):
    
    # 1. Popula Dropdowns Específicos
    @app.callback(
        [Output(f"emp-{col}", "options") for col in ["orgao", "coordenacao", "acao", "projeto", "elemento", 
                                                     "vinculacao", "fonte", "despesa", "filtro-empenho", "filtro-processo"]] + 
        [Output("emp-filtro-objeto", "options")],
        Input("emp-ano", "value")
    )
    def popula_opts(ano):
        df = carrega_base("empenhos", ano, None)
        if df.empty: return [[]] * 11
        def opts(col): 
            if col not in df.columns: return []
            return [{"label": str(v), "value": v} for v in sorted(df[col].dropna().unique())]
        def opts_todos(col):
            return [{"label": "Todos", "value": "Todos"}] + opts(col)
        
        return (opts_todos("orgao"), opts_todos("coordenacao"), opts_todos("acao_programatica"),
                opts_todos("codProjetoAtividade"), opts_todos("nome_elemento"), opts_todos("codVinculacaoRecurso"),
                opts_todos("txDescricaoFonteRecurso"), opts_todos("codDespesa"), opts("codEmpenho"), opts("codProcesso"),
                opts("anexo_descricaoAnexo"))

    # 2. UI -> STORE (Salva alterações e aplica lógica do "Todos")
    @app.callback(
        Output("store_filtros", "data", allow_duplicate=True),
        Input("emp-btn-limpar", "n_clicks"), Input("emp-ano", "value"),
        Input("emp-orgao", "value"), Input("emp-coordenacao", "value"),
        Input("emp-acao", "value"), Input("emp-projeto", "value"),
        Input("emp-elemento", "value"), Input("emp-vinculacao", "value"),
        Input("emp-fonte", "value"), Input("emp-despesa", "value"),
        State("store_filtros", "data"), prevent_initial_call=True
    )
    def update_store_emp(n_limpar, ano, orgao, coord, acao, proj, elem, vinc, fonte, desp, store):
        if store is None: store = {}
        ctx = callback_context
        trigger_id = ctx.triggered[0]["prop_id"]
        
        if "emp-btn-limpar" in trigger_id:
            return {**store, "ano": ano_padrao, "orgao": ["Todos"], "coordenacao": ["Todos"], "acao": ["Todos"],
                    "projeto": ["Todos"], "elemento": ["Todos"], "vinculacao": ["Todos"], "fonte": ["Todos"], "despesa": ["Todos"]}
        
        store.update({
            "ano": ano,
            "orgao": tratar_selecao_todos(orgao, store.get("orgao")),
            "coordenacao": tratar_selecao_todos(coord, store.get("coordenacao")),
            "acao": tratar_selecao_todos(acao, store.get("acao")),
            "projeto": tratar_selecao_todos(proj, store.get("projeto")),
            "elemento": tratar_selecao_todos(elem, store.get("elemento")),
            "vinculacao": tratar_selecao_todos(vinc, store.get("vinculacao")),
            "fonte": tratar_selecao_todos(fonte, store.get("fonte")),
            "despesa": tratar_selecao_todos(desp, store.get("despesa"))
        })
        return store

    # 3. STORE -> UI (Carrega dados do Store para os Dropdowns)
    @app.callback(
        [Output("emp-ano", "value")] + [Output(f"emp-{k}", "value") for k in ["orgao","coordenacao","acao","projeto","elemento","vinculacao","fonte","despesa"]],
        Input("store_filtros", "data")
    )
    def sync_ui_emp(store):
        if not store: return (ano_padrao,) + (["Todos"],)*8
        return (store.get("ano", ano_padrao),
                store.get("orgao", ["Todos"]), store.get("coordenacao", ["Todos"]), 
                store.get("acao", ["Todos"]), store.get("projeto", ["Todos"]),
                store.get("elemento", ["Todos"]), store.get("vinculacao", ["Todos"]), 
                store.get("fonte", ["Todos"]), store.get("despesa", ["Todos"]))

    # 4. GERA DADOS (CARDS + TABELA)
    @app.callback(
        Output("emp-info-atualizacao", "children"),
        Output("emp-cards-container", "children"),
        Output("emp-tabela", "data"), Output("emp-tabela", "columns"),
        Input("store_filtros", "data"),
        Input("emp-filtro-empenho", "value"), Input("emp-filtro-processo", "value")
        , Input("emp-filtro-objeto", "value")
    )
    def atualiza_dash_emp(store, f_empenho, f_processo, f_objeto):
        if not store or not store.get("ano"):
            return (no_update,) * 4
        
        df = carrega_base("empenhos", store["ano"], None)
        data_script = ler_info_versao()

        if df.empty:
            card_atualizacao = gera_card_atualizacao("-", data_script)
            return card_atualizacao, html.Div("Sem dados."), [], []

        # Aplica Filtros Globais
        mapa = {"orgao": "orgao", "coordenacao": "coordenacao", "acao": "acao_programatica", 
                "projeto": "codProjetoAtividade", "elemento": "nome_elemento", "vinculacao": "codVinculacaoRecurso", 
                "fonte": "txDescricaoFonteRecurso", "despesa": "codDespesa"}
        
        for k_store, col_df in mapa.items():
            vals = store.get(k_store, ["Todos"])
            if "Todos" not in vals and col_df in df.columns:
                if col_df in ["codVinculacaoRecurso", "codDespesa"]: # Trata codigo como string/int conforme base
                    df = df[df[col_df].isin(vals)] # Ajuste se precisar de conversão str/int
                else:
                    df = df[df[col_df].isin(vals)]
        
        # Filtros Locais (Empenho/Processo)
        if f_empenho: df = df[df["codEmpenho"].isin(f_empenho)]
        if f_processo: df = df[df["codProcesso"].isin(f_processo)]
        if f_objeto: df = df[df["anexo_descricaoAnexo"].isin(f_objeto)]

        # 1. Cards
        data_ext = "-"
        # Verifica variações comuns de nome de coluna de data
        col_data = "data_hora_extracao" if "data_hora_extracao" in df.columns else "datExtracao"
        if col_data in df.columns:
            datas = df[col_data].dropna().unique()
            if len(datas) > 0: data_ext = str(datas[0])
        
        card_atualizacao = gera_card_atualizacao(data_ext, data_script)

        totais = {c: df[c].sum() for c in DE_PARA_EMPENHOS.keys() if c in df.columns}
        cards = monta_cards_resumo(totais, DE_PARA_EMPENHOS)

        # 2. Tabela
        pivot = gera_tabela_pivot(df, "empenhos")
        cols_table = []
        for c in pivot.columns:
            if c in DE_PARA_EMPENHOS:
                nome = DE_PARA_EMPENHOS[c]
                tipo = "numeric"
                fmt = Format(
                    scheme=Scheme.fixed, 
                    precision=2, 
                    group=Group.yes, 
                    group_delimiter='.', 
                    decimal_delimiter=',', 
                    symbol=Symbol.yes, 
                    symbol_prefix='R$ '
                )
            elif c in DE_PARA_INDICES_EMPENHOS:
                nome = DE_PARA_INDICES_EMPENHOS[c]
                tipo = "text"
                fmt = None
            else:
                nome = c.replace("cod", "").replace("tx", "").title()
                tipo = "text"
                fmt = None
            cols_table.append({"name": nome, "id": c, "type": tipo, "format": fmt})

        return card_atualizacao, cards, pivot.to_dict("records"), cols_table

    # 5. GERA E FAZ DOWNLOAD DO PDF
    @app.callback(
        Output("emp-download-pdf", "data"),
        Input("emp-btn-download-pdf", "n_clicks"),
        State("store_filtros", "data"),
        State("emp-filtro-empenho", "value"),
        State("emp-filtro-processo", "value"),
        State("emp-filtro-objeto", "value"),
        prevent_initial_call=True
    )
    def download_pdf_report(n_clicks, store, f_empenho, f_processo, f_objeto):
        if not store or not store.get("ano"):
            return no_update
        
        # --- Replicar a lógica de filtragem ---
        df = carrega_base("empenhos", store["ano"], None)
        if df.empty:
            return no_update

        mapa = {"orgao": "orgao", "coordenacao": "coordenacao", "acao": "acao_programatica", 
                "projeto": "codProjetoAtividade", "elemento": "nome_elemento", "vinculacao": "codVinculacaoRecurso", 
                "fonte": "txDescricaoFonteRecurso", "despesa": "codDespesa"}
        
        for k_store, col_df in mapa.items():
            vals = store.get(k_store, ["Todos"])
            if "Todos" not in vals and col_df in df.columns:
                df = df[df[col_df].isin(vals)]
        
        if f_empenho: df = df[df["codEmpenho"].isin(f_empenho)]
        if f_processo: df = df[df["codProcesso"].isin(f_processo)]
        if f_objeto: df = df[df["anexo_descricaoAnexo"].isin(f_objeto)]
        
        # --- Obter dados para o relatório ---
        totais = {c: df[c].sum() for c in DE_PARA_EMPENHOS.keys() if c in df.columns}
        pivot = gera_tabela_pivot(df, "empenhos")

        # --- Gerar o PDF ---
        pdf_bytes = criar_relatorio_empenho_pdf(store, totais, pivot)
        
        return dcc.send_bytes(pdf_bytes, "relatorio_empenhos.pdf")
