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
        self.set_font('Arial', 'B', 15)
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

    # --- 1. Seção de Filtros ---
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, '1. Filtros Aplicados', 0, 1, 'L')
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
        pdf.cell(0, 5, "Nenhum filtro específico aplicado.", 0, 1)
    else:
        for f in filtros_str:
            pdf.multi_cell(0, 5, tratar_texto(f), 0, 'L')
    pdf.ln(5)

    # --- 2. Seção de Resumo (Cards) ---
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, '2. Resumo Financeiro', 0, 1, 'L')
    pdf.set_font('Arial', '', 10)

    for chave, nome_exibicao in DE_PARA_EMPENHOS.items():
        valor = totais.get(chave, 0)
        texto_valor = formata_moeda(valor)
        pdf.cell(40, 8, tratar_texto(f'{nome_exibicao}:'), 0, 0)
        pdf.cell(0, 8, texto_valor, 0, 1)
    pdf.ln(5)

    # --- 3. Seção da Tabela ---
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, '3. Detalhamento dos Empenhos', 0, 1, 'L')
    
    colunas_pdf = {
        "codEmpenho": ("Nº Empenho", 30), "codProcesso": ("Processo SEI", 40),
        "txtRazaoSocial": ("Credor", 60), "anexo_descricaoAnexo": ("Objeto", 70),
        "valEmpenhadoLiquido": ("Empenhado", 25), "valLiquidado": ("Liquidado", 25),
        "valPagoExercicio": ("Pago", 25)
    }
    
    df_pdf = df_tabela[[col for col in colunas_pdf if col in df_tabela.columns]].copy()

    if df_pdf.empty:
        pdf.set_font('Arial', '', 10)
        pdf.cell(0, 10, "Nenhum dado para exibir na tabela.", 0, 1)
    else:
        # Cabeçalho da tabela
        pdf.set_font('Arial', 'B', 9)
        pdf.set_fill_color(224, 235, 255)
        for col_id in df_pdf.columns:
            nome, largura = colunas_pdf[col_id]
            pdf.cell(largura, 7, tratar_texto(nome), 1, 0, 'C', 1)
        pdf.ln()

        # Dados da tabela
        pdf.set_font('Arial', '', 8)
        pdf.set_fill_color(255, 255, 255)
        for _, row in df_pdf.iterrows():
            for col_id in df_pdf.columns:
                _, largura = colunas_pdf[col_id]
                valor_celula = row[col_id]
                
                if col_id in ["valEmpenhadoLiquido", "valLiquidado", "valPagoExercicio"]:
                    texto = formata_moeda(valor_celula)
                    align = 'R'
                else:
                    texto = str(valor_celula) if pd.notna(valor_celula) else ""
                    align = 'L'
                
                if pdf.get_string_width(texto) > largura - 2:
                    texto = texto[:int(largura/pdf.get_string_width('a')) - 3] + '...'

                pdf.cell(largura, 6, tratar_texto(texto), 1, 0, align, 1)
            pdf.ln()

    return pdf.output(dest='S').encode('latin-1')

def criar_relatorio_execucao_pdf(store, totais, df_tabela):
    """
    Gera o relatório de execução orçamentária em PDF.
    """
    pdf = PDF('L', 'mm', 'A4') # Paisagem
    pdf.titulo_relatorio = 'Relatório de Execução Orçamentária'
    pdf.add_page()

    # --- 1. Seção de Filtros ---
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, '1. Filtros Aplicados', 0, 1, 'L')
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
        pdf.cell(0, 5, "Nenhum filtro específico aplicado.", 0, 1)
    else:
        for f in filtros_str:
            pdf.multi_cell(0, 5, tratar_texto(f), 0, 'L')
    pdf.ln(5)

    # --- 2. Seção de Resumo (Cards) ---
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, '2. Resumo Financeiro', 0, 1, 'L')
    pdf.set_font('Arial', '', 10)

    # Usa o dicionário de execução para iterar sobre os totais
    for chave, nome_exibicao in DE_PARA_EXECUCAO.items():
        valor = totais.get(chave, 0)
        texto_valor = formata_moeda(valor)
        # Ajusta largura para caber nomes maiores
        pdf.cell(50, 8, tratar_texto(f'{nome_exibicao}:'), 0, 0)
        pdf.cell(0, 8, texto_valor, 0, 1)
    pdf.ln(5)

    # --- 3. Seção da Tabela ---
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, '3. Detalhamento da Execução', 0, 1, 'L')
    
    # Define colunas específicas para o relatório de execução
    colunas_pdf = {
        "orgao": ("Órgão", 30),
        "coordenação": ("Coordenação", 40),
        "projeto_atividade": ("Ação", 20),
        "nome_elemento": ("Elemento", 50),
        "valOrcadoAtualizado": ("Orçado", 30),
        "valEmpenhadoLiquido": ("Empenhado", 30),
        "valLiquidado": ("Liquidado", 30),
        "valPagoExercicio": ("Pago", 30)
    }
    
    df_pdf = df_tabela[[col for col in colunas_pdf if col in df_tabela.columns]].copy()

    if df_pdf.empty:
        pdf.set_font('Arial', '', 10)
        pdf.cell(0, 10, "Nenhum dado para exibir na tabela.", 0, 1)
    else:
        pdf.set_font('Arial', 'B', 9)
        pdf.set_fill_color(224, 235, 255)
        for col_id in df_pdf.columns:
            nome, largura = colunas_pdf[col_id]
            pdf.cell(largura, 7, tratar_texto(nome), 1, 0, 'C', 1)
        pdf.ln()

        # --- Lógica de Subtotais e Total Geral ---
        pdf.set_font('Arial', '', 8)
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
            font_style = 'B' if negrito else ''
            pdf.set_font('Arial', font_style, 8)
            pdf.set_fill_color(230, 230, 230) if fundo else pdf.set_fill_color(255, 255, 255)
            
            # Célula de título (ocupa a largura de todas as colunas de texto)
            pdf.cell(largura_texto_total, 6, tratar_texto(titulo), 1, 0, 'R', 1)
            
            # Células de valor
            for col_id in df_pdf.columns:
                if col_id in cols_valor:
                    _, largura = colunas_pdf[col_id]
                    val = valores.get(col_id, 0)
                    pdf.cell(largura, 6, formata_moeda(val), 1, 0, 'R', 1)
            pdf.ln()
            
            # Restaura estilo padrão
            pdf.set_font('Arial', '', 8)
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
