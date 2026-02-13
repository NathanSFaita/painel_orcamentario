import dash
import pandas as pd
from dash import html, dcc, Input, Output, State, callback_context, no_update
import dash_bootstrap_components as dbc
from dash import dash_table as dt
from dash.dash_table.Format import Format, Scheme, Symbol, Group
from filtros import layout_filtros_padrao, ano_padrao, criar_label_com_tooltip
from utils import (
    carrega_base, gera_tabela_pivot, cabecalho_padrao,
    tratar_selecao_todos, monta_cards_resumo, DE_PARA_EMPENHOS, DE_PARA_INDICES_EMPENHOS,
    gera_card_atualizacao, descrição_cards
)
from gerar_pdf import criar_relatorio_empenho_pdf

# Mapa completo de colunas disponíveis para seleção
MAPA_COLUNAS_EMPENHOS = {**DE_PARA_INDICES_EMPENHOS, **DE_PARA_EMPENHOS}

def layout_empenhos():
    return dbc.Container([
        cabecalho_padrao("📊 Quadro de Detalhamento de Despesas", "💰 Consulta de Empenhos"),
        
        # CARDS + INFO ATUALIZAÇÃO
        html.Div(id="emp-cards-container", className="mb-4"),
        # Store para opções de empenhos
        dcc.Store(id="store_opcoes_emp", storage_type="memory"),
        
        layout_filtros_padrao("emp"),
        
        dbc.Row([
            dbc.Col([
                criar_label_com_tooltip("Nº Empenho", "emp"),
                dcc.Dropdown(id="emp-filtro-empenho", multi=True)], md=2),
            dbc.Col([
                criar_label_com_tooltip("Objeto do Empenho", "emp"),
                dcc.Dropdown(id="emp-filtro-objeto", multi=True, closeOnSelect=False, clearable=True)], md=7),
        ], className="mb-4", justify="center"),

        dbc.Row([
            dbc.Col([
                criar_label_com_tooltip("Processo SEI", "emp"),
                dcc.Dropdown(id="emp-filtro-processo", multi=True)], md=2),
            dbc.Col([
                criar_label_com_tooltip("Credor", "emp"),
                dcc.Dropdown(id="emp-filtro-credor", multi=True)], md=7),
        ], className="mb-4", justify="center"),

        dbc.Row([
            dbc.Col([dbc.Button("🗑️ Limpar Filtros", id="emp-btn-limpar", color="warning", className="w-100 mt-4")], md=2),
            dbc.Col([dbc.Button("⬅️ Voltar para Execução", href="/", color="secondary", className="w-100 mt-4")], md=2),
            dbc.Col([dbc.Button("🛠️ Colunas", id="emp-btn-colunas", color="info", className="w-100 mt-4")], md=2),
        ], className="mb-4", justify="center"),           
                
        # MODAL DE SELEÇÃO DE COLUNAS
        dbc.Modal([
            dbc.ModalHeader(dbc.ModalTitle("Selecionar Colunas para Exibição")),
            dbc.ModalBody([
                html.Div([
                    dbc.Button("✅ Selecionar Tudo", id="emp-btn-sel-todos", size="sm", color="primary", outline=True, className="me-2"),
                    dbc.Button("❌ Desmarcar Tudo", id="emp-btn-des-todos", size="sm", color="secondary", outline=True),
                ], className="mb-3 d-flex justify-content-center"),
                dbc.Checklist(
                    id="emp-checklist-colunas",
                    options=[{"label": v, "value": k} for k, v in MAPA_COLUNAS_EMPENHOS.items()],
                    value=list(MAPA_COLUNAS_EMPENHOS.keys()), # Todas selecionadas por padrão
                    switch=True,
                )
            ]),
            dbc.ModalFooter(dbc.Button("Fechar", id="emp-btn-fechar-modal", className="ms-auto", n_clicks=0))
        ], id="emp-modal-colunas", is_open=False),

        # TABELA
        html.H5("Lista de Empenhos", className="fw-bold"),
        dt.DataTable(
            id="emp-tabela",
            style_table={"overflowX": "auto"},
            style_header={"backgroundColor": "#1f77b4", "color": "white", "fontWeight": "bold", "fontSize": "14px",  "fontFamily": "Calibri, sans-serif"},
            style_cell={"textAlign": "left", "minWidth": "100px", "fontSize": "12px", "fontFamily": "Calibri, sans-serif", "whiteSpace": "normal", "height": "auto"},
            style_cell_conditional=[
                {
                    'if': {'column_id': 'anexo_descricaoAnexo'},
                    'width': '400px',
                    'maxWidth': '400px',
                    'minWidth': '200px'
                },
                {
                    'if': {'column_id': 'codProcesso'},
                    'whiteSpace': 'nowrap'
                }
            ],
            page_size=25, sort_action="native", #filter_action="native"
        ),
        dcc.Download(id="emp-download-xlsx"),
        dcc.Download(id="emp-download-pdf"),
        dbc.Button("📥 Download Excel", id="emp-btn-download", color="success", className="mt-3"),
        dbc.Button("📄 Download PDF", id="emp-btn-download-pdf", color="danger", className="mt-3", style={"marginLeft": "10px"}),
        html.Hr(),
        html.Div(id="emp-info-atualizacao")
    ], fluid=True, style={"backgroundColor": "#f8f9fa", "padding": "20px"})
       

