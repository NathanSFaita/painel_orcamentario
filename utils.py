import os
import pandas as pd
import numpy as np
import dash_bootstrap_components as dbc
from dash import html
from datetime import datetime
import pytz

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ======================================================
# CONFIGURAÇÃO DE EXIBIÇÃO (MAPA EXATO DAS SUAS COLUNAS)
# ======================================================
# Esquerda: Nome exato na sua base | Direita: Nome para exibir na tela
# Dicionário para colunas de índice (categorias)
DE_PARA_INDICES_EXECUCAO = {
    "dotacao_completa": "Dotação Completa",
    "orgao": "Órgão",
    "coordenação": "Coordenação",
    "politicas_para": "Descrição",
    "acao_programatica": "Atividade",
    "projeto_atividade": "Ação",
    "nome_elemento": "Elemento de Despesa",
    "fonte_descricao": "Fonte (Descrição)",
    "ds_fonte": "Vinculação"
    
}

# Dicionário para colunas de valores
DE_PARA_EXECUCAO = {
    "valOrcadoInicial": "Orçado Inicial",
    "valOrcadoAtualizado": "Orçado Atualizado",
    "valCongelado": "Congelado",
    "valDisponivel": "Disponível",
    "valReservadoLiquido": "Reservado",
    "valEmpenhadoLiquido": "Empenhado",
    "valLiquidado": "Liquidado",
    "valPagoExercicio": "Pago",
    "Saldo de Dotação": "Saldo de Dotação",  # Campo calculado manualmente no dash
    "Saldo de Reserva": "Saldo de Reserva"  # Campo calculado manualmente no dash
}

DE_PARA_INDICES_EMPENHOS = {
    "orgao": "Órgão",
    "codEmpenho": "Nº Empenho",
    "datEmpenho": "Data do Empenho",
    "codProcesso": "Processo SEI",
    "coordenacao": "Coordenação",
    "politicas_para": "Descrição",
    "acao_programatica": "Atividade",
    "codVinculacaoRecurso": "Vinculação (Código)",
    "codDespesa": "Despesa",
    "nome_elemento": "Elemento de Despesa",
    "txDescricaoFonteRecurso": "Vinculação",
    "txDescricaoItemDespesa": "Item de Despesa",
    "fonte_descricao": "Fonte (Descrição)",
    "situacao_empenho": "Situação do Empenho",
    "txtRazaoSocial": "Credor",
    "anexo_descricaoAnexo": "Objeto do Empenho"
}

DE_PARA_EMPENHOS = {
    "valEmpenhadoLiquido": "Empenhado",
    "valLiquidado": "Liquidado",
    "valPagoExercicio": "Pago"
}

DE_PARA_PRESSAO = {
    "Pressão": "Pressão Orçamentária",
    "valDisponivel": "Disponível",
    "Total necessário": "Total Necessário",
    "Valor Empenhado (SOF)": "Empenhado",
    "Valor Pago (SOF)": "Pago",
    "Falta Pagar": "Falta Pagar"
}

DE_PARA_INDICES_PRESSAO = DE_PARA_INDICES_EMPENHOS.copy()
DE_PARA_INDICES_PRESSAO['Dotação Formatada'] = 'Dotação Completa'
DE_PARA_INDICES_PRESSAO['Tem Pressão?'] = 'Tem Pressão?'

DE_PARA_PLANEJAMENTO = {
    "Total necessário": "Total Contratado",
    "Pressao do Contrato": "Pressão Orçamentária",
    "Valor Empenhado (SOF)": "Empenhado (SOF)",
    "Valor Liquidado (SOF)": "Liquidado (SOF)",
    "Valor Pago (SOF)": "Pago (SOF)",
    "Saldo de Dotação": "Saldo de Dotação"
}

DE_PARA_INDICES_PLANEJAMENTO = {
    "Dotação Formatada": "Dotação",
    "codProcesso": "Processo SEI",
    "Objeto do Contrato": "Objeto",
    "Credor": "Credor",
    "orgao": "Órgão",
    "coordenacao": "Coordenação",
    "acao_programatica": "Atividade",
    "nome_elemento": "Elemento de Despesa",
    "Origem": "Origem do Dado",
    "Fases": "Fase do Contrato",
    "Status Empenho": "Status de Empenho",
    "Data de Reajuste": "Data de Vencimento",
    "Status Cobertura": "Situação Orçamentária",
    "Descrição Genérica da Despesa": "Produto",
    "Número do Termo": "Número do Termo"
}


# ======================================================
# TRATAMENTO DE DADOS
# ======================================================
def tratar_dotacao_rigoroso(dot):
    """Garante que a dotação esteja no formato xx.xx.xx.xxx.xxxx.xxxx.xxxxxxxx.xx.x.xxx.xxxx"""
    if pd.isna(dot):
        return None
    dot_str = str(dot).strip()
    if not dot_str or dot_str.lower() == 'nan':
        return None

    # A abordagem mais robusta é limpar tudo que não for dígito e reconstruir.
    just_digits = "".join(filter(str.isdigit, dot_str))

    # Se não houver dígitos (ex: apenas pontos "......."), considera inválido/nulo.
    if not just_digits:
        return None

    # Trata o caso específico de um 36º dígito indesejado vindo da base de contratos.
    if len(just_digits) == 36:
        just_digits = just_digits[:-1]

    # Se tivermos exatamente 35 dígitos, podemos formatar perfeitamente.
    if len(just_digits) == 35:
        return (f"{just_digits[0:2]}.{just_digits[2:4]}.{just_digits[4:6]}."
                f"{just_digits[6:9]}.{just_digits[9:13]}.{just_digits[13:17]}."
                f"{just_digits[17:25]}.{just_digits[25:27]}.{just_digits[27:28]}."
                f"{just_digits[28:31]}.{just_digits[31:35]}")

    # Se não tiver 35 dígitos, tenta a lógica de 11 partes
    parts = dot_str.split('.')
    if len(parts) == 11:
        try:
            lengths = [2, 2, 2, 3, 4, 4, 8, 2, 1, 3, 4]
            padded_parts = []
            for i, part in enumerate(parts):
                cleaned_part = "".join(filter(str.isdigit, part))
                padded_parts.append(cleaned_part.zfill(lengths[i]))
            
            reconstructed_digits = "".join(padded_parts)
            if len(reconstructed_digits) == 35:
                return ".".join(padded_parts)
        except Exception:
            pass # Se a lógica de 11 partes falhar, continua para o fallback

    # Se nenhuma das lógicas acima funcionou, retorna a string original para inspeção.
    return dot_str

def parse_datas_mistas(series):
    """
    Converte uma Series para datetime lidando com formatos mistos (PT-BR e ISO)
    sem gerar warnings de inferência.
    """
    # Garante string e limpa nulos
    s_clean = series.astype(str).replace(['nan', 'NaT', 'None', ''], np.nan)
    
    # Tentativa 1: Formato Brasileiro DD/MM/AAAA com timestamp
    dates = pd.to_datetime(s_clean, format='%d/%m/%Y %H:%M:%S', errors='coerce')
    
    mask_fail = dates.isna() & s_clean.notna()
    if mask_fail.any():
        dates_no_time = pd.to_datetime(s_clean[mask_fail], format='%d/%m/%Y', errors='coerce')
        dates = dates.fillna(dates_no_time)
    
    # Tentativa 2: Fallback para o que falhou (ISO, DatetimeObjects ou outros formatos)
    mask_fail = dates.isna() & s_clean.notna()
    if mask_fail.any():
        # Usamos dayfirst=True para silenciar o warning e garantir a interpretação correta (DD/MM)
        dates_fallback = pd.to_datetime(s_clean[mask_fail], dayfirst=True, errors='coerce')
        dates = dates.fillna(dates_fallback)
        
    return dates

