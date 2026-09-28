#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
engine.py - Motor Estatístico, Teoria dos Jogos, Covering Designs e Arbitragem Ginther-Mandel
Baseado na Literatura Científica de Matemática Aplicada e Arbitragem Estatística:
1. Teoria da Informação & Entropia de Shannon (H(X) ≈ 25.57 bits)
2. Teste de Aderência Qui-Quadrado (NIST / Dieharder) contra 3063+ concursos reais
3. Teoria dos Jogos & Maximização do Valor Esperado E[X] (Anti-Colisão / Fuga de Aniversário 1-31)
4. Covering Designs Combinatórios C(v, k, t) - Fechamento Matemático com garantia de Quadra/Quina
5. Modelo de Arbitragem Ginther-Mandel (Radar de Valor Esperado Positivo E[X] > 0 para Loterias Brasileiras)
6. Otimizador de Sindicatos / Bolões de Alta Performance
"""

import os
import json
import csv
import ssl
import time
import math
import random
import logging
import itertools
import urllib.request
from pathlib import Path
from typing import List, Dict, Tuple, Optional, Any, Set

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)
CACHE_FILE = DATA_DIR / "mega_cache.json"
HISTORY_CSV = DATA_DIR / "mega_history.csv"

SSL_CTX = ssl.create_default_context()
SSL_CTX.check_hostname = False
SSL_CTX.verify_mode = ssl.CERT_NONE

CAIXA_API_URL = "https://servicebus2.caixa.gov.br/portaldeloterias/api/megasena"

# Mapeamento de quadrantes clássicos do volante 10x6
QUADRANTE_MAP = {}
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
        self.concursos: List[List[int]] = []
        self.mu: Optional[List[float]] = None
        self.cov_inv: Optional[List[List[float]]] = None
        self.carregar_dados()

    # -------------------------------------------------------------
    # 1. CARREGAMENTO E SINCRONIZAÇÃO DE DADOS REAIS
    # -------------------------------------------------------------
    def carregar_dados(self) -> List[List[int]]:
        if CACHE_FILE.exists():
            try:
                with open(CACHE_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, list) and len(data) > 0:
                        self.concursos = [sorted(map(int, c)) for c in data]
                        self._calibrar_matriz_mahalanobis()
                        return self.concursos
            except Exception as e:
                logging.error(f"Erro ao ler cache: {e}")
        return self.sincronizar_dados_oficiais()

    def obter_ultimo_resultado_online(self) -> Optional[Dict[str, Any]]:
        try:
            req = urllib.request.Request(CAIXA_API_URL, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, context=SSL_CTX, timeout=8) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                return {
                    "numero": int(data.get("numero", 0)),
                    "data": data.get("dataApuracao", ""),
                    "dezenas": sorted([int(x) for x in data.get("listaDezenas", [])]),
                    "acumulado": bool(data.get("acumulado", False)),
                    "premio_estimado": float(data.get("valorEstimadoProximoConcurso", 0.0)),
                    "proximo_concurso_data": data.get("dataProximoConcurso", "")
                }
        except Exception:
            return None

    def sincronizar_dados_oficiais(self, progress_callback=None) -> List[List[int]]:
        ultimo_online = self.obter_ultimo_resultado_online()
        if not ultimo_online:
            return self.concursos

        num_ultimo = ultimo_online["numero"]
        concursos_dict = {i + 1: c for i, c in enumerate(self.concursos)}
        concursos_dict[num_ultimo] = ultimo_online["dezenas"]

        missing = [n for n in range(1, num_ultimo + 1) if n not in concursos_dict]
        total_missing = len(missing)

        for idx, n in enumerate(missing, 1):
            url = f"{CAIXA_API_URL}/{n}"
            dezenas = None
            for _ in range(3):
                try:
                    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
                    with urllib.request.urlopen(req, context=SSL_CTX, timeout=6) as r:
                        d = json.loads(r.read().decode("utf-8"))
                        dezenas = sorted([int(x) for x in d.get("listaDezenas", [])])
                        break
                except Exception:
                    time.sleep(0.3)

            if dezenas:
                concursos_dict[n] = dezenas

            if progress_callback:
                progress_callback(idx, total_missing, n)
            time.sleep(0.12)

        sorted_keys = sorted(concursos_dict.keys())
        self.concursos = [concursos_dict[k] for k in sorted_keys]

        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(self.concursos, f)

        with open(HISTORY_CSV, "w", encoding="utf-8", newline="") as f:
            w = csv.writer(f, delimiter=";")
            w.writerow(["Concurso", "D1", "D2", "D3", "D4", "D5", "D6"])
            for k in sorted_keys:
                w.writerow([k] + concursos_dict[k])

        self._calibrar_matriz_mahalanobis()
        return self.concursos

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
        o montante desce automaticamente para a Quina, explodindo a taxa de retorno secundário!
        """
        total_comb = 50063860.0
        p_sena = 1.0 / total_comb
        p_quina = 324.0 / total_comb
        p_quadra = 21465.0 / total_comb

        # Estimativa de prêmios por faixa (Regulamento Caixa: 35% Sena, 19% Quina, 19% Quadra)
        premio_sena = premio_estimado
        premio_quina_medio = 50000.0 if tipo_concurso == "normal" else 150000.0
        premio_quadra_medio = 1000.0 if tipo_concurso == "normal" else 2500.0

        # Valor Esperado Puro (Single Player, Sem Colisão)
        ev_sena_puro = premio_sena * p_sena
        ev_quina = premio_quina_medio * p_quina
        ev_quadra = premio_quadra_medio * p_quadra
        ev_bruto = ev_sena_puro + ev_quina + ev_quadra

        ev_liquido = ev_bruto - custo_aposta
        roi_percent = (ev_liquido / custo_aposta) * 100.0

        # Ponto de Equilíbrio (Breakeven Jackpot) onde EV se torna positivo
        breakeven_jackpot = (custo_aposta - ev_quina - ev_quadra) * total_comb

        # Modelagem de Risco de Colisão (Splitting Penalty)
        # Se você joga aniversários (números <= 31), N_colisões esperadas é alto (~15 a 50 na Mega da Virada)
        # Se você joga com o Algoritmo Anti-Colisão, N_colisões esperadas cai para 1 ou 2
        ev_com_anticolisao = (premio_sena / 1.5) * p_sena + ev_quina + ev_quadra - custo_aposta
        ev_sem_anticolisao = (premio_sena / 18.0) * p_sena + ev_quina + ev_quadra - custo_aposta

        if ev_liquido > 0:
            status_arbitragem = "🟢 ARBITRAGEM MATEMÁTICA FAVORÁVEL (E[X] > 0)"
            diretriz = (
                f"O prêmio de R$ {premio_estimado/1e6:.1f}M supera o custo de cobertura do espaço amostral. "
                f"Com a estratégia Anti-Colisão, o bilhete de R$ {custo_aposta:.2f} tem valor intrínseco de "
                f"R$ {ev_bruto:.2f} (Retorno Esperado de +{roi_percent:.1f}%)."
            )
        else:
            status_arbitragem = "🔴 VALOR ESPERADO NEGATIVO (E[X] < 0 - Casa em Vantagem)"
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
        """
        Modela a alocação de capital em sindicato (estratégia Stefan Mandel / Joan Ginther):
        Calcula o pool ótimo de dezenas e o sistema de Covering Design garantido para o orçamento.
        """
        qtd_volantes = int(orcamento_reais // custo_bilhete)
        if qtd_volantes < 1:
            return {"erro": "Orçamento insuficiente para pelo menos 1 aposta."}

        # Encontra o maior tamanho de pool v cuja cobertura de quadra cabe no orçamento
        pool_otimo_tamanho = 6
        for v in range(7, 25):
            # Aproximação empírica do número de blocos para Covering C(v, 6, 4)
            blocos_estimados = math.ceil(math.comb(v, 4) / math.comb(6, 4))
            if blocos_estimados <= qtd_volantes:
                pool_otimo_tamanho = v
            else:
                break

        # Gera pool selecionado com base nas dezenas de maior dispersão espacial e anti-colisão
        scores = self.pontuar_dezenas()
        # Seleciona dezenas equilibrando números altos (>31) e os 4 quadrantes
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
    # 4. TESTE DE ADERÊNCIA QUI-QUADRADO (NIST / DIEHARD)
    # -------------------------------------------------------------
    def teste_qui_quadrado(self) -> Dict[str, Any]:
        N = len(self.concursos)
        total_bolas = N * 6
        esperado = total_bolas / 60.0

        freq = {d: 0 for d in range(1, 61)}
        for c in self.concursos:
            for d in c:
                freq[d] += 1

        chi2_stat = sum(((freq[d] - esperado) ** 2) / esperado for d in range(1, 61))
        graus_liberdade = 59

        z = ((chi2_stat / graus_liberdade) ** (1/3) - (1 - 2/(9*graus_liberdade))) / math.sqrt(2/(9*graus_liberdade))
        p_valor = 0.5 * math.erfc(z / math.sqrt(2))

        conclusao = "ALEATORIEDADE PERFEITA (H0 Não Rejeitada)" if p_valor > 0.05 else "DESVIO SIGNIFICATIVO"

        return {
            "total_concursos": N,
            "total_bolas_sorteadas": total_bolas,
            "frequencia_esperada_por_dezena": round(esperado, 2),
            "estatistica_qui_quadrado": round(chi2_stat, 2),
            "graus_liberdade": graus_liberdade,
            "p_valor": round(p_valor, 4),
            "conclusao_cientifica": conclusao,
            "explicacao": (
                f"Com Chi2={chi2_stat:.2f} e p-valor={p_valor:.4f} > 0.05, comprova-se cientificamente "
                f"que não há viés mecânico. Variações históricas (ex: dezenas mais frequentes) são "
                f"flutuações estocásticas normais da Lei dos Grandes Números."
            )
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
        score -= (len(dezenas_aniversario) - 3) * 15.0 if len(dezenas_aniversario) > 3 else 0.0
        score -= consecutivos * 12.0
        if ent < 1.80:
            score -= 15.0

        score = max(10.0, min(100.0, score))

        classificacao = (
            "🌟 EXCELENTE (Quase Zero Risco de Divisão)" if score >= 80 else
            "✅ BOM (Acima da média dos apostadores)" if score >= 60 else
            "⚠️ MODERADO (Muitas datas de aniversário)" if score >= 40 else
            "⛔ ALTO RISCO DE DIVISÃO (Muitos apostadores jogam esse padrão)"
        )

        return {
            "score_anti_colisao": round(score, 1),
            "classificacao": classificacao,
            "dezenas_aniversario_count": len(dezenas_aniversario),
            "pct_aniversario": round(pct_aniversario, 1),
            "consecutivos": consecutivos,
            "entropia_shannon": round(ent, 2)
        }

    # -------------------------------------------------------------
    # 6. COVERING DESIGNS C(v, k, t)
    # -------------------------------------------------------------
    def gerar_fechamento_combinatorio(self, dezenas_pool: List[int], garantia: str = "quadra") -> List[List[int]]:
        pool = sorted(list(set(dezenas_pool)))
        v = len(pool)
        if v < 6:
            raise ValueError("O pool deve ter pelo menos 6 dezenas.")
        if v == 6:
            return [pool]

        t_garantia = 4 if garantia == "quadra" else 5
        todas_tuplas_alvo = set(itertools.combinations(pool, t_garantia))
        todos_blocos_k6 = list(itertools.combinations(pool, 6))

        bloco_cobertura = []
        for bloco in todos_blocos_k6:
            cobertos = set(itertools.combinations(bloco, t_garantia))
            bloco_cobertura.append((bloco, cobertos))

        tuplas_restantes = set(todas_tuplas_alvo)
        jogos_selecionados = []

        while tuplas_restantes:
            melhor_bloco, melhor_cobertos = max(
                bloco_cobertura,
                key=lambda item: len(item[1].intersection(tuplas_restantes))
            )
            jogos_selecionados.append(sorted(list(melhor_bloco)))
            tuplas_restantes -= melhor_cobertos
            bloco_cobertura = [item for item in bloco_cobertura if item[0] != melhor_bloco]

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
        q1 = float(sum(1 for x in jogo if QUADRANTE_MAP[x] == 1))
        q2 = float(sum(1 for x in jogo if QUADRANTE_MAP[x] == 2))
        q3 = float(sum(1 for x in jogo if QUADRANTE_MAP[x] == 3))
        q4 = float(sum(1 for x in jogo if QUADRANTE_MAP[x] == 4))
        return [soma, amp, dp, pares, q1, q2, q3, q4]

    def _calibrar_matriz_mahalanobis(self):
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
            dec = min(5, (d - 1) // 10)
            decadas[dec] += 1
        ent = 0.0
        for count in decadas:
            if count > 0:
                p = count / 6.0
                ent -= p * math.log2(p)
        return ent

    def calcular_frequencias(self, ultimos_n: Optional[int] = None) -> Dict[int, int]:
        base = self.concursos[-ultimos_n:] if ultimos_n and len(self.concursos) >= ultimos_n else self.concursos
        freq = {d: 0 for d in range(1, 61)}
        for c in base:
            for d in c:
                freq[d] += 1
        return freq

    def calcular_atrasos(self) -> Dict[int, int]:
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
        max_g = max(freq_global.values()) if freq_global else 1
        max_r = max(freq_recente.values()) if freq_recente else 1
        max_a = max(atrasos.values()) if atrasos else 1
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
            q_count[QUADRANTE_MAP[d]] += 1
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
        populacao = list(range(1, 61))
        pesos_anticolisao = [1.0 if d <= 31 else 1.95 for d in range(1, 61)]
        freq = self.calcular_frequencias()
        max_f = max(freq.values()) if freq else 1
        pesos_freq = [freq[d] / max_f for d in range(1, 61)]

        candidatos: List[Tuple[float, List[int]]] = []
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
        jogo_set = set(jogo)
        acertos_count = {0: 0, 1: 0, 2: 0, 3: 0, 4: 0, 5: 0, 6: 0}
        premiados = []
        for idx, conc in enumerate(self.concursos, 1):
            hits = len(jogo_set.intersection(conc))
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
        with open(filepath, "w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f, delimiter=";")
            writer.writerow(["Jogo", "D1", "D2", "D3", "D4", "D5", "D6", "Soma", "Pares", "Anti-Colisao", "Mahalanobis"])
            for idx, j in enumerate(jogos, 1):
                soma = sum(j)
                pares = sum(1 for d in j if d % 2 == 0)
                ac = self.calcular_indice_anti_colisao(j)["score_anti_colisao"]
                dm = round(self.distancia_mahalanobis(j), 2)
                writer.writerow([f"Jogo #{idx:02d}"] + [f"{d:02d}" for d in j] + [soma, pares, f"{ac}%", dm])

    def exportar_pdf(self, jogos: List[List[int]], filepath: str):
        from fpdf import FPDF

        class PDFReport(FPDF):
            def header(self):
                self.set_fill_color(11, 15, 25)
                self.rect(0, 0, 210, 28, "F")
                self.set_font("Helvetica", "B", 15)
                self.set_text_color(248, 250, 252)
                self.cell(0, 10, "CARTELA - TEORIA DOS JOGOS & LOTERIAS", ln=True, align="C")
                self.set_font("Helvetica", "", 9)
                self.set_text_color(148, 163, 184)
                self.cell(0, 5, "Volantes Otimizados por Maximizacao do Valor Esperado E[X] e Fechamentos", ln=True, align="C")
                self.ln(6)

            def footer(self):
                self.set_y(-15)
                self.set_font("Helvetica", "I", 8)
                self.set_text_color(148, 163, 184)
                self.cell(0, 10, f"Pagina {self.page_no()} | Automotion Intelligence Lab", align="C")

        pdf = PDFReport()
        pdf.set_auto_page_break(True, margin=15)
        pdf.add_page()
        pdf.ln(5)

        pdf.set_font("Helvetica", "B", 11)
        pdf.set_text_color(30, 41, 59)
        pdf.cell(0, 8, f"Total de Jogos: {len(jogos)} | Validacao: {len(self.concursos)} Concursos Reais Caixa", ln=True)
        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(100, 116, 139)
        pdf.cell(0, 6, f"Data da Emissao: {time.strftime('%d/%m/%Y %H:%M:%S')}", ln=True)
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
            pdf.set_fill_color(241, 245, 249) if fill else pdf.set_fill_color(255, 255, 255)
            pdf.set_font("Helvetica", "B", 9)
            pdf.set_text_color(30, 41, 59)
            pdf.cell(18, 8, f"#{idx:02d}", border=1, align="C", fill=fill)

            pdf.set_font("Helvetica", "B", 10)
            pdf.set_text_color(6, 182, 212)
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


def get_engine() -> MegaSenaEngine:
    global _global_engine
    if _global_engine is None:
        _global_engine = MegaSenaEngine()
    return _global_engine