def registrar_callbacks_empenhos(app):
    
    # 1. Carrega Opções Base para o Store
    @app.callback(
        Output("store_opcoes_emp", "data"),
        Input("emp-ano", "value")
    )
    def carrega_opcoes_base_emp(ano):
        df = carrega_base("empenhos", ano, None)
        if df.empty: return {}
        
        def opts(col): 
            if col not in df.columns: return []
            return [{"label": str(v), "value": v} for v in sorted(df[col].dropna().unique())]
        def opts_todos(col):
            return [{"label": "Todos", "value": "Todos"}] + opts(col)
        
        return {
            "orgao": opts_todos("orgao"), "coordenacao": opts_todos("coordenacao"), 
            "acao": opts_todos("acao_programatica"), "projeto": opts_todos("codProjetoAtividade"),
            "elemento": opts_todos("nome_elemento"), "vinculacao": opts_todos("codVinculacaoRecurso"),
            "fonte": opts_todos("txDescricaoFonteRecurso"), "despesa": opts_todos("codDespesa"),
            "filtro-empenho": opts("codEmpenho"), "filtro-processo": opts("codProcesso"),
            "filtro-credor": opts("txtRazaoSocial"), "filtro-objeto": opts("anexo_descricaoAnexo")
        }

    # 2. Atualiza Dropdowns com Search Value
    @app.callback(
        [Output(f"emp-{col}", "options") for col in ["orgao", "coordenacao", "acao", "projeto", "elemento", 
                                                     "vinculacao", "fonte", "despesa", "filtro-empenho", "filtro-processo"]] + 
        [Output("emp-filtro-credor", "options"), Output("emp-filtro-objeto", "options")],
        Input("store_opcoes_emp", "data"),
        [Input(f"emp-{col}", "search_value") for col in ["orgao", "coordenacao", "acao", "projeto", "elemento", 
                                                     "vinculacao", "fonte", "despesa", "filtro-empenho", "filtro-processo"]] + 
        [Input("emp-filtro-credor", "search_value"), Input("emp-filtro-objeto", "search_value")]
    )
    def atualiza_dropdowns_emp(opcoes_base, *search_values):
        if not opcoes_base: return [[]] * 12
        
        keys = ["orgao", "coordenacao", "acao", "projeto", "elemento", "vinculacao", "fonte", "despesa", 
                "filtro-empenho", "filtro-processo", "filtro-credor", "filtro-objeto"]
        
        outputs = []
        for i, key in enumerate(keys):
            base = opcoes_base.get(key, [])
            search = search_values[i]
            if search:
                outputs.append([{"label": f"Selecionar todos contendo '{search}'", "value": f"SELECT_ALL:{search}"}] + base)
            else:
                outputs.append(base)
        return outputs

    # 3. UI -> STORE (Salva alterações e aplica lógica do "Todos" e "Select All")
    @app.callback(
        Output("store_filtros", "data", allow_duplicate=True),
        Input("emp-btn-limpar", "n_clicks"), Input("emp-ano", "value"),
        Input("emp-orgao", "value"), Input("emp-coordenacao", "value"),
        Input("emp-acao", "value"), Input("emp-projeto", "value"),
        Input("emp-elemento", "value"), Input("emp-vinculacao", "value"),
        Input("emp-fonte", "value"), Input("emp-despesa", "value"),
        State("store_filtros", "data"), 
        State("store_opcoes_emp", "data"), prevent_initial_call=True
    )
    def update_store_emp(n_limpar, ano, orgao, coord, acao, proj, elem, vinc, fonte, desp, store, opcoes_base):
        if store is None: store = {}
        ctx = callback_context
        trigger_id = ctx.triggered[0]["prop_id"]
        
        if "emp-btn-limpar" in trigger_id:
            return {**store, "ano": ano_padrao, "orgao": ["Todos"], "coordenacao": ["Todos"], "acao": ["Todos"],
                    "projeto": ["Todos"], "elemento": ["Todos"], "vinculacao": ["Todos"], "fonte": ["Todos"], "despesa": ["Todos"]}
        
        def processar_selecao(selecao, key):
            if not selecao: return ["Todos"]
            nova_selecao = []
            expandiu = False
            for item in selecao:
                if isinstance(item, str) and item.startswith("SELECT_ALL:"):
                    termo = item.split("SELECT_ALL:")[1].lower()
                    if opcoes_base and key in opcoes_base:
                        matches = [opt["value"] for opt in opcoes_base[key] if termo in str(opt["label"]).lower() and opt["value"] != "Todos"]
                        nova_selecao.extend(matches)
                    expandiu = True
                else:
                    nova_selecao.append(item)
            return tratar_selecao_todos(nova_selecao, store.get(key)) if not expandiu else nova_selecao

        store.update({
            "ano": ano,
            "orgao": processar_selecao(orgao, "orgao"),
            "coordenacao": processar_selecao(coord, "coordenacao"),
            "acao": processar_selecao(acao, "acao"),
            "projeto": processar_selecao(proj, "projeto"),
            "elemento": processar_selecao(elem, "elemento"),
            "vinculacao": processar_selecao(vinc, "vinculacao"),
            "fonte": processar_selecao(fonte, "fonte"),
            "despesa": processar_selecao(desp, "despesa")
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

    # 4. CONTROLE DO MODAL DE COLUNAS
    @app.callback(
        Output("emp-modal-colunas", "is_open"),
        Input("emp-btn-colunas", "n_clicks"),
        Input("emp-btn-fechar-modal", "n_clicks"),
        State("emp-modal-colunas", "is_open"),
        prevent_initial_call=True
    )
    def toggle_modal_colunas(n1, n2, is_open):
        if n1 or n2:
            return not is_open
        return is_open

    # 5. CONTROLE DOS BOTÕES SELECIONAR/DESMARCAR TUDO
    @app.callback(
        Output("emp-checklist-colunas", "value"),
        Input("emp-btn-sel-todos", "n_clicks"),
        Input("emp-btn-des-todos", "n_clicks"),
        State("emp-checklist-colunas", "options"),
        prevent_initial_call=True
    )
    def controlar_botoes_selecao(n_sel, n_des, options):
        ctx = callback_context
        if not ctx.triggered: return no_update
        trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]
        
        if trigger_id == "emp-btn-sel-todos":
            return [opt["value"] for opt in options]
        return [] # Retorna lista vazia para desmarcar tudo

    # 6. GERA DADOS (CARDS + TABELA)
    @app.callback(
        Output("emp-info-atualizacao", "children"),
        Output("emp-cards-container", "children"),
        Output("emp-tabela", "data"), Output("emp-tabela", "columns"),
        Input("store_filtros", "data"),
        Input("emp-filtro-empenho", "value"), Input("emp-filtro-processo", "value"),
        Input("emp-filtro-credor", "value"), Input("emp-filtro-objeto", "value"),
        Input("emp-checklist-colunas", "value"),
        State("store_opcoes_emp", "data")
    )
    def atualiza_dash_emp(store, f_empenho, f_processo, f_credor, f_objeto, cols_selecionadas, opcoes_base):
        if not store or not store.get("ano"):
            return (no_update,) * 4
        
        df = carrega_base("empenhos", store["ano"], None)

        if df.empty:
            card_atualizacao = gera_card_atualizacao("-")
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
        
        # Função auxiliar para expandir filtros locais
        def expandir_local(selecao, key):
            if not selecao: return []
            nova = []
            for item in selecao:
                if isinstance(item, str) and item.startswith("SELECT_ALL:"):
                    termo = item.split("SELECT_ALL:")[1].lower()
                    if opcoes_base and key in opcoes_base:
                        matches = [opt["value"] for opt in opcoes_base[key] if termo in str(opt["label"]).lower()]
                        nova.extend(matches)
                else:
                    nova.append(item)
            return nova

        # Filtros Locais (Empenho/Processo)
        if f_empenho: df = df[df["codEmpenho"].isin(expandir_local(f_empenho, "filtro-empenho"))]
        if f_processo: df = df[df["codProcesso"].isin(expandir_local(f_processo, "filtro-processo"))]
        if f_credor: df = df[df["txtRazaoSocial"].isin(expandir_local(f_credor, "filtro-credor"))]
        if f_objeto: df = df[df["anexo_descricaoAnexo"].isin(expandir_local(f_objeto, "filtro-objeto"))]

        # 1. Cards
        data_ext = "-"
        # Verifica variações comuns de nome de coluna de data
        col_data = "data_hora_extracao" if "data_hora_extracao" in df.columns else "datExtracao"
        if col_data in df.columns:
            datas = df[col_data].dropna().unique()
            if len(datas) > 0: data_ext = str(datas[0])
        
        card_atualizacao = gera_card_atualizacao(data_ext)

        totais = {c: df[c].sum() for c in DE_PARA_EMPENHOS.keys() if c in df.columns}
        cards = monta_cards_resumo(totais, DE_PARA_EMPENHOS)

        # 2. Tabela
        pivot = gera_tabela_pivot(df, "empenhos")
        
        # Filtra as colunas do DataFrame com base na seleção do usuário
        if cols_selecionadas:
            cols_to_keep = [c for c in pivot.columns if c in cols_selecionadas]
            pivot = pivot[cols_to_keep]

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

    # 7. GERA E FAZ DOWNLOAD DO PDF
    @app.callback(
        Output("emp-download-pdf", "data"),
        Input("emp-btn-download-pdf", "n_clicks"),
        State("store_filtros", "data"),
        State("emp-filtro-empenho", "value"),
        State("emp-filtro-processo", "value"),
        State("emp-filtro-credor", "value"),
        State("emp-filtro-objeto", "value"),
        State("emp-checklist-colunas", "value"),
        prevent_initial_call=True
    )
    def download_pdf_report(n_clicks, store, f_empenho, f_processo, f_credor, f_objeto, cols_selecionadas):
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
        if f_credor: df = df[df["txtRazaoSocial"].isin(f_credor)]
        if f_objeto: df = df[df["anexo_descricaoAnexo"].isin(f_objeto)]
        
        # --- Obter dados para o relatório ---
        totais = {c: df[c].sum() for c in DE_PARA_EMPENHOS.keys() if c in df.columns}
        pivot = gera_tabela_pivot(df, "empenhos")

        # Filtra colunas para o PDF também
        if cols_selecionadas:
            cols_to_keep = [c for c in pivot.columns if c in cols_selecionadas]
            pivot = pivot[cols_to_keep]

        # --- Gerar o PDF ---
        pdf_bytes = criar_relatorio_empenho_pdf(store, totais, pivot)
        
        return dcc.send_bytes(pdf_bytes, "relatorio_empenhos.pdf")

    # 8. GERA E FAZ DOWNLOAD DO EXCEL
    @app.callback(
        Output("emp-download-xlsx", "data"),
        Input("emp-btn-download", "n_clicks"),
        State("emp-tabela", "data"),
        prevent_initial_call=True
    )
    def download_excel_emp(n_clicks, dados_tabela):
        if not dados_tabela:
            return no_update
        
        df_excel = pd.DataFrame(dados_tabela)
        return dcc.send_data_frame(df_excel.to_excel, "empenhos.xlsx", index=False, sheet_name="Empenhos")

    # 10. EXPANDIR SELEÇÃO LOCAL (UI)
    @app.callback(
        Output("emp-filtro-empenho", "value", allow_duplicate=True),
        Output("emp-filtro-processo", "value", allow_duplicate=True),
        Output("emp-filtro-credor", "value", allow_duplicate=True),
        Output("emp-filtro-objeto", "value", allow_duplicate=True),
        Input("emp-filtro-empenho", "value"),
        Input("emp-filtro-processo", "value"),
        Input("emp-filtro-credor", "value"),
        Input("emp-filtro-objeto", "value"),
        State("store_opcoes_emp", "data"),
        prevent_initial_call=True
    )
    def expandir_selecao_ui(v_emp, v_proc, v_cred, v_obj, opcoes_base):
        ctx = callback_context
        if not ctx.triggered or not opcoes_base: return no_update, no_update, no_update, no_update
        
        def process(val, key):
            if not val: return no_update
            has_select_all = any(isinstance(x, str) and x.startswith("SELECT_ALL:") for x in val)
            if not has_select_all: return no_update
            
            nova = []
            for item in val:
                if isinstance(item, str) and item.startswith("SELECT_ALL:"):
                    termo = item.split("SELECT_ALL:")[1].lower()
                    if key in opcoes_base:
                        matches = [opt["value"] for opt in opcoes_base[key] if termo in str(opt["label"]).lower()]
                        nova.extend(matches)
                else:
                    nova.append(item)
            return list(set(nova))

        return (process(v_emp, "filtro-empenho"), process(v_proc, "filtro-processo"), 
                process(v_cred, "filtro-credor"), process(v_obj, "filtro-objeto"))

    # 9. LIMPA FILTROS LOCAIS
    @app.callback(
        Output("emp-filtro-empenho", "value"), Output("emp-filtro-processo", "value"),
        Output("emp-filtro-credor", "value"), Output("emp-filtro-objeto", "value"),
        Input("emp-btn-limpar", "n_clicks"),
        prevent_initial_call=True
    )
    def limpar_filtros_locais(n_clicks):
        return [], [], [], []
