import os
import pandas as pd
import numpy as np
import openpyxl
import plotly.express as px
from dash import Dash, html, dcc, Input, Output, State, callback_context
import dash.dash_table as dt
from dash.dash_table.Format import Format, Group, Scheme, Symbol
import pytz
import time
from datetime import datetime, timedelta

# Rodar

app = Dash(__name__)

# ✅ Corrigido: a pasta base_despesas está no mesmo diretório que este arquivo
base_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "base_despesas")

# ✅ Lista anos
anos_disponiveis = sorted([p for p in os.listdir(base_dir) if os.path.isdir(os.path.join(base_dir, p))])
print("Anos disponíveis:", anos_disponiveis)

if not anos_disponiveis:
    raise FileNotFoundError(f"❌ Nenhuma pasta de ano encontrada em: {base_dir}")

ano_padrao = anos_disponiveis[-1]

# Lista meses disponíveis para o ano padrão
def lista_meses(ano):
    pasta_ano = os.path.join(base_dir, ano)
    arquivos = [f for f in os.listdir(pasta_ano) if f.endswith('.xlsx')]
    meses = sorted([
        f.replace(f"despesas_{ano}", "").replace(".xlsx", "") for f in arquivos
    ])
    return meses

meses_disponiveis = lista_meses(ano_padrao)
mes_padrao = meses_disponiveis[-1] if meses_disponiveis else None

def carrega_base(ano, mes):
    caminho = os.path.join(base_dir, ano, f"despesas_{ano}{mes}.xlsx")
    return pd.read_excel(caminho)

# Inicializa com o padrão
base_despesas = carrega_base(ano_padrao, mes_padrao)

def gera_pivot(base_despesas):
    colunas = [
        "valOrcadoInicial",
        "valOrcadoAtualizado",
        "valCongelado",
        "valDescongelado",
        "valEmpenhadoLiquido",
        "valLiquidado",
        "valPagoExercicio",
        "valReservadoLiquido",
        "data_hora_extracao"
    ]
    pivot = base_despesas.pivot_table(
        index=["orgao", "projeto_atividade", "coordenação", "despesa", "nome_elemento"],   
        values=colunas,
        aggfunc="sum",
        fill_value=0
    ).reset_index()
    pivot["Congelado"] = (
        pivot["valCongelado"] - pivot["valDescongelado"]
    ).replace([np.inf, -np.inf, np.nan], 0)
    pivot["Congelado"] = pivot["Congelado"].round(2)

    pivot["Saldo de Dotação"] = (
        pivot["valOrcadoAtualizado"] - pivot["Congelado"] - pivot["valEmpenhadoLiquido"]
    ).replace([np.inf, -np.inf, np.nan], 0)
    pivot["Saldo de Dotação"] = pivot["Saldo de Dotação"].round(2)
    return pivot

pivot = gera_pivot(base_despesas)

opcoes_orgao = list(pivot["orgao"].unique())
opcoes_orgao.append("Todos")
opcoes_coordenacao = list(pivot["coordenação"].unique())
opcoes_coordenacao.append("Todas")
opcoes_elemento = list(pivot["nome_elemento"].unique())
opcoes_elemento.append("Todos")
opcoes_despesa = list(pivot["despesa"].unique())
opcoes_despesa.append("Todos")
opcoes_projeto_atividade = list(pivot["projeto_atividade"].unique())
opcoes_projeto_atividade.append("Todos")


colunas_brl = [
    "valOrcadoInicial",
    "valOrcadoAtualizado",
    "Congelado",
    "valEmpenhadoLiquido",
    "valLiquidado",
    "valPagoExercicio",
    "Saldo de Dotação"
]

colunas_exibir = [
    "orgao",
    "coordenação",
    "despesa",
    "nome_elemento",
    "valOrcadoInicial",
    "valOrcadoAtualizado",
    "valLiquidado",
    "valPagoExercicio",
    "Congelado",
    "valEmpenhadoLiquido",
    "Saldo de Dotação"
]

columns=[
    {
        "name": i,
        "id": i,
        "type": "numeric",
        "format": Format(
            scheme=Scheme.fixed, 
            precision=2, 
            group=Group.yes, 
            groups=3, 
            decimal_delimiter=",", 
            group_delimiter="."
        ).symbol(Symbol.yes).symbol_prefix("R$ ")
    } if i in colunas_brl else {"name": i, "id": i}
    for i in colunas_exibir
]