def _corrigir_dotacoes_com_base_execucao(df_contratos, df_execucao):
    """
    Corrige as dotações da base de contratos utilizando as dotações válidas da base de execução.
    Lógica: Usa Órgão+Unidade+Projeto (índices 0:4 e 13:17) para encontrar a Função+Subfunção+Programa (índices 4:13) corretos.
    """
    if df_contratos.empty or df_execucao.empty:
        return df_contratos
    if "Dotação Formatada" not in df_contratos.columns or "dotacao_completa" not in df_execucao.columns:
        return df_contratos

    # 1. Constrói dicionário de correção a partir da base de execução
    # Chave: Orgao(2) + Unidade(2) + Projeto(4) -> Indices digitos: 0-4 e 13-17
    # Valor: Função(2) + Subfunção(3) + Programa(4) -> Indices digitos: 4-13
    correcao_map = {}
    unique_dots = df_execucao['dotacao_completa'].dropna().unique()
    
    for dot in unique_dots:
        dot_clean = "".join(filter(str.isdigit, str(dot)))
        if len(dot_clean) >= 17:
            chave = dot_clean[0:4] + dot_clean[13:17]
            valor = dot_clean[4:13]
            correcao_map[chave] = valor

    # 2. Aplica a correção nos contratos
    def corrigir(row):
        dot = str(row)
        dot_clean = "".join(filter(str.isdigit, dot))
        if len(dot_clean) >= 17:
             chave = dot_clean[0:4] + dot_clean[13:17]
             if chave in correcao_map:
                 novo_miolo = correcao_map[chave]
                 # Reconstrói a dotação mantendo o início e o fim originais, mas substituindo o miolo (Func/Sub/Prog)
                 # OrgUnit(0:4) + NovoMiolo(4:13) + Resto(13:)
                 nova_dot_clean = dot_clean[0:4] + novo_miolo + dot_clean[13:]
                 return nova_dot_clean
        return dot

    df_contratos["Dotação Formatada"] = df_contratos["Dotação Formatada"].apply(corrigir)
    return df_contratos

def _corrigir_dotacoes_pelo_processo_projeto(df_contratos, df_empenhos):
    """
    Corrige dotações em contratos que possuem processo correspondente nos empenhos, mas dotação diferente.
    A correção é feita buscando um empenho com o mesmo Processo E mesmo Projeto/Atividade (extraído da dotação).
    """
    if df_contratos.empty or df_empenhos.empty:
        return df_contratos
    if "Dotação Formatada" not in df_contratos.columns or "dotacao_completa" not in df_empenhos.columns:
        return df_contratos

    # Helper para extrair Projeto (índice 5: Org.Unid.Func.SubF.Prog.PROJ.Elem.Fonte)
    def get_proj(dot):
        try:
            parts = str(dot).split('.')
            if len(parts) >= 6:
                return parts[5]
        except:
            return None
        return None

    # 1. Cria mapa de Empenhos: (Processo, Projeto) -> Dotação
    # Filtra apenas linhas válidas
    mask_valid = df_empenhos['codProcesso'].notna() & df_empenhos['dotacao_completa'].notna()
    df_emp_valid = df_empenhos[mask_valid].copy()
    df_emp_valid['proj_temp'] = df_emp_valid['dotacao_completa'].apply(get_proj)
    
    # Dicionário de busca: Chave=(Processo, Projeto) -> Valor=Dotação Completa do Empenho
    lookup_map = dict(zip(zip(df_emp_valid['codProcesso'], df_emp_valid['proj_temp']), df_emp_valid['dotacao_completa']))
    
    def corrigir(row):
        proc = row.get('codProcesso')
        dot_atual = row.get('Dotação Formatada')
        proj_atual = get_proj(dot_atual)
        # Se encontrar correspondência de Processo + Projeto no mapa, substitui pela dotação do empenho
        return lookup_map.get((proc, proj_atual), dot_atual)

    df_contratos['Dotação Formatada'] = df_contratos.apply(corrigir, axis=1)
    return df_contratos

def normalizar_colunas_contratos(df):
    """
    Padroniza os nomes das colunas da planilha de contratos para o padrão esperado pelo sistema.
    Baseado na lista enviada (contratos_2026).
    """
    mapa_colunas = {
        "Total_necessário": "Total necessário",
        "Processo": "codProcesso",
        "Objeto da Despesa": "Objeto do Contrato",
        "Credor": "Credor",
        "Credor/Contratado": "Credor", # Mantém compatibilidade com versões anteriores
        "Fases": "Fases",
        "Data de Reajuste": "Data de Reajuste",
        "Descrição Genérica": "Descrição Genérica da Despesa",
        "Descrição Genérica da Despesa": "Descrição Genérica da Despesa",
        "Nº do Termo": "Número do Termo",
        "Número do Termo": "Número do Termo"
    }
    return df.rename(columns=mapa_colunas)

def tratar_selecao_todos(valores_novos, valores_antigos):
    """
    Lógica para o comportamento do filtro 'Todos':
    1. Se a lista estiver vazia -> Retorna ["Todos"]
    2. Se selecionou "Todos" (e não estava antes) -> Limpa os outros e deixa só ["Todos"]
    3. Se "Todos" estava selecionado e selecionou outro -> Remove "Todos"
    """
    if valores_antigos is None: valores_antigos = ["Todos"]
    if not valores_novos: return ["Todos"]
    
    if "Todos" in valores_novos:
        if "Todos" not in valores_antigos: # Usuário acabou de clicar em Todos
            return ["Todos"]
        if len(valores_novos) > 1: # Usuário tinha Todos e clicou em outro
            return [x for x in valores_novos if x != "Todos"]
            
    return valores_novos

def formata_moeda(valor):
    try:
        return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except:
        return "R$ 0,00"

# ======================================================
# GERAÇÃO DE COMPONENTES VISUAIS
# ======================================================

descrição_cards = {
    "Orçado Inicial": "Valor aprovado na Lei Orçamentária Anual (LOA).",
    "Orçado Atualizado": "Orçamento inicial ajustado por créditos adicionais, suplementações e reduções.",
    "Disponível": "Saldo livre para empenhos (Disponível = Orçado Atualizado - Reservado - Congelado).",
    "Congelado": "Parcela do orçamento bloqueada pela Secretaria da Fazenda (SF).",
    "Reservado": "Valor reservado para futura contratação.",
    "Empenhado": "Valor comprometido com credores para entrega de bens ou serviços.",
    "Liquidado": "O bem foi entregue ou o serviço foi prestado, e o credor poderá receber o pagamento.",
    "Pago": "Pagamento foi efetivamente realizado ao credor.",
    "Saldo de Dotação": "Diferença entre o valor Disponível e o Reservado.",
    "Saldo Dotação (Direto)": "Cálculo global: Orçado Atualizado - Total Contratado. Mostra o saldo final se todos os contratos fossem pagos, sem considerar a ordem de prioridade.",
    "Saldo de Reserva": "Valor que ainda precisa ser empenhado (Saldo de Reserva = Reservado - Empenhado).",
    "Órgão": "Unidade orçamentária responsável pela despesa.",
    "Coordenação": "Coordenação gestora pela despesa.",
    "Atividade": "Atividade continuada de cada coordenação",
    "Ação": "Código numérico da atividade.",
    "Despesa (Código)": "Código numérico da despesa (ex: 339000 - Serviços de Terceiros - Pessoa Jurídica).",
    "Elemento de Despesa": "Classificação do objeto do gasto orçamentário (ex: material de consumo, serviços de terceiros, etc).",
    "Vinculação (Código)": "Código numérico da vinculação.",
    "Vinculação": "Indica se a despesa possui ou não alguma vinculação específica (Orçamento Cidadão, Emendas etc.).",
    "Fonte (Descrição)": "Descrição detalhada da fonte de recurso, incluindo código e nome.",
    "Item de Despesa": "Detalhamento do material ou serviço adquirido.",
    "Situação do Empenho": "Status do empenho baseado na relação entre valor total, anulado e líquido.",
    "Credor": "Nome do fornecedor ou prestador de serviço do empenho.",
    "Data do Empenho": "Data em que o empenho foi emitido.",
    "Nº Empenho": "Número identificador do empenho.",
    "Processo SEI": "Número do processo no Sistema Eletrônico de Informações (SEI) relacionado ao empenho.",
    "Pressão Orçamentária": "Diferença entre o Valor Disponível e o Total Contratado. Valores negativos indicam que o saldo disponível em dotação é insuficiente para cobrir o total dos contratos planejados.",
    "Objeto do Empenho": "Descrição do objeto ou serviço contratado no empenho.",
    "Origem do Dado": "Indica se a linha de dados se originou da planilha de Contratos, da base de Empenhos (sem um contrato correspondente), ou de ambos.",
    "Status de Empenho": "Categoriza o contrato com base na relação entre o valor contratado e o valor empenhado: Totalmente Empenhado (igual), Parcialmente Empenhado (menor), Não Empenhado (zero) ou Empenho Maior que Total (empenho supera o contrato)."
}

