# ...existing code...
import requests
import pandas as pd
from itertools import product
import time
from datetime import datetime, timedelta
from pathlib import Path
import math

inicio = time.time()
horario_inicio = datetime.now().strftime("%H:%M:%S")
print("Início da execução:", horario_inicio)
# -----------------------------
# CONFIGURAÇÃO
# -----------------------------

dt_inicio = datetime.fromtimestamp(inicio)
ANO = str(dt_inicio.year)
MES = str(dt_inicio.month)

BASE = "https://gateway.apilib.prefeitura.sp.gov.br/sf/sof/v4"
ORGAO = 34
UNIDADE = 10
LIMIT = 500
TOKEN = "b9c10754-7b28-3aee-b0bc-4f6785f9c6bd"
SAIDA = "execucao_org34_uo10.csv"
headers = {
    "Authorization": f"Bearer {TOKEN}"
}

p = {
    "anoExercicio": ANO
}

# -----------------------------
# FUNÇÕES AUXILIARES
# -----------------------------
def fetch_all(endpoint, params=None, list_=None):
    """Busca todos os registros paginados de um endpoint."""
    all_items = []
    while True:
        p = params.copy() if params else {}
        r = requests.get(f"{BASE}/{endpoint}", params=p, headers=headers)
        r.raise_for_status()
        data = r.json() or []
        if not data:
            break
        df = pd.json_normalize(data[list_])
        if endpoint == "modalidades":
            l = df.iloc[:, 1].tolist()
        else: 
            l = df.iloc[:, 0].tolist()
        all_items.extend(l)
        time.sleep(0.05)  # respeitar limites da API
        break
    return all_items


def separar_fontes(fonte_str):
    """Converte string '00.1.573.9001' em 4 parâmetros da API."""
    partes = fonte_str.split(".")
    return {
        "codFonteRecurso": partes[0],
        "codReferencia": partes[1],
        "codDestinacaoRecurso": partes[2],
        "codVinculacaoRecurso": partes[3]
    }

def salvar_incremental(dados, arquivo=SAIDA):
    """Salva dados em CSV incrementalmente."""
    df = pd.DataFrame(dados)
    df.to_csv(
        arquivo,
        mode='a',
        index=False,
        header=not Path(arquivo).exists(),
        encoding="utf-8-sig"
    )

# -----------------------------
# 1️⃣ BUSCAR LISTAS DE CÓDIGOS VÁLIDOS
# -----------------------------
print("Buscando listas de códigos auxiliares...")
funcoes = fetch_all("funcoes", p, "lstFuncao")
subfuncoes = fetch_all("subFuncoes", p, "lstSubFuncoes")
programas = fetch_all("programas", p, "lstProgramas")
acoes = fetch_all("projetosAtividades", p, "lstProjetosAtividades")
categorias = fetch_all("categorias", p, "lstCategorias")
grupos = fetch_all("grupos", p, "lstGrupos")
modalidades = fetch_all("modalidades", p, "lstModalidades")
elementos = fetch_all("elementos", p, "lstElementos")
fontes = fetch_all("fonteRecursos", p, "lstFonteRecurso")

print(f"Códigos carregados: {len(funcoes)} funções, {len(programas)} programas, {len(fontes)} fontes de recurso...")

# -----------------------------
# 2️⃣ LOOP PRINCIPAL
# -----------------------------
dados = []
contador = 0

# cálculo do total de iterações para ETA
lens = [
    len(funcoes), len(subfuncoes), len(programas), len(acoes),
    len(categorias), len(grupos), len(modalidades), len(elementos), len(fontes)
]
total_iteracoes = 1
for l in lens:
    total_iteracoes *= max(1, l)  # evita multiplicar por zero

# registro de tempo inicial
inicio_ts = time.time()
inicio_dt = datetime.now()
print("Início:", inicio_dt.strftime("%Y-%m-%d %H:%M:%S"))
print(f"Total de combinações a processar: {total_iteracoes}")

