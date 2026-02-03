import pandas as pd
import numpy as np
import openpyxl
import plotly.express as px
from dash import Dash, html, dcc, Input, Output

app = Dash(__name__)

# tudo acima deve ser feito antes de começar a fazer qualquer dash no python

# assume you have a "long-form" data frame

df = pd.read_excel("Vendas.xlsx")

fig = px.bar(df, x="Produto", y="Quantidade", color="ID Loja", barmode="group")
opcoes = list(df["ID Loja"].unique())
opcoes.append("Todas")

app.layout = html.Div(children=[
    html.H1(children='Faturamento'),
    html.H2(children="Gráfico do curso"),

    html.Div(children='''
        Futuramente isso será o painel orçamentário
    '''),
    dcc.Dropdown(opcoes, value='Todas', id='lista_lojas', multi=True),
    dcc.Graph(
        id='grafico_vendas',
        figure=fig
    )
])

@app.callback(
    Output('grafico_vendas', 'figure'),
    Output('lista_lojas', 'value'),
    Input('lista_lojas', 'value')
)

# Esse @ é um decorador. Ele serve para "decorar" a função que vem logo abaixo
# Ele indica o que a função update_output vai receber como parâmetros os valores indicados no Input

# Input é quem vai realizar as modificações. No caso, o botão dropdown. A informação que ele passa é o value
# Output é o que vai ser modificado. No caso, o gráfico. A informação editada é o figure

def update_output(value):
    # Garantindo que seja sempre uma lista
    if isinstance(value, str):
        value = [value]
    if value is None or len(value) == 0:
        value = ["Todas"]

    # Se "Todas" estiver na lista, remove os outros valores
    if "Todas" in value and len(value) > 1:
        value = [v for v in value if v != "Todas"]

    elif "Todas" in value:
        fig = px.bar(df, x="Produto", y="Quantidade", color="ID Loja", barmode="group")
        return fig, value
    elif "Todas" not in value:
        tabela_filtrada = df[df["ID Loja"].isin(value)]
        fig = px.bar(tabela_filtrada, x="Produto", y="Quantidade", color="ID Loja", barmode="group")
        return fig, value

if __name__ == '__main__':
    app.run(debug=True)