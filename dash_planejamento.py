import dash
import pandas as pd
from dash import html, dcc, Input, Output, State, callback_context, no_update
import dash_bootstrap_components as dbc
from dash import dash_table as dt
from dash.dash_table.Format import Format, Scheme, Symbol, Group
from filtros import layout_filtros_padrao, ano_padrao
from utils import (
    carrega_base_planejamento,
    cabecalho_padrao, tratar_selecao_todos, monta_cards_resumo, 
    DE_PARA_PLANEJAMENTO, DE_PARA_INDICES_PLANEJAMENTO, gera_card_atualizacao
)

# Mapa completo de colunas
MAPA_COLUNAS_PLANEJAMENTO = {**DE_PARA_INDICES_PLANEJAMENTO, **DE_PARA_PLANEJAMENTO}

def layout_planejamento():
    return dbc.Container([
        cabecalho_padrao("Planejamento de Pagamentos", "📊 Quadro de Detalhamento de Despesas"),
        
        html.Div(id="pln-cards-container", className="mb-4"),
        dcc.Store(id="store_opcoes_pln", storage_type="memory"),
        
        dbc.Row([
            dbc.Col([dbc.Button("🏠 Início", href="/", className="w-100 mt-4", 
                                style={"whiteSpace": "normal", "backgroundColor": "#6c757d", "borderColor": "#6c757d", "color": "white"})], md=2),
            dbc.Col([dbc.Button("Ir para Pressão ➡️", href="/pressao", className="w-100 mt-4",
                                style={"backgroundColor": "#dc3545", "borderColor": "#dc3545", "color": "white"})], md=2),
            dbc.Col([dbc.Button("🛠️ Colunas", id="pln-btn-colunas", className="w-100 mt-4", 
                                style={"backgroundColor": "#0dcaf0", "borderColor": "#0dcaf0", "color": "black"})], md=2),            
            dbc.Col([dbc.Button("ℹ️ Saiba Mais", href="/sobre", className="w-100 mt-4", 
                                style={"backgroundColor": "#722f37", "borderColor": "#722f37", "color": "white"})], md=2),
        ], className="mb-4", justify="center"),

        layout_filtros_padrao("pln"),

        dbc.Row([
                dbc.Col([dbc.Button("🗑️ Limpar Filtros", id="pln-btn-limpar", className="w-100 mt-4", 
                            style={"backgroundColor": "#ffc107", "borderColor": "#ffc107", "color": "black"})], md=2)
            ], className="mb-4", justify="center"),
        dbc.Row([ # This row is intentionally left empty as the "Limpar Filtros" button was moved to the bottom.
        ], className="mb-4", justify="center"),

        # MODAL DE SELEÇÃO DE COLUNAS
        dbc.Modal([
            dbc.ModalHeader(dbc.ModalTitle("Selecionar Colunas para Exibição")),
            dbc.ModalBody([
                dbc.Checklist(
                    id="pln-checklist-colunas",
                    options=[{"label": v, "value": k} for k, v in MAPA_COLUNAS_PLANEJAMENTO.items()],
                    value=list(MAPA_COLUNAS_PLANEJAMENTO.keys()),
                    switch=True,
                )
            ]),
            dbc.ModalFooter(dbc.Button("Fechar", id="pln-btn-fechar-modal", className="ms-auto", n_clicks=0))
        ], id="pln-modal-colunas", is_open=False),

        html.H5("Planejamento de Contratos", className="fw-bold"),
        dt.DataTable(
            id="pln-tabela",
            style_header={"backgroundColor": "#1f77b4", "color": "white", "fontWeight": "bold", "fontSize": "14px",  "fontFamily": "Calibri, sans-serif"},
            style_cell={"textAlign": "left", "minWidth": "100px", "fontSize": "12px", "fontFamily": "Calibri, sans-serif", "whiteSpace": "normal", "height": "auto"},
            style_cell_conditional=[
                {'if': {'column_id': 'Objeto do Contrato'}, 'width': '400px', 'maxWidth': '400px', 'minWidth': '200px'},
                {'if': {'column_id': 'Credor'}, 'width': '250px', 'maxWidth': '250px', 'minWidth': '150px'},
            ],
            page_size=25, sort_action="native",
        ),
        dbc.Button("📥 Download Excel", id="pln-btn-download", className="mt-3", 
                   style={"backgroundColor": "#198754", "borderColor": "#198754", "color": "white"}),
        dcc.Download(id="pln-download-xlsx"),
        html.Hr(),
        html.Div(id="pln-info-atualizacao")
    ], fluid=True, style={"backgroundColor": "#f8f9fa", "padding": "20px"})