app.layout = html.Div(children=[
    html.H1(children='Painel Orçamentário'),
    html.H2(children="Tabela Dinâmica de Despesas por coordenação"),
    html.Label("Ano:"),
    dcc.Dropdown(
        id="dropdown_ano",
        options=[{"label": a, "value": a} for a in anos_disponiveis],
        value=ano_padrao,
        clearable=False
    ),
    html.Label("Mês:"),
    dcc.Dropdown(
        id="dropdown_mes",
        options=[{"label": m, "value": m} for m in meses_disponiveis],
        value=mes_padrao,
        clearable=False
    ),
    html.Label('Órgão:'),
    dcc.Dropdown(opcoes_orgao, value=['Todos'], id='lista_orgao', multi=True),
    html.Label('Coordenação:'),
    dcc.Dropdown(opcoes_coordenacao, value=['Todas'], id='lista_coordenação', multi=True),
    html.Label('Projeto/Atividade:'),
    dcc.Dropdown(id='lista_projeto_atividade', value=['Todos'], multi=True),
    html.Label('Elemento de Despesa:'),
    dcc.Dropdown(opcoes_elemento, value=['Todos'], id='lista_elemento', multi=True),
    html.Label('Despesa (Código):'),
    dcc.Dropdown(opcoes_despesa, value=['Todos'], id='lista_despesa', multi=True),
    html.Br(),
    html.Button('Limpar Filtros', id='botao_limpar', n_clicks=0),
    html.Br(),
    html.Label('Colunas a Exibir e Ordem:'),
    dcc.Dropdown(
        id='ordem_colunas',
        options=[{"label": c, "value": c} for c in colunas_exibir],
        value=colunas_exibir,
        multi=True,
        placeholder='Selecione as colunas...'
    ),
    html.Br(),
    html.H3(id="data_hora_atualizacao"),
    html.Div(id='resumo_valores'),
    html.Label('Execução Orçamentária'),
    dt.DataTable(
        id='tabela_dinamica',
        data=pivot[colunas_exibir].to_dict('records'),
        columns=columns,
        style_table={'overflowX': 'auto'},
        style_cell={'textAlign': 'left'},
    ),
])

@app.callback(
    Output('dropdown_mes', 'options'),
    Output('dropdown_mes', 'value'),
    Input('dropdown_ano', 'value')
)
def atualiza_meses(ano):
    meses = lista_meses(ano)
    mes = meses[-1] if meses else None
    return [{"label": m, "value": m} for m in meses], mes

