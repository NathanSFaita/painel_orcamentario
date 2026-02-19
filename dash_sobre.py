import dash_bootstrap_components as dbc
from dash import html, Input, Output, State, dash_table
import pandas as pd
import os
from utils import cabecalho_padrao, descrição_cards, BASE_DIR

def layout_sobre():
    # Gera os itens do glossário dinamicamente a partir do dicionário existente
    itens_glossario = []
    for termo, definicao in descrição_cards.items():
        item = dbc.ListGroupItem([
            html.Div([
                html.H5(termo, className="mb-1 text-primary"),
                html.P(definicao, className="mb-1 text-muted")
            ], className="d-flex w-100 justify-content-between flex-column")
        ])
        itens_glossario.append(item)

    # Carregamento das tabelas auxiliares
    try:
        df_acoes = pd.read_excel(os.path.join(BASE_DIR, "dados_auxiliares", "procv_acoes.xlsx"))
    except Exception:
        df_acoes = pd.DataFrame()

    try:
        df_elementos = pd.read_excel(os.path.join(BASE_DIR, "dados_auxiliares", "procv_elemento.xlsx"))
    except Exception:
        df_elementos = pd.DataFrame()

    # Mapas para renomear as colunas (ID do Excel -> Nome na Tela)
    mapa_acoes = {
        "acao": "Código Ação",
        "coordenadoria": "Coordenação",
        "politicas_para": "Descrição da Coordenação",
        "acao_programatica": "Atividade"
    }

    mapa_elementos = {
        "num_elemento": "Código Elemento",
        "elemento_despesa": "Descrição do Elemento de Despesa"
    }

    return dbc.Container([
        cabecalho_padrao("📚 Informações e Glossário", "Entenda os termos do Orçamento"),
        
        dbc.Row([
            dbc.Col([
                dbc.Button("⬅️ Voltar para Execução", href="/", color="secondary", className="mb-4 me-2"),
                dbc.Button("Ir para Empenhos ➡️", href="/empenhos", color="primary", className="mb-4"),
            ], width=12, className="d-flex justify-content-center gap-2")
        ]),

        html.Hr(),

        dbc.Card([
            dbc.CardHeader(
                html.Div([
                    html.H5("Sobre este Painel", className="m-0"),
                    dbc.Button("➖/➕", id="btn-collapse-sobre", color="link", size="sm", className="text-decoration-none ms-2", n_clicks=1)
                ], className="d-flex align-items-center")
            ),
            dbc.Collapse(
                dbc.CardBody([
                    html.P(
                        "Este painel foi desenvolvido para fornecer uma visão clara e acessível sobre a" \
                        " execução orçamentária da Secretaria Municipal de Direitos Humanos e Cidadania (SMDHC). "
                        "Aqui você pode explorar os dados de despesas, empenhos e entender os " \
                        "termos técnicos utilizados no contexto orçamentário.",
                        className="card-text"
                    ),
                    html.P(
                        "Os dados apresentados são atualizados diariamente, refletindo as informações mais recentes disponíveis. ",
                        className="card-text"
                    ),
                    html.P(
                        "Nota: Os dados mensais são cumulativos. Portanto, o mês mais recente de cada ano apresenta o total acumulado " \
                        "do ano até aquele mês, enquanto os meses anteriores mostram os totais acumulados até o final de cada mês.",
                        className="card-text")
                ]),
                id="collapse-sobre", is_open=True
            )
        ], className="shadow-sm mb-5"),

        dbc.Card([
            dbc.CardHeader(
                html.Div([
                    html.H5("Sobre o Orçamento", className="m-0"),
                    dbc.Button("➖/➕", id="btn-collapse-orcamento", color="link", size="sm", className="text-decoration-none ms-2", n_clicks=1)
                ], className="d-flex align-items-center")
            ),
            dbc.Collapse(
                dbc.CardBody([
                    html.P(
                        "O Orçamento Público é o instrumento que o governo utiliza para planejar e controlar as receitas e despesas públicas. " \
                        "Ele é elaborado anualmente e serve como base para a gestão financeira do município.",                        
                        className="card-text"
                    ),
                    html.P(
                        "Historicamente, o orçamento público foi construído com a função de controle político dos órgãos de representação  " \
                        "(Legislativo) sobre o Executivo. Por isso, ele não se consolidou como um mero banlancete contábil com " \
                        "informações financeiras, pois foi necessário dotá-lo de informações úteis que permitissem " \
                        "a compreensão sobre o que estava sendo gasto, para que e com qual objetivo. (GIACOMONI, 2007)",
                        className="card-text"
                    ),
                    
                    html.P(
                        "A classificação do orçamento público é composta por quatro partes principais: " \
                        "a parte institucional, a parte funcional-programática, a parte da natureza econômica e a parte da fonte de recursos.",
                        className="card-text"),

                    html.H6("Classificação Institucional", className="mt-4"),
                    html.P(
                        "Esta parte evidencia quem é o responsável pela execução daquele gasto público, sendo um critério "\
                        "indispensável no que tange a responsabilidade do gasto. (GIACOMONI, 2007). "\
                        "Se divide em órgão e unidade orçamentária:",
                        className="card-text"),
                    html.Ul([
                        html.Li("Órgão: representa a estrutura administrativa do governo, como secretarias, fundações e autarquias. " \
                                "Cada órgão é responsável por um conjunto de atividades e políticas públicas."),
                        html.Li("Unidade Orçamentária: é a subdivisão do órgão, com o responsável sendo o ordenador de despesa. " \
                                "Por exemplo: Gabinete da Secretária, Diretorias Regionias de Ensino etc.")]),

                    html.H6("Classificação Funcional-Programática", className="mt-4"),
                    html.P(
                        "Uma das classificações mais importantes do orçamento público, pois "\
                        "tem como objetivo  fornecer as bases para a apresentação de dados e estatísticas sobre os gastos públicos nos "\
                        "principais segmentos em que atuam as organizações do Estado. (GIACOMONI, 2007)"\
                        "Se divide em Função, Subfunção, Programa e Projeto/Atividade:",
                        className="card-text"),
                    html.Ul([
                        html.Li("Função: representa a finalidade do gasto público, ou seja, o motivo pelo qual " \
                                "aquele gasto está sendo realizado. " \
                                "Exemplos de funções incluem Educação, Saúde, Assistência Social etc."),
                        html.Li("Subfunção: é uma subdivisão da função, que detalha ainda mais a finalidade do gasto. " \
                                "Por exemplo, dentro da função Educação, podemos ter subfunções como Ensino Fundamental, Ensino Médio etc."),
                        html.Li("Programa: é um conjunto de ações coordenadas para alcançar um objetivo específico. " \
                                "Os programas são compostos por projetos e atividades que contribuem para a " \
                                "realização dos objetivos estabelecidos de cada ente públci."),
                        html.Li("Projeto/Atividade: é a menor unidade de classificação funcional-programática, representando uma ação " \
                                "específica que contribui para o programa.")
                    ]),
                    html.P("A classificação das funções e subfunções seguem um padrão definido pelo governo federal, "\
                           "presente nos anexos da Lei 4.320/64. Já a classificação dos programas e projetos/atividades é definida " \
                           "por cada ente público, por meio de cada Plano Plurianual (PPA)."),
                    html.P(
                        "No caso da SMDHC, temos apenas Atividades no nosso orçamento. Elas, por sua vez, estão diretamente relacionadas à " \
                        "cada uma das nossas coordenações."),

                    html.H6("Classificação da Natureza Econômica", className="mt-4"),
                    html.P(
                        "Esta classificação tem como objetivo evidenciar a natureza do gasto público, ou seja, que tipo de gasto foi realizado (MTO, 2025). " \
                        "Ela é composta por quatro partes: Categoria Econômica, Grupo, Modalidade de Aplicação e Elemento de Despesa.",
                        className="card-text"),
                    html.Ul([
                        html.Li("Categoria Econômica: representa a categoria do gasto, ou seja, " \
                        "se é uma despesa corrente (gastos com custeio, pessoal, encargos sociais etc.) ou uma " \
                        "despesa de capital (investimentos, inversões financeiras etc.)."),
                        html.Li("Grupo: é uma subdivisão da categoria econômica que visa 'demonstrar importantes agregados da "
                        "despesa orçamentária', como despesas com pessoal, juros, custeios, encargos da dívida etc. " \
                                "Por exemplo, dentro da categoria de despesa corrente, podemos ter grupos como Pessoal e Encargos Sociais, Juros e Encargos da Dívida etc."),
                        html.Li("Modalidade de Aplicação: indica onde esses recursos serão aplicados: diretamente para empresas " \
                        "para Organizações da Sociedade Civil, outros órgãos da Administração Pública etc. "),
                        html.Li("Elemento de Despesa: é a menor unidade de classificação da natureza econômica, representando " \
                        "o objeto imediato de cada despesa. " \
                                "Por exemplo: material de consumo; contratações; vencimentos; auxílios financeiros etc.")
                                ]),
                    html.P(
                        "O conjunto dessas 4 classificações é o que permite inferir o que exatamente está sendo gasto. Por exemplo: " \
                        "o código 33903900 representa o custeio com contratos com Instituições Privadas com Fins Lucrativos, ou seja, " \
                        "contratações de serviços gerais, enquanto o código 33503900 representa o financiamento das parcerias com OSCs. " \
                        "A diferença entre ambos os códigos é justamente a Modalidade de Aplicação "
                        "(90 - Aplicações Diretas e 50 - Transferências à Instituições Privadas sem Fins Lucrativos, respectivamente), " \
                        "mesmo que o Elemento de Despesa seja o mesmo (39 - Outros Serviços de Terceiros - Pessoa Jurídica).",
                        className="card-text"),

                    html.H6("Classificação da Fonte de Recursos", className="mt-4"),
                    html.P(
                        "A fonte de recursos indica não apenas de onde vem o dinheiro utilizado para financiar os gastos públicos, " \
                        "mas também se há alguma destinação específica para este dinheiro. " \
                        "É composto por 4 partes: Fonte, Exercício, Destinação e Vinculação.",
                        className="card-text"),
                    html.Ul([
                        html.Li("Fonte: representa a origem dos recursos, como Tesouro Municipal, Transferências, " \
                                "Alienação de Bens etc."),
                        html.Li("Exercício: indica se o recurso é proveniente do Exercício Corrente ou de Exercícios Anteriores."),
                        html.Li("Destinação: indica se os recursos possuem uma destinação específica ou se são recursos livres. " \
                        "Por exemplo, recursos do Tesouro Municipal podem ser classificados como recursos livres" \
                       "(sem destinação pré-definida) enquanto os fundos possuem recursos com destinação específica à eles."),
                        html.Li("Vinculação: indica se os recursos estão vinculados a um programa ou ação específica, " \
                        "ou se são recursos livres para serem alocados conforme a necessidade. " \
                        "Aqui podemos localizar recursos vinculados ao Orçamento Cidadão, pagamento de concessionárias, "\
                        "emendas parlamentares etc."
                        )]),

                    html.P(
                        "A relação completa do significado de cada código está presente no Manual Técnico Orçamentário " \
                        "da União, no PPA municipal e no Manual de Elaboração da Proposta Orçamentária" \
                        " da Prefeitura de São Paulo. Links da seção de fontes e referências.",
                        className="card-text",
                    )

                ]),
                id="collapse-orcamento", is_open=True
            )
        ], className="shadow-sm mb-5"),

        dbc.Card([
            dbc.CardHeader(
                html.Div([
                    html.H5("Dotação Orçamentária (Códigos)", className="m-0"),
                    dbc.Button("➖/➕", id="btn-collapse-dotacao", color="link", size="sm", className="text-decoration-none ms-2", n_clicks=1)
                ], className="d-flex align-items-center")
            ),
            dbc.Collapse(
                dbc.CardBody([
                    html.P(
                        "Os códigos orçamentários são utilizados para classificar e organizar as despesas públicas. " \
                        "Eles seguem uma lógica que permite fácilmente identificar o objetivo, natureza e origem de cada gasto público, " \
                        "além de outros detalhes importantes para a gestão financeira do município.",
                        className="card-text"),
                    html.H6("Estrutura da dotação orçamentária - CPM", className="mt-4"),
                    html.Img(src="/assets/dotacao_mulheres.png", className="img-fluid", 
                             alt="Exemplo de estrutura de uma dotação orçamentária da coordenação de Políticas para Mulheres", 
                             style={"border": "1px solid #ddd", "borderRadius": "5px", "padding": "10px"}),
                    html.P("A dotação acima representa um gasto orçamentário especifico da Coordenação de Políticas para Mulheres. " \
                           "A ação orçamentária 6178, correspondente à parte funcional-programática do código, " \
                           "engloba as atividades referentes aos equipamentos públicos voltados ao atendimento de mulheres."
                           , className="card-text mt-3"),
                    html.P("Quanto à parte da natureza econômica, o conjunto dos códigos representa o financiamento " \
                           "das parcerias com Organizações da Sociedade Civil (OSC), indicado pela Modalidade de Aplicação " \
                           "50 (Transferências à Instituições Privadas sem Fins Lucrativos) e do Elemento de Despesa 39 " \
                           "(Outros Serviços de Terceiros - Pessoa Jurídica)." \
                           "O conjunto desses códigos (33503900) representa, portanto, o financiamento das parcerias com as OSCs", 
                           className="card-text"),
                    html.P("Já na parte da fonte, o conjunto 00.1.500.9001 representa recursos provenientes do Tesouro Municipal " \
                           "sem destinação pré-definida, ou seja, recursos que podem ser alocados para qualquer finalidade.",
                           className="card-text"),
                    html.Br(),
                    html.H6("Estrutura da dotação orçamentária - SESANA", className="mt-4"),
                    html.Img(src="/assets/dotacao_sesana.png", className="img-fluid", 
                             alt="Exemplo de estrutura de uma dotação orçamentária da Secretaria Executiva de Segurança Alimentar e Nutricional e de Abastecimento", 
                                style={"border": "1px solid #ddd", "borderRadius": "5px", "padding": "10px"}),
                    html.P("Já a dotação acima representa um gasto orçamentário de uma ação de SESANA, representado pela " \
                            "ação orçamentária 4426 (Políticas, Programas e Ações de Subsistência, Segurança Alimentar e Nutricional)"
                            , className="card-text mt-3"),
                    html.P("Quanto à parte da natureza econômica, repare que a Modalidade de Aplicação mudou (90 - Aplicações Diretas), " \
                           "enquanto o Elemento de Despesa é o mesmo (39 - Outros Serviços de Terceiros - Pessoa Jurídica). " \
                           "Com isso, o conjunto do código 33903900 representa o custeio com contratos com " \
                           "Instituições Privadas com Fins Lucrativos, ou seja, contratações de serviços gerais", 
                           className="card-text"),
                    html.P("Já na parte da fonte, destaca-se que o código 00.1.500.9005 rerepresenta recursos provenientes do Tesouro Municipal " \
                           "com destinação para o Orçamento Cidadão", 
                           className="card-text"),
                    html.Br(),
                                    ]),
                id="collapse-codigos", is_open=True
            )
        ], className="shadow-sm mb-5"),

        dbc.Card([
            dbc.CardHeader(
                html.Div([
                    html.H5("Descrição dos códigos e siglas", className="m-0"),
                    dbc.Button("➖/➕", id="btn-collapse-codigos", color="link", size="sm", className="text-decoration-none ms-2", n_clicks=1)
                ], className="d-flex align-items-center")
            ),
            dbc.Collapse(
                dbc.CardBody([
                    html.P(
                        "Abaixo estão as descrições dos principais códigos e siglas utilizados aqui na SMDHC, " \
                        "a fim de facilitar a compreensão dos dados apresentados. "),
                    html.H5("Tabela de Ações (Projeto/Atividade)", className="mb-3"),
                    dash_table.DataTable(
                        data=df_acoes.to_dict('records'),
                        columns=[{"name": mapa_acoes[col], "id": col} for col in mapa_acoes if col in df_acoes.columns],
                        style_table={'overflowX': 'auto'},
                        style_header={'backgroundColor': "#0f69c9", 'fontWeight': 'bold', "fontSize": "24px", 
                                      "fontFamily": "Calibri, sans-serif", "color": "#FFFFFF"},
                        style_cell={'textAlign': 'left', 'fontSize': '20px', "fontFamily": "Calibri, sans-serif", "color": "#333333"},
                        page_size=10,
                        sort_action="native"
                    ),
                    html.Hr(className="my-4"),
                    html.H5("Tabela de Elementos de Despesa", className="mb-3"),
                    dash_table.DataTable(
                        data=df_elementos.to_dict('records'),
                        columns=[{"name": mapa_elementos[col], "id": col} for col in mapa_elementos if col in df_elementos.columns],
                        style_table={'overflowX': 'auto'},
                        style_header={'backgroundColor': "#0f69c9", 'fontWeight': 'bold', "fontSize": "24px", 
                                      "fontFamily": "Calibri, sans-serif", "color": "#FFFFFF"},
                        style_cell={'textAlign': 'left', 'fontSize': '20px', "fontFamily": "Calibri, sans-serif", "color": "#333333"},
                        page_size=10,
                        sort_action="native"
                    ),
                ]),
                id="collapse-codigos-siglas", is_open=True
            )
        ], className="shadow-sm mb-5"),

        dbc.Card([
            dbc.CardHeader(
                html.Div([
                    html.H5("Glossário de Termos Orçamentários", className="m-0"),
                    dbc.Button("➖/➕", id="btn-collapse-glossario", color="link", size="sm", className="text-decoration-none ms-2", n_clicks=1)
                ], className="d-flex align-items-center")
            ),
            dbc.Collapse(
                dbc.CardBody([
                    html.P("Abaixo você encontra a definição de cada termo utilizado nos cards e tabelas deste painel.", className="card-text"),
                    dbc.ListGroup(itens_glossario, flush=True)
                ]),
                id="collapse-glossario", is_open=True
            )
        ], className="shadow-sm mb-5"),

        dbc.Card([
            dbc.CardHeader(
                html.Div([
                    html.H5("Fontes e Referências", className="m-0"),
                    dbc.Button("➖/➕", id="btn-collapse-fontes", color="link", size="sm", className="text-decoration-none ms-2", n_clicks=1)
                ], className="d-flex align-items-center")
            ),
            dbc.Collapse(
                dbc.CardBody([
                    html.H6("Referências Bibliográficas", className="mb-3"),
                    html.P("GIACOMONI, J. Orçamento Público. São Paulo: Atlas, 2007", className="card-text"),
                    html.P(
                        html.A("BRASIL, MANUAL TÉCNICO DE ORÇAMENTO (MTO). Ministério do Planejamento e Orçamento.",
                               href="https://www1.siop.planejamento.gov.br/mto/lib/exe/fetch.php/mto2026:mto2026.pdf",
                               target="_blank"),
                        className="card-text"
                    ),
                    html.P(
                        html.A("SÃO PAULO. Manual de Elaboração da Proposta Orçamentária. Prefeitura de São Paulo.",
                               href="https://orcamento.sf.prefeitura.sp.gov.br/orcamento/uploads/2026/SUPOMManualdaProposta2026.pdf",
                               target="_blank"),
                        className="card-text"
                    ),

                    html.Br(),

                    html.H6("Documentos complementares", className="mb-3 mt-4"),
                    html.P(
                        html.A("Lei nº 4.320/1964", href="https://www.planalto.gov.br/ccivil_03/leis/l4320.htm", target="_blank"),
                        className="card-text"
                    ),
                    html.P(
                        html.A("Plano Plurianual (PPA) de São Paulo",
                               href="https://orcamento.sf.prefeitura.sp.gov.br/orcamento/ppa.php",
                               target="_blank"),
                        className="card-text"
                    ),

                ]),
                id="collapse-fontes", is_open=True
            )
        ], className="shadow-sm mb-5"),


        html.Footer([
            html.P("Painel Orçamentário SMDHC - Desenvolvido em Python/Dash | "
            "(11) 2833-4832 - nsfaita@prefeitura.sp.gov.br", className="text-center text-muted mt-4")
        ])
        
    ], fluid=True, style={"backgroundColor": "#f8f9fa", "padding": "20px"})