def monta_cards_resumo(dados_totais, mapa_colunas):
    cards = []

    # Função auxiliar para criar card personalizado
    def criar_card(titulo, valor, cor_fundo="#FFFFFF", cor_texto="#212529", descricao=None):
        elementos_titulo = [
            html.Span(titulo, style={"verticalAlign": "middle"})
        ]

        if descricao:
            # Gera ID único para o tooltip baseado no título
            id_tooltip = f"tooltip-{titulo.replace(' ', '').replace('/', '').lower()}"
            elementos_titulo.append(html.Span(" ℹ️", id=id_tooltip, 
                                              style={"cursor": "help", "fontSize": "0.8em", "marginLeft": "5px", "verticalAlign": "middle", "opacity": "0.7"}))
            elementos_titulo.append(dbc.Tooltip(descricao, target=id_tooltip, placement="top"))

        return dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H6(elementos_titulo, className="card-subtitle mb-2", style={"color": cor_texto, "opacity": "0.9"}),
                    html.H4(formata_moeda(valor), className="card-title", style={"color": cor_texto, "fontWeight": "bold", "fontSize": "22px"})
                ])
            ], className="h-100 shadow-sm", style={"backgroundColor": cor_fundo, "border": "none"})
        ], xs=12, sm=6, md=4, lg=2, className="mb-3")

    # Função auxiliar para criar quebra de linha
    def criar_quebra():
        return html.Div(className="w-100")

    # Verifica contexto Execução (baseado nas chaves do mapa)
    if "valOrcadoInicial" in mapa_colunas:
        # --- EXECUÇÃO: Definição Manual dos Cards ---
        cards.append(criar_card("Orçado Inicial", dados_totais.get("valOrcadoInicial", 0), 
                                cor_fundo="#6c757d", cor_texto="#FFFFFF", descricao=descrição_cards["Orçado Inicial"]))
        cards.append(criar_card("Orçado Atualizado", dados_totais.get("valOrcadoAtualizado", 0), 
                                cor_fundo="#28a745", cor_texto="#FFFFFF", descricao=descrição_cards["Orçado Atualizado"]))
        cards.append(criar_card("Congelado", dados_totais.get("valCongelado", 0), 
                                cor_fundo="#17a2b8", cor_texto="#FFFFFF", descricao=descrição_cards["Congelado"]))
        cards.append(criar_card("Disponível", dados_totais.get("valDisponivel", 0), 
                                cor_fundo="#007bff", cor_texto="#FFFFFF", descricao=descrição_cards["Disponível"]))
        
        cards.append(criar_quebra())

        cards.append(criar_card("Reservado", dados_totais.get("valReservadoLiquido", 0), 
                                cor_fundo="#d4c11b", cor_texto="#FFFFFF", descricao=descrição_cards["Reservado"]))
        cards.append(criar_card("Saldo de Reserva", dados_totais.get("Saldo de Reserva", 0), 
                                cor_fundo="#af865a", cor_texto="#FFFFFF", descricao=descrição_cards["Saldo de Reserva"]))
        cards.append(criar_card("Empenhado", dados_totais.get("valEmpenhadoLiquido", 0), 
                                cor_fundo="#ff7f0e", cor_texto="#FFFFFF", descricao=descrição_cards["Empenhado"]))
        cards.append(criar_card("Liquidado", dados_totais.get("valLiquidado", 0), 
                                cor_fundo="#b22222", cor_texto="#FFFFFF", descricao=descrição_cards["Liquidado"]))
        cards.append(criar_card("Pago", dados_totais.get("valPagoExercicio", 0), 
                                cor_fundo="#871987", cor_texto="#FFFFFF", descricao=descrição_cards["Pago"]))        
        
        cards.append(criar_card("Saldo de Dotação", dados_totais.get("Saldo de Dotação", 0), 
                                cor_fundo="#03bb85", cor_texto="#FFFFFF", descricao=descrição_cards["Saldo de Dotação"]))
        
    # Verifica contexto Empenhos
    elif "valEmpenhadoLiquido" in mapa_colunas:
        cards.append(criar_card("Empenhado", dados_totais.get("valEmpenhadoLiquido", 0), 
                                cor_fundo="#fd7e14", cor_texto="#FFFFFF", descricao=descrição_cards["Empenhado"]))
        cards.append(criar_card("Liquidado", dados_totais.get("valLiquidado", 0), 
                                cor_fundo="#b82e2e", cor_texto="#FFFFFF", descricao=descrição_cards["Liquidado"]))
        cards.append(criar_card("Pago", dados_totais.get("valPagoExercicio", 0), 
                                cor_fundo="#871987", cor_texto="#FFFFFF", descricao=descrição_cards["Pago"]))

    # Verifica contexto Pressão
    elif "Pressão" in mapa_colunas:
        # Ordem explícita para os cards de pressão
        ordem_cards_pressao = [
            ("Pressão", "Pressão Orçamentária"),
            ("valDisponivel", "Disponível"),
            ("Total necessário", "Total Necessário"),
            ("Valor Empenhado (SOF)", "Empenhado"),
            ("Valor Pago (SOF)","Pago"),
            ("Falta Pagar", "Falta Pagar")
        ]
        for col, nome in ordem_cards_pressao:
            if col in mapa_colunas: # Garante que só adiciona cards que estão no mapa
                if col == "Pressão":
                    # Card especial para a Pressão
                    cards.append(criar_card(nome, dados_totais.get(col, 0), 
                                       cor_fundo="#dc3545", cor_texto="#FFFFFF", descricao=descrição_cards.get(nome)))
                else:
                    # Cards normais
                    cards.append(criar_card(nome, dados_totais.get(col, 0), cor_fundo="#f8f9fa", cor_texto="#212529", descricao=descrição_cards.get(nome)))

    # Verifica contexto Planejamento
    elif "Valor Empenhado (SOF)" in mapa_colunas:
        ordem_cards_planejamento = [ # Ordem explícita para os cards de planejamento
            ("valDisponivel", "Disponível"),
            ("Total necessário", "Total Contratado"),
            ("Pressao do Contrato", "Pressão Orçamentária"),
            ("Saldo de Dotação (Direto)", "Saldo Dotação (Direto)"),
            ("Valor Empenhado (SOF)", "Empenhado (SOF)"),
            ("Valor Liquidado (SOF)", "Liquidado (SOF)"),
            ("Valor Pago (SOF)", "Pago (SOF)")
        ]
        for col, nome in ordem_cards_planejamento:
            if col in mapa_colunas:
                cor_fundo = "#6f42c1" if col == "Pressao do Contrato" else "#f8f9fa"
                if col == "Saldo de Dotação (Direto)": cor_fundo = "#03bb85" # Verde para Saldo
                cor_texto = "#FFFFFF" if col == "Pressao do Contrato" else "#212529"
                if col == "Saldo de Dotação (Direto)": cor_texto = "#FFFFFF"
                
                cards.append(criar_card(nome, dados_totais.get(col, 0), cor_fundo=cor_fundo, cor_texto=cor_texto, descricao=descrição_cards.get(nome)))
    else:
        # Fallback para outros casos
        for col, nome in mapa_colunas.items():
            cards.append(criar_card(nome, dados_totais.get(col, 0), cor_fundo="#f8f9fa", cor_texto="#212529", descricao=f"Total acumulado de {nome}"))
            
    return dbc.Row(cards, justify="center")

def gera_card_atualizacao(data_extracao_df):
    """Gera um card informativo com as datas de atualização."""
    data_exibicao = data_extracao_df if data_extracao_df and data_extracao_df != "-" else "Dados não encontrados"

    return dbc.Card(
        dbc.CardBody([
            dbc.Row([
                dbc.Col(
                    html.Div([
                        html.H6("Data de Atualização", 
                                className="card-subtitle text-muted", 
                                style={"fontSize": "0.9rem"}),
                        html.H5(data_exibicao, 
                                className="card-title", 
                                style={"fontSize": "1.1rem"}),
                        html.H6("Fonte: API-SOF", className="card-subtitle text-muted mt-2")
                    ]),
                    width="auto"
                ),
                dbc.Col(
                    html.Div([
                        html.H5("Desenvolvido pela Coordenadoria de Planejamento e Informação (CPI)", 
                                className="card-title text-end"),
                        html.H6("Dúvidas: (11) 2833-4832 | nsfaita@prefeitura.sp.gov.br", 
                                className="text-muted text-end")
                    ]),
                    width="auto",
                    className="text-end" # Alinha à direita
                )
            ], justify="between", align="center")
        ]),
        className="mb-4",
        color="light",
    )

