import dash
import pandas as pd
import numpy as np
import plotly.express as px
from dash import html, dcc, Input, Output, State, callback_context, no_update
import dash_bootstrap_components as dbc
from dash import dash_table as dt
from dash.dash_table.Format import Format, Scheme, Symbol, Group
from filtros import layout_filtros_padrao, ano_padrao, criar_label_com_tooltip
from utils import (
    carrega_base_planejamento, gera_tabela_pivot, cabecalho_padrao,
    tratar_selecao_todos, monta_cards_resumo, DE_PARA_PRESSAO, DE_PARA_INDICES_PRESSAO,
    gera_card_atualizacao
)

# Mapa completo de colunas
MAPA_COLUNAS_PRESSAO = {**DE_PARA_INDICES_PRESSAO, **DE_PARA_PRESSAO}

def layout_pressao():
    return dbc.Container([
        cabecalho_padrao("💰 Pressão Orçamentária (Contratos)", "📊 Quadro de Detalhamento de Despesas"),
        html.Div(id="pre-cards-container", className="mb-4"),
        dcc.Store(id="store_opcoes_pre", storage_type="memory"),
        
        dbc.Row([
            dbc.Col([dbc.Button("🏠 Início", href="/", className="w-100 mt-4", 
                                style={"whiteSpace": "normal", "backgroundColor": "#6c757d", "borderColor": "#6c757d", "color": "white"})], md=2),
            dbc.Col([dbc.Button("Ir para Planejamento ➡️", href="/planejamento", className="w-100 mt-4",
                                style={"backgroundColor": "#bb35dc", "borderColor": "#bb35dc", "color": "white"})], md=2),
            dbc.Col([dbc.Button("🛠️ Colunas", id="pre-btn-colunas", className="w-100 mt-4", 
                                style={"backgroundColor": "#0dcaf0", "borderColor": "#0dcaf0", "color": "black"})], md=2),
            dbc.Col([dbc.Button("ℹ️ Saiba Mais", href="/sobre", className="w-100 mt-4", 
                                style={"backgroundColor": "#722f37", "borderColor": "#722f37", "color": "white"})], md=2),
        ], className="mb-4", justify="center"),

        layout_filtros_padrao("pre"),
        
        # MODAL DE SELEÇÃO DE COLUNAS
        dbc.Modal([
            dbc.ModalHeader(dbc.ModalTitle("Selecionar Colunas para Exibição")),
            dbc.ModalBody([
                dbc.Checklist(
                    id="pre-checklist-colunas",
                    options=[{"label": v, "value": k} for k, v in MAPA_COLUNAS_PRESSAO.items()],
                    value=list(MAPA_COLUNAS_PRESSAO.keys()),
                    switch=True,
                )
            ]),
            dbc.ModalFooter(dbc.Button("Fechar", id="pre-btn-fechar-modal", className="ms-auto", n_clicks=0))
        ], id="pre-modal-colunas", is_open=False),

        html.H5("Lista de Contratos", className="fw-bold"),
        dt.DataTable(
            id="pre-tabela",
            style_header={"backgroundColor": "#1f77b4", "color": "white", "fontWeight": "bold", "fontSize": "14px",  "fontFamily": "Calibri, sans-serif"},
            style_cell={"textAlign": "left", "minWidth": "100px", "fontSize": "12px", "fontFamily": "Calibri, sans-serif"},
            page_size=25, sort_action="native",
        ),
        dbc.Row([
            dbc.Col([dbc.Button("🗑️ Limpar Filtros", id="pre-btn-limpar", className="w-100 mt-4", style={"backgroundColor": "#ffc107", "borderColor": "#ffc107", "color": "black"})], md=2),
        ], className="mb-4", justify="center"),
        html.Hr(),

        dbc.Button("📥 Download Excel", id="pre-btn-download", className="mt-3", 
                   style={"backgroundColor": "#198754", "borderColor": "#198754", "color": "white"}),
        dcc.Download(id="pre-download-xlsx"),

        dbc.Row([
            dbc.Col(dcc.Graph(id="pre-grafico-orgao"), width=12)
        ], className="mt-4 mb-4"),

        html.Hr(),
        html.Div(id="pre-info-atualizacao")
    ], fluid=True, style={"backgroundColor": "#f8f9fa", "padding": "20px"})

