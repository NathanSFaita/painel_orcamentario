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
        # Store para gerenciar estado de loading do botão de download
        dcc.Store(id="trigger-pdf-empenho"),
        
        dbc.Row([
            dbc.Col([dbc.Button("⬅️ Voltar para Execução", href="/", className="w-100 mt-4", 
                                style={"backgroundColor": "#6c757d", "borderColor": "#6c757d", "color": "white"})], md=2),
            dbc.Col([dbc.Button("🛠️ Colunas", id="emp-btn-colunas", className="w-100 mt-4", 
                                style={"backgroundColor": "#0dcaf0", "borderColor": "#0dcaf0", "color": "black"})], md=2),
            dbc.Col([dbc.Button("ℹ️ Saiba Mais", href="/sobre", className="w-100 mt-4", 
                                style={"backgroundColor": "#722f37", "borderColor": "#722f37", "color": "white"})], md=2),
        ], className="mb-4", justify="center"),
        

        layout_filtros_padrao("emp"),
        
        dbc.Row([
            dbc.Col([dbc.Button("🗑️ Limpar Filtros", id="emp-btn-limpar", className="w-100 mt-4", 
                                style={"backgroundColor": "#ffc107", "borderColor": "#ffc107", "color": "black"})], md=2),
            
        ], className="mb-4", justify="center"),           
                
        # MODAL DE SELEÇÃO DE COLUNAS
        dbc.Modal([
            dbc.ModalHeader(dbc.ModalTitle("Selecionar Colunas para Exibição")),
            dbc.ModalBody([
                html.Div([
                    dbc.Button("✅ Selecionar Tudo", id="emp-btn-sel-todos", size="sm", className="me-2", 
                               style={"backgroundColor": "transparent", "borderColor": "#0d6efd", "color": "#0d6efd"}),
                    dbc.Button("❌ Desmarcar Tudo", id="emp-btn-des-todos", size="sm", 
                               style={"backgroundColor": "transparent", "borderColor": "#6c757d", "color": "#6c757d"}),
                ], className="mb-3 d-flex justify-content-center"),
                dbc.Checklist(
                    id="emp-checklist-colunas",
                    options=[{"label": v, "value": k} for k, v in MAPA_COLUNAS_EMPENHOS.items()],
                    value=list(MAPA_COLUNAS_EMPENHOS.keys()), # Todas selecionadas por padrão
                    switch=True,
                )
            ]),
            dbc.ModalFooter(dbc.Button("Fechar", id="emp-btn-fechar-modal", className="ms-auto", n_clicks=0, style={"backgroundColor": "#6c757d", "borderColor": "#6c757d", "color": "white"}))
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
            style_data_conditional=[
                {
                    'if': {'filter_query': '{valEmpenhadoLiquido} > 1000000'},
                    'backgroundColor': '#ffdddd', # Vermelho claro
                    'fontWeight': 'bold'
                },
                {
                    'if': {'filter_query': '{valEmpenhadoLiquido} > 100000 && {valEmpenhadoLiquido} <= 1000000'},
                    'backgroundColor': '#fff3cd', # Amarelo claro
                }
            ],
            page_size=25, sort_action="native", #filter_action="native"
        ),
        dcc.Download(id="emp-download-xlsx"),
        dcc.Download(id="emp-download-pdf"),
        dbc.Button("📥 Download Excel", id="emp-btn-download", className="mt-3", 
                   style={"backgroundColor": "#198754", "borderColor": "#198754", "color": "white"}),
        dbc.Button("📄 Download PDF", id="emp-btn-download-pdf", className="mt-3", 
                   style={"marginLeft": "10px", "backgroundColor": "#dc3545", "borderColor": "#dc3545", "color": "white"}),
        html.Hr(),
        html.Div(id="emp-info-atualizacao")
    ], fluid=True, style={"backgroundColor": "#f8f9fa", "padding": "20px"})
       