def gera_tabela_pivot(df, tipo):
    if df.empty: return pd.DataFrame()
    
    # Normaliza nomes de colunas (remove espaços nas pontas)
    df.columns = [c.strip() for c in df.columns]

    if tipo == "pressao":
        # A base de contratos já vem pré-agregada pela função de carga.
        # Apenas retorna o dataframe para exibição.
        return df
    elif tipo == "execucao":
        # Colunas de Agrupamento (Linhas da Tabela)
        cols_index = list(DE_PARA_INDICES_EXECUCAO.keys())
        # Colunas de Valor
        cols_values = [k for k in DE_PARA_EXECUCAO.keys() if "Saldo" not in k]
    else:  # tipo == "empenhos"
        cols_index = list(DE_PARA_INDICES_EMPENHOS.keys())
        cols_values = list(DE_PARA_EMPENHOS.keys())

    # O código abaixo agora só executa para 'execucao' e 'empenhos'
    # Filtra colunas que realmente existem para evitar erro
    index_validos = [c for c in cols_index if c in df.columns]
    values_validos = [c for c in cols_values if c in df.columns]
    
    if not index_validos:
        return pd.DataFrame()

    pivot = df.pivot_table(index=index_validos, values=values_validos, aggfunc="sum", fill_value=0).reset_index()
    return pivot

def cabecalho_padrao(titulo, subtitulo):
    return dbc.Row([
        dbc.Col([
            html.Img(src="/assets/smdhc_logo.png", height="100px"),
            html.H2(titulo, className="text-center mb-2 mt-4", style={"color": "#1f77b4", "fontWeight": "bold"}),
            html.H4(subtitulo, className="text-center mb-4", style={"color": "#6c757d"}),
            html.Hr(className="my-4", style={"borderColor": "#111111"})
        ], className="text-center")
    ])

# ======================================================
# CARREGAMENTO DE ARQUIVOS
# ======================================================
def ler_info_versao():
    """Lê a data de última execução do arquivo version.txt."""
    try:
        version_path = os.path.join(BASE_DIR, "version.txt")
        with open(version_path, "r", encoding="utf-8") as f:
            content = f.read().strip() # ex: ultima_execucao=2026-02-03 13:42:18 UTC
            date_str_utc_full = content.split("=")[1]
            
            # Remove o " UTC" para um parse mais seguro e consistente
            date_str_utc = date_str_utc_full.replace(" UTC", "")
            
            # Converte a string para um objeto datetime "naive" (sem timezone)
            dt_naive = datetime.strptime(date_str_utc, "%Y-%m-%d %H:%M:%S")
            
            # Torna o objeto datetime ciente do seu timezone (UTC)
            dt_utc = pytz.utc.localize(dt_naive)
            
            # Converte para o timezone de Brasília
            tz_brasilia = pytz.timezone('America/Sao_Paulo')
            dt_brasilia = dt_utc.astimezone(tz_brasilia)
            
            # Formata para o padrão brasileiro
            return dt_brasilia.strftime("%d/%m/%Y %H:%M:%S")
    except Exception:
        return "Não disponível"

def lista_meses(base, ano):
    if not ano: return []
    try:
        # A função lista_meses é usada apenas para a base de execução
        pasta = os.path.join(BASE_DIR, "base_despesas", str(ano)) if base == "execucao" else os.path.join(BASE_DIR, "base_empenhos")
        if not os.path.exists(pasta): return []
        arquivos = [f for f in os.listdir(pasta) if f.endswith(".xlsx") and not f.startswith("~$")]
        return sorted([f.replace(f"despesas_{ano}", "").replace(".xlsx", "") for f in arquivos])
    except: return []

def carrega_base(base, ano, mes):
    try:
        if base == "execucao":
            caminho = os.path.join(BASE_DIR, "base_despesas", str(ano), f"despesas_{ano}{mes}.xlsx")
            # Colunas de filtro que podem ser lidas como números, mas devem ser tratadas como texto
            dtype_map = {
                'cd_orgao': str,
                'projeto_atividade': str,
                'despesa': str,
                'vinculacao': str,
                'dotacao_completa': str
            }
            if os.path.exists(caminho):
                df = pd.read_excel(caminho, dtype=dtype_map)
            else: df = pd.DataFrame()
        else:
            caminho = os.path.join(BASE_DIR, "base_empenhos", f"empenhos_{ano}.csv")
            # Colunas de filtro que podem ser lidas como números, mas devem ser tratadas como texto
            dtype_map = {
                'codOrgao': str,
                'codUnidade': str,
                'codProjetoAtividade': str,
                'codDespesa': str,
                'codVinculacaoRecurso': str,
                'codEmpenho': str,
                'codProcesso': str,
                'numContrato': str,
                'anoContrato': str,
                'dotacao_completa': str
            }
            if os.path.exists(caminho):
                df = pd.read_csv(caminho, sep=';', dtype=dtype_map, low_memory=False)
            else: df = pd.DataFrame()

        if not df.empty:
            # Ajuste de terminologia: Desaparecidas -> Desaparecidos
            for col in ["coordenação", "coordenacao", "acao_programatica"]:
                if col in df.columns:
                    df[col] = df[col].str.replace("Desaparecidas", "Desaparecidos", regex=False)
        
        return df
    except Exception as e:
        print(f"Erro ao carregar base '{base}': {e}")
        return pd.DataFrame()

def carrega_base_contratos(ano):
    """
    Carrega e trata a base de contratos (Pressão), e junta com a execução orçamentária.
    """
    try:
        # --- PREPARAÇÃO: Carregar Execução para Correção ---
        meses_despesa = lista_meses("execucao", ano)
        df_despesas = pd.DataFrame()
        if meses_despesa:
            mes_recente = meses_despesa[-1]
            df_despesas = carrega_base("execucao", ano, mes_recente)

        # --- PARTE 1: Carregar e processar CONTRATOS ---
        caminho_contratos = os.path.join(BASE_DIR, "base_contratos", f"contratos_{ano}.xlsx")
        if not os.path.exists(caminho_contratos):
            return pd.DataFrame()
        
        df_contratos = pd.read_excel(caminho_contratos)
        # Garante que os nomes das colunas sejam strings e sem espaços nas pontas
        df_contratos.columns = [str(c).strip() for c in df_contratos.columns]
        
        # --- NORMALIZAÇÃO DE COLUNAS ---
        df_contratos = normalizar_colunas_contratos(df_contratos)

        # --- CORREÇÃO DE DOTAÇÕES ---
        if not df_despesas.empty:
            df_contratos = _corrigir_dotacoes_com_base_execucao(df_contratos, df_despesas)

        if "Dotação Formatada" in df_contratos.columns:
            df_contratos["Dotação Formatada"] = df_contratos["Dotação Formatada"].astype(str)
            df_contratos["Dotação Formatada"] = df_contratos["Dotação Formatada"].apply(tratar_dotacao_rigoroso)

        # Agrega os valores dos contratos por Dotação para garantir uma chave primária única
        cols_valores_contrato = ['Total necessário', 'Valor Reservado', 'Valor Empenhado', 'Valor Pago']
        for col in cols_valores_contrato:
            df_contratos[col] = pd.to_numeric(df_contratos[col], errors='coerce').fillna(0)
        contratos_agg = df_contratos.groupby('Dotação Formatada', as_index=False)[cols_valores_contrato].sum()

        # --- PARTE 2: Carregar e processar DESPESAS ---
        df_despesas_agg = pd.DataFrame(columns=['dotacao_completa', 'valOrcadoAtualizado']) # Cria um DF vazio como fallback
        
        # Reutiliza df_despesas carregado no início
        if not df_despesas.empty and 'dotacao_completa' in df_despesas.columns and 'valOrcadoAtualizado' in df_despesas.columns:
            # Agrega o orçamento por dotação para garantir uma chave primária única
            df_despesas_agg = df_despesas.groupby('dotacao_completa', as_index=False)[['valOrcadoAtualizado']].sum()

        # --- PARTE 3: Juntar as bases agregadas ---
        df_final = pd.merge(
            contratos_agg,
            df_despesas_agg,
            left_on="Dotação Formatada",
            right_on="dotacao_completa",
            how="outer" # Garante que dotações de ambas as bases sejam incluídas
        )

        # --- PARTE 4: Limpeza e enriquecimento dos dados ---
        # Unifica a coluna de dotação e preenche valores nulos com 0
        df_final['Dotação Formatada'] = df_final['Dotação Formatada'].fillna(df_final['dotacao_completa'])
        df_final.drop(columns=['dotacao_completa'], inplace=True, errors='ignore')

        cols_valores_final = cols_valores_contrato + ['valOrcadoAtualizado']
        for col in cols_valores_final:
            if col in df_final.columns:
                df_final[col] = df_final[col].fillna(0)

        # Carrega tabelas auxiliares para preencher dados descritivos
        path_aux = os.path.join(BASE_DIR, "dados_auxiliares")
        df_orgao = pd.read_excel(os.path.join(path_aux, "procv_orgao.xlsx"))
        df_acoes = pd.read_excel(os.path.join(path_aux, "procv_acoes.xlsx"))
        df_elem = pd.read_excel(os.path.join(path_aux, "procv_elemento.xlsx"))

        # Extrai os códigos da string da dotação para fazer o 'procv'
        dotacao_split = df_final['Dotação Formatada'].str.split('.', expand=True)
        if not dotacao_split.empty:
            if dotacao_split.shape[1] >= 7:
                df_final['cod_orgao_temp'] = pd.to_numeric(dotacao_split[0], errors='coerce')
                df_final['codProjetoAtividade'] = dotacao_split[5].astype(str).str.zfill(4)
                df_final['codElemento'] = pd.to_numeric(dotacao_split[6], errors='coerce')

        # Junta com as tabelas auxiliares para obter as descrições
        df_final = df_final.merge(df_orgao[['cod_orgao', 'orgao']], left_on='cod_orgao_temp', right_on='cod_orgao', how='left')
        df_acoes.rename(columns={"coordenadoria": "coordenacao"}, inplace=True, errors='ignore')
        # Força conversão robusta para string com 4 dígitos no arquivo de ações
        df_acoes['acao'] = pd.to_numeric(df_acoes['acao'], errors='coerce').fillna(0).astype(int).astype(str).str.zfill(4)
        df_final = df_final.merge(df_acoes[['acao', 'coordenacao', 'politicas_para', 'acao_programatica']], left_on='codProjetoAtividade', right_on='acao', how='left')
        df_elem.rename(columns={"elemento_despesa": "nome_elemento"}, inplace=True, errors='ignore')
        df_final = df_final.merge(df_elem[['num_elemento', 'nome_elemento']], left_on='codElemento', right_on='num_elemento', how='left')

        # Limpa colunas temporárias usadas para a junção
        df_final.drop(columns=[c for c in df_final.columns if '_temp' in c or c in ['cod_orgao', 'acao', 'num_elemento']], inplace=True, errors='ignore')

        # --- PARTE 5: Cálculos finais ---
        df_final["Falta Reservar"] = df_final["Total necessário"] - df_final["Valor Reservado"]
        df_final["Falta Pagar"] = df_final["Valor Empenhado"] - df_final["Valor Pago"]
        df_final["Pressão"] = df_final["valOrcadoAtualizado"] - df_final["Total necessário"]
        
        return df_final
        
    except Exception as e:
        print(f"Erro ao carregar e juntar contratos com despesas: {e}")
        return pd.DataFrame()