@app.callback(
    Output('tabela_dinamica', 'data'),
    Output('tabela_dinamica', 'columns'),
    Output('lista_coordenação', 'value'),
    Output('resumo_valores', 'children'),
    Output('lista_orgao', 'value'),
    Output('lista_projeto_atividade', 'value'),
    Output('lista_elemento', 'value'),
    Output('lista_despesa', 'value'),
    Output('data_hora_atualizacao', 'children'),
    Output('lista_orgao', 'options'),
    Output('lista_coordenação', 'options'),
    Output('lista_projeto_atividade', 'options'),
    Output('lista_elemento', 'options'),
    Output('lista_despesa', 'options'),
    Output('ordem_colunas', 'options'),
    Input('lista_orgao', 'value'),
    Input('lista_coordenação', 'value'),
    Input('lista_projeto_atividade', 'value'),
    Input('lista_elemento', 'value'),
    Input('lista_despesa', 'value'),
    Input('dropdown_ano', 'value'),
    Input('dropdown_mes', 'value'),
    Input('botao_limpar', 'n_clicks'),
    Input('ordem_colunas', 'value'),
    prevent_initial_call=False
)
def update_output(orgao, coordenacao, projeto_atividade, elemento, despesa, ano, mes, n_clicks, ordem_colunas):
    # Se o botão foi clicado, limpa todos os filtros
    ctx = callback_context
    if ctx.triggered and ctx.triggered[0]['prop_id'] == 'botao_limpar.n_clicks':
        orgao = ['Todos']
        coordenacao = ['Todas']
        projeto_atividade = ['Todos']
        elemento = ['Todos']
        despesa = ['Todos']

    # Se nenhuma coluna foi selecionada, exibe todas
    if not ordem_colunas:
        ordem_colunas = colunas_exibir

    ordem_final = ordem_colunas

    base_despesas = carrega_base(ano, mes)
    pivot = gera_pivot(base_despesas)

    # Opções dos filtros (sempre baseado nos dados carregados)
    opcoes_orgao = list(pivot["orgao"].unique()) + ["Todos"]
    opcoes_coordenacao = list(pivot["coordenação"].unique()) + ["Todas"]
    opcoes_projeto_atividade = list(pivot["projeto_atividade"].unique()) + ["Todos"]
    opcoes_elemento = list(pivot["nome_elemento"].unique()) + ["Todos"]
    opcoes_despesa = list(pivot["despesa"].unique()) + ["Todos"]

    # Converte None em lista padrão
    orgao = orgao if orgao else ["Todos"]
    coordenacao = coordenacao if coordenacao else ["Todas"]
    projeto_atividade = projeto_atividade if projeto_atividade else ["Todos"]
    elemento = elemento if elemento else ["Todos"]
    despesa = despesa if despesa else ["Todos"]

    # Remove "Todos"/"Todas" se houver outros selecionados
    if "Todos" in orgao and len(orgao) > 1:
        orgao = [v for v in orgao if v != "Todos"]
    if "Todas" in coordenacao and len(coordenacao) > 1:
        coordenacao = [v for v in coordenacao if v != "Todas"]
    if "Todos" in projeto_atividade and len(projeto_atividade) > 1:
        projeto_atividade = [v for v in projeto_atividade if v != "Todos"]
    if "Todos" in elemento and len(elemento) > 1:
        elemento = [v for v in elemento if v != "Todos"]
    if "Todos" in despesa and len(despesa) > 1:
        despesa = [v for v in despesa if v != "Todos"]

    # Sincronização inteligente entre despesa e elemento
    # Só sincroniza se um deles não está em "Todos"
    if elemento != ["Todos"] or despesa != ["Todos"]:
        # Se elemento foi selecionado, sincroniza despesa
        if elemento != ["Todos"]:
            despesa_valida = pivot[pivot["nome_elemento"].isin(elemento)]["despesa"].unique().tolist()
            despesa = [d for d in despesa if d in despesa_valida]
            if not despesa:
                despesa = ["Todos"]
            opcoes_despesa = despesa_valida + ["Todos"]
        
        # Se despesa foi selecionado, sincroniza elemento
        if despesa != ["Todos"]:
            elemento_valida = pivot[pivot["despesa"].isin(despesa)]["nome_elemento"].unique().tolist()
            elemento = [e for e in elemento if e in elemento_valida]
            if not elemento:
                elemento = ["Todos"]
            opcoes_elemento = elemento_valida + ["Todos"]

    # Filtra o DataFrame conforme os filtros selecionados
    tabela = pivot.copy()
    if orgao != ["Todos"]:
        tabela = tabela[tabela["orgao"].isin(orgao)]
    if coordenacao != ["Todas"]:
        tabela = tabela[tabela["coordenação"].isin(coordenacao)]
    if projeto_atividade != ["Todos"]:
        tabela = tabela[tabela["projeto_atividade"].isin(projeto_atividade)]
    if elemento != ["Todos"]:
        tabela = tabela[tabela["nome_elemento"].isin(elemento)]
    if despesa != ["Todos"]:
        tabela = tabela[tabela["despesa"].isin(despesa)]
    
    # Seleciona apenas as colunas desejadas na ordem definida
    tabela = tabela[ordem_final]

    # Calcula os totais para o resumo
    orcado_inicial_total = tabela["valOrcadoInicial"].sum() if "valOrcadoInicial" in ordem_final else 0
    orcado_atualizado_total = tabela["valOrcadoAtualizado"].sum() if "valOrcadoAtualizado" in ordem_final else 0
    congelado_total = tabela["Congelado"].sum() if "Congelado" in ordem_final else 0
    empenhado_total = tabela["valEmpenhadoLiquido"].sum() if "valEmpenhadoLiquido" in ordem_final else 0
    liquidado_total = tabela["valLiquidado"].sum() if "valLiquidado" in ordem_final else 0
    pago_total = tabela["valPagoExercicio"].sum() if "valPagoExercicio" in ordem_final else 0
    saldo_dotacao_total = tabela["Saldo de Dotação"].sum() if "Saldo de Dotação" in ordem_final else 0

    resumo = (
        f"Orçado Inicial Total: R$ {orcado_inicial_total:,.2f} | "
        f"Orçado Atualizado Total: R$ {orcado_atualizado_total:,.2f} | "
        f"Congelado Total: R$ {congelado_total:,.2f} | "
        f"Empenhado Líquido Total: R$ {empenhado_total:,.2f} | "
        f"Liquidado Total: R$ {liquidado_total:,.2f} | "
        f"Pago no Exercício Total: R$ {pago_total:,.2f} | "
        f"Saldo de Dotação Total: R$ {saldo_dotacao_total:,.2f}"
    )
    resumo = resumo.replace(",", "X").replace(".", ",").replace("X", ".")

    # Data/hora de atualização
    data_atualizacao = pd.to_datetime(pivot["data_hora_extracao"], errors="coerce").max()
    data_atualizacao_str = data_atualizacao.strftime("%d/%m/%Y %H:%M:%S") if pd.notnull(data_atualizacao) else ""

    # Gera as colunas dinamicamente baseado na ordem final
    columns_dinamicas = [
        {
            "name": i,
            "id": i,
            "type": "numeric",
            "format": Format(
                scheme=Scheme.fixed, 
                precision=2, 
                group=Group.yes, 
                groups=3, 
                decimal_delimiter=",", 
                group_delimiter="."
            ).symbol(Symbol.yes).symbol_prefix("R$ ")
        } if i in colunas_brl else {"name": i, "id": i}
        for i in ordem_final
    ]

    return (
        tabela.to_dict('records'),
        columns_dinamicas,
        coordenacao,
        resumo,
        orgao,
        projeto_atividade,
        elemento,
        despesa,
        f"Atualizado em: {data_atualizacao_str}",
        [{"label": o, "value": o} for o in opcoes_orgao],
        [{"label": c, "value": c} for c in opcoes_coordenacao],
        [{"label": p, "value": p} for p in opcoes_projeto_atividade],
        [{"label": e, "value": e} for e in opcoes_elemento],
        [{"label": d, "value": d} for d in opcoes_despesa],
        [{"label": c, "value": c} for c in colunas_exibir]
    )


server = app.server

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8050))
    app.run(host="0.0.0.0", port=port, debug=False)