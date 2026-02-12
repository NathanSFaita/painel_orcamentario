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
        self.cell(0, 10, f'Gerado em: {data_geracao}', 0, 0, 'L')
        self.cell(0, 10, f'Página {self.page_no()}', 0, 0, 'C')

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

    y_inicio = pdf.get_y()

    # --- 1. Seção de Filtros (Esquerda) ---
    pdf.set_xy(10, y_inicio)
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(130, 10, '1. Filtros Aplicados', 0, 1, 'L')
    pdf.set_font('Arial', '', 10)
    
    filtros_str = []
    for chave in ["ano", "orgao", "coordenacao", "acao", "projeto", "elemento", "vinculacao", "fonte", "despesa"]:
        valor = store.get(chave)
        if valor:
            if isinstance(valor, list):
                if "Todos" not in valor and valor:
                    filtros_str.append(f"{chave.title()}: {', '.join(map(str, valor))}")
            else:
                filtros_str.append(f"{chave.title()}: {valor}")

    if not filtros_str:
        pdf.set_x(10)
        pdf.multi_cell(130, 5, "Nenhum filtro específico aplicado.", 0, 'L')
    else:
        for f in filtros_str:
            pdf.set_x(10)
            pdf.multi_cell(130, 5, tratar_texto(f), 0, 'L')
    
    y_filtros = pdf.get_y()

    # --- 2. Seção de Resumo (Direita) ---
    pdf.set_xy(150, y_inicio)
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, '2. Resumo Financeiro', 0, 1, 'L')
    pdf.set_font('Arial', '', 10)

    for chave, nome_exibicao in DE_PARA_EMPENHOS.items():
        valor = totais.get(chave, 0)
        texto_valor = formata_moeda(valor)
        pdf.set_x(150)
        pdf.cell(50, 8, tratar_texto(f'{nome_exibicao}:'), 0, 0)
        pdf.cell(0, 8, texto_valor, 0, 1)
    
    y_resumo = pdf.get_y()
    pdf.set_y(max(y_filtros, y_resumo) + 5)

    # --- 3. Seção da Tabela ---
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, '3. Detalhamento dos Empenhos', 0, 1, 'L')
    
    colunas_pdf = {
        "acao_programatica": ("Atividade", 20), "nome_elemento": ("Elemento", 40),
        "codEmpenho": ("Nº Emp", 15), "codProcesso": ("Processo SEI", 25),
        "txtRazaoSocial": ("Credor", 55), "anexo_descricaoAnexo": ("Objeto", 60),
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

def criar_relatorio_execucao_pdf(store, totais, df_tabela):
    """
    Gera o relatório de execução orçamentária em PDF.
    """
    pdf = PDF('L', 'mm', 'A4') # Paisagem
    pdf.titulo_relatorio = 'Relatório de Execução Orçamentária'
    pdf.add_page()

    y_inicio = pdf.get_y()

    # --- 1. Seção de Filtros (Esquerda) ---
    pdf.set_xy(10, y_inicio)
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(130, 10, '1. Filtros Aplicados', 0, 1, 'L')
    pdf.set_font('Arial', '', 10)
    
    filtros_str = []
    # Lista de chaves relevantes para execução
    for chave in ["ano", "mes", "orgao", "coordenacao", "acao", "projeto", "elemento", "vinculacao", "fonte", "despesa"]:
        valor = store.get(chave)
        if valor:
            if isinstance(valor, list):
                if "Todos" not in valor and valor:
                    filtros_str.append(f"{chave.title()}: {', '.join(map(str, valor))}")
            else:
                filtros_str.append(f"{chave.title()}: {valor}")

    if not filtros_str:
        pdf.set_x(10)
        pdf.multi_cell(130, 5, "Nenhum filtro específico aplicado.", 0, 'L')
    else:
        for f in filtros_str:
            pdf.set_x(10)
            pdf.multi_cell(130, 5, tratar_texto(f), 0, 'L')
    
    y_filtros = pdf.get_y()

    # --- 2. Seção de Resumo (Direita) ---
    pdf.set_xy(150, y_inicio)
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, '2. Resumo Financeiro', 0, 1, 'L')
    pdf.set_font('Arial', '', 10)

    # Usa o dicionário de execução para iterar sobre os totais
    for chave, nome_exibicao in DE_PARA_EXECUCAO.items():
        valor = totais.get(chave, 0)
        texto_valor = formata_moeda(valor)
        # Ajusta largura para caber nomes maiores
        pdf.set_x(150)
        pdf.cell(50, 8, tratar_texto(f'{nome_exibicao}:'), 0, 0)
        pdf.cell(0, 8, texto_valor, 0, 1)
    
    y_resumo = pdf.get_y()
    pdf.set_y(max(y_filtros, y_resumo) + 5)

    # --- 3. Seção da Tabela ---
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, '3. Detalhamento da Execução', 0, 1, 'L')
    
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
