import dash
import pandas as pd
from dash import html, dcc, Input, Output, State, callback_context, no_update
import dash_bootstrap_components as dbc
from dash import dash_table as dt
from dash.dash_table.Format import Format, Scheme, Symbol, Group
from filtros import layout_filtros_padrao, ano_padrao
from utils import (carrega_base, lista_meses, gera_tabela_pivot,
                   cabecalho_padrao, tratar_selecao_todos, monta_cards_resumo,
                   DE_PARA_EXECUCAO, DE_PARA_INDICES_EXECUCAO, gera_card_atualizacao)
from gerar_pdf import criar_relatorio_execucao_pdf

# Mapa completo de colunas disponíveis para seleção
MAPA_COLUNAS_EXECUCAO = {**DE_PARA_INDICES_EXECUCAO, **DE_PARA_EXECUCAO}

def layout_execucao():
    return dbc.Container([
        cabecalho_padrao("📊 Quadro de Detalhamento de Despesas", "📈 Execução Orçamentária"),
        
        html.Div(id="exe-cards-container", className="mb-4"),
        # Store para guardar as opções dos filtros e evitar recargas desnecessárias
        dcc.Store(id="store_opcoes_exe", storage_type="memory"),
        
        dbc.Row([
            dbc.Col([dbc.Button("Ir para Empenhos ➡️", href="/empenhos", className="w-100 mt-4", 
                                style={"whiteSpace": "normal", "backgroundColor": "#0d6efd", "borderColor": "#0d6efd", "color": "white"})], md=2),
            dbc.Col([dbc.Button("🛠️ Colunas", id="exe-btn-colunas", className="w-100 mt-4", 
                                style={"whiteSpace": "normal", "backgroundColor": "#0dcaf0", "borderColor": "#0dcaf0", "color": "black"})], md=2),
            dbc.Col([dbc.Button("ℹ️ Saiba Mais", href="/sobre", className="w-100 mt-4", 
                                style={"whiteSpace": "normal", "backgroundColor": "#722f37", "borderColor": "#722f37", "color": "white"})], md=2),
        ], className="mb-4", justify="center"),
        

        layout_filtros_padrao("exe"),
        
        dbc.Row([
            # dbc.Col([html.Label("Mês:", className="fw-bold"), dcc.Dropdown(id="exe-mes", clearable=False)], md=1),
            dbc.Col([dbc.Button("🗑️ Limpar Filtros", id="exe-btn-limpar", className="w-100 mt-4", style={"whiteSpace": "normal", "backgroundColor": "#ffc107", "borderColor": "#ffc107", "color": "black"})], md=2),
            
        ], className="mb-4", justify="center"),

        # MODAL DE SELEÇÃO DE COLUNAS
        dbc.Modal([
            dbc.ModalHeader(dbc.ModalTitle("Selecionar Colunas para Exibição")),
            dbc.ModalBody([
                html.Div([
                    dbc.Button("✅ Selecionar Tudo", id="exe-btn-sel-todos", size="sm", className="me-2", 
                               style={"backgroundColor": "transparent", "borderColor": "#0d6efd", "color": "#0d6efd"}),
                    dbc.Button("❌ Desmarcar Tudo", id="exe-btn-des-todos", size="sm", 
                               style={"backgroundColor": "transparent", "borderColor": "#6c757d", "color": "#6c757d"}),
                ], className="mb-3 d-flex justify-content-center"),
                dbc.Checklist(
                    id="exe-checklist-colunas",
                    options=[{"label": v, "value": k} for k, v in MAPA_COLUNAS_EXECUCAO.items()],
                    value=list(MAPA_COLUNAS_EXECUCAO.keys()), # Todas selecionadas por padrão
                    switch=True,
                )
            ]),
            dbc.ModalFooter(dbc.Button("Fechar", id="exe-btn-fechar-modal", className="ms-auto", n_clicks=0, 
                                       style={"backgroundColor": "#6c757d", "borderColor": "#6c757d", "color": "white"}))
        ], id="exe-modal-colunas", is_open=False),

        html.H5("Detalhamento", className="fw-bold"),
        dt.DataTable(
            id="exe-tabela",
            style_table={"overflowX": "auto"},
            style_header={"backgroundColor": "#1f77b4", "color": "white", "fontWeight": "bold", "fontSize": "14px",  "fontFamily": "Arial, sans-serif"},
            style_cell={"textAlign": "left", "minWidth": "100px", "fontSize": "12px", "fontFamily": "Arial, sans-serif"},
            page_size=25, sort_action="native", #filter_action="native"
        ),
        dcc.Download(id="exe-download-xlsx"),
        dcc.Download(id="exe-download-pdf"),
        dbc.Button("📥 Download Excel", id="exe-btn-download", className="mt-3", 
                   style={"backgroundColor": "#198754", "borderColor": "#198754", "color": "white"}),
        dbc.Button("📄 Download PDF", id="exe-btn-download-pdf", className="mt-3", 
                    style={"marginLeft": "10px", "backgroundColor": "#dc3545", "borderColor": "#dc3545", "color": "white"}),
        html.Hr(),
        html.Div(id="exe-info-atualizacao")
        ], fluid=True, style={"backgroundColor": "#f8f9fa", "padding": "20px"})

