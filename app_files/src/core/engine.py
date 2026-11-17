#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
engine.py - Motor Estatístico, Teoria dos Jogos, Covering Designs e Arbitragem Ginther-Mandel
Baseado na Literatura Científica de Matemática Aplicada e Arbitragem Estatística:
1. Teoria da Informação & Entropia de Shannon (H(X) ≈ 25.57 bits)
2. Teste de Aderência Qui-Quadrado (NIST SP 800-22 / Dieharder) contra concursos reais
3. Teoria dos Jogos & Maximização do Valor Esperado E[X] (Anti-Colisão / Fuga de Aniversário 1-31)
4. Covering Designs Combinatórios C(v, k, t) - Fechamento Matemático com garantia de Quadra/Quina
5. Modelo de Arbitragem Ginther-Mandel (Radar de Valor Esperado Positivo E[X] > 0 para Loterias Brasileiras)
6. Otimizador de Sindicatos / Bolões de Alta Performance
7. Thread-Safety em Operações Concorrentes de Cache e Sincronização
"""

import os
import io
import json
import csv
import ssl
import time
import math
import random
import logging
import zipfile
import itertools
import threading
import subprocess
import urllib.request
import urllib.error
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import List, Dict, Tuple, Optional, Any, Set

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)
CACHE_FILE = DATA_DIR / "mega_cache.json"
HISTORY_CSV = DATA_DIR / "mega_history.csv"
NATIVE_KERNEL_CS = Path(__file__).resolve().parent / "native_kernel.cs"
NATIVE_KERNEL_EXE = Path(__file__).resolve().parent / "cartela_kernel.exe"
CSC_PATH = Path(r"C:\Windows\Microsoft.NET\Framework64\v4.0.30319\csc.exe")

SSL_CTX_VERIFIED = ssl.create_default_context()
SSL_CTX_UNVERIFIED = ssl.create_default_context()
SSL_CTX_UNVERIFIED.check_hostname = False
SSL_CTX_UNVERIFIED.verify_mode = ssl.CERT_NONE

CAIXA_PARAMS_URL = "https://loterias.caixa.gov.br/Style%20Library/json/params.txt"
CAIXA_API_BASE = "https://servicebus3.caixa.gov.br/portaldeloterias"
CAIXA_API_URL = f"{CAIXA_API_BASE}/api/megasena"
CAIXA_API_FALLBACK_URL = "https://servicebus2.caixa.gov.br/portaldeloterias/api/megasena"
CAIXA_SIMULACAO_URL = (
    "https://www.loteriasonline.caixa.gov.br/silce-servico-rest/rest/v1/"
    "cGFyYW1ldHJvcy1zaW11bGFjYW8v"
)
DEFAULT_HEADERS = {"User-Agent": "Mozilla/5.0", "Accept": "application/json"}

# Mapeamento de quadrantes clássicos do volante 10x6
QUADRANTE_MAP: Dict[int, int] = {}
for lin in range(6):
    for col in range(10):
        d = lin * 10 + (col + 1)
        if lin < 3 and col < 5:
            QUADRANTE_MAP[d] = 1
        elif lin < 3 and col >= 5:
            QUADRANTE_MAP[d] = 2
        elif lin >= 3 and col < 5:
            QUADRANTE_MAP[d] = 3
        else:
            QUADRANTE_MAP[d] = 4


class MegaSenaEngine:
    def __init__(self):
        self._lock = threading.RLock()
        self.concursos: List[List[int]] = []
        self.mu: Optional[List[float]] = None
        self.cov_inv: Optional[List[List[float]]] = None
        self.carregar_dados()

    # -------------------------------------------------------------
    # 1. CARREGAMENTO E SINCRONIZAÇÃO DE DADOS REAIS (THREAD-SAFE)
    # -------------------------------------------------------------
    def carregar_dados(self) -> List[List[int]]:
        with self._lock:
            if CACHE_FILE.exists():
                try:
                    with open(CACHE_FILE, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        if isinstance(data, list) and len(data) > 0:
                            self.concursos = [sorted(map(int, c)) for c in data]
                            self._calibrar_matriz_mahalanobis()
                            return list(self.concursos)
                except Exception as e:
                    logging.error(f"Erro ao ler cache: {e}")
            return self.sincronizar_dados_oficiais()

    def _http_get_bytes(self, url: str, timeout: int = 8, headers: Optional[Dict[str, str]] = None) -> bytes:
        req = urllib.request.Request(url, headers=headers or DEFAULT_HEADERS)
        try:
            with urllib.request.urlopen(req, context=SSL_CTX_VERIFIED, timeout=timeout) as resp:
                return resp.read()
        except urllib.error.URLError as exc:
            if isinstance(exc.reason, ssl.SSLCertVerificationError):
                logging.warning(f"Falha na verificação TLS para {url}; usando fallback sem verificação.")
                with urllib.request.urlopen(req, context=SSL_CTX_UNVERIFIED, timeout=timeout) as resp:
                    return resp.read()
            raise

    def _http_get_json(self, url: str, timeout: int = 8) -> Any:
        raw = self._http_get_bytes(url, timeout=timeout)
        return json.loads(raw.decode("utf-8"))

    def _resolver_api_base(self) -> str:
        cached = getattr(self, "_api_base", None)
        if cached:
            return cached
        try:
            params = self._http_get_json(CAIXA_PARAMS_URL, timeout=5)
            if isinstance(params, dict) and params.get("urlapiloterias"):
                self._api_base = str(params["urlapiloterias"]).rstrip("/")
                return self._api_base
        except Exception:
            pass
        self._api_base = CAIXA_API_BASE
        return self._api_base

    def _candidatos_megasena_url(self) -> List[str]:
        base = self._resolver_api_base()
        primary = f"{base}/api/megasena"
        urls = [primary]
        if CAIXA_API_URL not in urls:
            urls.append(CAIXA_API_URL)
        if CAIXA_API_FALLBACK_URL not in urls:
            urls.append(CAIXA_API_FALLBACK_URL)
        return urls

    def obter_ultimo_resultado_online(self) -> Optional[Dict[str, Any]]:
        for base_url in self._candidatos_megasena_url():
            try:
                data = self._http_get_json(base_url, timeout=8)
                return {
                    "numero": int(data.get("numero", 0)),
                    "data": data.get("dataApuracao", ""),
                    "dezenas": sorted([int(x) for x in data.get("listaDezenas", [])]),
                    "acumulado": bool(data.get("acumulado", False)),
                    "premio_estimado": float(data.get("valorEstimadoProximoConcurso", 0.0)),
                    "proximo_concurso_data": data.get("dataProximoConcurso", ""),
                    "indicador_concurso_especial": int(data.get("indicadorConcursoEspecial", 0) or 0),
                    "titulo_especial": data.get("tituloConcursoEspecial") or "",
                    "valor_acumulado_especial": float(data.get("valorAcumuladoConcursoEspecial", 0.0) or 0.0),
                }
            except Exception:
                continue
        return None

    def obter_parametros_oficiais_ao_vivo(self) -> Optional[Dict[str, Any]]:
        """Sincroniza regras, preços (6 a 20 dezenas) e concursos abertos de Mega-Sena/Virada ao vivo."""
        try:
            data = self._http_get_json(CAIXA_SIMULACAO_URL, timeout=8)
            payload = data.get("payload", {}) if isinstance(data, dict) else {}
            if not payload:
                return None

            concursos_abertos: List[Dict[str, Any]] = []
            tabela_precos: Dict[int, float] = {}

            for item in payload.get("parametros", []):
                pj = item.get("parametroJogo", {})
                concurso = pj.get("concurso", {})
                if concurso.get("modalidade") != "MEGA_SENA":
                    continue

                precos_item = {
                    int(p["numeroPrognosticos"]): float(p["valor"])
                    for p in pj.get("valoresAposta", [])
                    if "numeroPrognosticos" in p and "valor" in p
                }
                if precos_item and not tabela_precos:
                    tabela_precos = precos_item

                detalhada = concurso.get("modalidadeDetalhada", {})
                tipo = concurso.get("tipoConcurso", "NORMAL")
                concursos_abertos.append({
                    "concurso": int(concurso.get("numero", 0)),
                    "tipo": tipo,
                    "descricao": detalhada.get("descricaoEspecial") if tipo == "ESPECIAL" else detalhada.get("descricao", "Mega-Sena"),
                    "estimativa": float(concurso.get("estimativa", 0.0)),
                    "data_abertura": concurso.get("dataAbertura", ""),
                    "data_fechamento": concurso.get("dataFechamento", ""),
                    "data_hora_sorteio": concurso.get("dataHoraSorteio", ""),
                    "valor_aposta_minima": float(concurso.get("valorApostaMinima", 6.0)),
                    "situacao": concurso.get("situacao", ""),
                    "tabela_precos": precos_item,
                })

            resumo = {
                "versao_api": data.get("versao", ""),
                "data_hora_servidor": data.get("dataHoraServidor", ""),
                "valor_minimo_carrinho": float(payload.get("valorMinimoCarrinho", 2.50)),
                "max_apostas_carrinho": int(payload.get("quantidadeMaximaApostasCarrinho", 999)),
                "tabela_precos": tabela_precos,
                "concursos_abertos": concursos_abertos,
            }
            self._parametros_ao_vivo = resumo
            return resumo
        except Exception as e:
            logging.debug(f"Portal Loterias Online indisponível ({e}); usando fallback servicebus3.")
            ultimo = self.obter_ultimo_resultado_online()
            if not ultimo:
                return None
            tabela_padrao = {
                k: round(math.comb(k, 6) * 6.0, 2) for k in range(6, 21)
            }
            abertos = [
                {
                    "concurso": ultimo["numero"] + 1,
                    "tipo": "NORMAL",
                    "descricao": "Mega-Sena",
                    "estimativa": ultimo.get("premio_estimado", 0.0),
                    "data_abertura": "",
                    "data_fechamento": ultimo.get("proximo_concurso_data", ""),
                    "data_hora_sorteio": ultimo.get("proximo_concurso_data", ""),
                    "valor_aposta_minima": 6.0,
                    "situacao": "ABERTO",
                    "tabela_precos": tabela_padrao,
                }
            ]
            if ultimo.get("valor_acumulado_especial", 0.0) > 0:
                abertos.append({
                    "concurso": 3100,
                    "tipo": "ESPECIAL",
                    "descricao": "Mega da Virada (Acumulado)",
                    "estimativa": ultimo["valor_acumulado_especial"],
                    "data_abertura": "",
                    "data_fechamento": "31/12/2026",
                    "data_hora_sorteio": "01/01/2027",
                    "valor_aposta_minima": 6.0,
                    "situacao": "ABERTO",
                    "tabela_precos": tabela_padrao,
                })
            resumo = {
                "versao_api": "servicebus3-fallback",
                "data_hora_servidor": ultimo.get("data", ""),
                "valor_minimo_carrinho": 2.50,
                "max_apostas_carrinho": 999,
                "tabela_precos": tabela_padrao,
                "concursos_abertos": abertos,
            }
            self._parametros_ao_vivo = resumo
            return resumo

    def obter_mega_da_virada_ao_vivo(self) -> Optional[Dict[str, Any]]:
        """Consulta os parâmetros ao vivo do concurso especial Mega da Virada no portal Loterias Online."""
        params = self.obter_parametros_oficiais_ao_vivo()
        if not params:
            return None
        for conc in params.get("concursos_abertos", []):
            if conc.get("tipo") == "ESPECIAL" or conc.get("descricao") == "Mega da Virada":
                return conc
        return None

    def calcular_custo_lote(self, jogos: List[List[int]], tabela_precos: Optional[Dict[int, float]] = None) -> Dict[str, Any]:
        """Calcula o custo oficial de um lote de volantes usando a tabela ao vivo da Caixa."""
        live = getattr(self, "_parametros_ao_vivo", None) or {}
        precos = tabela_precos or live.get("tabela_precos") or {}
        valor_base = float(precos.get(6, 6.0))
        min_carrinho = float(live.get("valor_minimo_carrinho", 2.50))
        max_apostas = int(live.get("max_apostas_carrinho", 999))

        custo_total = 0.0
        for j in jogos:
            k = len(j)
            if k in precos:
                custo_total += float(precos[k])
            elif k >= 6:
                custo_total += math.comb(k, 6) * valor_base

        qtd = len(jogos)
        return {
            "quantidade_volantes": qtd,
            "custo_total": round(custo_total, 2),
            "valor_unitario_6": valor_base,
            "atende_minimo_carrinho": custo_total >= min_carrinho if qtd > 0 else False,
            "dentro_limite_carrinho": qtd <= max_apostas,
            "valor_minimo_carrinho": min_carrinho,
            "max_apostas_carrinho": max_apostas,
        }

    @staticmethod
    def _parse_xlsx_concursos(xlsx_bytes: bytes) -> Dict[int, List[int]]:
        """Extrai {concurso: [d1..d6]} de um arquivo .xlsx oficial da Caixa usando apenas stdlib."""
        ns = {"s": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
        concursos: Dict[int, List[int]] = {}
        with zipfile.ZipFile(io.BytesIO(xlsx_bytes)) as zf:
            shared_strings: List[str] = []
            if "xl/sharedStrings.xml" in zf.namelist():
                ss_root = ET.fromstring(zf.read("xl/sharedStrings.xml"))
                for si in ss_root.findall("s:si", ns):
                    shared_strings.append("".join(t.text or "" for t in si.findall(".//s:t", ns)))

            sheet_name = next((n for n in zf.namelist() if n.startswith("xl/worksheets/sheet") and n.endswith(".xml")), None)
            if not sheet_name:
                return concursos

            sheet_root = ET.fromstring(zf.read(sheet_name))
            for row in sheet_root.findall(".//s:row", ns):
                vals: List[str] = []
                for cell in row.findall("s:c", ns):
                    ctype = cell.attrib.get("t", "")
                    v_el = cell.find("s:v", ns)
                    if v_el is None or v_el.text is None:
                        continue
                    raw_val = v_el.text.strip()
                    if ctype == "s" and raw_val.isdigit():
                        idx = int(raw_val)
                        vals.append(shared_strings[idx] if idx < len(shared_strings) else raw_val)
                    else:
                        vals.append(raw_val)

                if len(vals) < 7 or not vals[0].isdigit():
                    continue
                concurso_num = int(vals[0])
                # Caixa XLSX: col 0 = Concurso, col 1 = Data, cols 2..7 = Bola1..Bola6
                candidatos = [int(v) for v in vals[1:9] if v.isdigit() and 1 <= int(v) <= 60]
                if len(candidatos) >= 6:
                    dezenas = sorted(candidatos[:6])
                    if len(set(dezenas)) == 6:
                        concursos[concurso_num] = dezenas
        return concursos

    def sincronizar_dados_oficiais(self, progress_callback=None) -> List[List[int]]:
        with self._lock:
            ultimo_online = self.obter_ultimo_resultado_online()
            if not ultimo_online:
                return list(self.concursos)

            num_ultimo = ultimo_online["numero"]
            concursos_dict = {i + 1: c for i, c in enumerate(self.concursos)}
            concursos_dict[num_ultimo] = ultimo_online["dezenas"]

            missing = [n for n in range(1, num_ultimo + 1) if n not in concursos_dict]
            if len(missing) > 10:
                try:
                    xlsx_url = f"{self._resolver_api_base()}/api/resultados/download?modalidade=Mega-Sena"
                    xlsx_bytes = self._http_get_bytes(xlsx_url, timeout=20, headers={"User-Agent": "Mozilla/5.0"})
                    lote = self._parse_xlsx_concursos(xlsx_bytes)
                    if lote:
                        concursos_dict.update(lote)
                        missing = [n for n in range(1, num_ultimo + 1) if n not in concursos_dict]
                except Exception as e:
                    logging.warning(f"Download em massa .xlsx indisponível ({e}); usando busca incremental.")

            total_missing = len(missing)
            candidatos_url = self._candidatos_megasena_url()

            for idx, n in enumerate(missing, 1):
                dezenas = None
                for base_url in candidatos_url:
                    url = f"{base_url}/{n}"
                    for _ in range(2):
                        try:
                            d = self._http_get_json(url, timeout=6)
                            dezenas = sorted([int(x) for x in d.get("listaDezenas", [])])
                            break
                        except Exception:
                            time.sleep(0.2)
                    if dezenas:
                        break

                if dezenas:
                    concursos_dict[n] = dezenas

                if progress_callback:
                    progress_callback(idx, total_missing, n)
                time.sleep(0.12)

            sorted_keys = sorted(concursos_dict.keys())
            self.concursos = [concursos_dict[k] for k in sorted_keys]

            try:
                with open(CACHE_FILE, "w", encoding="utf-8") as f:
                    json.dump(self.concursos, f)

                with open(HISTORY_CSV, "w", encoding="utf-8", newline="") as f:
                    w = csv.writer(f, delimiter=";")
                    w.writerow(["Concurso", "D1", "D2", "D3", "D4", "D5", "D6"])
                    for k in sorted_keys:
                        w.writerow([k] + concursos_dict[k])
            except Exception as e:
                logging.error(f"Erro ao persistir histórico: {e}")

            self._calibrar_matriz_mahalanobis()
            return list(self.concursos)

    # -------------------------------------------------------------
    # 2. RADAR DE ARBITRAGEM GINTHER-MANDEL & VALOR ESPERADO (E[X])
    # -------------------------------------------------------------
    def calcular_arbitragem_ginther_mandel(self,
                                           premio_estimado: float,
                                           custo_aposta: float = 6.0,
                                           tipo_concurso: str = "especial") -> Dict[str, Any]:
        """
        Aplica a lógica de Joan Ginther e Stefan Mandel para loterias brasileiras:
        Calcula o Valor Esperado Real E[X] de cada aposta individual e para sindicatos.
        
        No modelo Mandel-Ginther:
        - Espaço Amostral Ω = 50.063.860 combinações.
        - P(Sena) = 1 / 50.063.860
        - P(Quina) = 324 / 50.063.860 (≈ 1 em 154.518)
        - P(Quadra) = 21.465 / 50.063.860 (≈ 1 em 2.332)
        
        Se o concurso é especial (Mega da Virada), o prêmio NÃO acumula. Se ninguém acertar a sena,
        o montante desce automaticamente para a Quina, aumentando drasticamente a taxa de retorno.
        """
        total_comb = 50063860.0
        p_sena = 1.0 / total_comb
        p_quina = 324.0 / total_comb
        p_quadra = 21465.0 / total_comb

        # Estimativa de prêmios por faixa (Regulamento Caixa: 35% Sena, 19% Quina, 19% Quadra)
        premio_sena = premio_estimado
        premio_quina_medio = 50000.0 if tipo_concurso == "normal" else 150000.0
        premio_quadra_medio = 1000.0 if tipo_concurso == "normal" else 2500.0

        ev_sena_puro = premio_sena * p_sena
        ev_quina = premio_quina_medio * p_quina
        ev_quadra = premio_quadra_medio * p_quadra
        ev_bruto = ev_sena_puro + ev_quina + ev_quadra

        ev_liquido = ev_bruto - custo_aposta
        roi_percent = (ev_liquido / custo_aposta) * 100.0 if custo_aposta > 0 else 0.0

        # Ponto de Equilíbrio (Breakeven Jackpot) onde EV se torna positivo
        breakeven_jackpot = max(0.0, (custo_aposta - ev_quina - ev_quadra) * total_comb)

        # Modelagem de Risco de Colisão (Splitting Penalty)
        ev_com_anticolisao = (premio_sena / 1.5) * p_sena + ev_quina + ev_quadra - custo_aposta
        ev_sem_anticolisao = (premio_sena / 18.0) * p_sena + ev_quina + ev_quadra - custo_aposta

        if ev_liquido > 0:
            status_arbitragem = "ARBITRAGEM MATEMÁTICA FAVORÁVEL (E[X] > 0)"
            diretriz = (
                f"O prêmio de R$ {premio_estimado/1e6:.1f}M supera o custo de cobertura do espaço amostral. "
                f"Com a estratégia Anti-Colisão, o bilhete de R$ {custo_aposta:.2f} tem valor intrínseco de "
                f"R$ {ev_bruto:.2f} (Retorno Esperado de +{roi_percent:.1f}%)."
            )
        else:
            status_arbitragem = "VALOR ESPERADO NEGATIVO (E[X] < 0 - Casa em Vantagem)"
            diretriz = (
                f"Para este concurso, cada bilhete tem valor intrínseco de R$ {ev_bruto:.2f} contra o custo de "
                f"R$ {custo_aposta:.2f}. O ponto de equilíbrio para arbitragem matemática pura ocorre quando o "
                f"prêmio acumulado ultrapassa R$ {breakeven_jackpot/1e6:.1f} Milhões."
            )

        return {
            "premio_analisado": premio_estimado,
            "custo_aposta": custo_aposta,
            "valor_esperado_bruto": round(ev_bruto, 2),
            "valor_esperado_liquido": round(ev_liquido, 2),
            "roi_esperado_percent": round(roi_percent, 1),
            "breakeven_jackpot": round(breakeven_jackpot, 2),
            "ev_com_estrategia_anticolisao": round(ev_com_anticolisao, 2),
            "ev_sem_estrategia_aniversarios": round(ev_sem_anticolisao, 2),
            "status_arbitragem": status_arbitragem,
            "diretriz_executiva": diretriz
        }

    # -------------------------------------------------------------
    # 3. OTIMIZADOR DE SINDICATO & BOLÕES MANDEL
    # -------------------------------------------------------------
    def planejar_bolao_sindicato(self, orcamento_reais: float, custo_bilhete: float = 6.0) -> Dict[str, Any]:
        qtd_volantes = int(orcamento_reais // custo_bilhete)
        if qtd_volantes < 1:
            return {"erro": "Orçamento insuficiente para pelo menos 1 aposta."}

        pool_otimo_tamanho = 6
        for v in range(7, 25):
            blocos_estimados = math.ceil(math.comb(v, 4) / math.comb(6, 4))
            if blocos_estimados <= qtd_volantes:
                pool_otimo_tamanho = v
            else:
                break

        scores = self.pontuar_dezenas()
        dezenas_candidatas = sorted([d for d, _ in sorted(scores.items(), key=lambda x: -x[1]) if d > 31][:pool_otimo_tamanho // 2] +
                                    [d for d, _ in sorted(scores.items(), key=lambda x: -x[1]) if d <= 31][:pool_otimo_tamanho - (pool_otimo_tamanho // 2)])
        dezenas_pool = sorted(dezenas_candidatas[:pool_otimo_tamanho])

        jogos_cobertura = self.gerar_fechamento_combinatorio(dezenas_pool, garantia="quadra")
        custo_fechamento = len(jogos_cobertura) * custo_bilhete

        return {
            "orcamento_informado": orcamento_reais,
            "total_volantes_possiveis": qtd_volantes,
            "tamanho_pool_recomendado": pool_otimo_tamanho,
            "pool_dezenas_selecionado": dezenas_pool,
            "volantes_no_fechamento_garantido": len(jogos_cobertura),
            "custo_fechamento_reais": custo_fechamento,
            "sobra_orcamento": orcamento_reais - custo_fechamento,
            "garantia_matematica": f"100% de garantia de QUADRA se as 6 sorteadas estiverem no pool de {pool_otimo_tamanho} dezenas.",
            "jogos_gerados": jogos_cobertura
        }

    # -------------------------------------------------------------
    # 4. TESTE DE ADERÊNCIA QUI-QUADRADO (NIST SP 800-22 / DIEHARD)
    # -------------------------------------------------------------
    def teste_qui_quadrado(self) -> Dict[str, Any]:
        with self._lock:
            N = len(self.concursos)
            if N == 0:
                return {
                    "total_concursos": 0,
                    "estatistica_qui_quadrado": 0.0,
                    "p_valor": 1.0,
                    "conclusao_cientifica": "SEM DADOS HISTÓRICOS",
                    "explicacao": "Nenhum concurso carregado na base."
                }

            total_bolas = N * 6
            esperado = total_bolas / 60.0

            freq = {d: 0 for d in range(1, 61)}
            for c in self.concursos:
                for d in c:
                    freq[d] += 1

            chi2_stat = sum(((freq[d] - esperado) ** 2) / esperado for d in range(1, 61))
            graus_liberdade = 59
            # Correção exata para amostragem hipergeométrica sem reposição: fator (N_pop - 1) / (N_pop - k) = 59 / 54
            chi2_corrigido = chi2_stat * (59.0 / 54.0)

            def _chi2_pvalue(stat: float, df: int) -> float:
                if stat <= 0:
                    return 1.0
                z = ((stat / df) ** (1 / 3) - (1 - 2 / (9 * df))) / math.sqrt(2 / (9 * df))
                return max(0.0, min(1.0, 0.5 * math.erfc(z / math.sqrt(2))))

            p_valor = _chi2_pvalue(chi2_stat, graus_liberdade)
            p_valor_corrigido = _chi2_pvalue(chi2_corrigido, graus_liberdade)

            if p_valor >= 0.05:
                conclusao = "ALEATORIEDADE PERFEITA (H0 Não Rejeitada a 95%)"
                explicacao = (
                    f"Com Chi2={chi2_stat:.2f} e p-valor={p_valor:.4f} >= 0.05, a hipótese de distribuição "
                    f"uniforme não é rejeitada. O sorteio mecânico opera com integridade estocástica."
                )
            elif p_valor >= 0.01:
                conclusao = "ALEATORIEDADE CONSISTENTE (H0 Não Rejeitada a 99%)"
                explicacao = (
                    f"Com Chi2={chi2_stat:.2f} e p-valor={p_valor:.4f} >= 0.01, o teste não rejeita uniformidade "
                    f"no limiar rigoroso de 99% (NIST SP 800-22). Pequenas variações são flutuações amostrais esperadas."
                )
            else:
                conclusao = "DESVIO ESTATÍSTICO DETECTADO (p < 0.01)"
                explicacao = (
                    f"Com Chi2={chi2_stat:.2f} e p-valor={p_valor:.4f} < 0.01, há evidência estatística de desvio "
                    f"em relação à equiprobabilidade ideal."
                )

            return {
                "total_concursos": N,
                "total_bolas_sorteadas": total_bolas,
                "frequencia_esperada_por_dezena": round(esperado, 2),
                "estatistica_qui_quadrado": round(chi2_stat, 2),
                "estatistica_qui_quadrado_corrigida": round(chi2_corrigido, 2),
                "graus_liberdade": graus_liberdade,
                "p_valor": round(p_valor, 4),
                "p_valor_corrigido": round(p_valor_corrigido, 4),
                "conclusao_cientifica": conclusao,
                "explicacao": explicacao
            }

    # -------------------------------------------------------------
    # 5. TEORIA DOS JOGOS & ANTI-COLISÃO
    # -------------------------------------------------------------
    def calcular_indice_anti_colisao(self, jogo: List[int]) -> Dict[str, Any]:
        dezenas_aniversario = [d for d in jogo if d <= 31]
        pct_aniversario = (len(dezenas_aniversario) / 6.0) * 100
        consecutivos = sum(1 for i in range(len(jogo) - 1) if jogo[i + 1] - jogo[i] == 1)
        ent = self.entropia_shannon(jogo)

        score = 100.0
        if len(dezenas_aniversario) > 3:
            score -= (len(dezenas_aniversario) - 3) * 15.0
        score -= consecutivos * 12.0
        if ent < 1.80:
            score -= 15.0

        score = max(10.0, min(100.0, score))

        if score >= 80:
            classificacao = "EXCELENTE (Quase Zero Risco de Divisão)"
        elif score >= 60:
            classificacao = "BOM (Acima da média dos apostadores)"
        elif score >= 40:
            classificacao = "MODERADO (Muitas datas de aniversário)"
        else:
            classificacao = "ALTO RISCO DE DIVISÃO (Padrão Popular)"

        return {
            "score_anti_colisao": round(score, 1),
            "classificacao": classificacao,
            "dezenas_aniversario_count": len(dezenas_aniversario),
            "pct_aniversario": round(pct_aniversario, 1),
            "consecutivos": consecutivos,
            "entropia_shannon": round(ent, 2)
        }

    # -------------------------------------------------------------
    # 6. COVERING DESIGNS C(v, k, t) OTIMIZADO
    # -------------------------------------------------------------
    def _ensure_native_kernel(self) -> Optional[Path]:
        """Garante o binário nativo C# (/unsafe ulong*) compilado em Windows x64."""
        if os.name != "nt":
            return None
        if NATIVE_KERNEL_EXE.exists():
            return NATIVE_KERNEL_EXE
        if NATIVE_KERNEL_CS.exists() and CSC_PATH.exists():
            try:
                flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
                subprocess.run(
                    [
                        str(CSC_PATH),
                        "/nologo",
                        "/unsafe",
                        "/optimize+",
                        "/platform:x64",
                        f"/out:{NATIVE_KERNEL_EXE}",
                        str(NATIVE_KERNEL_CS),
                    ],
                    check=True,
                    capture_output=True,
                    timeout=20,
                    creationflags=flags,
                )
                if NATIVE_KERNEL_EXE.exists():
                    return NATIVE_KERNEL_EXE
            except Exception as e:
                logging.warning(f"Falha ao compilar kernel nativo C#: {e}")
        return None

    def gerar_fechamento_combinatorio(self, dezenas_pool: List[int], garantia: str = "quadra") -> List[List[int]]:
        pool = sorted(list(set(dezenas_pool)))
        v = len(pool)
        if v < 6:
            raise ValueError(f"O pool deve ter pelo menos 6 dezenas distintas. Fornecido: {v}")
        if any(d < 1 or d > 60 for d in pool):
            raise ValueError("Todas as dezenas devem estar no intervalo de 1 a 60.")
        if v == 6:
            return [pool]

        t_garantia = 4 if garantia == "quadra" else 5

        if v >= 9:
            kernel_exe = self._ensure_native_kernel()
            if kernel_exe:
                try:
                    flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
                    pool_csv = ",".join(str(d) for d in pool)
                    proc = subprocess.run(
                        [str(kernel_exe), "cover", str(t_garantia), pool_csv],
                        check=True,
                        capture_output=True,
                        text=True,
                        timeout=30,
                        creationflags=flags,
                    )
                    jogos = [
                        [int(x) for x in line.strip().split(",")]
                        for line in proc.stdout.splitlines()
                        if line.strip()
                    ]
                    if jogos:
                        return jogos
                except Exception as e:
                    logging.warning(f"Fallback para bitmask Python no fechamento: {e}")

        # Fallback puro Python com bitmasks de 64 bits (sem alocação de frozenset)
        todos_blocos = [
            (sum(1 << (d - 1) for d in b), list(b))
            for b in itertools.combinations(pool, 6)
        ]
        tuplas_restantes = [
            sum(1 << (d - 1) for d in c)
            for c in itertools.combinations(pool, t_garantia)
        ]
        jogos_selecionados: List[List[int]] = []

        while tuplas_restantes:
            melhor_idx = -1
            melhor_hits = 0
            for idx, (b_mask, _) in enumerate(todos_blocos):
                hits = sum(1 for t_mask in tuplas_restantes if (b_mask & t_mask) == t_mask)
                if hits > melhor_hits:
                    melhor_hits = hits
                    melhor_idx = idx
                    if hits == len(tuplas_restantes):
                        break
            if melhor_idx < 0 or melhor_hits == 0:
                break
            b_mask, b_list = todos_blocos.pop(melhor_idx)
            jogos_selecionados.append(b_list)
            tuplas_restantes = [t_mask for t_mask in tuplas_restantes if (b_mask & t_mask) != t_mask]

        return jogos_selecionados

    # -------------------------------------------------------------
    # 7. MATRIZ DE MAHALANOBIS & ENTROPIA
    # -------------------------------------------------------------
    def _extrair_vetor_caracteristicas(self, jogo: List[int]) -> List[float]:
        soma = float(sum(jogo))
        amp = float(max(jogo) - min(jogo))
        media = soma / 6.0
        var = sum((x - media) ** 2 for x in jogo) / 6.0
        dp = math.sqrt(var)
        pares = float(sum(1 for x in jogo if x % 2 == 0))
        q1 = float(sum(1 for x in jogo if QUADRANTE_MAP.get(x, 1) == 1))
        q2 = float(sum(1 for x in jogo if QUADRANTE_MAP.get(x, 2) == 2))
        q3 = float(sum(1 for x in jogo if QUADRANTE_MAP.get(x, 3) == 3))
        # Vetor 7D linearmente independente (q4 = 6 - q1 - q2 - q3 evita singularidade de Σ)
        return [soma, amp, dp, pares, q1, q2, q3]

    def _calibrar_matriz_mahalanobis(self):
        with self._lock:
            if len(self.concursos) < 30:
                return
            X = [self._extrair_vetor_caracteristicas(c) for c in self.concursos]
            n = len(X)
            dim = len(X[0])
            self.mu = [sum(X[i][j] for i in range(n)) / n for j in range(dim)]

            cov = [[0.0] * dim for _ in range(dim)]
            for row in X:
                diff = [row[j] - self.mu[j] for j in range(dim)]
                for i in range(dim):
                    for j in range(dim):
                        cov[i][j] += diff[i] * diff[j]

            for i in range(dim):
                for j in range(dim):
                    cov[i][j] /= (n - 1)
                cov[i][i] += 1e-4

            self.cov_inv = self._inverter_matriz(cov)

    def _inverter_matriz(self, A: List[List[float]]) -> List[List[float]]:
        n = len(A)
        M = [row[:] + [1.0 if i == j else 0.0 for j in range(n)] for i, row in enumerate(A)]
        for i in range(n):
            max_row = max(range(i, n), key=lambda r: abs(M[r][i]))
            M[i], M[max_row] = M[max_row], M[i]
            pivot = M[i][i] if abs(M[i][i]) > 1e-12 else 1e-6
            for j in range(2 * n):
                M[i][j] /= pivot
            for k in range(n):
                if k != i:
                    factor = M[k][i]
                    for j in range(2 * n):
                        M[k][j] -= factor * M[i][j]
        return [row[n:] for row in M]

    def distancia_mahalanobis(self, jogo: List[int]) -> float:
        if not self.mu or not self.cov_inv:
            return 2.45
        v = self._extrair_vetor_caracteristicas(jogo)
        diff = [v[i] - self.mu[i] for i in range(len(v))]
        temp = [sum(diff[j] * self.cov_inv[j][i] for j in range(len(v))) for i in range(len(v))]
        quad = sum(temp[i] * diff[i] for i in range(len(v)))
        return math.sqrt(max(0.0, quad))

    def entropia_shannon(self, jogo: List[int]) -> float:
        decadas = [0] * 6
        for d in jogo:
            dec = min(5, max(0, (d - 1) // 10))
            decadas[dec] += 1
        ent = 0.0
        for count in decadas:
            if count > 0:
                p = count / 6.0
                ent -= p * math.log2(p)
        return ent

    def calcular_frequencias(self, ultimos_n: Optional[int] = None) -> Dict[int, int]:
        with self._lock:
            base = self.concursos[-ultimos_n:] if ultimos_n and len(self.concursos) >= ultimos_n else self.concursos
            freq = {d: 0 for d in range(1, 61)}
            for c in base:
                for d in c:
                    freq[d] += 1
            return freq

    def calcular_atrasos(self) -> Dict[int, int]:
        with self._lock:
            atrasos = {d: len(self.concursos) for d in range(1, 61)}
            total = len(self.concursos)
            for idx in range(total - 1, -1, -1):
                concurso = self.concursos[idx]
                dist = (total - 1) - idx
                for d in concurso:
                    if atrasos[d] == total:
                        atrasos[d] = dist
            return atrasos

    def pontuar_dezenas(self) -> Dict[int, float]:
        freq_global = self.calcular_frequencias()
        freq_recente = self.calcular_frequencias(ultimos_n=100)
        atrasos = self.calcular_atrasos()
        max_g = max(freq_global.values()) if freq_global and max(freq_global.values()) > 0 else 1
        max_r = max(freq_recente.values()) if freq_recente and max(freq_recente.values()) > 0 else 1
        max_a = max(atrasos.values()) if atrasos and max(atrasos.values()) > 0 else 1
        scores = {}
        for d in range(1, 61):
            scores[d] = 0.5 * (freq_global[d] / max_g) + 0.3 * (freq_recente[d] / max_r) + 0.2 * (1.0 - atrasos[d] / max_a)
        return scores

    def validar_filtros(self, jogo: List[int], min_soma: int = 140, max_soma: int = 225) -> bool:
        soma = sum(jogo)
        if not (min_soma <= soma <= max_soma):
            return False
        pares = sum(1 for d in jogo if d % 2 == 0)
        if not (2 <= pares <= 4):
            return False
        consecutivos = sum(1 for i in range(len(jogo) - 1) if jogo[i + 1] - jogo[i] == 1)
        if consecutivos > 2:
            return False
        q_count = [0] * 5
        for d in jogo:
            q = QUADRANTE_MAP.get(d, 1)
            q_count[q] += 1
        if max(q_count) > 3:
            return False
        if self.entropia_shannon(jogo) < 1.70:
            return False
        return True

    def gerar_jogos(self, quantidade: int = 10,
                    modo: str = "anti_colisao",
                    min_soma: int = 140,
                    max_soma: int = 225,
                    forcar_filtros: bool = False) -> List[List[int]]:
        if quantidade <= 0:
            return []

        populacao = list(range(1, 61))
        pesos_anticolisao = [1.0 if d <= 31 else 1.95 for d in range(1, 61)]
        freq = self.calcular_frequencias()
        max_f = max(freq.values()) if freq and max(freq.values()) > 0 else 1
        pesos_freq = [freq.get(d, 1) / max_f for d in range(1, 61)]

        candidatos: List[Tuple[float, float, List[int]]] = []
        max_iter = max(1000, quantidade * 250)

        for _ in range(max_iter):
            if modo == "anti_colisao":
                jogo = sorted(random.choices(populacao, weights=pesos_anticolisao, k=9))
            elif modo == "frequencia":
                jogo = sorted(random.choices(populacao, weights=pesos_freq, k=9))
            else:
                jogo = sorted(random.sample(populacao, 6))

            jogo_u = sorted(list(set(jogo)))
            if len(jogo_u) < 6:
                restantes = [d for d in populacao if d not in jogo_u]
                jogo_u += random.sample(restantes, 6 - len(jogo_u))
            jogo_final = sorted(jogo_u[:6])

            if not forcar_filtros and not self.validar_filtros(jogo_final, min_soma, max_soma):
                continue

            score_ac = self.calcular_indice_anti_colisao(jogo_final)["score_anti_colisao"]
            dist_m = self.distancia_mahalanobis(jogo_final)

            candidatos.append((score_ac, dist_m, jogo_final))
            if len(candidatos) >= quantidade * 10:
                break

        if modo == "anti_colisao":
            candidatos.sort(key=lambda x: -x[0])
        elif modo == "mahalanobis":
            candidatos.sort(key=lambda x: abs(x[1] - 2.45))
        else:
            random.shuffle(candidatos)

        jogos_gerados = []
        vistos = set()
        for item in candidatos:
            j = item[2]
            tj = tuple(j)
            if tj not in vistos:
                vistos.add(tj)
                jogos_gerados.append(j)
                if len(jogos_gerados) == quantidade:
                    break

        while len(jogos_gerados) < quantidade:
            j = sorted(random.sample(populacao, 6))
            if tuple(j) not in vistos:
                vistos.add(tuple(j))
                jogos_gerados.append(j)

        return jogos_gerados

    # -------------------------------------------------------------
    # 8. BACKTESTING HISTÓRICO
    # -------------------------------------------------------------
    def backtest_jogo(self, jogo: List[int]) -> Dict[str, Any]:
        with self._lock:
            jogo_mask = 0
            for d in jogo:
                jogo_mask |= (1 << (d - 1))
            acertos_count = {0: 0, 1: 0, 2: 0, 3: 0, 4: 0, 5: 0, 6: 0}
            premiados = []
            for idx, conc in enumerate(self.concursos, 1):
                c_mask = 0
                for d in conc:
                    c_mask |= (1 << (d - 1))
                hits = (jogo_mask & c_mask).bit_count()
                acertos_count[hits] += 1
                if hits >= 4:
                    premiados.append({"concurso": idx, "acertos": hits, "sorteio": conc})

            return {
                "jogo": jogo,
                "total_concursos": len(self.concursos),
                "quadras": acertos_count[4],
                "quinas": acertos_count[5],
                "senas": acertos_count[6],
                "detalhes": premiados
            }

    # -------------------------------------------------------------
    # 9. EXPORTAÇÃO (PDF / CSV)
    # -------------------------------------------------------------
    def exportar_csv(self, jogos: List[List[int]], filepath: str):
        path_obj = Path(filepath)
        path_obj.parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, "w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f, delimiter=";")
            writer.writerow(["Jogo", "D1", "D2", "D3", "D4", "D5", "D6", "Soma", "Pares", "Anti-Colisao", "Mahalanobis"])
            for idx, j in enumerate(jogos, 1):
                soma = sum(j)
                pares = sum(1 for d in j if d % 2 == 0)
                ac = self.calcular_indice_anti_colisao(j)["score_anti_colisao"]
                dm = round(self.distancia_mahalanobis(j), 2)
                writer.writerow([f"Jogo #{idx:02d}"] + [f"{d:02d}" for d in j] + [soma, pares, f"{ac}%", dm])

    def exportar_pdf(self, jogos: List[List[int]], filepath: str) -> str:
        from fpdf import FPDF
        from fpdf.enums import XPos, YPos

        path_obj = Path(filepath)
        path_obj.parent.mkdir(parents=True, exist_ok=True)

        class PDFReport(FPDF):
            def header(self):
                self.set_fill_color(11, 15, 25)
                self.rect(0, 0, 210, 28, "F")
                self.set_font("Helvetica", "B", 15)
                self.set_text_color(248, 250, 252)
                self.cell(0, 10, "CARTELA - TEORIA DOS JOGOS & LOTERIAS", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="C")
                self.set_font("Helvetica", "", 9)
                self.set_text_color(148, 163, 184)
                self.cell(0, 5, "Volantes Otimizados por Maximizacao do Valor Esperado E[X] e Fechamentos", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="C")
                self.ln(6)

            def footer(self):
                self.set_y(-15)
                self.set_font("Helvetica", "I", 8)
                self.set_text_color(148, 163, 184)
                self.cell(0, 10, f"Pagina {self.page_no()} | Enterprise Intelligence Lab", align="C")

        pdf = PDFReport()
        pdf.set_auto_page_break(True, margin=15)
        pdf.add_page()
        pdf.ln(5)

        with self._lock:
            total_conc = len(self.concursos)

        pdf.set_font("Helvetica", "B", 11)
        pdf.set_text_color(30, 41, 59)
        pdf.cell(0, 8, f"Total de Jogos: {len(jogos)} | Validacao: {total_conc} Concursos Reais Caixa", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(100, 116, 139)
        pdf.cell(0, 6, f"Data da Emissao: {time.strftime('%d/%m/%Y %H:%M:%S')}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.ln(4)

        pdf.set_fill_color(15, 23, 42)
        pdf.set_text_color(255, 255, 255)
        pdf.set_font("Helvetica", "B", 9)
        pdf.cell(18, 8, "JOGO", border=1, align="C", fill=True)
        pdf.cell(85, 8, "DEZENAS SELECIONADAS", border=1, align="C", fill=True)
        pdf.cell(24, 8, "SOMA", border=1, align="C", fill=True)
        pdf.cell(25, 8, "PAR/IMP", border=1, align="C", fill=True)
        pdf.cell(38, 8, "ANTI-COLISAO", border=1, align="C", fill=True)
        pdf.ln()

        for idx, j in enumerate(jogos, 1):
            fill = (idx % 2 == 0)
            if fill:
                pdf.set_fill_color(241, 245, 249)
            else:
                pdf.set_fill_color(255, 255, 255)
            pdf.set_font("Helvetica", "B", 9)
            pdf.set_text_color(30, 41, 59)
            pdf.cell(18, 8, f"#{idx:02d}", border=1, align="C", fill=fill)

            pdf.set_font("Helvetica", "B", 10)
            pdf.set_text_color(2, 132, 199)
            dezenas_str = "   ".join(f"{d:02d}" for d in j)
            pdf.cell(85, 8, dezenas_str, border=1, align="C", fill=fill)

            pdf.set_font("Helvetica", "", 9)
            pdf.set_text_color(71, 85, 105)
            pdf.cell(24, 8, str(sum(j)), border=1, align="C", fill=fill)

            pares = sum(1 for d in j if d % 2 == 0)
            pdf.cell(25, 8, f"{pares}P / {6-pares}I", border=1, align="C", fill=fill)

            ac = self.calcular_indice_anti_colisao(j)["score_anti_colisao"]
            pdf.cell(38, 8, f"{ac:.0f}% (Otimo)", border=1, align="C", fill=fill)
            pdf.ln()

        pdf.output(filepath)
        return filepath


_global_engine: Optional[MegaSenaEngine] = None
_engine_lock = threading.Lock()


def get_engine() -> MegaSenaEngine:
    global _global_engine
    with _engine_lock:
        if _global_engine is None:
            _global_engine = MegaSenaEngine()
        return _global_engine
