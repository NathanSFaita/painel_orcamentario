import os
import pandas as pd
import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from fpdf import FPDF
from datetime import datetime
from PIL import Image
import io
import pytz

# Importa funções e variáveis úteis do seu projeto
from utils import (
    carrega_base, lista_meses, DE_PARA_EXECUCAO, formata_moeda, BASE_DIR
)

# --- 1. CONFIGURAÇÕES ---

# Lista de órgãos para gerar o relatório. O script criará uma página para cada um.
ORGAOS_RELATORIO = ["SMDHC", "FUMCAD", "FAASP", "FMID", "FUMCAF"]

# Configurações de E-mail (IMPORTANTE: USAR VARIÁVEIS DE AMBIENTE)
# Para segurança, configure estas variáveis no seu sistema, não diretamente no código.
SMTP_SERVER = os.getenv("SMTP_SERVER")  # Ex: "smtp.gmail.com" para Gmail
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
SMTP_USER = os.getenv("SMTP_USER")      # Seu endereço de e-mail
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD") # Sua senha de aplicativo (não a senha normal)

# Arquivo com a lista de e-mails e pasta de saída para os relatórios
EMAILS_FILE = os.path.join(BASE_DIR, "dados_auxiliares",  "emails_relatorio.xlsx")
PDF_OUTPUT_DIR = os.path.join(BASE_DIR, "relatorios", "relatorios_gerados")


# --- 2. CLASSE PARA GERAR O PDF ---

class PDF(FPDF):
    """ Classe customizada para o PDF com cabeçalho e rodapé. """
    def header(self):
        self.set_font('Arial', 'B', 18)
        titulo = getattr(self, 'titulo_pagina', 'Relatório Resumido de Execução Orçamentária')
        
        # --- Correção para o erro de 'Interlacing' no FPDF ---
        # O FPDF não suporta PNGs com 'interlacing'. Abrimos a imagem com a biblioteca
        # Pillow e a re-salvamos em memória sem essa opção para torná-la compatível.
        image_path = os.path.join(BASE_DIR, 'assets', 'smdhc_logo.png')
        try:
            with Image.open(image_path) as img:
                with io.BytesIO() as buffer:
                    # Salva a imagem em um buffer de bytes em formato PNG, que por padrão não usa 'interlacing'.
                    img.save(buffer, format='PNG')
                    buffer.seek(0)
                    # Usa o buffer com a FPDF, especificando o tipo.
                    self.image(buffer, 10, 8, 33, type='PNG')
        except Exception as e:
            # Captura erros (ex: arquivo não encontrado) e continua sem o logo.
            print(f"Aviso: Não foi possível carregar a imagem do logo. Erro: {e}")

        self.cell(0, 10, titulo, 0, 1, 'C')
        self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        data_geracao = datetime.now(pytz.timezone('America/Sao_Paulo')).strftime("%d/%m/%Y %H:%M:%S")
        self.cell(0, 10, f'Gerado em: {data_geracao}', 0, 0, 'L')
        self.cell(0, 10, f'Página {self.page_no()}', 0, 0, 'C')