def registrar_callbacks_execucao(app):
    
    # Callback para expandir/recolher filtros
    @app.callback(
        Output("exe-collapse-filtros", "is_open"),
        Input("exe-btn-toggle-filtros", "n_clicks"),
        State("exe-collapse-filtros", "is_open"),
    )
    def toggle_filtros_exe(n, is_open):
        if n:
            return not is_open
        return is_open

    # @app.callback(
    #     Output("exe-mes", "options"), Output("exe-mes", "value"),
    #     Input("exe-ano", "value"),
    #     State("store_filtros", "data")
    # )
    # def atualiza_meses(ano, store):
    #     if not ano: return [], None
    #     meses = lista_meses("execucao", ano)
        
    #     # Se o ano mudou manualmente (diferente do store), pega o último mês.
    #     # Se for load inicial ou reset (ano == store), respeita o mês do store.
    #     ano_store = store.get("ano") if store else None
    #     mes_store = store.get("mes") if store else None
        
    #     if str(ano) != str(ano_store):
    #         mes_selecionado = meses[-1] if meses else None
    #     else:
    #         mes_selecionado = mes_store if mes_store in meses else (meses[-1] if meses else None)
            
    #     return [{"label": m, "value": m} for m in meses], mes_selecionado

    # 1. Gera as opções base e salva no Store (Separado da renderização visual)
    @app.callback(
        Output("store_opcoes_exe", "data"),
        Input("exe-ano", "value")
    )
    def carrega_opcoes_base_exe(ano):
        if not ano:
            return {}

        meses = lista_meses("execucao", ano)
        mes = meses[-1] if meses else None
        if not mes:
            return {}
        df = carrega_base("execucao", ano, mes)
        if df.empty:
            return {}

        mapa_cols = {
            "orgao": "orgao", "coordenacao": "coordenação", "acao": "acao_programatica",
            "projeto": "projeto_atividade", "elemento": "nome_elemento", "vinculacao": "vinculacao",
            "fonte": "ds_fonte", "despesa": "despesa", "descricao": "politicas_para"
        }
        
        opcoes_dict = {}
        def get_opts(col_df):
            if col_df in df.columns:
                opcoes = sorted(df[col_df].dropna().unique())
                return [{"label": "Todos", "value": "Todos"}] + [{"label": str(o), "value": o} for o in opcoes]
            return [{"label": "Todos", "value": "Todos"}]

        for k, col in mapa_cols.items():
            opcoes_dict[k] = get_opts(col)
            
        return opcoes_dict

    # 2. Atualiza os Dropdowns com base no Store e no Search Value (Injeta "Selecionar Todos")
    @app.callback(
        [Output(f"exe-{k}", "options") for k in ["orgao","coordenacao","acao","projeto","elemento","vinculacao","fonte","despesa","descricao"]],
        Input("store_filtros", "data"),
        [Input(f"exe-{k}", "search_value") for k in ["orgao","coordenacao","acao","projeto","elemento","vinculacao","fonte","despesa","descricao"]]
    )
    def atualiza_dropdowns_exe(store, s_orgao, s_coord, s_acao, s_proj, s_elem, s_vinc, s_fonte, s_desp, s_desc):
        if not store:
            return [[{"label": "Todos", "value": "Todos"}] for _ in range(9)]
        
        ano = store.get("ano")
        mes = store.get("mes")
        
        df = carrega_base("execucao", ano, mes)
        if df.empty:
             return [[{"label": "Todos", "value": "Todos"}] for _ in range(9)]

        keys = ["orgao","coordenacao","acao","projeto","elemento","vinculacao","fonte","despesa","descricao"]
        mapa_cols = {
            "orgao": "orgao", "coordenacao": "coordenação", "acao": "acao_programatica",
            "projeto": "projeto_atividade", "elemento": "nome_elemento", "vinculacao": "vinculacao",
            "fonte": "ds_fonte", "despesa": "despesa", "descricao": "politicas_para"
        }
        
        # Lista de search values na mesma ordem dos outputs
        search_values = [s_orgao, s_coord, s_acao, s_proj, s_elem, s_vinc, s_fonte, s_desp, s_desc]
        
        outputs = []
        for i, key_target in enumerate(keys):
            # Filtra o DF com base em todos os filtros EXCETO o atual
            df_filtered = df.copy()
            for key_filter in keys:
                if key_filter == key_target:
                    continue
                
                vals = store.get(key_filter, ["Todos"])
                col_name = mapa_cols[key_filter]
                
                if "Todos" not in vals and col_name in df_filtered.columns:
                    df_filtered = df_filtered[df_filtered[col_name].isin(vals)]
            
            # Gera opções a partir do DF filtrado
            col_target = mapa_cols[key_target]
            options = []
            if col_target in df_filtered.columns:
                unique_vals = sorted(df_filtered[col_target].dropna().unique())
                options = [{"label": "Todos", "value": "Todos"}] + [{"label": str(v), "value": v} for v in unique_vals]
            else:
                options = [{"label": "Todos", "value": "Todos"}]
            
            # Filtro de busca (search_value)
            search = search_values[i]
            if search:
                options = [opt for opt in options if search.lower() in str(opt["label"]).lower()]
                options.insert(0, {"label": f"Selecionar todos contendo '{search}'", "value": f"SELECT_ALL:{search}"})
            
            outputs.append(options)
        
        return outputs

    # 1. UI -> STORE (Salva alterações e aplica lógica do "Todos")
    @app.callback(
        Output("store_filtros", "data", allow_duplicate=True),
        Input("exe-btn-limpar", "n_clicks"), Input("exe-ano", "value"), # Input("exe-mes", "value")
        Input("exe-orgao", "value"), Input("exe-coordenacao", "value"), Input("exe-acao", "value"), Input("exe-projeto", "value"),
        Input("exe-elemento", "value"), Input("exe-vinculacao", "value"),
        Input("exe-fonte", "value"), Input("exe-despesa", "value"), Input("exe-descricao", "value"),
        State("store_filtros", "data"), 
        State("store_opcoes_exe", "data"), prevent_initial_call=True
    )
    def salva_filtros_exe(n_clicks, ano, orgao, coord, acao, proj, elem, vinc, fonte, desp, desc, store, opcoes_base):
        if store is None: store = {}
        ctx = callback_context
        trigger_id = ctx.triggered[0]["prop_id"]

        if "exe-btn-limpar" in trigger_id:
            # Reseta para o ano e mês mais recentes
            novo_ano = ano_padrao
            meses = lista_meses("execucao", novo_ano)
            novo_mes = meses[-1] if meses else None
            return {**store, "ano": novo_ano, "mes": novo_mes, "orgao": ["Todos"], "coordenacao": ["Todos"],
                    "acao": ["Todos"], "projeto": ["Todos"], "descricao": ["Todos"], "elemento": ["Todos"], "vinculacao": ["Todos"],
                    "fonte": ["Todos"], "despesa": ["Todos"]}
        
        # Função para expandir "SELECT_ALL"
        def processar_selecao(selecao, key):
            if not selecao: return ["Todos"]
            nova_selecao = []
            expandiu = False
            for item in selecao:
                if isinstance(item, str) and item.startswith("SELECT_ALL:"):
                    termo = item.split("SELECT_ALL:")[1].lower()
                    # Busca nas opções base
                    if opcoes_base and key in opcoes_base:
                        matches = [opt["value"] for opt in opcoes_base[key] if termo in str(opt["label"]).lower() and opt["value"] != "Todos"]
                        nova_selecao.extend(matches)
                    expandiu = True
                else:
                    nova_selecao.append(item)
            
            return tratar_selecao_todos(nova_selecao, store.get(key)) if not expandiu else nova_selecao

        # A base a ser exibida é sempre a mais recente de cada ano
        meses = lista_meses("execucao", ano)
        mes_atualizado = meses[-1] if meses else None

        store.update({
            "ano": ano, "mes": mes_atualizado,
            "orgao": processar_selecao(orgao, "orgao"),
            "coordenacao": processar_selecao(coord, "coordenacao"),
            "acao": processar_selecao(acao, "acao"),
            "projeto": processar_selecao(proj, "projeto"),
            "elemento": processar_selecao(elem, "elemento"),
            "vinculacao": processar_selecao(vinc, "vinculacao"),
            "fonte": processar_selecao(fonte, "fonte"),
            "despesa": processar_selecao(desp, "despesa"),
            "descricao": processar_selecao(desc, "descricao")
        })
        return store

    # 2. STORE -> UI (Carrega dados do Store para os Dropdowns)
    @app.callback(
        [Output("exe-ano", "value")] + [Output(f"exe-{k}", "value") for k in ["orgao","coordenacao","acao","projeto","elemento","vinculacao","fonte","despesa","descricao"]],
        Input("store_filtros", "data")
    )
    def carrega_ui_exe(store):
        if not store: return (ano_padrao,) + (["Todos"],)*9
        return (store.get("ano", ano_padrao),
                store.get("orgao", ["Todos"]), store.get("coordenacao", ["Todos"]), 
                store.get("acao", ["Todos"]), store.get("projeto", ["Todos"]),
                store.get("elemento", ["Todos"]), store.get("vinculacao", ["Todos"]), 
                store.get("fonte", ["Todos"]), store.get("despesa", ["Todos"]), store.get("descricao", ["Todos"]))

    # 3. CONTROLE DO MODAL DE COLUNAS
    @app.callback(
        Output("exe-modal-colunas", "is_open"),
        Input("exe-btn-colunas", "n_clicks"),
        Input("exe-btn-fechar-modal", "n_clicks"),
        State("exe-modal-colunas", "is_open"),
        prevent_initial_call=True
    )
    def toggle_modal_colunas(n1, n2, is_open):
        if n1 or n2:
            return not is_open
        return is_open

    # 4. CONTROLE DOS BOTÕES SELECIONAR/DESMARCAR TUDO
    @app.callback(
        Output("exe-checklist-colunas", "value"),
        Input("exe-btn-sel-todos", "n_clicks"),
        Input("exe-btn-des-todos", "n_clicks"),
        State("exe-checklist-colunas", "options"),
        prevent_initial_call=True
    )
    def controlar_botoes_selecao(n_sel, n_des, options):
        ctx = callback_context
        if not ctx.triggered: return no_update
        trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]
        
        if trigger_id == "exe-btn-sel-todos":
            return [opt["value"] for opt in options]
        return [] # Retorna lista vazia para desmarcar tudo

    # 5. GERA DADOS (Cards + Tabela)
    @app.callback(
        Output("exe-info-atualizacao", "children"),
        Output("exe-cards-container", "children"),
        Output("exe-tabela", "data"), Output("exe-tabela", "columns"),
        Input("store_filtros", "data"),
        Input("exe-checklist-colunas", "value")
    )
    def atualiza_dashboard_exe(store, cols_selecionadas):
        if not store or not store.get("mes"):
            return no_update, [], [], []

        df = carrega_base("execucao", store["ano"], store["mes"])

        if df.empty:
            card_atualizacao = gera_card_atualizacao("-")
            return card_atualizacao, html.Div("Sem dados para o período."), [], []
            
        # =========================================
        # MAPA DE FILTROS - BASEADO NA SUA LISTA
        # =========================================
        mapa_filtros = {
            "orgao": "orgao",
            "coordenacao": "coordenação", # Atenção ao acento
            "acao": "acao_programatica", 
            "projeto": "projeto_atividade",
            "elemento": "nome_elemento",
            "vinculacao": "vinculacao",
            "fonte": "ds_fonte",
            "despesa": "despesa",
            "descricao": "politicas_para"
        }

        for k_store, col_df in mapa_filtros.items():
            vals = store.get(k_store, ["Todos"])
            if "Todos" not in vals and col_df in df.columns:
                df = df[df[col_df].isin(vals)]

        # Ajuste do Valor Congelado (Congelado Líquido = Congelado - Descongelado)
        if "valCongelado" in df.columns and "valDescongelado" in df.columns:
            df["valCongelado"] = df["valCongelado"].fillna(0) - df["valDescongelado"].fillna(0)

        # Cálculo de Totais
        # Soma apenas as colunas numéricas que existem no DataFrame
        cols_numericas = [c for c in DE_PARA_EXECUCAO.keys() if c in df.columns and c != "Saldo de Dotação"]
        totais = {c: df[c].sum() for c in cols_numericas}
        
        # Calcula Saldo de Dotação e Saldo de Reserva: 
        disponivel = totais.get("valDisponivel", 0)
        reservado = totais.get("valReservadoLiquido", 0)
        empenhado = totais.get("valEmpenhadoLiquido", 0)
        totais["Saldo de Dotação"] = disponivel - reservado
        totais["Saldo de Reserva"] = reservado - empenhado


        # Data de extração
        data_ext = "-"
        if "data_hora_extracao" in df.columns:
            datas_unicas = df["data_hora_extracao"].dropna().unique()
            if len(datas_unicas) > 0:
                data_ext = str(datas_unicas[0])
        
        card_atualizacao = gera_card_atualizacao(data_ext)

        # Gera componentes
        cards = monta_cards_resumo(totais, DE_PARA_EXECUCAO)
        pivot = gera_tabela_pivot(df, "execucao")

        # Adiciona colunas calculadas na tabela (Saldo de Dotação e Saldo de Reserva)
        if not pivot.empty:
            for col in ["valDisponivel", "valReservadoLiquido", "valEmpenhadoLiquido"]:
                if col not in pivot.columns: pivot[col] = 0.0
            
            pivot["Saldo de Dotação"] = pivot["valDisponivel"] - pivot["valReservadoLiquido"]
            pivot["Saldo de Reserva"] = pivot["valReservadoLiquido"] - pivot["valEmpenhadoLiquido"]

        # Filtra as colunas do DataFrame com base na seleção do usuário
        if cols_selecionadas:
            cols_to_keep = [c for c in pivot.columns if c in cols_selecionadas]
            pivot = pivot[cols_to_keep]
        
        cols_table = []
        
        # 1. Colunas de Texto (Índices) - Segue a ordem do dicionário
        for c in DE_PARA_INDICES_EXECUCAO:
            if c in pivot.columns:
                cols_table.append({
                    "name": DE_PARA_INDICES_EXECUCAO[c], 
                    "id": c, 
                    "type": "text", 
                    "format": None
                })

        # 2. Colunas Numéricas (Valores) - Segue a ordem do dicionário
        for c in DE_PARA_EXECUCAO:
            if c in pivot.columns:
                cols_table.append({
                    "name": DE_PARA_EXECUCAO[c], 
                    "id": c, 
                    "type": "numeric", 
                    "format": Format(
                        scheme=Scheme.fixed, 
                        precision=2, 
                        group=Group.yes, 
                        group_delimiter='.', 
                        decimal_delimiter=',', 
                        symbol=Symbol.yes, 
                        symbol_prefix='R$ '
                    )
                })

        return card_atualizacao, cards, pivot.to_dict("records"), cols_table

    # 6. GERA E FAZ DOWNLOAD DO PDF
    @app.callback(
        Output("exe-download-pdf", "data"),
        Input("exe-btn-download-pdf", "n_clicks"),
        State("store_filtros", "data"),
        State("exe-checklist-colunas", "value"),
        prevent_initial_call=True
    )
    def download_pdf_exe(n_clicks, store, cols_selecionadas):
        if not store or not store.get("mes"):
            return no_update

        df = carrega_base("execucao", store["ano"], store["mes"])
        if df.empty:
            return no_update

        # Extrai data de extração
        data_ext = "-"
        if "data_hora_extracao" in df.columns:
            datas = df["data_hora_extracao"].dropna().unique()
            if len(datas) > 0:
                data_ext = str(datas[0])

        # Replicar filtros
        mapa_filtros = {
            "orgao": "orgao", "coordenacao": "coordenação", "acao": "acao_programatica", 
            "projeto": "projeto_atividade", "elemento": "nome_elemento", "vinculacao": "vinculacao",
            "fonte": "ds_fonte", "despesa": "despesa", "descricao": "politicas_para"
        }
        for k_store, col_df in mapa_filtros.items():
            vals = store.get(k_store, ["Todos"])
            if "Todos" not in vals and col_df in df.columns:
                df = df[df[col_df].isin(vals)]

        # Ajuste do Valor Congelado (Congelado Líquido = Congelado - Descongelado)
        if "valCongelado" in df.columns and "valDescongelado" in df.columns:
            df["valCongelado"] = df["valCongelado"].fillna(0) - df["valDescongelado"].fillna(0)

        # Calcular Totais
        cols_numericas = [c for c in DE_PARA_EXECUCAO.keys() if c in df.columns and c != "Saldo de Dotação"]
        totais = {c: df[c].sum() for c in cols_numericas}
        
        disponivel = totais.get("valDisponivel", 0)
        reservado = totais.get("valReservadoLiquido", 0)
        empenhado = totais.get("valEmpenhadoLiquido", 0)
        totais["Saldo de Dotação"] = disponivel - reservado
        totais["Saldo de Reserva"] = reservado - empenhado

        pivot = gera_tabela_pivot(df, "execucao")

        # Adiciona colunas calculadas na tabela do PDF
        if not pivot.empty:
            for col in ["valDisponivel", "valReservadoLiquido", "valEmpenhadoLiquido"]:
                if col not in pivot.columns: pivot[col] = 0.0
            pivot["Saldo de Dotação"] = pivot["valDisponivel"] - pivot["valReservadoLiquido"]
            pivot["Saldo de Reserva"] = pivot["valReservadoLiquido"] - pivot["valEmpenhadoLiquido"]

        # Filtra colunas para o PDF também
        if cols_selecionadas:
            cols_to_keep = [c for c in pivot.columns if c in cols_selecionadas]
            pivot = pivot[cols_to_keep]
        
        pdf_bytes = criar_relatorio_execucao_pdf(store, totais, pivot, data_ext)
        return dcc.send_bytes(pdf_bytes, "relatorio_execucao.pdf")

    # 5. GERA E FAZ DOWNLOAD DO EXCEL
    @app.callback(
        Output("exe-download-xlsx", "data"),
        Input("exe-btn-download", "n_clicks"),
        State("exe-tabela", "data"),
        prevent_initial_call=True
    )
    def download_excel_exe(n_clicks, dados_tabela):
        if not dados_tabela:
            return no_update
        
        df_excel = pd.DataFrame(dados_tabela)
        return dcc.send_data_frame(df_excel.to_excel, "execucao_orcamentaria.xlsx", index=False, sheet_name="Execução")
