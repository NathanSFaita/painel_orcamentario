import dash_bootstrap_components as dbc
from dash import dcc, html
import os
from utils import BASE_DIR, descrição_cards

# --- Lógica para descobrir anos disponíveis ---
anos_despesas = []
despesas_dir = os.path.join(BASE_DIR, "base_despesas")
if os.path.exists(despesas_dir):
    anos_despesas = [
        p for p in os.listdir(despesas_dir)
        if os.path.isdir(os.path.join(despesas_dir, p)) and p.isdigit() and len(p) == 4
    ]

anos_empenhos = []
empenhos_dir = os.path.join(BASE_DIR, "base_empenhos")
if os.path.exists(empenhos_dir):
    anos_empenhos_bruto = [
        f.replace("empenhos_", "").replace(".csv", "") for f in os.listdir(empenhos_dir)
        if f.startswith("empenhos_") and f.endswith(".csv") and not f.startswith("~$")
    ]
    # Garante que apenas anos com 4 dígitos sejam incluídos
    anos_empenhos = [ano for ano in anos_empenhos_bruto if ano.isdigit() and len(ano) == 4]

anos_contratos = []
contratos_dir = os.path.join(BASE_DIR, "base_contratos")
if os.path.exists(contratos_dir):
    anos_contratos_bruto = [
        f.replace("contratos_", "").replace(".xlsx", "") for f in os.listdir(contratos_dir)
        if f.startswith("contratos_") and f.endswith(".xlsx") and not f.startswith("~$")
    ]
    # Garante que apenas anos com 4 dígitos sejam incluídos
    anos_contratos = [ano for ano in anos_contratos_bruto if ano.isdigit() and len(ano) == 4]

# Combina as listas, remove duplicatas e ordena
anos_disponiveis = sorted(list(set(anos_despesas + anos_empenhos + anos_contratos)))
    
ano_padrao = anos_disponiveis[-1] if anos_disponiveis else None

def criar_label_com_tooltip(texto, prefixo):
    """Cria um label com tooltip se houver descrição no dicionário."""
    descricao = descrição_cards.get(texto)
    elementos = [html.Span(texto, style={"verticalAlign": "middle"})]

    if descricao:
        # Gera ID único para o tooltip
        id_safe = texto.replace(" ", "").replace("(", "").replace(")", "").lower()
        id_tooltip = f"tooltip-{prefixo}-{id_safe}"
        
        elementos.append(html.Span(" ℹ️", id=id_tooltip, style={"cursor": "help", "fontSize": "0.8em", "marginLeft": "5px", "verticalAlign": "middle", "opacity": "0.7"}))
        elementos.append(dbc.Tooltip(descricao, target=id_tooltip, placement="top"))

    return html.Label(elementos, className="fw-bold w-100", style={"minHeight": "50px", "display": "flex", "alignItems": "end"})