def carrega_base_planejamento(ano):
    """
    Constrói a base de dados para o painel de Planejamento de Pagamentos. A lógica segue os seguintes passos:
    1. Carrega a planilha de contratos, preservando cada linha original.
    2. Carrega a base de empenhos e a agrega (soma) por 'Processo SEI' e 'Dotação', garantindo um valor de empenho único por chave.
    3. Realiza uma junção externa ('outer merge') entre contratos e empenhos agregados. Isso assegura que:
        - Contratos com empenhos correspondentes são combinados.
        - Empenhos que não possuem um contrato na planilha (não planejados) são adicionados como novas linhas.
        - Contratos sem empenhos ainda são listados.
    4. O resultado é uma base completa que reflete o total empenhado do ano, garantindo consistência com o painel de Empenhos.
    """
    try:
        # --- PREPARAÇÃO: Carregar Execução para Correção ---
        meses_despesa = lista_meses("execucao", ano)
        df_despesas = pd.DataFrame()
        if meses_despesa:
            mes_recente = meses_despesa[-1]
            df_despesas = carrega_base("execucao", ano, mes_recente)

        # --- PARTE 1: Carregar e processar CONTRATOS ---
        caminho_contratos = os.path.join(BASE_DIR, "base_contratos", f"contratos_{ano}.xlsx")
        if not os.path.exists(caminho_contratos):
            df_contratos = pd.DataFrame()
        else:
            df_contratos = pd.read_excel(caminho_contratos)
            # Garante que os nomes das colunas sejam strings e sem espaços nas pontas
            df_contratos.columns = [str(c).strip() for c in df_contratos.columns]
            
            # --- NORMALIZAÇÃO DE COLUNAS ---
            df_contratos = normalizar_colunas_contratos(df_contratos)
            
            # --- LIMPEZA PRÉVIA DE LINHAS VAZIAS/LIXO ---
            # Remove linhas onde colunas essenciais estão todas vazias ou nulas
            # Usa os nomes já padronizados
            cols_essenciais = [c for c in ['codProcesso', 'Objeto do Contrato', 'Credor', 'Total necessário'] if c in df_contratos.columns]
            if cols_essenciais:
                df_contratos = df_contratos.dropna(subset=cols_essenciais, how='all')
            
            # CORREÇÃO DO ERRO DE TIPO: Garante que 'Total necessário' seja numérico desde o início
            if 'Total necessário' in df_contratos.columns:
                df_contratos['Total necessário'] = pd.to_numeric(df_contratos['Total necessário'], errors='coerce').fillna(0)

            # Adiciona um ID único para cada linha de contrato para permitir a de-duplicação após o merge
            df_contratos['_contract_row_id'] = range(len(df_contratos))

            # --- CORREÇÃO DE DOTAÇÕES (ANTIGA REMOVIDA) ---
            # A correção agora é feita mais abaixo, usando a base de empenhos
            # para garantir o match exato de Processo + Projeto.

            # Formata a data de início para DD/MM/AAAA
            if "Data de Reajuste" in df_contratos.columns:
                # Usa parser robusto para evitar warnings de formato misto
                df_contratos["Data de Reajuste"] = parse_datas_mistas(df_contratos["Data de Reajuste"])
                df_contratos["Data de Reajuste"] = df_contratos["Data de Reajuste"].dt.strftime('%d/%m/%Y')

            if "Dotação Formatada" in df_contratos.columns:
                df_contratos["Dotação Formatada"] = df_contratos["Dotação Formatada"].astype(str)
                df_contratos["Dotação Formatada"] = df_contratos["Dotação Formatada"].apply(tratar_dotacao_rigoroso)

            # Garante que as novas colunas existam no dataframe de contratos para evitar erros posteriores
            for col in ["Descrição Genérica da Despesa", "Número do Termo"]:
                if col not in df_contratos.columns:
                    df_contratos[col] = None

            # Limpeza e formatação rigorosa da coluna 'codProcesso'
            if 'codProcesso' in df_contratos.columns:
                # Converte para string, remove caracteres não numéricos e preenche com zeros à esquerda
                codproc = (
                    df_contratos["codProcesso"]
                    .astype("string")
                    .fillna("")
                    .str.replace(r"\D", "", regex=True)
                    .str.zfill(16)
                )
                
                # Se o processo for inválido (apenas zeros ou vazio), define como None para NÃO cruzar indevidamente
                mascara_invalida = (codproc == '0000000000000000') | (codproc == '')
                df_contratos.loc[mascara_invalida, "codProcesso"] = None
                
                # Aplica a formatação "xxxx.xxxx/xxxxxxx-x" apenas para strings com 16 dígitos
                mascara_valida = (codproc.str.len() == 16) & (~mascara_invalida)
                df_contratos.loc[mascara_valida, "codProcesso"] = (
                    codproc[mascara_valida].str.slice(0, 4) + "." +
                    codproc[mascara_valida].str.slice(4, 8) + "/" +
                    codproc[mascara_valida].str.slice(8, 15) + "-" +
                    codproc[mascara_valida].str.slice(15)
                )

        # --- PARTE 2: Carregar e processar EMPENHOS ---
        df_empenhos = carrega_base("empenhos", ano, None)
        if df_empenhos.empty:
            df_empenhos_agg = pd.DataFrame(columns=['codProcesso', 'dotacao_completa', 'valEmpenhadoLiquido', 'Credor_emp', 'Objeto_emp', 'Data_emp'])
        else:
            # Garante que as colunas necessárias existam para evitar erros no groupby
            cols_necessarias_emp = ['codProcesso', 'dotacao_completa', 'valEmpenhadoLiquido', 'txtRazaoSocial', 'anexo_descricaoAnexo', 'datEmpenho']
            for col in cols_necessarias_emp:
                if col not in df_empenhos.columns:
                    df_empenhos[col] = 0 if 'val' in col else None
            
            # Garante que dotacao_completa seja string antes de tratar
            df_empenhos['dotacao_completa'] = df_empenhos['dotacao_completa'].astype(str)

            # Garante que os valores monetários sejam numéricos antes de agrupar (evita erro de soma/concatenação)
            for col in ['valEmpenhadoLiquido', 'valLiquidado', 'valPagoExercicio']:
                df_empenhos[col] = pd.to_numeric(df_empenhos[col], errors='coerce').fillna(0)
                
            # Padroniza a dotação dos empenhos para o mesmo formato rigoroso dos contratos
            df_empenhos['dotacao_completa'] = df_empenhos['dotacao_completa'].apply(tratar_dotacao_rigoroso)
            
            # Preenche valores nulos nas chaves de agrupamento para evitar que o groupby descarte linhas.
            df_empenhos['codProcesso'] = df_empenhos['codProcesso'].fillna('Sem Processo')
            df_empenhos['dotacao_completa'] = df_empenhos['dotacao_completa'].fillna('Sem Dotação')
            
            # Agrega os empenhos por Processo e Dotação, somando os valores.
            # Isso garante que cada contrato seja comparado com a soma total de seus empenhos.
            df_empenhos_agg = df_empenhos.groupby(['codProcesso', 'dotacao_completa'], as_index=False).agg(
                valEmpenhadoLiquido=('valEmpenhadoLiquido', 'sum'),
                valLiquidado=('valLiquidado', 'sum'),
                valPagoExercicio=('valPagoExercicio', 'sum'),
                Credor_emp=('txtRazaoSocial', 'first'),
                Objeto_emp=('anexo_descricaoAnexo', 'first'),
                Data_emp=('datEmpenho', 'first')
            )
            
            # Após agrupar, transformamos as chaves genéricas 'Sem Processo/Dotação' de volta para NaN.
            # Isso impede que elas se liguem aos contratos que também não têm processo/dotação, evitando a multiplicação cartesiana.
            df_empenhos_agg['codProcesso'] = df_empenhos_agg['codProcesso'].replace('Sem Processo', np.nan)
            df_empenhos_agg['dotacao_completa'] = df_empenhos_agg['dotacao_completa'].replace('Sem Dotação', np.nan)

        # --- PARTE 2.1: Carregar Orçamento (Execução) para cálculo de Pressão ---
        # Necessário para obter o 'Orçado Atualizado' por dotação
        df_despesas_agg = pd.DataFrame(columns=['dotacao_completa', 'valOrcadoAtualizado', 'valDisponivel'])
        # Reutiliza df_despesas carregado no início
        if not df_despesas.empty and 'dotacao_completa' in df_despesas.columns and 'valOrcadoAtualizado' in df_despesas.columns:
                # Garante formatação rigorosa na chave de execução para match perfeito com contratos
                df_despesas['dotacao_completa'] = df_despesas['dotacao_completa'].astype(str).apply(tratar_dotacao_rigoroso)
                
                # O valor 'Orçado Atualizado' é por dotação, não deve ser somado. Usamos 'first' para pegar o valor único de cada dotação.
                # Adicionado dropna=False para incluir dotações que não puderam ser formatadas (ficam como NaN) e não perdê-las.
                df_despesas_agg = df_despesas.groupby('dotacao_completa', as_index=False, dropna=False).agg(
                    valOrcadoAtualizado=('valOrcadoAtualizado', 'first'),
                    valDisponivel=('valDisponivel', 'first')
                )
                # Renomeia a coluna para evitar conflito no merge, que causa a criação de sufixos _x e _y
                # Padroniza o nome para 'Dotação Formatada' para permitir a concatenação correta
                df_despesas_agg = df_despesas_agg.rename(columns={'dotacao_completa': 'Dotação Formatada'})
                df_despesas_agg['Origem'] = 'Orçamento'

        # --- PARTE 3: Juntar as bases ---
        if 'codProcesso' not in df_contratos.columns: df_contratos['codProcesso'] = None
        if 'Dotação Formatada' not in df_contratos.columns: df_contratos['Dotação Formatada'] = None
        
        # A junção 'outer' é essencial para incluir empenhos que não estavam na planilha de contratos.
        # O 'indicator=True' cria uma coluna que nos permite identificar a origem de cada linha.
        df_final = pd.merge(df_contratos, df_empenhos_agg, left_on=["codProcesso", "Dotação Formatada"], right_on=["codProcesso", "dotacao_completa"], how="outer", indicator=True)
        
        # Mapeia a origem do dado baseado no resultado do merge
        df_final['Origem'] = df_final['_merge'].map({
            'left_only': 'Apenas Contrato',
            'right_only': 'Empenho s/ Contrato',
            'both': 'Contrato + Empenho'
        })
        # Converte a coluna 'Origem' para string para permitir a adição de novas categorias.
        # O merge com indicator=True cria uma coluna categórica, que causa erro ao adicionar novos valores.
        df_final['Origem'] = df_final['Origem'].astype(str)
        
        # CONCATENAÇÃO COM ORÇAMENTO (Ao invés de merge)
        # Adiciona as linhas de orçamento como registros independentes
        df_final = pd.concat([df_final, df_despesas_agg], ignore_index=True)

        # Isola as linhas de Orçamento (que não têm processo) atribuindo um valor fictício.
        # Isso impede que elas se agrupem com empenhos órfãos (que têm processo nulo) durante a distribuição de valores.
        df_final.loc[df_final['Origem'] == 'Orçamento', 'codProcesso'] = 'ORCAMENTO'

        
        # --- REFINAMENTO DA ORIGEM (Apenas Contrato) ---
        # Lista de processos que existem nos empenhos para verificação cruzada
        processos_empenhos = set(df_empenhos['codProcesso'].dropna().unique()) if not df_empenhos.empty else set()
        
        mask_apenas_contrato = df_final['Origem'] == 'Apenas Contrato'
        mask_com_processo = df_final['codProcesso'].isin(processos_empenhos)
        mask_processo_zerado = df_final['codProcesso'].isin(['0000.0000/0000000-0', '0000000000000000', '0', 0, 'Sem Processo', None, np.nan])

        # Aplica as novas categorias
        df_final.loc[mask_apenas_contrato & mask_com_processo & ~mask_processo_zerado, 'Origem'] = 'Apenas Contrato - com processo'
        df_final.loc[mask_apenas_contrato & (~mask_com_processo | mask_processo_zerado), 'Origem'] = 'Apenas Contrato - sem processo'

        # --- CORREÇÃO DE DOTAÇÃO (MATCH PROCESSO + PROJETO) ---
        # Estratégia: Para linhas 'Apenas Contrato - com processo' (processo existe no empenho mas dotação não bateu),
        # buscamos no empenho a dotação correta usando Processo + Projeto/Atividade.
        
        mask_target = df_final['Origem'] == 'Apenas Contrato - com processo'
        if mask_target.any() and not df_empenhos.empty:
            # Helper para extrair projeto da string da dotação (índice 5)
            def get_proj_safe(dot):
                try: return str(dot).split('.')[5]
                except: return None
            
            # Helper para extrair órgão da string da dotação (índice 0)
            def get_orgao_safe(dot):
                try: return str(dot).split('.')[0]
                except: return None
            
            # Monta lookup: (Processo, Órgão, Projeto) -> Dotação Correta
            df_emp_lookup = df_empenhos[['codProcesso', 'dotacao_completa']].dropna().copy()
            df_emp_lookup['projeto'] = df_emp_lookup['dotacao_completa'].apply(get_proj_safe)
            df_emp_lookup['orgao'] = df_emp_lookup['dotacao_completa'].apply(get_orgao_safe)
            
            # Cria dicionário removendo duplicatas (chave agora inclui órgão)
            lookup_dict = df_emp_lookup.drop_duplicates(subset=['codProcesso', 'orgao', 'projeto']).set_index(['codProcesso', 'orgao', 'projeto'])['dotacao_completa'].to_dict()
            
            # Função de correção aplicada linha a linha
            def corrigir_dotacao_linha(row):
                proc = row['codProcesso']
                dot_atual = row['Dotação Formatada']
                proj = get_proj_safe(dot_atual)
                orgao = get_orgao_safe(dot_atual)
                # Retorna a dotação do empenho se houver match (Processo + Órgão + Projeto), senão mantém a original
                return lookup_dict.get((proc, orgao, proj), dot_atual)
            
            # Calcula as novas dotações
            novas_dotacoes = df_final[mask_target].apply(corrigir_dotacao_linha, axis=1)
            
            # Identifica quais linhas realmente mudaram (encontrou match de projeto/atividade)
            mask_mudou = novas_dotacoes != df_final.loc[mask_target, 'Dotação Formatada']
            idx_mudou = mask_mudou[mask_mudou].index

            # Aplica a correção (sobrescreve todas, mas as que não mudaram mantêm o valor)
            df_final.loc[mask_target, 'Dotação Formatada'] = novas_dotacoes

            # --- ATUALIZAÇÃO DA ORIGEM DO CONTRATO ---
            # Garante que a classificação reflita que a dotação foi corrigida via match de processo
            # APENAS para as linhas que de fato mudaram
            if not idx_mudou.empty:
                df_final.loc[idx_mudou, 'Origem'] = 'Contrato - Dotação Corrigida'
            
            # Nota: Ao corrigir a dotação, agora existe uma linha de 'Empenho s/ Contrato' (órfã) que na verdade corresponde a este contrato.
            # Para evitar dupla contagem no painel (somar contrato + empenho órfão), alteramos a Origem dessas linhas de empenho.
            # Identificamos os pares (Processo, Dotação) que agora existem nos contratos corrigidos.
            # Usamos apenas os índices que mudaram para buscar os órfãos correspondentes
            keys_corrected = df_final.loc[idx_mudou, ['codProcesso', 'Dotação Formatada']].drop_duplicates()
            
            # Identifica linhas órfãs que coincidem com os contratos corrigidos
            mask_orphans = df_final['Origem'] == 'Empenho s/ Contrato'
            
            # Usa MultiIndex para fazer o 'isin' de forma vetorizada e rápida
            idx_corrected = pd.MultiIndex.from_frame(keys_corrected)
            idx_orphans = pd.MultiIndex.from_frame(df_final.loc[mask_orphans, ['codProcesso', 'Dotação Formatada']])
            
            # Encontra quais órfãos agora têm par e atualiza sua origem para não serem somados como "novos"
            matches = idx_orphans.isin(idx_corrected)
            idx_to_update = df_final[mask_orphans].index[matches]
            
            if len(idx_to_update) > 0:
                df_final.loc[idx_to_update, 'Origem'] = 'Empenho - Dado Corrigido'

        # Para linhas que vêm apenas de empenhos, a fase do contrato é assumida como "Firmado".
        if 'Fases' not in df_final.columns:
            df_final['Fases'] = None
        df_final.loc[df_final['_merge'] == 'right_only', 'Fases'] = 'Firmado'

        df_final = df_final.drop(columns=['_merge'])

        # [CORREÇÃO] Preenche Dotação Formatada (vindo dos empenhos para os órfãos) ANTES da distribuição.
        # Isso é crucial para que os empenhos órfãos se agrupem corretamente com os contratos corrigidos.
        df_final['Dotação Formatada'] = df_final['Dotação Formatada'].fillna(df_final.get('dotacao_completa'))

        # --- DISTRIBUIÇÃO PROPORCIONAL DOS VALORES DE EMPENHO (RESOLUÇÃO DE DUPLA CONTAGEM) ---
        # Quando múltiplos contratos compartilham o mesmo empenho (Processo + Dotação), o merge duplica o valor do empenho.
        # Aqui distribuímos o valor do empenho proporcionalmente ao 'Total necessário' de cada contrato.
        
        # 1. Calcula totais do grupo para rateio
        cols_rateio = ['codProcesso', 'Dotação Formatada']
        
        # Garante novamente que é numérico no df_final (pós-concatenação) antes de somar, prevenindo o erro 'float' + 'str'
        if 'Total necessário' in df_final.columns:
             df_final['Total necessário'] = pd.to_numeric(df_final['Total necessário'], errors='coerce').fillna(0)
        
        # Adicionado dropna=False para não excluir empenhos órfãos (que têm Processo=NaN) do cálculo
        df_final['total_nec_grupo'] = df_final.groupby(cols_rateio, dropna=False)['Total necessário'].transform('sum')
        df_final['count_grupo'] = df_final.groupby(cols_rateio, dropna=False)['Total necessário'].transform('count')
        
        # 2. Define fator de distribuição: Proporcional ao valor ou Divisão igualitária se valor for zero
        df_final['fator_dist'] = np.where(df_final['total_nec_grupo'] > 0,
                                          df_final['Total necessário'] / df_final['total_nec_grupo'],
                                          1 / df_final['count_grupo'])
        
        # 3. Aplica o fator nas colunas financeiras da execução (SOF)
        cols_sof_raw = ['valEmpenhadoLiquido', 'valLiquidado', 'valPagoExercicio']
        for col in cols_sof_raw:
            if col in df_final.columns:
                # Garante numérico
                df_final[col] = pd.to_numeric(df_final[col], errors='coerce').fillna(0)
                
                # Recalcula a "Contabilidade de Empenhos":
                # Usa 'max' para pegar o valor cheio do empenho do grupo (ignorando os 0s dos contratos que entraram no grupo após correção).
                # Assim, o valor do "empenho órfão" é capturado e redistribuído para o contrato corrigido.
                # Adicionado dropna=False para garantir que órfãos (com processo NaN) sejam processados corretamente.
                total_sof_grupo = df_final.groupby(cols_rateio, dropna=False)[col].transform('max')
                
                # Aplica o rateio sobre o total real do grupo
                df_final[col] = total_sof_grupo * df_final['fator_dist'].fillna(1)
        
        # Limpa auxiliares
        df_final.drop(columns=['total_nec_grupo', 'count_grupo', 'fator_dist'], inplace=True)

        # --- PARTE 4: Pós-processamento e Enriquecimento ---
        # Para linhas de "Empenho s/ Contrato", preenche informações faltantes (Credor, Objeto)
        # com os dados que vieram da base de empenhos.
        if 'Credor' not in df_final.columns:
            df_final['Credor'] = None
        if 'Objeto do Contrato' not in df_final.columns:
            df_final['Objeto do Contrato'] = None
        if 'Data de Reajuste' not in df_final.columns:
            df_final['Data de Reajuste'] = None

        df_final['Credor'] = df_final['Credor'].fillna(df_final.get('Credor_emp'))
        df_final['Objeto do Contrato'] = df_final['Objeto do Contrato'].fillna(df_final.get('Objeto_emp'))
        
        if 'Data_emp' in df_final.columns:
             # Usa parser robusto
             dates_emp = parse_datas_mistas(df_final['Data_emp'])
             data_emp_fmt = dates_emp.dt.strftime('%d/%m/%Y')
             df_final['Data de Reajuste'] = df_final['Data de Reajuste'].fillna(data_emp_fmt)

        df_final = df_final.drop(columns=['dotacao_completa', 'dotacao_completa_x', 'dotacao_completa_y', 'dotacao_despesa', 'Credor_emp', 'Objeto_emp', 'Data_emp'], errors='ignore')

        cols_sof = ['valEmpenhadoLiquido', 'valLiquidado', 'valPagoExercicio']
        cols_valores = ['Total necessário', 'Valor Reservado', 'Valor Empenhado', 'Valor Pago'] + cols_sof
        for col in cols_valores:
            if col in df_final.columns:
                df_final[col] = pd.to_numeric(df_final[col], errors='coerce').fillna(0)
        
        # Enriquecimento com dados descritivos a partir da dotação (para todas as linhas)
        path_aux = os.path.join(BASE_DIR, "dados_auxiliares")
        df_orgao = pd.read_excel(os.path.join(path_aux, "procv_orgao.xlsx"))
        df_acoes = pd.read_excel(os.path.join(path_aux, "procv_acoes.xlsx"))
        df_elem = pd.read_excel(os.path.join(path_aux, "procv_elemento.xlsx"))
        df_fonte = pd.read_excel(os.path.join(path_aux, "procv_fonte.xlsx"))

        # Garante que as chaves de junção nas tabelas auxiliares sejam únicas para evitar duplicação de linhas no merge
        df_orgao = df_orgao.drop_duplicates(subset=['cod_orgao'])
        df_acoes = df_acoes.drop_duplicates(subset=['acao'])
        df_elem = df_elem.drop_duplicates(subset=['num_elemento'])
        df_fonte = df_fonte.drop_duplicates(subset=['cd_fonte'])

        dotacao_split = df_final['Dotação Formatada'].str.split('.', expand=True)
        if not dotacao_split.empty and dotacao_split.shape[1] >= 11:
            df_final['cod_orgao_temp'] = pd.to_numeric(dotacao_split[0], errors='coerce')
            df_final['codProjetoAtividade'] = dotacao_split[5].astype(str).str.zfill(4)
            df_final['codElemento'] = pd.to_numeric(dotacao_split[6], errors='coerce')
            df_final['codFonte_temp'] = pd.to_numeric(dotacao_split[7], errors='coerce')
            df_final['codDespesa'] = dotacao_split[6] # Mantém como string para display/filtro
            df_final['codVinculacao'] = dotacao_split[10]
            
            # Junta com as tabelas auxiliares para obter as descrições
            df_final = df_final.merge(df_orgao[['cod_orgao', 'orgao']], left_on='cod_orgao_temp', right_on='cod_orgao', how='left')
            df_acoes = df_acoes.rename(columns={"coordenadoria": "coordenacao"}, errors='ignore')
            # Força conversão robusta para string com 4 dígitos no arquivo de ações
            df_acoes['acao'] = pd.to_numeric(df_acoes['acao'], errors='coerce').fillna(0).astype(int).astype(str).str.zfill(4)
            df_final = df_final.merge(df_acoes[['acao', 'coordenacao', 'politicas_para', 'acao_programatica']], left_on='codProjetoAtividade', right_on='acao', how='left')
            df_elem = df_elem.rename(columns={"elemento_despesa": "nome_elemento"}, errors='ignore')
            df_final = df_final.merge(df_elem[['num_elemento', 'nome_elemento']], left_on='codElemento', right_on='num_elemento', how='left')
            
            # Fonte e Descrição
            df_final = df_final.merge(df_fonte[['cd_fonte', 'ds_fonte']], left_on='codFonte_temp', right_on='cd_fonte', how='left')
            df_final['fonte_descricao'] = df_final['codFonte_temp'].fillna(0).astype(int).astype(str).str.zfill(2) + " - " + df_final['ds_fonte'].fillna("Não informado")

        df_final = df_final.drop(columns=[c for c in df_final.columns if '_temp' in c or c in ['cod_orgao', 'acao', 'num_elemento', 'cd_fonte']], errors='ignore')
        
        df_final = df_final.rename(columns={
            'valEmpenhadoLiquido': 'Valor Empenhado (SOF)',
            'valLiquidado': 'Valor Liquidado (SOF)',
            'valPagoExercicio': 'Valor Pago (SOF)'
        })

        # Para linhas de "Empenho s/ Contrato", o valor contratado é o próprio valor empenhado.
        df_final.loc[df_final['Origem'] == 'Empenho s/ Contrato', 'Total necessário'] = df_final['Valor Empenhado (SOF)']
        
        # --- CÁLCULO DO STATUS DO EMPENHO ---
        conditions = [
            df_final['Valor Empenhado (SOF)'] > (df_final['Total necessário'] + 0.01),
            np.isclose(df_final['Valor Empenhado (SOF)'], df_final['Total necessário']),
            df_final['Valor Empenhado (SOF)'] < 0.01
        ]
        choices = [
            'Empenho maior que total',
            'Totalmente empenhado',
            'Não empenhado'
        ]
        df_final['Status Empenho'] = np.select(conditions, choices, default='Parcialmente empenhado')

        # Nova coluna "Pressão do Contrato"
        df_final["Pressao do Contrato"] = df_final["Total necessário"] - df_final["Valor Empenhado (SOF)"]
        
        # --- CÁLCULO DA PRESSÃO ORÇAMENTÁRIA ---
        # 1. Critérios de Prioridade
        # Prioridade 1: Contratos já totalmente empenhados (Pressão do Contrato <= 0)
        df_final['prioridade_pressao_zero'] = np.where(df_final['Pressao do Contrato'] <= 0.01, 0, 1)
        
        # Prioridade 2: Data de Vencimento (Dia/Mês)
        # Extrai MM-DD para ordenação (ignorando ano)
        def extrair_mmdd(data_str):
            try:
                # Espera formato DD/MM/AAAA
                return datetime.strptime(str(data_str), '%d/%m/%Y').strftime('%m%d')
            except:
                return "9999" # Data inválida vai para o final
        
        df_final['_sort_data'] = df_final['Data de Reajuste'].apply(extrair_mmdd)
        
        # Ordena o DataFrame para o cálculo acumulativo
        # Ordem: Dotação -> Prioridade Empenho -> Data (Dia/Mês) -> Valor (Menor primeiro)
        df_final = df_final.sort_values(
            by=['Dotação Formatada', 'prioridade_pressao_zero', '_sort_data', 'Total necessário'],
            ascending=[True, True, True, True]
        )
        
        # 2. Cálculo Acumulado por Dotação
        # Define o valor a ser consumido do orçamento
        df_final['valor_a_consumir'] = np.where(
            df_final['prioridade_pressao_zero'] == 0,
            0,                                  # [MODIFICAÇÃO] Já empenhado não consome Disponível (pois já foi deduzido na origem)
            df_final['Pressao do Contrato']     # [MODIFICAÇÃO] Apenas o que falta empenhar consome o Disponível
        )
        df_final['acumulado_consumido'] = df_final.groupby('Dotação Formatada')['valor_a_consumir'].cumsum()
        
        # PROPAGAÇÃO DO ORÇAMENTO E CÁLCULO DE SALDO
        # Como as linhas de orçamento agora são separadas (Origem='Orçamento'), as linhas de contrato têm valOrcadoAtualizado=NaN/0.
        # Precisamos propagar o valor do orçamento da dotação para todas as linhas dessa dotação para fazer o cálculo correto do saldo.
        # Usamos transform('max') assumindo que a linha de 'Orçamento' contém o valor total e as outras 0/NaN.
        df_final['disponivel_base_calculo'] = df_final.groupby('Dotação Formatada')['valDisponivel'].transform('max')
        df_final['disponivel_base_calculo'] = df_final['disponivel_base_calculo'].fillna(0)
        
        df_final['Saldo de Dotação'] = df_final['disponivel_base_calculo'] - df_final['acumulado_consumido']
        
        # 3. Determinação da Cobertura e Pressão
        # Define Status de Cobertura para exibição
        conditions_cob = [
            df_final['prioridade_pressao_zero'] == 0, # Contratos já empenhados
            df_final['Saldo de Dotação'] >= 0,        # Contratos com saldo positivo
            df_final['Saldo de Dotação'] < 0         # Contratos com saldo negativo
        ]
        choices_cob = [
            'Já empenhado',
            'Com cobertura orçamentária',
            'Sem cobertura orçamentária'
        ]
        df_final['Status Cobertura'] = np.select(conditions_cob, choices_cob, default='Verificar')
        
        # Para as linhas puramente de Orçamento, o Status Cobertura deve ser informativo ou vazio, não 'Já empenhado'
        df_final.loc[df_final['Origem'] == 'Orçamento', 'Status Cobertura'] = 'Disponível'
        
        # Remove colunas auxiliares de ordenação e cálculo
        df_final = df_final.drop(columns=['prioridade_pressao_zero', '_sort_data', 'valor_a_consumir', 'acumulado_consumido', 'disponivel_base_calculo'], errors='ignore')

        # Preenche com 0 o valOrcadoAtualizado nas linhas que não são de orçamento para exibição correta na tabela (sem duplicar soma)
        if 'valOrcadoAtualizado' in df_final.columns:
             df_final.loc[df_final['Origem'] != 'Orçamento', 'valOrcadoAtualizado'] = 0
        if 'valDisponivel' in df_final.columns:
             df_final.loc[df_final['Origem'] != 'Orçamento', 'valDisponivel'] = 0

        # [LÓGICA ADICIONADA] Classifica empenhos órfãos na Descrição Genérica
        if 'Descrição Genérica da Despesa' in df_final.columns:
             mask_orfaos = df_final['Origem'] == 'Empenho s/ Contrato'
             df_final.loc[mask_orfaos, 'Descrição Genérica da Despesa'] = df_final.loc[mask_orfaos, 'Descrição Genérica da Despesa'].fillna('Pontuais: Outros')

        # Garante que todas as colunas de texto não tenham valores nulos, que podem quebrar a DataTable.
        # Isso é crucial por causa do 'outer join' que pode deixar campos em branco.
        cols_texto_para_limpar = ['codProcesso', 'Objeto do Contrato', 'Credor', 'orgao', 'coordenacao', 'acao_programatica', 'nome_elemento', 'politicas_para', 'Fases', 'Status Empenho', 'Data de Reajuste', 'Status Cobertura', 'Descrição Genérica da Despesa', 'Número do Termo']
        for col in cols_texto_para_limpar:
            if col in df_final.columns:
                df_final[col] = df_final[col].fillna('Não informado')

        # Garante que os nomes das colunas sejam strings (previne erro de ID numérico no Dash DataTable)
        df_final.columns = df_final.columns.astype(str)

        # --- REMOÇÃO DE LINHAS SEM INFORMAÇÃO ---
        # Elimina linhas que não possuem processo, credor, objeto E valores (Total necessário e Empenhado SOF zerados)
        # Mantém linhas que tenham Orçado Atualizado > 0 para garantir que o card de resumo bata com a Execução
        mask_sem_info = (
            (df_final['Total necessário'] == 0) &
            (df_final['Valor Empenhado (SOF)'] == 0) &
            (df_final['valOrcadoAtualizado'] == 0) &
            # (df_final['codProcesso'].isin(['Não informado', ''])) &
            # (df_final['Credor'].isin(['Não informado', ''])) &
            (df_final['Objeto do Contrato'].isin(['Não informado', '']))
        )
        df_final = df_final[~mask_sem_info]

        return df_final

    except Exception as e:
        print(f"Erro ao carregar base de planejamento: {e}")
        return pd.DataFrame()