last_progress_print = 0
print_interval = 10  # mostrar progresso a cada N iterações

print("Iniciando coleta de execução...")
for func, subf, prog, acao, cat, grp, mod, elem, fonte_str in product(
    funcoes or [None],
    subfuncoes or [None],
    programas or [None],
    acoes or [None],
    categorias or [None],
    grupos or [None],
    modalidades or [None],
    elementos or [None],
    fontes or [None]
):
    fonte_codigos = separar_fontes(fonte_str) if fonte_str else {
        "codFonteRecurso": "", "codReferencia": "", "codDestinacaoRecurso": "", "codVinculacaoRecurso": ""
    }

    params = {
        "anoDotacao": ANO,
        "mesDotacao": MES,
        "codOrgao": ORGAO,
        "codUnidade": UNIDADE,
        "codFuncao": func,
        "codSubfuncao": subf,
        "codPrograma": prog,
        "codAcao": acao,
        "codCategoriaEconomica": cat,
        "codGrupoNatureza": grp,
        "codModalidadeAplicacao": mod,
        "codElementoDespesa": elem,
        **fonte_codigos,
        "limit": LIMIT,
        "offset": 0
    }

    try:
        r = requests.get(f"{BASE}/despesas", params=params, headers=headers)
        if r.status_code != 200:
            print(f"Erro {r.status_code} com params {params}")
            contador += 1
            continue

        resp_data = r.json().get("data") or []
        if resp_data:
            dados.extend(resp_data)

        contador += 1

        # Salvamento incremental a cada 100 requisições
        if contador % 100 == 0 and dados:
            salvar_incremental(dados)
            dados = []
            print(f"{contador} requisições processadas...")

        # progresso e ETA (substituir o bloco atual por este)
        if contador - last_progress_print >= print_interval or contador == total_iteracoes:
            now = time.time()
            elapsed = now - inicio_ts
            processed = contador
            percent = (processed / total_iteracoes) * 100 if total_iteracoes else 0
            avg_per_iter = elapsed / processed if processed else 0
            remaining_iters = max(0, total_iteracoes - processed)

            # calcula remaining_seconds com proteção contra valores absurdos
            try:
                remaining_seconds = remaining_iters * avg_per_iter
                # limite razoável (ex: 10 anos em segundos) para evitar overflow em timedelta
                MAX_SECONDS = 10 * 365 * 24 * 3600
                if remaining_seconds > MAX_SECONDS or remaining_seconds < 0 or not math.isfinite(remaining_seconds):
                    eta_str = "ETA: indisponível (valor muito grande)"
                else:
                    eta_dt = datetime.now() + timedelta(seconds=int(remaining_seconds))
                    eta_str = eta_dt.strftime('%Y-%m-%d %H:%M:%S')
            except Exception:
                eta_str = "ETA: erro ao calcular"

            # imprime elapsed de forma segura
            try:
                elapsed_str = str(timedelta(seconds=int(elapsed)))
            except Exception:
                elapsed_str = f"{elapsed:.1f}s"

            print(f"Progresso: {processed}/{total_iteracoes} ({percent:.2f}%) - Elapsed: {elapsed_str} - ETA: {eta_str}")
            last_progress_print = contador

        time.sleep(0.05)  # respeitar limites da API
    except Exception as e:
        print(f"Erro na requisição: {e}")
        contador += 1
        continue

# Salvar qualquer dado restante
if dados:
    salvar_incremental(dados)

fim_ts = time.time()
fim_dt = datetime.now()
elapsed_total = fim_ts - inicio_ts

print(f"Fim: {fim_dt.strftime('%Y-%m-%d %H:%M:%S')}")
print(f"Tempo decorrido: {timedelta(seconds=int(elapsed_total))}")
if total_iteracoes and contador < total_iteracoes:
    print(f"Processado: {contador}/{total_iteracoes} (não completou todas as combinações)")
else:
    print(f"Processado: {contador}/{total_iteracoes}")

print(f"Base de execução gerada com sucesso: {SAIDA}")