def _get_filter_definitions(prefixo):
    """Retorna um dicionário mapeando chaves de filtro para suas definições de componente."""
    return {
        "ano": dbc.Col([
            criar_label_com_tooltip("Ano", prefixo),
            dcc.Dropdown(
                id=f"{prefixo}-ano",
                options=[{"label": a, "value": a} for a in anos_disponiveis],
                value=None, clearable=False,
                style={"height": "38px", "width": "100%"}
            ),
        ], md=1),
        "orgao": dbc.Col([
            criar_label_com_tooltip("Órgão", prefixo),
            dcc.Dropdown(id=f"{prefixo}-orgao", multi=True, closeOnSelect=False, optionHeight=75,
                         style={"maxHeight": "45px"})
        ], md=1),
        "coordenacao": dbc.Col([
            criar_label_com_tooltip("Coordenação", prefixo),
            dcc.Dropdown(id=f"{prefixo}-coordenacao", multi=True, closeOnSelect=False, optionHeight=75,
                         style={"maxHeight": "45px"})
        ], md=1),
        "descricao": dbc.Col([
            criar_label_com_tooltip("Descrição da Coordenação", prefixo),
            dcc.Dropdown(id=f"{prefixo}-descricao", multi=True, closeOnSelect=False, optionHeight=75,
                         style={"maxHeight": "45px"})
        ], md=1),
        "projeto": dbc.Col([
            criar_label_com_tooltip("Ação", prefixo),
            dcc.Dropdown(id=f"{prefixo}-projeto", multi=True, closeOnSelect=False, optionHeight=75,
                         style={"maxHeight": "45px"})
        ], md=1),
        "acao": dbc.Col([
            criar_label_com_tooltip("Atividade", prefixo),
            dcc.Dropdown(id=f"{prefixo}-acao", multi=True, closeOnSelect=False, optionHeight=75,
                         style={"maxHeight": "45px"})
        ], md=1),
        "despesa": dbc.Col([
            criar_label_com_tooltip("Despesa (Código)", prefixo),
            dcc.Dropdown(id=f"{prefixo}-despesa", multi=True, closeOnSelect=False, optionHeight=75, style={"maxHeight": "45px"})
        ], md=1),
        "elemento": dbc.Col([
            criar_label_com_tooltip("Elemento de Despesa", prefixo),
            dcc.Dropdown(id=f"{prefixo}-elemento", multi=True, closeOnSelect=False, optionHeight=75, style={"maxHeight": "45px"})
        ], md=1),
        "fonte-descricao": dbc.Col([
            criar_label_com_tooltip("Fonte (Descrição)", prefixo),
            dcc.Dropdown(id=f"{prefixo}-fonte-descricao", multi=True, closeOnSelect=False, optionHeight=75, style={"maxHeight": "45px"})
        ], md=2),
        "vinculacao": dbc.Col([
            criar_label_com_tooltip("Vinculação (Código)", prefixo),
            dcc.Dropdown(id=f"{prefixo}-vinculacao", multi=True, closeOnSelect=False, optionHeight=75, style={"maxHeight": "45px"})
        ], md=1),
        "fonte": dbc.Col([
            criar_label_com_tooltip("Vinculação", prefixo),
            dcc.Dropdown(id=f"{prefixo}-fonte", multi=True, closeOnSelect=False, optionHeight=75, style={"maxHeight": "45px"})
        ], md=1),
        "processo": dbc.Col([
            criar_label_com_tooltip("Processo SEI", prefixo),
            dcc.Dropdown(id=f"{prefixo}-processo", multi=True, closeOnSelect=False, optionHeight=75, style={"maxHeight": "45px"})
        ], md=2),
        "credor": dbc.Col([
            criar_label_com_tooltip("Credor", prefixo),
            dcc.Dropdown(id=f"{prefixo}-credor", multi=True, closeOnSelect=False, optionHeight=75, style={"maxHeight": "45px"})
        ], md=2),
        "objeto": dbc.Col([
            criar_label_com_tooltip("Objeto", prefixo),
            dcc.Dropdown(id=f"{prefixo}-objeto", multi=True, closeOnSelect=False, clearable=True, optionHeight=75, style={"maxHeight": "45px"})
        ], md=3),
        "origem": dbc.Col([
            criar_label_com_tooltip("Origem do Dado", prefixo),
            dcc.Dropdown(id=f"{prefixo}-origem", multi=True, closeOnSelect=False, optionHeight=75, style={"maxHeight": "45px"})
        ], md=3),
        "fase": dbc.Col([
            criar_label_com_tooltip("Fase do Contrato", prefixo),
            dcc.Dropdown(id=f"{prefixo}-fase", multi=True, closeOnSelect=False, optionHeight=75, style={"maxHeight": "45px"})
        ], md=2),
        "status_empenho": dbc.Col([
            criar_label_com_tooltip("Status de Empenho", prefixo),
            dcc.Dropdown(id=f"{prefixo}-status_empenho", multi=True, closeOnSelect=False, optionHeight=75, style={"maxHeight": "45px"})
        ], md=2),
        "situacao_orcamentaria": dbc.Col([
            criar_label_com_tooltip("Situação Orçamentária", prefixo),
            dcc.Dropdown(id=f"{prefixo}-situacao_orcamentaria", multi=True, closeOnSelect=False, optionHeight=75, style={"maxHeight": "45px"})
        ], md=2),
        "tem_pressao": dbc.Col([
            criar_label_com_tooltip("Tem Pressão?", prefixo),
            dcc.Dropdown(id=f"{prefixo}-tem_pressao", multi=True, closeOnSelect=False,
                         options=[{"label": "Sim", "value": "Sim"}, {"label": "Não", "value": "Não"}],
                         style={"maxHeight": "45px"})
        ], md=1),
        "descricao_generica": dbc.Col([
            criar_label_com_tooltip("Produto", prefixo),
            dcc.Dropdown(id=f"{prefixo}-descricao_generica", multi=True, closeOnSelect=False, optionHeight=75, style={"maxHeight": "45px"})
        ], md=2),
        "numero_termo": dbc.Col([
            criar_label_com_tooltip("Nº Termo", prefixo),
            dcc.Dropdown(id=f"{prefixo}-numero_termo", multi=True, closeOnSelect=False, optionHeight=75, style={"maxHeight": "45px"})
        ], md=2),
    }

