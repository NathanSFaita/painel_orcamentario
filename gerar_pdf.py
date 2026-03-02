import io
from datetime import datetime
import pandas as pd
from fpdf import FPDF
from utils import formata_moeda, DE_PARA_EMPENHOS, DE_PARA_EXECUCAO

def tratar_texto(texto):
    """
    Garante que o texto esteja compatível com latin-1 (usado pelo FPDF).
    Acentos e 'ç' são mantidos. Caracteres não suportados (ex: emojis) viram '?'.
    """
    if texto is None: return ""
    return str(texto).encode('latin-1', 'replace').decode('latin-1')

class PDF(FPDF):
    """ Classe customizada para o PDF com cabeçalho e rodapé. """
    def header(self):
        self.set_font('Arial', 'B', 18)
        titulo = getattr(self, 'titulo_relatorio', 'Relatório')
        self.cell(0, 10, tratar_texto(titulo), 0, 1, 'C')
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        data_geracao = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        
        data_base = getattr(self, 'data_extracao', None)
        texto_rodape = f'Gerado em: {data_geracao}'
        if data_base and data_base != "-":
            texto_rodape += f' | Base atualizada em: {data_base}'
            
        self.cell(0, 10, tratar_texto(texto_rodape), 0, 0, 'L')
        self.cell(0, 10, f'Página {self.page_no()}', 0, 0, 'C')

def desenhar_cards_empenho_pdf(pdf, totais):
    """
    Desenha os cards de resumo de empenho no PDF.
    """
    # Layout e cores dos cards (RGB)
    cards_layout = [
        {'titulo': "Empenhado", 'key': 'valEmpenhadoLiquido', 'color': (253, 126, 20)}, # #fd7e14
        {'titulo': "Liquidado", 'key': 'valLiquidado', 'color': (184, 46, 46)}, # #b82e2e
        {'titulo': "Pago", 'key': 'valPagoExercicio', 'color': (135, 25, 135)}, # #871987
    ]

    card_w, card_h = 51, 25
    spacing = 5
    start_x = 10 # Margem esquerda

    y_pos = pdf.get_y()

    for i, card_info in enumerate(cards_layout):
        x = start_x + i * (card_w + spacing)
        valor = totais.get(card_info['key'], 0)

        # Desenha o card
        pdf.set_fill_color(*card_info['color'])
        pdf.rect(x, y_pos, card_w, card_h, 'F')

        # Escreve o título
        pdf.set_xy(x + 2, y_pos + 4)
        pdf.set_font('Arial', 'B', 10)
        pdf.set_text_color(255, 255, 255)
        pdf.cell(card_w - 4, 6, tratar_texto(card_info['titulo']))

        # Escreve o valor
        pdf.set_xy(x + 2, y_pos + 12)
        pdf.set_font('Arial', 'B', 12)
        pdf.cell(card_w - 4, 8, formata_moeda(valor))
    
    # Move o cursor para baixo dos cards
    pdf.set_y(y_pos + card_h + 10)
    pdf.set_text_color(0, 0, 0)

def desenhar_cards_execucao_pdf(pdf, totais):
    """
    Desenha uma representação dos cards de resumo de execução no PDF.
    """
    cards_layout = [
        {'titulo': "Orçado Inicial", 'key': 'valOrcadoInicial', 'color': (108, 117, 125)},
        {'titulo': "Orçado Atualizado", 'key': 'valOrcadoAtualizado', 'color': (40, 167, 69)},
        {'titulo': "Congelado", 'key': 'valCongelado', 'color': (23, 162, 184)},
        {'titulo': "Disponível", 'key': 'valDisponivel', 'color': (0, 123, 255)},
        {'titulo': "Saldo de Dotação", 'key': 'Saldo de Dotação', 'color': (3, 187, 133)},
        {'titulo': "Reservado", 'key': 'valReservadoLiquido', 'color': (212, 193, 27)},
        {'titulo': "Saldo de Reserva", 'key': 'Saldo de Reserva', 'color': (175, 134, 90)},
        {'titulo': "Empenhado", 'key': 'valEmpenhadoLiquido', 'color': (255, 127, 14)},
        {'titulo': "Liquidado", 'key': 'valLiquidado', 'color': (178, 34, 34)},
        {'titulo': "Pago", 'key': 'valPagoExercicio', 'color': (135, 25, 135)},
    ]

    card_w, card_h, spacing = 51, 25, 5
    start_x = 11
    y_pos = pdf.get_y()

    for i, card_info in enumerate(cards_layout):
        col_index, row_index = i % 5, i // 5
        x = start_x + col_index * (card_w + spacing)
        y = y_pos + row_index * (card_h + 10)
        valor = totais.get(card_info['key'], 0)
        pdf.set_fill_color(*card_info['color'])
        pdf.rect(x, y, card_w, card_h, 'F')
        pdf.set_text_color(255, 255, 255)
        pdf.set_font('Arial', 'B', 10)
        pdf.set_xy(x + 2, y + 4)
        pdf.cell(card_w - 4, 6, tratar_texto(card_info['titulo']))
        pdf.set_font('Arial', 'B', 12)
        pdf.set_xy(x + 2, y + 12)
        pdf.cell(card_w - 4, 8, formata_moeda(valor))

    pdf.set_y(y_pos + 2 * (card_h + 10))
    pdf.set_text_color(0, 0, 0)