def registrar_callbacks_pressao(app):
    
    @app.callback(
        Output("pre-collapse-filtros", "is_open"),
        Input("pre-btn-toggle-filtros", "n_clicks"),
        State("pre-collapse-filtros", "is_open"),
    )
    def toggle_filtros_pre(n, is_open):
        if n: return not is_open
        return is_open

    # 1. Carrega Opções
    @app.callback(
        Output("store_opcoes_pre", "data"),
        Input("pre-ano", "value")
    )
    def carrega_opcoes_base_pre(ano):
        if not ano: return {}
        df = carrega_base_planejamento(ano)
        if df.empty: return {}
        
        mapa_cols = {
            "orgao": "orgao", "coordenacao": "coordenacao", "acao": "acao_programatica",
            "projeto": "codProjetoAtividade", "elemento": "nome_elemento", "vinculacao": "codVinculacao",
            "fonte": "ds_fonte", "despesa": "codDespesa", "descricao": "politicas_para", "fonte_descricao": "fonte_descricao"
        }
        
        opcoes_dict = {}
        for k, col in mapa_cols.items():
            if col in df.columns:
                opcoes = sorted(df[col].dropna().unique(), key=str)
                opcoes_dict[k] = [{"label": "Todos", "value": "Todos"}] + [{"label": str(o), "value": o} for o in opcoes]
            else:
                opcoes_dict[k] = [{"label": "Todos", "value": "Todos"}]
        return opcoes_dict

    # 2. Atualiza Dropdowns
    @app.callback(
        [Output(f"pre-{k}", "options") for k in ["orgao","coordenacao","acao","projeto","elemento","vinculacao","fonte","despesa","descricao", "fonte-descricao", "tem_pressao"]],
        Input("store_filtros", "data"),
        [Input(f"pre-{k}", "search_value") for k in ["orgao","coordenacao","acao","projeto","elemento","vinculacao","fonte","despesa","descricao", "fonte-descricao", "tem_pressao"]]
    )
    def atualiza_dropdowns_pre(store, *search_values):
        if not store: return [[{"label": "Todos", "value": "Todos"}] for _ in range(11)]
        ano = store.get("ano", ano_padrao)
        df = carrega_base_planejamento(ano)
        if df.empty: return [[{"label": "Todos", "value": "Todos"}] for _ in range(11)]

        keys = ["orgao","coordenacao","acao","projeto","elemento","vinculacao","fonte","despesa","descricao", "fonte-descricao", "tem_pressao"]
        mapa_cols = {
            "orgao": "orgao", "coordenacao": "coordenacao", "acao": "acao_programatica",
            "projeto": "codProjetoAtividade", "elemento": "nome_elemento", "vinculacao": "codVinculacao",
            "fonte": "ds_fonte", "despesa": "codDespesa", "descricao": "politicas_para",
            "fonte-descricao": "fonte_descricao"
        }
        
        outputs = []
        for i, key_target in enumerate(keys):
            if key_target == "tem_pressao":
                outputs.append([{"label": "Todos", "value": "Todos"}, {"label": "Sim", "value": "Sim"}, {"label": "Não", "value": "Não"}])
                continue
            df_filtered = df.copy()
            for key_filter in keys:
                if key_filter == key_target or key_filter == "tem_pressao": continue
                vals = store.get(key_filter.replace("-", "_"), ["Todos"])
                col_name = mapa_cols[key_filter]
                if "Todos" not in vals and col_name in df_filtered.columns:
                    df_filtered = df_filtered[df_filtered[col_name].isin(vals)]
            
            col_target = mapa_cols[key_target]
            options = []
            current_selection = store.get(key_target.replace("-", "_"), ["Todos"])
            if col_target in df_filtered.columns:
                unique_vals = set(df_filtered[col_target].dropna().unique())
                final_vals = unique_vals if "Todos" in current_selection else set(current_selection).union(unique_vals)
                options = [{"label": str(v), "value": v} for v in sorted(list(final_vals), key=str)]
            
            options.insert(0, {"label": "Todos", "value": "Todos"})
            search = search_values[i]
            if search:
                options = [opt for opt in options if search.lower() in str(opt["label"]).lower()]
            outputs.append(options)
        return outputs

    # 3. UI -> STORE (Reutiliza lógica global, mas o trigger é 'pre')
    @app.callback(
        Output("store_filtros", "data", allow_duplicate=True),
        Input("pre-btn-limpar", "n_clicks"), Input("pre-ano", "value"),
        Input("pre-orgao", "value"), Input("pre-coordenacao", "value"),
        Input("pre-acao", "value"), Input("pre-elemento", "value"), Input("pre-descricao", "value"),
        Input("pre-projeto", "value"), Input("pre-despesa", "value"), Input("pre-fonte-descricao", "value"),
        Input("pre-vinculacao", "value"), Input("pre-fonte", "value"), Input("pre-tem_pressao", "value"),
        State("store_filtros", "data"), prevent_initial_call=True
    )
    def update_store_pre(n_limpar, ano, orgao, coord, acao, elem, desc, proj, desp, fonte_desc, vinc, fonte, tem_pre, store):
        if not ano: return no_update
        if store is None: store = {}
        ctx = callback_context
        trigger_id = ctx.triggered[0]["prop_id"]
        
        if "pre-btn-limpar" in trigger_id:
            return {**store, "ano": ano_padrao, "orgao": ["Todos"], "coordenacao": ["Todos"], "acao": ["Todos"],
                    "elemento": ["Todos"], "descricao": ["Todos"], "projeto": ["Todos"], "despesa": ["Todos"],
                    "fonte_descricao": ["Todos"], "vinculacao": ["Todos"], "fonte": ["Todos"], "tem_pressao": ["Todos"]}

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
            "tem_pressao": tratar_selecao_todos(tem_pre, store.get("tem_pressao"))
        })
        return store

    # 4. STORE -> UI
    @app.callback(
        [Output("pre-ano", "value")] + [Output(f"pre-{k}", "value") for k in ["orgao","coordenacao","acao","projeto","elemento","vinculacao","fonte","despesa","descricao", "fonte-descricao", "tem_pressao"]],
        Input("store_filtros", "data")
    )
    def sync_ui_pre(store):
        if not store: return (ano_padrao,) + (["Todos"],)*11
        return (store.get("ano", ano_padrao),
                store.get("orgao", ["Todos"]), store.get("coordenacao", ["Todos"]), 
                store.get("acao", ["Todos"]), store.get("projeto", ["Todos"]), store.get("elemento", ["Todos"]),
                store.get("vinculacao", ["Todos"]), store.get("fonte", ["Todos"]), store.get("despesa", ["Todos"]),
                store.get("descricao", ["Todos"]), store.get("fonte_descricao", ["Todos"]),
                store.get("tem_pressao", ["Todos"]))

    # 5. Gera Dados
    @app.callback(
        Output("pre-info-atualizacao", "children"),
        Output("pre-cards-container", "children"),
        Output("pre-tabela", "data"), Output("pre-tabela", "columns"),
        Output("pre-tabela", "style_data_conditional"),
        Output("pre-tabela", "page_current"), # Resetar paginação
        Output("pre-grafico-orgao", "figure"),
        Input("store_filtros", "data"),
        Input("pre-checklist-colunas", "value")
    )
    def atualiza_dash_pre(store, cols_selecionadas):
        if not store or not store.get("ano"):
            return (no_update,) * 7
        
        df = carrega_base_planejamento(store["ano"])
        if df.empty:
            return gera_card_atualizacao("-"), html.Div("Sem dados."), [], [], [], 0, {}

        # Filtros
        mapa = {
            "orgao": "orgao", "coordenacao": "coordenacao", "acao": "acao_programatica", 
            "elemento": "nome_elemento", "descricao": "politicas_para",
            "projeto": "codProjetoAtividade", "despesa": "codDespesa", 
            "fonte_descricao": "fonte_descricao", "vinculacao": "codVinculacao", "fonte": "ds_fonte"
        }
        
        for k_store, col_df in mapa.items():
            vals = store.get(k_store, ["Todos"])
            if vals and "Todos" not in vals and col_df in df.columns:
                df = df[df[col_df].isin(vals)]

        # Se o dataframe ficar vazio após os filtros, retorna tabela vazia mas mantém os cards zerados
        if df.empty:
            totais_vazio = {c: 0 for c in DE_PARA_PRESSAO.keys()}
            cards_vazios = monta_cards_resumo(totais_vazio, DE_PARA_PRESSAO)
            return gera_card_atualizacao("-"), cards_vazios, [], [], [], 0, {}
        
        # --- AGREGAÇÃO POR DOTAÇÃO ---
        # 1. De-duplica valores de contrato e empenho antes de somar
        df_contratos = df[df['_contract_row_id'].notna()].drop_duplicates(subset=['_contract_row_id'])
        df_orfaos = df[df['Origem'] == 'Empenho s/ Contrato']
        df_orcamento = df[df['Origem'] == 'Orçamento']
        df_dedup = pd.concat([df_contratos, df_orfaos, df_orcamento], ignore_index=True)

        # 2. Agrega os valores por Dotação, preservando as colunas descritivas já identificadas
        # Definimos quais colunas queremos manter (os índices da tabela)
        cols_indices = ['orgao', 'coordenacao', 'acao_programatica', 'nome_elemento', 'politicas_para']
        
        # Criamos o dicionário de agregação
        agg_dict = {
            'valDisponivel': ('valDisponivel', 'sum'),
            'total_necessario': ('Total necessário', 'sum'), # Nome temporário para evitar conflito
            'valor_empenhado': ('Valor Empenhado (SOF)', 'sum'), # Nome temporário
            'valor_pago': ('Valor Pago (SOF)', 'sum') # Nome temporário
        }
        
        # Adicionamos as colunas descritivas ao agg usando 'first' (elas são constantes por dotação)
        for col in cols_indices:
            if col in df_dedup.columns:
                agg_dict[col] = (col, 'first')

        df_pressao = df_dedup.groupby('Dotação Formatada', as_index=False).agg(**agg_dict)

        # 4. Calcula os campos de pressão
        df_pressao["Pressão"] = df_pressao["valDisponivel"] - df_pressao["total_necessario"]
        df_pressao["Tem Pressão?"] = np.where(df_pressao["Pressão"] < 0, "Sim", "Não")
        df_pressao["Falta Pagar"] = df_pressao["valor_empenhado"] - df_pressao["valor_pago"]
        df_pressao.rename(columns={'total_necessario': 'Total necessário', 'valor_empenhado': 'Valor Empenhado (SOF)', 'valor_pago': 'Valor Pago (SOF)'}, inplace=True)

        # 4.1 Aplica Filtro Local de Pressão
        vals_tp = store.get("tem_pressao", ["Todos"])
        if vals_tp and "Todos" not in vals_tp:
            df_pressao = df_pressao[df_pressao["Tem Pressão?"].isin(vals_tp)]

        # --- GERAÇÃO DO GRÁFICO POR ÓRGÃO ---
        df_grafico = df_pressao.groupby('orgao', as_index=False).agg({
            'valDisponivel': 'sum',
            'Total necessário': 'sum'
        })
        
        df_melted = df_grafico.melt(
            id_vars='orgao', 
            value_vars=['valDisponivel', 'Total necessário'],
            var_name='Métrica', 
            value_name='Valor'
        )
        df_melted['Métrica'] = df_melted['Métrica'].replace({'valDisponivel': 'Disponível', 'Total necessário': 'Total Necessário'})

        fig = px.bar(
            df_melted, x='orgao', y='Valor', color='Métrica', barmode='group',
            title='Comparativo: Disponível vs Total Necessário por Órgão',
            labels={'orgao': 'Órgão', 'Valor': 'Valor (R$)'},
            color_discrete_map={'Disponível': '#007bff', 'Total Necessário': '#6c757d'},
            template='plotly_white'
        )
        fig.update_layout(yaxis_tickformat=",.2f", legend_title_text='')

        totais = {c: df_pressao[c].sum() for c in DE_PARA_PRESSAO.keys() if c in df_pressao.columns}
        cards = monta_cards_resumo(totais, DE_PARA_PRESSAO)

        # Se nenhuma coluna for selecionada, exibe os cards mas não a tabela para evitar erro.
        if not cols_selecionadas:
            return gera_card_atualizacao("-"), cards, [], [], [], 0, fig
        
        pivot = df_pressao

        # Filtra as colunas do DataFrame com base na seleção do usuário
        if cols_selecionadas and not pivot.empty:
            # Ordena as colunas com base na definição do MAPA_COLUNAS
            ordem_preferencial = list(MAPA_COLUNAS_PRESSAO.keys())
            cols_to_keep = [c for c in ordem_preferencial if c in cols_selecionadas and c in pivot.columns]
            cols_to_keep += [c for c in cols_selecionadas if c in pivot.columns and c not in ordem_preferencial]
            
            if not cols_to_keep:
                return gera_card_atualizacao("-"), cards, [], [], [], 0, fig
            pivot = pivot[cols_to_keep]
        
        cols_table = []
        for c in pivot.columns:
            if c in DE_PARA_PRESSAO:
                nome = DE_PARA_PRESSAO[c]
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
            elif c in DE_PARA_INDICES_PRESSAO:
                nome = DE_PARA_INDICES_PRESSAO.get(c, c) # Usa .get para fallback
                tipo = "text"
                fmt = None
            else:
                # Fallback para colunas não mapeadas (como 'Objeto' ou 'Dotação Formatada')
                nome = c
                tipo = "text"
                fmt = None
            cols_table.append({"name": nome, "id": c, "type": tipo, "format": fmt})
        
        style_conditional = []
        if "Pressão" in cols_to_keep:
            style_conditional.append({
                'if': {'filter_query': '{Pressão} < 0'},
                'backgroundColor': '#ffdddd', # Vermelho claro
                'fontWeight': 'bold'
            })
        return gera_card_atualizacao("-"), cards, pivot.to_dict("records"), cols_table, style_conditional, 0, fig