def desenhar_cards_no_pdf(pdf, totais):
    """
    Desenha uma representação dos cards de resumo diretamente no PDF.
    """
    # Layout e cores dos cards (RGB)
    cards_layout = [
        # Linha 1
        {'titulo': "Orçado Inicial", 'key': 'valOrcadoInicial', 'color': (108, 117, 125)},
        {'titulo': "Orçado Atualizado", 'key': 'valOrcadoAtualizado', 'color': (40, 167, 69)},
        {'titulo': "Congelado", 'key': 'valCongelado', 'color': (23, 162, 184)},
        {'titulo': "Disponível", 'key': 'valDisponivel', 'color': (0, 123, 255)},
        {'titulo': "Saldo de Dotação", 'key': 'Saldo de Dotação', 'color': (3, 187, 133)},
        # Linha 2
        {'titulo': "Reservado", 'key': 'valReservadoLiquido', 'color': (212, 193, 27)},
        {'titulo': "Saldo de Reserva", 'key': 'Saldo de Reserva', 'color': (175, 134, 90)},
        {'titulo': "Empenhado", 'key': 'valEmpenhadoLiquido', 'color': (255, 127, 14)},
        {'titulo': "Liquidado", 'key': 'valLiquidado', 'color': (178, 34, 34)},
        {'titulo': "Pago", 'key': 'valPagoExercicio', 'color': (135, 25, 135)},
    ]

    card_w, card_h = 51, 25
    spacing = 5
    start_x = 11
    start_y_row1 = pdf.get_y()
    start_y_row2 = start_y_row1 + card_h + 10

    for i, card_info in enumerate(cards_layout):
        is_row1 = i < 5
        col_index = i % 5

        x = start_x + col_index * (card_w + spacing)
        y = start_y_row1 if is_row1 else start_y_row2
        valor = totais.get(card_info['key'], 0)

        # Desenha o card
        pdf.set_fill_color(*card_info['color'])
        pdf.rect(x, y, card_w, card_h, 'F')

        # Escreve o título
        pdf.set_xy(x + 2, y + 4)
        pdf.set_font('Arial', 'B', 10)
        pdf.set_text_color(255, 255, 255)
        pdf.cell(card_w - 4, 6, card_info['titulo'])

        # Escreve o valor
        pdf.set_xy(x + 2, y + 12)
        pdf.set_font('Arial', 'B', 12)
        pdf.cell(card_w - 4, 8, formata_moeda(valor))


def gerar_pdf_resumo(df, ano, mes):
    """
    Gera o PDF com uma página para cada órgão, contendo os cards de resumo.
    """
    print("Iniciando geração do PDF...")
    pdf = PDF('L', 'mm', 'A4') # 'L' para paisagem (landscape)

    for orgao_nome in ORGAOS_RELATORIO:
        pdf.add_page()
        pdf.titulo_pagina = f"Resumo da Execução - {orgao_nome}"

        # Filtra o DataFrame para o órgão atual
        df_filtrado = df[df['orgao'] == orgao_nome].copy()

        if df_filtrado.empty:
            pdf.set_font('Arial', '', 12)
            pdf.cell(0, 10, "Nenhum dado encontrado para este órgão no período.", 0, 1, 'C')
            continue

        # --- Calcula os totais (lógica replicada de dash_execucao.py) ---
        if "valCongelado" in df_filtrado.columns and "valDescongelado" in df_filtrado.columns:
            df_filtrado["valCongelado"] = df_filtrado["valCongelado"].fillna(0) - df_filtrado["valDescongelado"].fillna(0)

        cols_numericas = [c for c in DE_PARA_EXECUCAO.keys() if c in df_filtrado.columns and "Saldo" not in c]
        totais = {c: df_filtrado[c].sum() for c in cols_numericas}

        disponivel = totais.get("valDisponivel", 0)
        reservado = totais.get("valReservadoLiquido", 0)
        empenhado = totais.get("valEmpenhadoLiquido", 0)
        totais["Saldo de Dotação"] = disponivel - reservado
        totais["Saldo de Reserva"] = reservado - empenhado

        # Desenha os cards na página atual do PDF
        desenhar_cards_no_pdf(pdf, totais)

    # Salva o arquivo PDF
    os.makedirs(PDF_OUTPUT_DIR, exist_ok=True)
    pdf_filename = f"relatorio_resumo_{ano}_{mes}.pdf"
    pdf_filepath = os.path.join(PDF_OUTPUT_DIR, pdf_filename)
    pdf.output(pdf_filepath)

    print(f"PDF gerado com sucesso em: {pdf_filepath}")
    return pdf_filepath


# --- 3. FUNÇÃO DE ENVIO DE E-MAIL ---