def criar_relatorio_empenho_pdf(store, totais, df_tabela):
    """
    Gera o relatório de empenhos em PDF.
    
    Args:
        store (dict): Dicionário com os filtros aplicados.
        totais (dict): Dicionário com os valores totais dos cards.
        df_tabela (pd.DataFrame): DataFrame com os dados da tabela.
        
    Returns:
        bytes: O conteúdo do PDF gerado.
    """
    pdf = PDF('L', 'mm', 'A4') # 'L' para paisagem (landscape)
    pdf.titulo_relatorio = 'Relatório de Empenhos'
    pdf.add_page()

    # --- 1. Seção de Resumo (Cards) ---
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, '1. Resumo Financeiro', 0, 1, 'L')
    desenhar_cards_empenho_pdf(pdf, totais)

    # --- 2. Seção da Tabela ---
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, '2. Detalhamento dos Empenhos', 0, 1, 'L')
    
    colunas_pdf = {
        "datEmpenho": ("Data Emp.", 20),
        "acao_programatica": ("Atividade", 20), "nome_elemento": ("Elemento", 30),
        "codEmpenho": ("Nº Emp", 15), "codProcesso": ("Processo SEI", 25),
        "txtRazaoSocial": ("Credor", 50), "anexo_descricaoAnexo": ("Objeto", 55),
        "valEmpenhadoLiquido": ("Empenhado", 20), "valLiquidado": ("Liquidado", 20),
        "valPagoExercicio": ("Pago", 20)
    }
    
    df_pdf = df_tabela[[col for col in colunas_pdf if col in df_tabela.columns]].copy()

    if df_pdf.empty:
        pdf.set_font('Arial', '', 10)
        pdf.cell(0, 10, "Nenhum dado para exibir na tabela.", 0, 1)
    else:
        # Cabeçalho da tabela
        pdf.set_font('Arial', 'B', 8)
        pdf.set_fill_color(224, 235, 255)
        for col_id in df_pdf.columns:
            nome, largura = colunas_pdf[col_id]
            pdf.cell(largura, 7, tratar_texto(nome), 1, 0, 'C', 1)
        pdf.ln()

        # --- Preparação para Subtotais ---
        cols_valor = ["valEmpenhadoLiquido", "valLiquidado", "valPagoExercicio"]
        cols_valor = [c for c in cols_valor if c in df_pdf.columns]
        cols_texto = [c for c in df_pdf.columns if c not in cols_valor]
        largura_texto_total = sum([colunas_pdf[c][1] for c in cols_texto])

        # Ordenação para garantir agrupamento
        sort_cols = []
        if "acao_programatica" in df_pdf.columns: sort_cols.append("acao_programatica")
        if "nome_elemento" in df_pdf.columns: sort_cols.append("nome_elemento")
        if sort_cols:
            df_pdf = df_pdf.sort_values(by=sort_cols)

        subtotal_atividade = {c: 0.0 for c in cols_valor}
        subtotal_elemento = {c: 0.0 for c in cols_valor}
        total_geral = {c: 0.0 for c in cols_valor}
        
        atividade_atual = None
        elemento_atual = None

        def imprimir_linha_total(titulo, valores, negrito=False, fundo=False):
            if pdf.get_y() + 7 > 190:
                pdf.add_page()
                pdf.set_font('Arial', 'B', 6)
                pdf.set_fill_color(224, 235, 255)
                for col_id in df_pdf.columns:
                    nome, largura = colunas_pdf[col_id]
                    pdf.cell(largura, 7, tratar_texto(nome), 1, 0, 'C', 1)
                pdf.ln()
            
            font_style = 'B' if negrito else ''
            pdf.set_font('Arial', font_style, 6)
            pdf.set_fill_color(230, 230, 230) if fundo else pdf.set_fill_color(255, 255, 255)
            
            pdf.cell(largura_texto_total, 6, tratar_texto(titulo), 1, 0, 'C', 1)
            for col_id in df_pdf.columns:
                if col_id in cols_valor:
                    _, largura = colunas_pdf[col_id]
                    val = valores.get(col_id, 0)
                    pdf.cell(largura, 6, formata_moeda(val), 1, 0, 'R', 1)
            pdf.ln()
            pdf.set_font('Arial', '', 6)
            pdf.set_fill_color(255, 255, 255)

        # Dados da tabela
        pdf.set_font('Arial', '', 6)
        pdf.set_fill_color(255, 255, 255)
        for _, row in df_pdf.iterrows():
            # Lógica de Subtotais
            val_atividade = row.get("acao_programatica")
            val_elemento = row.get("nome_elemento")

            if "acao_programatica" in df_pdf.columns and atividade_atual is not None and val_atividade != atividade_atual:
                if "nome_elemento" in df_pdf.columns and elemento_atual is not None:
                    imprimir_linha_total(f"Subtotal {elemento_atual}", subtotal_elemento, negrito=False, fundo=True)
                    subtotal_elemento = {c: 0.0 for c in cols_valor}
                imprimir_linha_total(f"Total {atividade_atual}", subtotal_atividade, negrito=True, fundo=True)
                subtotal_atividade = {c: 0.0 for c in cols_valor}
                atividade_atual = val_atividade
                elemento_atual = val_elemento
            
            elif "nome_elemento" in df_pdf.columns and elemento_atual is not None and val_elemento != elemento_atual:
                imprimir_linha_total(f"Subtotal {elemento_atual}", subtotal_elemento, negrito=False, fundo=True)
                subtotal_elemento = {c: 0.0 for c in cols_valor}
                elemento_atual = val_elemento

            if atividade_atual is None: atividade_atual = val_atividade
            if elemento_atual is None: elemento_atual = val_elemento

            for c in cols_valor:
                val = row.get(c, 0)
                if pd.notna(val):
                    subtotal_elemento[c] += val
                    subtotal_atividade[c] += val
                    total_geral[c] += val

            # 1. Calcular altura da linha (baseado no Objeto e Credor)
            altura_base = 6
            max_linhas = 1
            textos_quebra = {}
            cols_quebra = ["anexo_descricaoAnexo", "txtRazaoSocial"]
            
            for col in cols_quebra:
                if col in df_pdf.columns:
                    texto = tratar_texto(str(row[col]) if pd.notna(row[col]) else "")
                    textos_quebra[col] = texto
                    largura = colunas_pdf[col][1]
                    
                    # Calcula quantas linhas o texto vai ocupar
                    palavras = texto.split()
                    linha_atual = ""
                    linhas_calc = 1
                    for palavra in palavras:
                        if pdf.get_string_width(linha_atual + palavra) < largura - 4: # Margem de segurança
                            linha_atual += palavra + " "
                        else:
                            linhas_calc += 1
                            linha_atual = palavra + " "
                    if linhas_calc > max_linhas:
                        max_linhas = linhas_calc
            
            altura_linha = altura_base * max_linhas

            # Verifica quebra de página
            if pdf.get_y() + altura_linha > 190:
                pdf.add_page()
                # Reimprime cabeçalho
                pdf.set_font('Arial', 'B', 8)
                pdf.set_fill_color(224, 235, 255)
                for col_id in df_pdf.columns:
                    nome, largura = colunas_pdf[col_id]
                    pdf.cell(largura, 7, tratar_texto(nome), 1, 0, 'C', 1)
                pdf.ln()
                pdf.set_font('Arial', '', 6)
                pdf.set_fill_color(255, 255, 255)

            for col_id in df_pdf.columns:
                _, largura = colunas_pdf[col_id]
                valor_celula = row[col_id]
                
                if col_id in cols_quebra:
                    # Coluna com quebra de linha (MultiCell)
                    x_antes = pdf.get_x()
                    y_antes = pdf.get_y()
                    
                    # Desenha borda e fundo da célula completa
                    pdf.rect(x_antes, y_antes, largura, altura_linha, 'DF')
                    
                    texto = textos_quebra.get(col_id, "")
                    pdf.multi_cell(largura, altura_base, texto, 0, 'L', 0)
                    
                    pdf.set_xy(x_antes + largura, y_antes) # Retorna ao topo para a próxima célula
                
                elif col_id in ["valEmpenhadoLiquido", "valLiquidado", "valPagoExercicio"]:
                    texto = formata_moeda(valor_celula)
                    pdf.cell(largura, altura_linha, tratar_texto(texto), 1, 0, 'R', 1)
                
                else:
                    texto = str(valor_celula) if pd.notna(valor_celula) else ""
                    texto_tratado = tratar_texto(texto)
                    # Trunca se necessário
                    if pdf.get_string_width(texto_tratado) > largura - 2:
                        texto_tratado = texto_tratado[:int(largura/pdf.get_string_width('a')) - 3] + '...'
                    pdf.cell(largura, altura_linha, texto_tratado, 1, 0, 'L', 1)
            
            pdf.ln(altura_linha)
        
        # Totais Finais
        if "nome_elemento" in df_pdf.columns and elemento_atual is not None:
            imprimir_linha_total(f"Subtotal {elemento_atual}", subtotal_elemento, negrito=False, fundo=True)
        if "acao_programatica" in df_pdf.columns and atividade_atual is not None:
            imprimir_linha_total(f"Total {atividade_atual}", subtotal_atividade, negrito=True, fundo=True)
        imprimir_linha_total("TOTAL GERAL", total_geral, negrito=True, fundo=True)

    return pdf.output(dest='S').encode('latin-1')

