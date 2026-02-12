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

def layout_execucao():
    return dbc.Container([
        cabecalho_padrao("📊 Quadro de Detalhamento de Despesas", "📈 Execução Orçamentária"),
        html.Div(id="exe-cards-container", className="mb-4"),
        
        layout_filtros_padrao("exe"),
        
        dbc.Row([
            dbc.Col([html.Label("Mês:", className="fw-bold"), dcc.Dropdown(id="exe-mes", clearable=False)], md=1),
            dbc.Col([dbc.Button("🗑️ Limpar Filtros", id="exe-btn-limpar", color="warning", className="w-100 mt-4")], md=2),
            dbc.Col([dbc.Button("Ir para Empenhos ➡️", href="/empenhos", color="primary", className="w-100 mt-4")], md=2),
        ], className="mb-4", justify="center"),

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
        dbc.Button("📥 Download Excel", id="exe-btn-download", color="success", className="mt-3"),
        dbc.Button("📄 Download PDF", id="exe-btn-download-pdf", color="danger", className="mt-3", style={"marginLeft": "10px"}),
        html.Hr(),
        html.Div(id="exe-info-atualizacao")
        ], fluid=True, style={"backgroundColor": "#f8f9fa", "padding": "20px"})

def registrar_callbacks_execucao(app):
    
    @app.callback(
        Output("exe-mes", "options"), Output("exe-mes", "value"),
        Input("exe-ano", "value"),
        State("store_filtros", "data")
    )
    def atualiza_meses(ano, store):
        if not ano: return [], None
        meses = lista_meses("execucao", ano)
        
        # Se o ano mudou manualmente (diferente do store), pega o último mês.
        # Se for load inicial ou reset (ano == store), respeita o mês do store.
        ano_store = store.get("ano") if store else None
        mes_store = store.get("mes") if store else None
        
        if str(ano) != str(ano_store):
            mes_selecionado = meses[-1] if meses else None
        else:
            mes_selecionado = mes_store if mes_store in meses else (meses[-1] if meses else None)
            
        return [{"label": m, "value": m} for m in meses], mes_selecionado

    # Popula as opções dos filtros com base no ano/mês
    @app.callback(
        [Output(f"exe-{k}", "options") for k in ["orgao","coordenacao","acao","projeto","elemento","vinculacao","fonte","despesa"]],
        Input("exe-mes", "value"),
        State("exe-ano", "value")
    )
    def popula_opcoes_filtros_exe(mes, ano):
        if not ano or not mes:
            return [[{"label": "Todos", "value": "Todos"}] for _ in range(8)]

        df = carrega_base("execucao", ano, mes)
        if df.empty:
            return [[{"label": "Todos", "value": "Todos"}] for _ in range(8)]

        mapa_cols = {
            "orgao": "orgao", "coordenacao": "coordenação", "acao": "acao_programatica",
            "projeto": "projeto_atividade", "elemento": "nome_elemento", "vinculacao": "vinculacao",
            "fonte": "ds_fonte", "despesa": "despesa"
        }

        def get_opts(col_df):
            if col_df in df.columns:
                opcoes = sorted(df[col_df].dropna().unique())
                return [{"label": "Todos", "value": "Todos"}] + [{"label": str(o), "value": o} for o in opcoes]
            return [{"label": "Todos", "value": "Todos"}]

        # A ordem deve ser a mesma da lista de Outputs
        return [get_opts(mapa_cols[k]) for k in ["orgao","coordenacao","acao","projeto","elemento","vinculacao","fonte","despesa"]]


    # 1. UI -> STORE (Salva alterações e aplica lógica do "Todos")
    @app.callback(
        Output("store_filtros", "data", allow_duplicate=True),
        Input("exe-btn-limpar", "n_clicks"), Input("exe-ano", "value"), Input("exe-mes", "value"),
        Input("exe-orgao", "value"), Input("exe-coordenacao", "value"), Input("exe-acao", "value"), Input("exe-projeto", "value"),
        Input("exe-elemento", "value"), Input("exe-vinculacao", "value"),
        Input("exe-fonte", "value"), Input("exe-despesa", "value"),
        State("store_filtros", "data"), prevent_initial_call=True
    )
    def salva_filtros_exe(n_clicks, ano, mes, orgao, coord, acao, proj, elem, vinc, fonte, desp, store):
        if store is None: store = {}
        ctx = callback_context
        trigger_id = ctx.triggered[0]["prop_id"]

        if "exe-btn-limpar" in trigger_id:
            # Reseta para o ano e mês mais recentes
            novo_ano = ano_padrao
            meses = lista_meses("execucao", novo_ano)
            novo_mes = meses[-1] if meses else None
            return {**store, "ano": novo_ano, "mes": novo_mes, "orgao": ["Todos"], "coordenacao": ["Todos"],
                    "acao": ["Todos"], "projeto": ["Todos"], "elemento": ["Todos"], "vinculacao": ["Todos"],
                    "fonte": ["Todos"], "despesa": ["Todos"]}
        
        store.update({
            "ano": ano, "mes": mes,
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

    # 2. STORE -> UI (Carrega dados do Store para os Dropdowns)
    @app.callback(
        [Output("exe-ano", "value")] + [Output(f"exe-{k}", "value") for k in ["orgao","coordenacao","acao","projeto","elemento","vinculacao","fonte","despesa"]],
        Input("store_filtros", "data")
    )
    def carrega_ui_exe(store):
        if not store: return (ano_padrao,) + (["Todos"],)*8
        return (store.get("ano", ano_padrao),
                store.get("orgao", ["Todos"]), store.get("coordenacao", ["Todos"]), 
                store.get("acao", ["Todos"]), store.get("projeto", ["Todos"]),
                store.get("elemento", ["Todos"]), store.get("vinculacao", ["Todos"]), 
                store.get("fonte", ["Todos"]), store.get("despesa", ["Todos"]))

    # 3. GERA DADOS (Cards + Tabela)
    @app.callback(
        Output("exe-info-atualizacao", "children"),
        Output("exe-cards-container", "children"),
        Output("exe-tabela", "data"), Output("exe-tabela", "columns"),
        Input("store_filtros", "data")
    )
    def atualiza_dashboard_exe(store):
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
            "despesa": "despesa"
        }

        for k_store, col_df in mapa_filtros.items():
            vals = store.get(k_store, ["Todos"])
            if "Todos" not in vals and col_df in df.columns:
                df = df[df[col_df].isin(vals)]

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

    # 4. GERA E FAZ DOWNLOAD DO PDF
    @app.callback(
        Output("exe-download-pdf", "data"),
        Input("exe-btn-download-pdf", "n_clicks"),
        State("store_filtros", "data"),
        prevent_initial_call=True
    )
    def download_pdf_exe(n_clicks, store):
        if not store or not store.get("mes"):
            return no_update

        df = carrega_base("execucao", store["ano"], store["mes"])
        if df.empty:
            return no_update

        # Replicar filtros
        mapa_filtros = {
            "orgao": "orgao", "coordenacao": "coordenação", "acao": "acao_programatica", 
            "projeto": "projeto_atividade", "elemento": "nome_elemento", "vinculacao": "vinculacao",
            "fonte": "ds_fonte", "despesa": "despesa"
        }
        for k_store, col_df in mapa_filtros.items():
            vals = store.get(k_store, ["Todos"])
            if "Todos" not in vals and col_df in df.columns:
                df = df[df[col_df].isin(vals)]

        # Calcular Totais
        cols_numericas = [c for c in DE_PARA_EXECUCAO.keys() if c in df.columns and c != "Saldo de Dotação"]
        totais = {c: df[c].sum() for c in cols_numericas}
        
        orcado = totais.get("valOrcadoAtualizado", 0)
        empenhado = totais.get("valEmpenhadoLiquido", 0)
        totais["Saldo de Dotação"] = orcado - empenhado

        pivot = gera_tabela_pivot(df, "execucao")
        
        pdf_bytes = criar_relatorio_execucao_pdf(store, totais, pivot)
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
        return dcc.send_data_frame(df_excel.to_excel, "execucao_orcamentaria.xlsx", index=False)