def registrar_callbacks_sobre(app):
    @app.callback(
        Output("collapse-sobre", "is_open"),
        Input("btn-collapse-sobre", "n_clicks"),
        State("collapse-sobre", "is_open"),
    )
    def toggle_sobre(n, is_open):
        if n:
            return not is_open
        return is_open
    
    @app.callback(
        Output("collapse-orcamento", "is_open"),
        Input("btn-collapse-orcamento", "n_clicks"),
        State("collapse-orcamento", "is_open"),
    )
    def toggle_orcamento(n, is_open):
        if n:
            return not is_open
        return is_open

    @app.callback(
        Output("collapse-codigos", "is_open"),
        Input("btn-collapse-dotacao", "n_clicks"),
        State("collapse-codigos", "is_open"),
    )
    def toggle_dotacao(n, is_open):
        if n:
            return not is_open
        return is_open
    
    @app.callback(
        Output("collapse-codigos-siglas", "is_open"),
        Input("btn-collapse-codigos", "n_clicks"),
        State("collapse-codigos-siglas", "is_open"),
    )
    def toggle_codigos_siglas(n, is_open):
        if n:
            return not is_open
        return is_open

    @app.callback(
        Output("collapse-glossario", "is_open"),
        Input("btn-collapse-glossario", "n_clicks"),
        State("collapse-glossario", "is_open"),
    )
    def toggle_glossario(n, is_open):
        if n:
            return not is_open
        return is_open
    
    @app.callback(
        Output("collapse-fontes", "is_open"),
        Input("btn-collapse-fontes", "n_clicks"),
        State("collapse-fontes", "is_open"),
    )
    def toggle_fontes(n, is_open):
        if n:
            return not is_open
        return is_open
    