def registrar_callbacks_empenhos(app):
    
    # Callback para expandir/recolher filtros
    @app.callback(
        Output("emp-collapse-filtros", "is_open"),
        Input("emp-btn-toggle-filtros", "n_clicks"),
        State("emp-collapse-filtros", "is_open"),
    )
    def toggle_filtros_emp(n, is_open):
        if n:
            return not is_open
        return is_open

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
            "elemento": opts_todos("nome_elemento"), "vinculacao": opts_todos("codVinculacaoRecurso"), "fonte_descricao": opts_todos("fonte_descricao"),
            "fonte": opts_todos("txDescricaoFonteRecurso"), "despesa": opts_todos("codDespesa"),
            "descricao": opts_todos("politicas_para"),
            "filtro-empenho": opts("codEmpenho"), "filtro-processo": opts("codProcesso"),
            "filtro-credor": opts("txtRazaoSocial"), "filtro-objeto": opts("anexo_descricaoAnexo")
        }

    # 2. Atualiza Dropdowns com Search Value
    @app.callback(
        [Output(f"emp-{col}", "options") for col in ["orgao", "coordenacao", "acao", "projeto", "elemento", 
                                                     "vinculacao", "fonte", "despesa", "descricao", "fonte-descricao", "filtro-empenho", "filtro-processo"]] + 
        [Output("emp-filtro-credor", "options"), Output("emp-filtro-objeto", "options")],
        Input("store_filtros", "data"),
        Input("emp-filtro-empenho", "value"), Input("emp-filtro-processo", "value"),
        Input("emp-filtro-credor", "value"), Input("emp-filtro-objeto", "value"),
        [Input(f"emp-{col}", "search_value") for col in ["orgao", "coordenacao", "acao", "projeto", "elemento", 
                                                     "vinculacao", "fonte", "despesa", "descricao", "fonte-descricao", "filtro-empenho", "filtro-processo"]] + 
        [Input("emp-filtro-credor", "search_value"), Input("emp-filtro-objeto", "search_value")]
    )
    def atualiza_dropdowns_emp(store, f_empenho, f_processo, f_credor, f_objeto, *search_values):
        if not store: return [[]] * 14
        
        ano = store.get("ano")
        df = carrega_base("empenhos", ano, None)
        if df.empty: return [[]] * 14

        # Converte data se necessário (para filtro de data)
        if "datEmpenho" in df.columns:
            df["datEmpenho"] = pd.to_datetime(df["datEmpenho"], dayfirst=True, errors='coerce')
        
        keys = ["orgao", "coordenacao", "acao", "projeto", "elemento", "vinculacao", "fonte", "despesa", "descricao",
                "fonte-descricao", "filtro-empenho", "filtro-processo", "filtro-credor", "filtro-objeto"]
        
        mapa_cols = {
            "orgao": "orgao", "coordenacao": "coordenacao", "acao": "acao_programatica", 
            "projeto": "codProjetoAtividade", "elemento": "nome_elemento", "vinculacao": "codVinculacaoRecurso", "fonte_descricao": "fonte_descricao",
            "fonte": "txDescricaoFonteRecurso", "despesa": "codDespesa", "descricao": "politicas_para",
            "filtro-empenho": "codEmpenho", "filtro-processo": "codProcesso",
            "filtro-credor": "txtRazaoSocial", "filtro-objeto": "anexo_descricaoAnexo"
        }

        # Dicionário com os valores atuais de cada filtro (Global + Local)
        valores_atuais = {
            "filtro-empenho": f_empenho, "filtro-processo": f_processo,
            "filtro-credor": f_credor, "filtro-objeto": f_objeto
        }
        # Adiciona os globais do store
        for k in keys[:10]: # As 10 primeiras chaves são globais
            valores_atuais[k] = store.get(k, ["Todos"])

        outputs = []
        for i, key in enumerate(keys):
            df_filtered = df.copy()
            
            # 1. Aplica Filtro de Data (sempre)
            if store.get("data_inicio") and store.get("data_fim") and "datEmpenho" in df_filtered.columns:
                start = pd.to_datetime(store["data_inicio"])
                end = pd.to_datetime(store["data_fim"])
                df_filtered = df_filtered[(df_filtered["datEmpenho"] >= start) & (df_filtered["datEmpenho"] <= end)]

            # 2. Aplica todos os outros filtros EXCETO o atual
            for key_filter in keys:
                if key_filter == key: continue
                
                vals = valores_atuais.get(key_filter)
                col_name = mapa_cols[key_filter]
                
                if vals and "Todos" not in vals and col_name in df_filtered.columns:
                     df_filtered = df_filtered[df_filtered[col_name].isin(vals)]

            # 3. Gera opções, garantindo que a seleção atual seja mantida
            col_target = mapa_cols[key]
            options = []
            
            # Pega a seleção atual do store para este filtro
            current_selection = valores_atuais.get(key, ["Todos"])
            if current_selection is None:
                current_selection = [] # Garante que é uma lista para evitar TypeError

            if col_target in df_filtered.columns:
                unique_vals_from_filtered_df = set(df_filtered[col_target].dropna().unique())
                
                # Combina a seleção atual com as opções possíveis para não perder o valor
                if "Todos" in current_selection:
                    final_vals = unique_vals_from_filtered_df
                else:
                    final_vals = set(current_selection).union(unique_vals_from_filtered_df)
                
                options = [{"label": str(v), "value": v} for v in sorted(list(final_vals))]

            # Adiciona "Todos" no início
            options.insert(0, {"label": "Todos", "value": "Todos"})
            search = search_values[i]
            if search:
                options = [opt for opt in options if search.lower() in str(opt["label"]).lower()]
            
            outputs.append(options)

        return outputs

    # 3. UI -> STORE (Salva alterações e aplica lógica do "Todos")
    @app.callback(
        Output("store_filtros", "data", allow_duplicate=True),
        Input("emp-btn-limpar", "n_clicks"), Input("emp-ano", "value"),
        Input("emp-orgao", "value"), Input("emp-coordenacao", "value"),
        Input("emp-acao", "value"), Input("emp-projeto", "value"),
        Input("emp-elemento", "value"), Input("emp-vinculacao", "value"),
        Input("emp-fonte", "value"), Input("emp-despesa", "value"), Input("emp-descricao", "value"), Input("emp-fonte-descricao", "value"),
        Input("emp-date-picker", "start_date"), Input("emp-date-picker", "end_date"),
        State("store_filtros", "data"), prevent_initial_call=True
    )
    def update_store_emp(n_limpar, ano, orgao, coord, acao, proj, elem, vinc, fonte, desp, desc, fonte_desc, start_date, end_date, store):
        if not ano: return no_update
        if store is None: store = {}
        ctx = callback_context
        trigger_id = ctx.triggered[0]["prop_id"]
        
        if "emp-btn-limpar" in trigger_id:
            return {**store, "ano": ano_padrao, "orgao": ["Todos"], "coordenacao": ["Todos"], "acao": ["Todos"],
                    "projeto": ["Todos"], "descricao": ["Todos"], "elemento": ["Todos"], "vinculacao": ["Todos"], 
                    "fonte": ["Todos"], "despesa": ["Todos"], "fonte_descricao": ["Todos"], "data_inicio": None, "data_fim": None}

        store.update({
            "ano": ano,
            "orgao": tratar_selecao_todos(orgao, store.get("orgao")),
            "coordenacao": tratar_selecao_todos(coord, store.get("coordenacao")),
            "acao": tratar_selecao_todos(acao, store.get("acao")),
            "projeto": tratar_selecao_todos(proj, store.get("projeto")),
            "elemento": tratar_selecao_todos(elem, store.get("elemento")),
            "vinculacao": tratar_selecao_todos(vinc, store.get("vinculacao")),
            "fonte": tratar_selecao_todos(fonte, store.get("fonte")),
            "despesa": tratar_selecao_todos(desp, store.get("despesa")),
            "descricao": tratar_selecao_todos(desc, store.get("descricao")),
            "fonte_descricao": tratar_selecao_todos(fonte_desc, store.get("fonte_descricao")),
            "data_inicio": start_date,
            "data_fim": end_date
        })
        return store

    # 3. STORE -> UI (Carrega dados do Store para os Dropdowns)
    @app.callback(
        [Output("emp-ano", "value")] + [Output(f"emp-{k}", "value") for k in ["orgao","coordenacao","acao","projeto","elemento","vinculacao","fonte","despesa","descricao", "fonte-descricao"]] +
        [Output("emp-date-picker", "start_date"), Output("emp-date-picker", "end_date")],
        Input("store_filtros", "data")
    )
    def sync_ui_emp(store):
        if not store: return (ano_padrao,) + (["Todos"],)*10 + (None, None)
        return (store.get("ano", ano_padrao),
                store.get("orgao", ["Todos"]), store.get("coordenacao", ["Todos"]), 
                store.get("acao", ["Todos"]), store.get("projeto", ["Todos"]),
                store.get("elemento", ["Todos"]), store.get("vinculacao", ["Todos"]), 
                store.get("fonte", ["Todos"]), store.get("despesa", ["Todos"]), store.get("descricao", ["Todos"]),
                store.get("fonte_descricao", ["Todos"]),
                store.get("data_inicio"), store.get("data_fim"))

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
        Input("emp-checklist-colunas", "value")
    )
    def atualiza_dash_emp(store, f_empenho, f_processo, f_credor, f_objeto, cols_selecionadas):
        if not store or not store.get("ano"):
            return (no_update,) * 4
        
        df = carrega_base("empenhos", store["ano"], None)

        if df.empty:
            card_atualizacao = gera_card_atualizacao("-")
            return card_atualizacao, html.Div("Sem dados."), [], []

        # Converte para datetime para permitir ordenação e filtragem corretas
        if "datEmpenho" in df.columns:
            df["datEmpenho"] = pd.to_datetime(df["datEmpenho"], dayfirst=True, errors='coerce')

        # Aplica Filtros Globais
        mapa = {"orgao": "orgao", "coordenacao": "coordenacao", "acao": "acao_programatica", 
                "projeto": "codProjetoAtividade", "elemento": "nome_elemento", "vinculacao": "codVinculacaoRecurso", 
                "fonte": "txDescricaoFonteRecurso", "despesa": "codDespesa", "descricao": "politicas_para", "fonte_descricao": "fonte_descricao"}
        
        for k_store, col_df in mapa.items():
            vals = store.get(k_store, ["Todos"])
            if "Todos" not in vals and col_df in df.columns:
                if col_df in ["codVinculacaoRecurso", "codDespesa"]: # Trata codigo como string/int conforme base
                    df = df[df[col_df].isin(vals)] # Ajuste se precisar de conversão str/int
                else:
                    df = df[df[col_df].isin(vals)]
        

        # Filtro de Data (Range)
        if store.get("data_inicio") and store.get("data_fim") and "datEmpenho" in df.columns:
            start = pd.to_datetime(store["data_inicio"])
            end = pd.to_datetime(store["data_fim"])
            df = df[(df["datEmpenho"] >= start) & (df["datEmpenho"] <= end)]

        # Filtros Locais (Empenho/Processo)
        if f_empenho: df = df[df["codEmpenho"].isin(f_empenho)]
        if f_processo: df = df[df["codProcesso"].isin(f_processo)]
        if f_credor: df = df[df["txtRazaoSocial"].isin(f_credor)]
        if f_objeto: df = df[df["anexo_descricaoAnexo"].isin(f_objeto)]

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
        
        # Ordena por Data do Empenho (Decrescente) e formata para exibição
        if "datEmpenho" in pivot.columns:
            pivot = pivot.sort_values("datEmpenho", ascending=False)
            pivot["datEmpenho"] = pivot["datEmpenho"].dt.strftime('%d/%m/%Y')

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

    @app.callback(
        Output("trigger-pdf-empenho", "data"),
        Output("emp-btn-download-pdf", "disabled"),
        Input("emp-btn-download-pdf", "n_clicks"),
        State("trigger-pdf-empenho", "data"),
        prevent_initial_call=True
    )
    def trigger_download_empenho(n_clicks, data):
        """Callback rápido que desabilita o botão e dispara o processo de geração."""
        counter = (data or 0) + 1
        return counter, True

    @app.callback(
        Output("emp-download-pdf", "data"),
        Output("emp-btn-download-pdf", "disabled", allow_duplicate=True),
        Input("trigger-pdf-empenho", "data"),
        State("store_filtros", "data"),
        State("emp-filtro-empenho", "value"),
        State("emp-filtro-processo", "value"),
        State("emp-filtro-credor", "value"),
        State("emp-filtro-objeto", "value"),
        State("emp-checklist-colunas", "value"),
        prevent_initial_call=True
    )
    def download_pdf_report(trigger, store, f_empenho, f_processo, f_credor, f_objeto, cols_selecionadas):
        """Callback 'worker' que gera o PDF e reabilita o botão no final."""
        if not trigger or not store or not store.get("ano"):
            return no_update, False
        
        # --- Replicar a lógica de filtragem ---
        df = carrega_base("empenhos", store["ano"], None)
        if df.empty: return no_update, False

        mapa = {"orgao": "orgao", "coordenacao": "coordenacao", "acao": "acao_programatica", 
                "projeto": "codProjetoAtividade", "elemento": "nome_elemento", "vinculacao": "codVinculacaoRecurso", 
                "fonte": "txDescricaoFonteRecurso", "despesa": "codDespesa", "descricao": "politicas_para", "fonte_descricao": "fonte_descricao"}
        
        for k_store, col_df in mapa.items():
            vals = store.get(k_store, ["Todos"])
            if "Todos" not in vals and col_df in df.columns:
                df = df[df[col_df].isin(vals)]
        
        # Filtro de Data
        if store.get("data_inicio") and store.get("data_fim") and "datEmpenho" in df.columns:
            df["dt_temp"] = pd.to_datetime(df["datEmpenho"], dayfirst=True, errors="coerce")
            start = pd.to_datetime(store["data_inicio"])
            end = pd.to_datetime(store["data_fim"])
            df = df[(df["dt_temp"] >= start) & (df["dt_temp"] <= end)]

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
        
        return dcc.send_bytes(pdf_bytes, "relatorio_empenhos.pdf"), False

    # 8. GERA E FAZ DOWNLOAD DO EXCEL
    @app.callback(
        Output("emp-download-xlsx", "data"),
        Input("emp-btn-download", "n_clicks"),
        State("emp-tabela", "data"),prevent_initial_call=True
    )
    def download_excel_emp(n_clicks, dados_tabela):
        if not dados_tabela:
            return no_update
        
        df_excel = pd.DataFrame(dados_tabela)
        return dcc.send_data_frame(df_excel.to_excel, "empenhos.xlsx", index=False, sheet_name="Empenhos")

    # 9. LIMPA FILTROS LOCAIS
    @app.callback(
        Output("emp-filtro-empenho", "value"), Output("emp-filtro-processo", "value"),
        Output("emp-filtro-credor", "value"), Output("emp-filtro-objeto", "value"),
        Input("emp-btn-limpar", "n_clicks"),
        prevent_initial_call=True
    )
    def limpar_filtros_locais(n_clicks):
        return [], [], [], []