def _get_empenho_specific_filters(prefixo):
    """Retorna uma lista de componentes de filtro específicos para a página de empenhos."""
    return [
        html.Hr(className="my-3"),
        dbc.Row([
            dbc.Col([
                criar_label_com_tooltip("Nº Empenho", prefixo),
                dcc.Dropdown(id=f"{prefixo}-filtro-empenho", multi=True, closeOnSelect=False, optionHeight=75,
                             style={"maxHeight": "45px"})], md=1),
            dbc.Col([
                criar_label_com_tooltip("Processo SEI", prefixo),
                dcc.Dropdown(id=f"{prefixo}-filtro-processo", multi=True, closeOnSelect=False, optionHeight=75,
                             style={"maxHeight": "45px"})], md=2),
            dbc.Col([
                html.Label("Data Empenho", className="fw-bold w-100", style={"minHeight": "50px", "display": "flex", "alignItems": "end"}),
                dcc.DatePickerRange(
                    id=f"{prefixo}-date-picker",
                    display_format="DD/MM/YYYY",
                    start_date_placeholder_text="Início",
                    end_date_placeholder_text="Fim",
                    style={"width": "100%", "position": "relative"}
                )
            ], md=2),
            dbc.Col([
                criar_label_com_tooltip("Credor", prefixo),
                dcc.Dropdown(id=f"{prefixo}-filtro-credor", multi=True, closeOnSelect=False, optionHeight=75,
                             style={"maxHeight": "45px"})], md=2),
            dbc.Col([
                criar_label_com_tooltip("Item de Despesa", prefixo),
                dcc.Dropdown(id=f"{prefixo}-filtro-item", multi=True, closeOnSelect=False, optionHeight=75,
                             style={"maxHeight": "45px"})], md=1),
            dbc.Col([
                criar_label_com_tooltip("Situação do Empenho", prefixo),
                dcc.Dropdown(id=f"{prefixo}-filtro-situacao", multi=True, closeOnSelect=False, optionHeight=75,
                             style={"maxHeight": "45px"})], md=1),
            dbc.Col([
                criar_label_com_tooltip("Objeto do Empenho", prefixo),
                dcc.Dropdown(id=f"{prefixo}-filtro-objeto", multi=True, closeOnSelect=False, clearable=True, optionHeight=75,
                             style={"maxHeight": "45px"})], md=3),
        ], className="mb-4 g-1", justify="center"),
    ]

def layout_filtros_padrao(prefixo):
    """
    Gera o Grid de filtros com base no prefixo da página.
    prefixo: 'exe', 'emp', 'pre' ou 'pln' para diferenciar IDs.
    """
    # Define quais filtros cada página usa
    filtros_por_pagina = {
        "exe": ["ano", "orgao", "coordenacao", "descricao", "projeto", "acao", "despesa", "elemento", "fonte-descricao", "vinculacao", "fonte"],
        "emp": ["ano", "orgao", "coordenacao", "descricao", "projeto", "acao", "despesa", "elemento", "fonte-descricao", "vinculacao", "fonte"],
        "pre": ["ano", "orgao", "coordenacao", "descricao", "projeto", "acao", "despesa", "elemento", "fonte-descricao", "vinculacao", "fonte", "tem_pressao"],
        "pln": ["ano", "orgao", "coordenacao", "descricao", "projeto", "acao", "despesa", "elemento", "fonte-descricao", "vinculacao", "fonte", "processo", "credor", "objeto", "origem", "fase", "status_empenho", "situacao_orcamentaria", "descricao_generica", "numero_termo"],
    }
    
    filtros_necessarios = filtros_por_pagina.get(prefixo, [])
    todas_definicoes = _get_filter_definitions(prefixo)
    componentes_filtros = [todas_definicoes[key] for key in filtros_necessarios if key in todas_definicoes]
    
    layout_principal = [dbc.Row(componentes_filtros, className="mb-2 g-1", justify="center")]
    
    if prefixo == 'emp':
        layout_principal.extend(_get_empenho_specific_filters(prefixo))

    return html.Div([
        dbc.Button(
            "🔽 Filtros de Pesquisa (Clique para expandir/recolher)",
            id=f"{prefixo}-btn-toggle-filtros",
            className="mb-3 w-100",
            style={"textAlign": "left", "fontWeight": "bold", "border": "1px solid #ddd", "color": "#555", "backgroundColor": "#f8f9fa"}
        ),
        dbc.Collapse(
            id=f"{prefixo}-collapse-filtros", 
            is_open=True,
            children=layout_principal
        )
    ])