def criar_relatorio_execucao_pdf(store, totais, df_tabela, data_extracao=None):
    """
    Gera o relatório de execução orçamentária em PDF.
    """
    pdf = PDF('L', 'mm', 'A4') # Paisagem
    pdf.titulo_relatorio = 'Relatório de Execução Orçamentária'
    pdf.data_extracao = data_extracao
    pdf.add_page()

    # --- 1. Seção de Resumo (Cards) ---
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, '1. Resumo Financeiro', 0, 1, 'L')
    desenhar_cards_execucao_pdf(pdf, totais)

    # --- 2. Seção da Tabela ---
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, '2. Detalhamento da Execução', 0, 1, 'L')
    
    # Define colunas específicas para o relatório de execução
    colunas_pdf = {
        "orgao": ("Órgão", 13),
        "coordenação": ("Coordenação", 20),
        "acao_programatica": ("Atividade", 20),
        "nome_elemento": ("Elemento", 40),
        "valOrcadoInicial": ("LOA", 20),
        "valOrcadoAtualizado": ("Atualizado", 20),
        "valCongelado": ("Congelado", 20),
        "valDisponivel": ("Disponível", 20),
        "valReservadoLiquido": ("Reservado", 20),
        "valEmpenhadoLiquido": ("Empenhado", 20),
        "valLiquidado": ("Liquidado", 20),
        "valPagoExercicio": ("Pago", 20),
        "Saldo de Dotação": ("Saldo de Dotação", 20)
    }
    
    df_pdf = df_tabela[[col for col in colunas_pdf if col in df_tabela.columns]].copy()

    if df_pdf.empty:
        pdf.set_font('Arial', '', 10)
        pdf.cell(0, 10, "Nenhum dado para exibir na tabela.", 0, 1)
    else:
        pdf.set_font('Arial', 'B', 8)
        pdf.set_fill_color(224, 235, 255)
        for col_id in df_pdf.columns:
            nome, largura = colunas_pdf[col_id]
            pdf.cell(largura, 7, tratar_texto(nome), 1, 0, 'C', 1)
        pdf.ln()

        # --- Lógica de Subtotais e Total Geral ---
        pdf.set_font('Arial', '', 6)
        pdf.set_fill_color(255, 255, 255)
        
        # Identifica colunas de valor e texto
        cols_valor = [c for c in colunas_pdf if "val" in c]
        cols_texto = [c for c in colunas_pdf if "val" not in c]
        # Calcula largura total das colunas de texto para alinhar o título do subtotal
        largura_texto_total = sum([colunas_pdf[c][1] for c in cols_texto if c in df_pdf.columns])
        
        subtotal_orgao = {c: 0.0 for c in cols_valor}
        subtotal_coord = {c: 0.0 for c in cols_valor}
        total_geral = {c: 0.0 for c in cols_valor}
        
        col_orgao = "orgao"
        col_coord = "coordenação"
        
        orgao_atual = None
        coord_atual = None

        def imprimir_linha_total(titulo, valores, negrito=False, fundo=False):
            if pdf.get_y() + 7 > 190:
                pdf.add_page()
                pdf.set_font('Arial', 'B', 8)
                pdf.set_fill_color(224, 235, 255)
                for col_id in df_pdf.columns:
                    nome, largura = colunas_pdf[col_id]
                    pdf.cell(largura, 7, tratar_texto(nome), 1, 0, 'C', 1)
                pdf.ln()

            font_style = 'B' if negrito else ''
            pdf.set_font('Arial', font_style, 6)
            pdf.set_fill_color(230, 230, 230) if fundo else pdf.set_fill_color(255, 255, 255)
            
            # Célula de título (ocupa a largura de todas as colunas de texto)
            pdf.cell(largura_texto_total, 6, tratar_texto(titulo), 1, 0, 'C', 1)
            
            # Células de valor
            for col_id in df_pdf.columns:
                if col_id in cols_valor:
                    _, largura = colunas_pdf[col_id]
                    val = valores.get(col_id, 0)
                    pdf.cell(largura, 6, formata_moeda(val), 1, 0, 'R', 1)
            pdf.ln()
            
            # Restaura estilo padrão
            pdf.set_font('Arial', '', 6)
            pdf.set_fill_color(255, 255, 255)

        for _, row in df_pdf.iterrows():
            val_orgao = row.get(col_orgao)
            val_coord = row.get(col_coord)

            # Verifica mudança de Órgão
            if orgao_atual is not None and val_orgao != orgao_atual:
                # Fecha Coordenação anterior
                if coord_atual is not None:
                     imprimir_linha_total(f"Subtotal {coord_atual}", subtotal_coord, negrito=False, fundo=True)
                     subtotal_coord = {c: 0.0 for c in cols_valor}
                
                # Fecha Órgão anterior
                imprimir_linha_total(f"Total {orgao_atual}", subtotal_orgao, negrito=True, fundo=True)
                subtotal_orgao = {c: 0.0 for c in cols_valor}
                
                orgao_atual = val_orgao
                coord_atual = val_coord
            
            # Verifica mudança de Coordenação (dentro do mesmo órgão)
            elif coord_atual is not None and val_coord != coord_atual:
                imprimir_linha_total(f"Subtotal {coord_atual}", subtotal_coord, negrito=False, fundo=True)
                subtotal_coord = {c: 0.0 for c in cols_valor}
                coord_atual = val_coord
            
            # Inicializa na primeira linha
            if orgao_atual is None:
                orgao_atual = val_orgao
                coord_atual = val_coord

            # Acumula valores
            for c in cols_valor:
                if c in row and pd.notna(row[c]):
                    val = row[c]
                    subtotal_coord[c] += val
                    subtotal_orgao[c] += val
                    total_geral[c] += row[c]

            # Verifica quebra de página antes de imprimir a linha de dados
            if pdf.get_y() + 6 > 190:
                pdf.add_page()
                pdf.set_font('Arial', 'B', 8)
                pdf.set_fill_color(224, 235, 255)
                for col_id in df_pdf.columns:
                    nome, largura = colunas_pdf[col_id]
                    pdf.cell(largura, 7, tratar_texto(nome), 1, 0, 'C', 1)
                pdf.ln()
                pdf.set_font('Arial', '', 6)
                pdf.set_fill_color(255, 255, 255)

            # Imprime linha de dados
            for col_id in df_pdf.columns:
                _, largura = colunas_pdf[col_id]
                valor_celula = row[col_id]
                
                if "val" in col_id: # Colunas de valor
                    texto = formata_moeda(valor_celula)
                    align = 'R'
                else:
                    texto = str(valor_celula) if pd.notna(valor_celula) else ""
                    align = 'L'
                
                # Trunca texto muito longo
                if pdf.get_string_width(texto) > largura - 2:
                    texto = texto[:int(largura/pdf.get_string_width('a')) - 3] + '...'

                pdf.cell(largura, 6, tratar_texto(texto), 1, 0, align, 1)
            pdf.ln()

        # Fecha últimos grupos
        if coord_atual is not None:
             imprimir_linha_total(f"Subtotal {coord_atual}", subtotal_coord, negrito=False, fundo=True)
        if orgao_atual is not None:
             imprimir_linha_total(f"Total {orgao_atual}", subtotal_orgao, negrito=True, fundo=True)
             
        imprimir_linha_total("TOTAL GERAL", total_geral, negrito=True, fundo=True)

    return pdf.output(dest='S').encode('latin-1')