def enviar_emails(caminho_pdf):
    """
    Lê a planilha de e-mails e envia o relatório em anexo para cada destinatário.
    """
    if not all([SMTP_SERVER, SMTP_PORT, SMTP_USER, SMTP_PASSWORD]):
        print("\nAVISO: As variáveis de ambiente para envio de e-mail não estão configuradas.")
        print("O PDF foi gerado, mas nenhum e-mail será enviado.")
        return

    if not os.path.exists(EMAILS_FILE):
        print(f"\nERRO: Arquivo de e-mails '{EMAILS_FILE}' não encontrado.")
        return

    try:
        df_emails = pd.read_excel(EMAILS_FILE)
        print(f"\nEnviando e-mails para {len(df_emails)} destinatário(s)...")
    except Exception as e:
        print(f"\nERRO: Falha ao ler o arquivo Excel de e-mails: {e}")
        return

    context = ssl.create_default_context()
    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls(context=context)
            server.login(SMTP_USER, SMTP_PASSWORD)

            for _, row in df_emails.iterrows():
                nome = row['nome']
                email_destinatario = row['email']

                msg = MIMEMultipart()
                msg['Subject'] = f"Relatório Orçamentário Semanal - {datetime.now().strftime('%d/%m/%Y')}"
                msg['From'] = SMTP_USER
                msg['To'] = email_destinatario

                corpo_email = f"""
                <p>Olá, {nome},</p>
                <p>Segue em anexo o relatório resumido da execução orçamentária.</p>
                <p>Este é um e-mail automático, por favor, não responda.</p>
                <br>
                <p>Atenciosamente,</p>
                <p>Painel Orçamentário SMDHC</p>
                """
                msg.attach(MIMEText(corpo_email, 'html'))

                # Anexa o PDF
                with open(caminho_pdf, "rb") as attachment:
                    part = MIMEApplication(attachment.read(), Name=os.path.basename(caminho_pdf))
                part['Content-Disposition'] = f'attachment; filename="{os.path.basename(caminho_pdf)}"'
                msg.attach(part)

                # Envia o e-mail
                server.sendmail(SMTP_USER, email_destinatario, msg.as_string())
                print(f" - E-mail enviado para: {email_destinatario}")

    except smtplib.SMTPAuthenticationError:
        print("\nERRO DE AUTENTICAÇÃO: Verifique seu usuário/senha de e-mail.")
        print("Se usar Gmail, certifique-se de ter uma 'Senha de App' configurada.")
    except Exception as e:
        print(f"\nERRO ao enviar e-mails: {e}")


# --- 4. FUNÇÃO PRINCIPAL ---

def main():
    """
    Orquestra a execução do script: carrega dados, gera PDF e envia e-mails.
    """
    print("--- INICIANDO SCRIPT DE RELATÓRIO SEMANAL ---")

    # Encontra o ano e mês mais recentes
    try:
        anos = sorted([d for d in os.listdir(os.path.join(BASE_DIR, "base_despesas")) if os.path.isdir(os.path.join(BASE_DIR, "base_despesas", d))])
        ano_recente = anos[-1]
        meses = lista_meses("execucao", ano_recente)
        mes_recente = meses[-1]
    except IndexError:
        print("ERRO: Não foi possível encontrar dados de despesas para processar.")
        return

    print(f"Processando dados para o período: {mes_recente}/{ano_recente}")

    # Carrega a base de dados
    df = carrega_base("execucao", ano_recente, mes_recente)

    if df.empty:
        print("ERRO: A base de dados carregada está vazia. Abortando.")
        return

    # 1. Gera o relatório em PDF
    caminho_pdf_gerado = gerar_pdf_resumo(df, ano_recente, mes_recente)

    # 2. Envia o PDF por e-mail
    enviar_emails(caminho_pdf_gerado)

    print("\n--- SCRIPT FINALIZADO ---")


if __name__ == "__main__":
    main()