def registrar_callbacks_planejamento(app):
    
    @app.callback(
        Output("pln-collapse-filtros", "is_open"),
        Input("pln-btn-toggle-filtros", "n_clicks"),
        State("pln-collapse-filtros", "is_open"),
    )
    def toggle_filtros_pln(n, is_open):
        if n: return not is_open
        return is_open

    # Callback para carregar as opções dos filtros com base no ano
    @app.callback(
        [Output(f"pln-{col}", "options") for col in ["orgao", "coordenacao", "acao", "elemento", "descricao", "projeto", "despesa", "fonte-descricao", "vinculacao", "fonte", "processo", "credor", "objeto", "origem", "fase", "status_empenho", "situacao_orcamentaria", "descricao_generica", "numero_termo"]],
        Input("store_filtros", "data")
    )
    def atualiza_dropdowns_pln(store):
        if not store or not store.get("ano"):
            return [[]] * 19
        
        df = carrega_base_planejamento(store.get("ano"))
        if df.empty:
            return [[]] * 19
        
        # [MODIFICAÇÃO] Cria um DF auxiliar apenas para gerar as opções dos filtros.
        # Removemos as linhas de 'Orçamento' para que não sujem as listas (ex: Processo 'ORCAMENTO').
        df_opts = df[df['Origem'] != 'Orçamento'] if 'Origem' in df.columns else df
        
        def opts_todos(col):
            if col not in df_opts.columns:
                return [{"label": "Todos", "value": "Todos"}]
            opcoes = sorted(df_opts[col].dropna().unique(), key=str)
            return [{"label": "Todos", "value": "Todos"}] + [{"label": str(o), "value": o} for o in opcoes]

        return (
            opts_todos("orgao"),
            opts_todos("coordenacao"),
            opts_todos("acao_programatica"), # para pln-acao
            opts_todos("nome_elemento"),     # para pln-elemento
            opts_todos("politicas_para"),    # para pln-descricao
            opts_todos("codProjetoAtividade"), # para pln-projeto
            opts_todos("codDespesa"),        # para pln-despesa
            opts_todos("fonte_descricao"),   # para pln-fonte-descricao
            opts_todos("codVinculacao"),     # para pln-vinculacao
            opts_todos("ds_fonte"),          # para pln-fonte (Label: Vinculação)
            opts_todos("codProcesso"),       # para pln-processo
            opts_todos("Credor"),            # para pln-credor
            opts_todos("Objeto do Contrato"), # para pln-objeto
            opts_todos("Origem"),            # para pln-origem
            opts_todos("Fases"),             # para pln-fase
            opts_todos("Status Empenho"),    # para pln-status_empenho
            opts_todos("Status Cobertura"),  # para pln-situacao_orcamentaria
            opts_todos("Descrição Genérica da Despesa"), # para pln-descricao_generica
            opts_todos("Número do Termo")    # para pln-numero_termo
        )

    # Callback para sincronizar a UI dos filtros com o store global
    @app.callback(
        [Output("pln-ano", "value")] + [Output(f"pln-{k}", "value") for k in ["orgao","coordenacao","acao","elemento","descricao", "projeto", "despesa", "fonte-descricao", "vinculacao", "fonte", "processo", "credor", "objeto", "origem", "fase", "status_empenho", "situacao_orcamentaria", "descricao_generica", "numero_termo"]],
        Input("store_filtros", "data")
    )
    def sync_ui_pln(store):
        if not store: return (ano_padrao,) + (["Todos"],)*18
        return (store.get("ano", ano_padrao),
                store.get("orgao", ["Todos"]), store.get("coordenacao", ["Todos"]), 
                store.get("acao", ["Todos"]), store.get("elemento", ["Todos"]), store.get("descricao", ["Todos"]),
                store.get("projeto", ["Todos"]), store.get("despesa", ["Todos"]), store.get("fonte_descricao", ["Todos"]),
                store.get("vinculacao", ["Todos"]), store.get("fonte", ["Todos"]),
                store.get("processo", ["Todos"]), store.get("credor", ["Todos"]), store.get("objeto", ["Todos"]),
                store.get("origem", ["Todos"]), store.get("fase", ["Todos"]),
                store.get("status_empenho", ["Todos"]), store.get("situacao_orcamentaria", ["Todos"]),
                store.get("descricao_generica", ["Todos"]), store.get("numero_termo", ["Todos"]))

    # 1. UI -> STORE (Reutiliza lógica global, mas o trigger é 'pln')
    @app.callback(
        Output("store_filtros", "data", allow_duplicate=True),
        Input("pln-btn-limpar", "n_clicks"), Input("pln-ano", "value"),
        Input("pln-orgao", "value"), Input("pln-coordenacao", "value"),
        Input("pln-acao", "value"), Input("pln-elemento", "value"), Input("pln-descricao", "value"),
        Input("pln-projeto", "value"), Input("pln-despesa", "value"), Input("pln-fonte-descricao", "value"),
        Input("pln-vinculacao", "value"), Input("pln-fonte", "value"),
        Input("pln-processo", "value"), Input("pln-credor", "value"), Input("pln-objeto", "value"),
        Input("pln-origem", "value"), Input("pln-fase", "value"), Input("pln-status_empenho", "value"),
        Input("pln-situacao_orcamentaria", "value"), Input("pln-descricao_generica", "value"),
        Input("pln-numero_termo", "value"),
        State("store_filtros", "data"), prevent_initial_call=True
    )
    def update_store_pln(n_limpar, ano, orgao, coord, acao, elem, desc, proj, desp, fonte_desc, vinc, fonte, proc, cred, obj, origem, fase, status_empenho, situacao_orcamentaria, desc_gen, num_termo, store):
        if not ano: return no_update
        if store is None: store = {}
        ctx = callback_context
        trigger_id = ctx.triggered[0]["prop_id"]
        
        if "pln-btn-limpar" in trigger_id:
            return {**store, "ano": ano_padrao, "orgao": ["Todos"], "coordenacao": ["Todos"], "acao": ["Todos"],
                    "elemento": ["Todos"], "descricao": ["Todos"], "projeto": ["Todos"], "despesa": ["Todos"],
                    "fonte_descricao": ["Todos"], "vinculacao": ["Todos"], "fonte": ["Todos"],
                    "processo": ["Todos"], "credor": ["Todos"], "objeto": ["Todos"], "origem": ["Todos"], "fase": ["Todos"], 
                    "status_empenho": ["Todos"], "situacao_orcamentaria": ["Todos"], "descricao_generica": ["Todos"], "numero_termo": ["Todos"]}

        store.update({
            "ano": ano,
            "orgao": tratar_selecao_todos(orgao, store.get("orgao")),
            "coordenacao": tratar_selecao_todos(coord, store.get("coordenacao")),
            "acao": tratar_selecao_todos(acao, store.get("acao")),
            "elemento": tratar_selecao_todos(elem, store.get("elemento")),
            "descricao": tratar_selecao_todos(desc, store.get("descricao")),
            "projeto": tratar_selecao_todos(proj, store.get("projeto")),
            "despesa": tratar_selecao_todos(desp, store.get("despesa")),
            "fonte_descricao": tratar_selecao_todos(fonte_desc, store.get("fonte_descricao")),
            "vinculacao": tratar_selecao_todos(vinc, store.get("vinculacao")),
            "fonte": tratar_selecao_todos(fonte, store.get("fonte")),
            "processo": tratar_selecao_todos(proc, store.get("processo")),
            "credor": tratar_selecao_todos(cred, store.get("credor")),
            "objeto": tratar_selecao_todos(obj, store.get("objeto")),
            "origem": tratar_selecao_todos(origem, store.get("origem")),
            "fase": tratar_selecao_todos(fase, store.get("fase")),
            "status_empenho": tratar_selecao_todos(status_empenho, store.get("status_empenho")),
            "situacao_orcamentaria": tratar_selecao_todos(situacao_orcamentaria, store.get("situacao_orcamentaria")),
            "descricao_generica": tratar_selecao_todos(desc_gen, store.get("descricao_generica")),
            "numero_termo": tratar_selecao_todos(num_termo, store.get("numero_termo"))
        })
        return store

    # 2. Gera Dados
    @app.callback(
        Output("pln-info-atualizacao", "children"),
        Output("pln-cards-container", "children"),
        Output("pln-tabela", "data"), Output("pln-tabela", "columns"),
        Output("pln-tabela", "style_data_conditional"),
        Output("pln-tabela", "sort_by"), # Adicionado para resetar a ordenação
        Output("pln-tabela", "page_current"), # Resetar paginação para evitar erro de índice
        Output("pln-tabela", "active_cell"), # Resetar célula ativa para evitar erro de coluna inexistente
        Output("pln-tabela", "selected_cells"), # Resetar seleção de células
        Input("store_filtros", "data"),
        Input("pln-checklist-colunas", "value")
    )
    def atualiza_dash_pln(store, cols_selecionadas):
        if not store or not store.get("ano"): return (no_update,) * 9
        
        df = carrega_base_planejamento(store["ano"])
        if df.empty: return gera_card_atualizacao("-"), html.Div("Sem dados."), [], [], [], [], 0, None, []

        # Filtros
        mapa = {"orgao": "orgao", "coordenacao": "coordenacao", "acao": "acao_programatica", 
                "elemento": "nome_elemento", "descricao": "politicas_para",
                "projeto": "codProjetoAtividade", "despesa": "codDespesa", 
                "fonte_descricao": "fonte_descricao", "vinculacao": "codVinculacao", "fonte": "ds_fonte",
                "processo": "codProcesso", "credor": "Credor", "objeto": "Objeto do Contrato",
                "origem": "Origem", "fase": "Fases", "status_empenho": "Status Empenho",
                "situacao_orcamentaria": "Status Cobertura", "descricao_generica": "Descrição Genérica da Despesa",
                "numero_termo": "Número do Termo"}
        
        # [MODIFICAÇÃO] Definição de quais colunas são ESTRUTURAIS (devem filtrar o Orçamento também)
        # e quais são CONTRATUAIS (não devem remover o Orçamento para manter os totais dos cards corretos).
        cols_estruturais = [
            "orgao", "coordenacao", "acao_programatica", "nome_elemento", "politicas_para",
            "codProjetoAtividade", "codDespesa", "fonte_descricao", "codVinculacao", "ds_fonte"
        ]

        for k_store, col_df in mapa.items():
            vals = store.get(k_store, ["Todos"])
            if "Todos" not in vals and col_df in df.columns:
                if col_df in cols_estruturais:
                    # Filtros estruturais (ex: Órgão): Aplicam-se a tudo, inclusive linhas de orçamento.
                    df = df[df[col_df].isin(vals)]
                else:
                    # Filtros contratuais (ex: Credor, Processo):
                    # Aplicam-se aos contratos, mas PRESERVAM as linhas de orçamento para não zerar os cards de Disponível/Orçado.
                    # Lógica: (Linha atende ao filtro) OU (Linha é de Origem 'Orçamento')
                    df = df[df[col_df].isin(vals) | (df['Origem'] == 'Orçamento')]

        # Se o dataframe ficar vazio após os filtros, retorna tabela vazia mas mantém os cards zerados
        if df.empty or (len(df) == len(df[df['Origem'] == 'Orçamento']) and df[df['Origem'] == 'Orçamento'].empty):
            totais_vazio = {c: 0 for c in DE_PARA_PLANEJAMENTO.keys()}
            cards_vazios = monta_cards_resumo(totais_vazio, DE_PARA_PLANEJAMENTO)
            return gera_card_atualizacao("-"), cards_vazios, [], [], [], [], 0, None, []

        # --- CÁLCULO DOS TOTAIS PARA OS CARDS (COM DEDUPLICAÇÃO) ---
        # A junção de contratos e empenhos pode duplicar valores. Para os cards,
        # precisamos somar os valores únicos de cada "entidade" (contrato, empenho, orçamento).
        totais = {}

        # 1. Orçado Atualizado: Após a modificação em utils.py, o valor do orçamento só existe nas linhas de origem 'Orçamento',
        # que já são únicas por dotação. A soma da coluna no DF filtrado reflete o orçamento dos itens exibidos.
        if 'valOrcadoAtualizado' in df.columns:
            totais['valOrcadoAtualizado'] = df['valOrcadoAtualizado'].sum()

        # 1.1 Disponível: Mesma lógica do Orçado
        if 'valDisponivel' in df.columns:
            totais['valDisponivel'] = df['valDisponivel'].sum()

        # 2. Empenhado, Liquidado, Pago (SOF):
        # Como os valores agora são distribuídos proporcionalmente em utils.py (evitando dupla contagem),
        # podemos fazer a soma direta da coluna.
        for col in ['Valor Empenhado (SOF)', 'Valor Liquidado (SOF)', 'Valor Pago (SOF)']:
            if col in df.columns:
                totais[col] = df[col].sum()

        # 3. Total Contratado: 
        # Deve somar:
        # A) O valor dos contratos (únicos pelo ID de linha)
        # B) O valor dos empenhos órfãos (que não têm contrato, mas devem constar como "Total Necessário" = "Empenhado")
        soma_contratos = 0
        soma_orfaos = 0
        if 'Total necessário' in df.columns and '_contract_row_id' in df.columns:
            # A) Soma de linhas originadas de contratos (tem ID)
            df_contratos_unicos = df[df['_contract_row_id'].notna()].drop_duplicates(subset=['_contract_row_id'])
            soma_contratos = df_contratos_unicos['Total necessário'].sum()
            
            # B) Soma de linhas originadas APENAS de empenhos (Empenho s/ Contrato)
            # Para estes casos, Total Necessário == Valor Empenhado (definido em utils.py)
            # Como a origem "Empenho s/ Contrato" vem da agregação de empenhos, as linhas já são únicas por Processo+Dotação
            soma_orfaos = df[df['Origem'] == 'Empenho s/ Contrato']['Total necessário'].sum()

        totais['Total necessário'] = soma_contratos + soma_orfaos
        
        # 4. Pressão Orçamentária (Renomeado e Recalculado)
        # Agora calcula a diferença entre o que está disponível na dotação e o que foi contratado.
        totais['Pressao do Contrato'] = totais.get('valDisponivel', 0) - totais.get('Total necessário', 0)
            
        # 5. Saldo de Dotação - DUAS VERSÕES PARA COMPARAÇÃO
        # Versão 1: Subtração direta (Disponível - Total Contratado)
        totais['Saldo de Dotação (Direto)'] = totais.get('valDisponivel', 0) - totais.get('Total necessário', 0)

        # Adiciona Disponível apenas para os cards (oculto na tabela)
        de_para_cards = DE_PARA_PLANEJAMENTO.copy()
        de_para_cards["valDisponivel"] = "Disponível"
        cards = monta_cards_resumo(totais, de_para_cards)

        # Se nenhuma coluna for selecionada, exibe os cards mas não a tabela para evitar erro.
        if not cols_selecionadas:
            return gera_card_atualizacao("-"), cards, [], [], [], [], 0, None, []
        
        tabela_final = df

        # [MODIFICAÇÃO] Oculta visualmente as linhas de "Orçamento" na tabela,
        # mas mantém os valores nos cards (que foram calculados usando 'df' acima).
        if 'Origem' in tabela_final.columns:
            tabela_final = tabela_final[tabela_final['Origem'] != 'Orçamento']

        if cols_selecionadas and not tabela_final.empty:
            # Ordena as colunas com base na definição do MAPA_COLUNAS para respeitar a personalização do utils.py
            ordem_preferencial = list(MAPA_COLUNAS_PLANEJAMENTO.keys())
            cols_to_keep = [c for c in ordem_preferencial if c in cols_selecionadas and c in tabela_final.columns]
            # Adiciona eventuais colunas extras que não estejam no mapa
            cols_to_keep += [c for c in cols_selecionadas if c in tabela_final.columns and c not in ordem_preferencial]
            
            if not cols_to_keep:
                return gera_card_atualizacao("-"), cards, [], [], [], [], 0, None, []
            tabela_final = tabela_final[cols_to_keep]
        
        # Garantir que os nomes das colunas sejam strings ANTES de gerar a definição das colunas
        tabela_final.columns = tabela_final.columns.astype(str)

        cols_table = []
        for c in tabela_final.columns:
            if c in DE_PARA_PLANEJAMENTO:
                nome = DE_PARA_PLANEJAMENTO[c]
                tipo = "numeric"
                fmt = Format(scheme=Scheme.fixed, precision=2, group=Group.yes, group_delimiter='.', decimal_delimiter=',', symbol=Symbol.yes, symbol_prefix='R$ ')
            elif c in DE_PARA_INDICES_PLANEJAMENTO:
                nome = DE_PARA_INDICES_PLANEJAMENTO.get(c, c)
                tipo = "text"
                fmt = None
            else:
                nome = c
                tipo = "text"
                fmt = None
            cols_table.append({"name": nome, "id": c, "type": tipo, "format": fmt})

        style_conditional = []
        if "Falta Pagar" in tabela_final.columns:
            style_conditional.append({
                'if': {'filter_query': '{Falta Pagar} > 0'}, # Correção: Remover chaves duplas
                'backgroundColor': '#fff3cd', # Amarelo claro
            })

        return gera_card_atualizacao("-"), cards, tabela_final.to_dict("records"), cols_table, style_conditional, [], 0, None, []

    # Modal de colunas
    @app.callback(
        Output("pln-modal-colunas", "is_open"),
        Input("pln-btn-colunas", "n_clicks"),
        Input("pln-btn-fechar-modal", "n_clicks"),
        State("pln-modal-colunas", "is_open"),
        prevent_initial_call=True
    )
    def toggle_modal_colunas_pln(n1, n2, is_open):
        if n1 or n2:
            return not is_open
        return is_open
    
    # Download Excel
    @app.callback(
        Output("pln-download-xlsx", "data"),
        Input("pln-btn-download", "n_clicks"),
        State("pln-tabela", "data"),
        prevent_initial_call=True
    )
    def download_excel_pln(n_clicks, dados_tabela):
        if not dados_tabela:
            return no_update
        

        df_excel = pd.DataFrame(dados_tabela)
        return dcc.send_data_frame(df_excel.to_excel, "planejamento_pagamentos.xlsx", index=False, sheet_name="Planejamento")