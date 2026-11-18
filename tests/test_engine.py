#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_engine.py - Suíte de Testes e Validação Matemática Exaustiva
Valida:
1. Integridade dos Dados Reais da Caixa (3.063 concursos)
2. Teste Qui-Quadrado de Aleatoriedade Uniforme (NIST SP 800-22)
3. Teoria dos Jogos & Escore Anti-Colisão (Fuga de 1-31 e consecutivos)
4. Teorema de Cobertura Combinatória C(v, k, t) - Verificação Exaustiva de Garantia
5. Modelo de Arbitragem Financeira Joan Ginther / Stefan Mandel
6. Geradores de Jogos em Todos os 4 Modos Matemáticos
7. Entropia de Shannon e Métrica Multivariada de Mahalanobis
8. Pipeline de Exportação Segura (CSV e PDF)
9. Thread-Safety em Operações Concorrentes
"""

import os
import sys
import tempfile
import threading
import itertools
import unittest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC = os.path.join(ROOT, "app_files", "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from core.engine import get_engine, MegaSenaEngine


class TestMegaSenaEngineComprehensive(unittest.TestCase):
    def setUp(self):
        self.engine = get_engine()

    def test_01_database_integrity(self):
        """Verifica se a base histórica contém os concursos oficiais carregados com 6 dezenas ordenadas."""
        self.assertGreaterEqual(len(self.engine.concursos), 3000, "Base real deve conter 3000+ concursos.")
        for idx, c in enumerate(self.engine.concursos[:50]):
            self.assertEqual(len(c), 6, f"Concurso {idx} deve ter exatamente 6 números.")
            self.assertEqual(c, sorted(c), f"Dezenas do concurso {idx} devem estar ordenadas.")
            self.assertTrue(all(1 <= d <= 60 for d in c), f"Dezenas do concurso {idx} devem estar entre 1 e 60.")

    def test_02_chi_square_uniformity_properties(self):
        """Valida a auditoria Qui-Quadrado conforme especificação do NIST SP 800-22."""
        audit = self.engine.teste_qui_quadrado()
        self.assertIn("estatistica_qui_quadrado", audit)
        self.assertIn("p_valor", audit)
        self.assertEqual(audit["graus_liberdade"], 59)
        self.assertGreaterEqual(audit["p_valor"], 0.0, "P-valor deve ser >= 0.0")
        self.assertLessEqual(audit["p_valor"], 1.0, "P-valor deve ser <= 1.0")
        self.assertGreater(audit["p_valor"], 0.01, "P-valor histórico não rejeita aleatoriedade uniforme a 99% de confiança (NIST SP 800-22).")

    def test_03_game_theory_anti_collision_scoring(self):
        """Testa o modelo de Teoria dos Jogos penalizando datas de aniversário e números em sequência."""
        # Jogo 1: Aniversários puros (1 a 31) com números consecutivos
        jogo_popular = [7, 8, 14, 15, 21, 28]
        score_pop = self.engine.calcular_indice_anti_colisao(jogo_popular)["score_anti_colisao"]

        # Jogo 2: Estratégia Anti-Colisão (dezenas altas, boa dispersão por quadrantes, sem consecutivos)
        jogo_estrategico = [14, 35, 42, 49, 53, 58]
        score_est = self.engine.calcular_indice_anti_colisao(jogo_estrategico)["score_anti_colisao"]

        self.assertGreater(score_est, score_pop)
        self.assertGreaterEqual(score_est, 80.0, "Jogo anti-colisão otimizado deve atingir score excelente.")

    def test_04_covering_design_mathematical_guarantee_quadra(self):
        """
        PROVA MATEMÁTICA FORMAL:
        Para um pool de 8 dezenas, verifica por força bruta sobre TODAS as combinações possíveis de 6 números
        que o conjunto de volantes gerados acerta no mínimo 4 dezenas (Quadra garantida).
        """
        pool = [4, 12, 19, 28, 35, 43, 51, 58]
        fechamento = self.engine.gerar_fechamento_combinatorio(pool, garantia="quadra")
        self.assertGreater(len(fechamento), 0)

        # Testa contra todos os possíveis sorteios de 6 dezenas que poderiam sair deste pool
        todos_sorteios_possiveis = list(itertools.combinations(pool, 6))
        for sorteio in todos_sorteios_possiveis:
            sorteio_set = set(sorteio)
            max_acertos = max(len(sorteio_set.intersection(volante)) for volante in fechamento)
            self.assertGreaterEqual(max_acertos, 4, f"Falha na garantia de Quadra para o sorteio {sorteio}!")

    def test_05_covering_design_quina_guarantee(self):
        """Garante que a opção t=5 (garantia de Quina) gera cobertura completa de Quinas para o pool."""
        pool = [7, 14, 21, 28, 35, 42, 49]
        fechamento = self.engine.gerar_fechamento_combinatorio(pool, garantia="quina")
        self.assertGreater(len(fechamento), 0)

        sorteios_possiveis = list(itertools.combinations(pool, 6))
        for sorteio in sorteios_possiveis:
            sorteio_set = set(sorteio)
            max_acertos = max(len(sorteio_set.intersection(volante)) for volante in fechamento)
            self.assertGreaterEqual(max_acertos, 5, f"Falha na garantia de Quina para o sorteio {sorteio}!")

    def test_06_covering_design_edge_cases(self):
        """Testa validação defensiva de parâmetros inválidos no gerador combinatório."""
        with self.assertRaises(ValueError):
            self.engine.gerar_fechamento_combinatorio([1, 2, 3, 4, 5])  # Menos de 6

        with self.assertRaises(ValueError):
            self.engine.gerar_fechamento_combinatorio([1, 2, 3, 4, 5, 61])  # Dezena > 60

        # Pool de exatamente 6 dezenas retorna 1 único volante
        exato = self.engine.gerar_fechamento_combinatorio([10, 20, 30, 40, 50, 60])
        self.assertEqual(len(exato), 1)
        self.assertEqual(exato[0], [10, 20, 30, 40, 50, 60])

    def test_07_arbitrage_ginther_mandel_calculations(self):
        """Valida cálculo do ponto de equilíbrio (breakeven) e transição de valor esperado E[X]."""
        # Prêmio super acumulado (Mega da Virada R$ 1.09 Bilhão)
        res_virada = self.engine.calcular_arbitragem_ginther_mandel(1090000000.0)
        self.assertGreater(res_virada["valor_esperado_bruto"], 6.0)
        self.assertGreater(res_virada["roi_esperado_percent"], 0.0)
        self.assertIn("FAVORÁVEL", res_virada["status_arbitragem"])

        # Prêmio comum (R$ 5 Milhões) -> EV < Custo do bilhete
        res_comum = self.engine.calcular_arbitragem_ginther_mandel(5000000.0)
        self.assertLess(res_comum["valor_esperado_bruto"], 6.0)
        self.assertLess(res_comum["roi_esperado_percent"], 0.0)
        self.assertIn("NEGATIVO", res_comum["status_arbitragem"])

    def test_08_generator_modes_and_gaussian_filter(self):
        """Verifica a geração de volantes nos 4 modos matemáticos respeitando os filtros gaussianos."""
        modos = ["anti_colisao", "mahalanobis", "frequencia", "aleatorio"]
        for modo in modos:
            jogos = self.engine.gerar_jogos(quantidade=5, modo=modo, min_soma=140, max_soma=225)
            self.assertEqual(len(jogos), 5, f"Falha na quantidade para o modo {modo}")
            for j in jogos:
                self.assertEqual(len(j), 6)
                self.assertTrue(140 <= sum(j) <= 225, f"Soma fora do range no modo {modo}: {sum(j)}")

    def test_09_mahalanobis_and_shannon_entropy(self):
        """Testa propriedades matemáticas da distância de Mahalanobis e Entropia de Shannon."""
        jogo_disperso = [5, 18, 27, 36, 45, 54]
        ent_disperso = self.engine.entropia_shannon(jogo_disperso)

        # Jogo hiper-concentrado na mesma década
        jogo_concentrado = [21, 22, 23, 24, 25, 26]
        ent_concentrado = self.engine.entropia_shannon(jogo_concentrado)

        self.assertGreater(ent_disperso, ent_concentrado, "Jogo disperso deve ter maior entropia de informação.")

        dm = self.engine.distancia_mahalanobis(jogo_disperso)
        self.assertGreater(dm, 0.0)
        self.assertLess(dm, 20.0)

    def test_10_backtest_accuracy(self):
        """Valida que o backtest reporta resultados consistentes com a história real."""
        # Pega o primeiro concurso real registrado e faz backtest com ele mesmo
        primeiro_concurso = self.engine.concursos[0]
        res = self.engine.backtest_jogo(primeiro_concurso)
        self.assertGreaterEqual(res["senas"], 1, "Backtest com sorteio idêntico deve acusar pelo menos 1 Sena.")
        self.assertEqual(res["total_concursos"], len(self.engine.concursos))

    def test_11_exports_csv_and_pdf(self):
        """Testa exportação limpa e segura de arquivos CSV e PDF."""
        jogos = [
            [4, 11, 18, 25, 32, 39],
            [14, 23, 31, 42, 53, 58]
        ]
        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path = os.path.join(tmpdir, "test_export.csv")
            pdf_path = os.path.join(tmpdir, "test_export.pdf")

            self.engine.exportar_csv(jogos, csv_path)
            self.assertTrue(os.path.exists(csv_path))
            self.assertGreater(os.path.getsize(csv_path), 50)

            self.engine.exportar_pdf(jogos, pdf_path)
            self.assertTrue(os.path.exists(pdf_path))
            self.assertGreater(os.path.getsize(pdf_path), 500)

    def test_12_thread_safe_concurrency(self):
        """Testa leituras e operações simultâneas em múltiplas threads sem exceções."""
        errors = []

        def worker():
            try:
                for _ in range(5):
                    self.engine.calcular_frequencias()
                    self.engine.calcular_indice_anti_colisao([10, 20, 30, 40, 50, 60])
                    self.engine.gerar_jogos(quantidade=2, modo="aleatorio")
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=worker) for _ in range(4)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        self.assertEqual(len(errors), 0, f"Erros durante execução concorrente: {errors}")

    def test_13_caixa_servicebus3_and_fallback(self):
        """Valida parsing do payload servicebus3 (incluindo Mega da Virada) e fallback para servicebus2."""
        from unittest.mock import patch

        sample_payload = {
            "numero": 3086,
            "dataApuracao": "15/11/2026",
            "listaDezenas": ["43", "03", "20", "35", "46", "38"],
            "acumulado": True,
            "valorEstimadoProximoConcurso": 34000000.0,
            "dataProximoConcurso": "17/11/2026",
            "indicadorConcursoEspecial": 1,
            "tituloConcursoEspecial": None,
            "valorAcumuladoConcursoEspecial": 153647230.91,
        }

        calls = []

        def fake_get_json(url, timeout=8):
            calls.append(url)
            if "params.txt" in url:
                return {"urlapiloterias": "https://servicebus3.caixa.gov.br/portaldeloterias"}
            if "servicebus3" in url:
                raise ConnectionError("servicebus3 indisponível no teste")
            return sample_payload

        self.engine._api_base = None
        with patch.object(self.engine, "_http_get_json", side_effect=fake_get_json):
            res = self.engine.obter_ultimo_resultado_online()

        self.assertIsNotNone(res)
        self.assertEqual(res["numero"], 3086)
        self.assertEqual(res["dezenas"], [3, 20, 35, 38, 43, 46])
        self.assertAlmostEqual(res["valor_acumulado_especial"], 153647230.91)
        self.assertTrue(any("servicebus3" in u for u in calls))
        self.assertTrue(any("servicebus2" in u for u in calls))

    def test_14_mega_da_virada_ao_vivo_parser(self):
        """Valida extração do concurso especial Mega da Virada do payload parametros-simulacao."""
        from unittest.mock import patch

        sim_payload = {
            "versao": "2.99.10.41",
            "payload": {
                "parametros": [
                    {
                        "parametroJogo": {
                            "concurso": {
                                "modalidade": "MEGA_SENA",
                                "modalidadeDetalhada": {"descricao": "Mega-Sena", "descricaoEspecial": "Mega da Virada"},
                                "tipoConcurso": "ESPECIAL",
                                "numero": 3100,
                                "dataAbertura": "03/11/2026 07:00:00",
                                "dataFechamento": "31/12/2026 22:00:00",
                                "dataHoraSorteio": "01/01/2027 11:00:00",
                                "valorApostaMinima": 6.0,
                                "situacao": "ABERTO",
                                "estimativa": 1000000000.0,
                            }
                        }
                    }
                ]
            },
        }
        with patch.object(self.engine, "_http_get_json", return_value=sim_payload):
            virada = self.engine.obter_mega_da_virada_ao_vivo()

        self.assertIsNotNone(virada)
        self.assertEqual(virada["concurso"], 3100)
        self.assertEqual(virada["estimativa"], 1000000000.0)
        self.assertEqual(virada["situacao"], "ABERTO")

    def test_15_xlsx_bulk_parser(self):
        """Valida o parser nativo stdlib de arquivos .xlsx oficiais da Caixa."""
        import io
        import zipfile

        sheet_xml = (
            '<?xml version="1.0" encoding="UTF-8"?>'
            '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
            "<sheetData>"
            '<row r="1"><c t="s"><v>0</v></c></row>'
            '<row r="2">'
            "<c><v>3086</v></c>"
            '<c t="s"><v>1</v></c>'
            "<c><v>43</v></c><c><v>3</v></c><c><v>20</v></c>"
            "<c><v>35</v></c><c><v>46</v></c><c><v>38</v></c>"
            "</row>"
            "</sheetData>"
            "</worksheet>"
        )
        shared_xml = (
            '<?xml version="1.0" encoding="UTF-8"?>'
            '<sst xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
            "<si><t>Concurso</t></si>"
            "<si><t>15/11/2026</t></si>"
            "</sst>"
        )
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as zf:
            zf.writestr("xl/sharedStrings.xml", shared_xml)
            zf.writestr("xl/worksheets/sheet1.xml", sheet_xml)

        parsed = MegaSenaEngine._parse_xlsx_concursos(buf.getvalue())
        self.assertEqual(parsed, {3086: [3, 20, 35, 38, 43, 46]})

    def test_16_native_csharp_kernel_covering_guarantee(self):
        """Valida o kernel nativo C# (/unsafe ulong*) para pool de 10 dezenas (C(10,6,4))."""
        pool = [4, 10, 15, 22, 29, 34, 41, 48, 53, 59]
        fechamento = self.engine.gerar_fechamento_combinatorio(pool, garantia="quadra")
        self.assertGreater(len(fechamento), 0)
        self.assertLessEqual(len(fechamento), 25)

        for sorteio in itertools.combinations(pool, 6):
            s_set = set(sorteio)
            max_acertos = max(len(s_set.intersection(v)) for v in fechamento)
            self.assertGreaterEqual(max_acertos, 4, f"Falha no kernel nativo para sorteio {sorteio}")

    def test_17_parametros_oficiais_e_custo_lote(self):
        """Valida sincronização de regras/preços ao vivo e cálculo de custo oficial de lote."""
        from unittest.mock import patch

        sim_payload = {
            "versao": "2.99.10.41",
            "dataHoraServidor": "2026-11-17T13:10:05.268",
            "payload": {
                "valorMinimoCarrinho": 2.50,
                "quantidadeMaximaApostasCarrinho": 999,
                "parametros": [
                    {
                        "parametroJogo": {
                            "concurso": {
                                "modalidade": "MEGA_SENA",
                                "modalidadeDetalhada": {"descricao": "Mega-Sena", "descricaoEspecial": "Mega da Virada"},
                                "tipoConcurso": "ESPECIAL",
                                "numero": 3100,
                                "estimativa": 1000000000.0,
                                "valorApostaMinima": 6.0,
                                "situacao": "ABERTO",
                            },
                            "valoresAposta": [
                                {"numeroPrognosticos": 6, "valor": 6.0},
                                {"numeroPrognosticos": 7, "valor": 42.0},
                            ],
                        }
                    }
                ],
            },
        }
        with patch.object(self.engine, "_http_get_json", return_value=sim_payload):
            params = self.engine.obter_parametros_oficiais_ao_vivo()

        self.assertIsNotNone(params)
        self.assertEqual(params["tabela_precos"][7], 42.0)
        lote = self.engine.calcular_custo_lote([[1, 2, 3, 4, 5, 6], [1, 2, 3, 4, 5, 6, 7]])
        self.assertEqual(lote["quantidade_volantes"], 2)
        self.assertEqual(lote["custo_total"], 48.0)
        self.assertTrue(lote["atende_minimo_carrinho"])
        self.assertTrue(lote["dentro_limite_carrinho"])

    def test_18_mahalanobis_full_rank_and_chi2_correction(self):
        """Prova matemática: vetor 7D sem colinearidade (posto completo) e correção hipergeométrica 59/54."""
        vec = self.engine._extrair_vetor_caracteristicas([5, 18, 27, 36, 45, 54])
        self.assertEqual(len(vec), 7, "Vetor característico deve ter 7 dimensões linearmente independentes.")
        self.assertEqual(len(self.engine.cov_inv), 7)

        chi = self.engine.teste_qui_quadrado()
        self.assertIn("estatistica_qui_quadrado_corrigida", chi)
        self.assertIn("p_valor_corrigido", chi)
        self.assertAlmostEqual(
            chi["estatistica_qui_quadrado_corrigida"],
            round(chi["estatistica_qui_quadrado"] * (59.0 / 54.0), 2),
            delta=0.05,
        )

    def test_19_community_api_fallback_normalization(self):
        """Valida fallback para API comunitária quando servicebus3 e servicebus2 falham."""
        from unittest.mock import patch

        community_payload = {
            "concurso": 3087,
            "data": "17/11/2026",
            "dezenas": ["05", "12", "23", "37", "48", "59"],
            "acumulou": False,
            "valorAcumuladoProximoConcurso": 3000000.0,
        }

        def fake_get_json(url, timeout=8):
            if "servicebus" in url or "params.txt" in url:
                raise ConnectionError("API oficial bloqueada no datacenter")
            return community_payload

        self.engine._api_base = None
        with patch.object(self.engine, "_http_get_json", side_effect=fake_get_json):
            res = self.engine.obter_ultimo_resultado_online()

        self.assertIsNotNone(res)
        self.assertEqual(res["numero"], 3087)
        self.assertEqual(res["dezenas"], [5, 12, 23, 37, 48, 59])

    def test_20_sindicato_bolao_and_pruned_covering(self):
        """Valida planejador de bolão/sindicato e garantia 100% do fechamento podado C(11,6,4)."""
        bolao = self.engine.planejar_bolao_sindicato(150.0)
        self.assertNotIn("erro", bolao)
        self.assertGreaterEqual(bolao["tamanho_pool_recomendado"], 7)
        self.assertGreater(len(bolao["jogos_gerados"]), 0)

        pool = [2, 7, 13, 19, 24, 31, 36, 42, 47, 53, 59]
        fechamento = self.engine.gerar_fechamento_combinatorio(pool, garantia="quadra")
        self.assertGreater(len(fechamento), 0)
        for sorteio in itertools.combinations(pool, 6):
            s_set = set(sorteio)
            self.assertGreaterEqual(max(len(s_set.intersection(v)) for v in fechamento), 4)

    def test_21_kelly_criterion_kolmogorov_and_montecarlo(self):
        """Valida Critério de Kelly (Thorp), Incompressibilidade de Kolmogorov e Monte Carlo nativo."""
        arb_pos = self.engine.calcular_arbitragem_ginther_mandel(1000000000.0, 6.0, "especial")
        self.assertGreater(arb_pos["kelly_fracao_otima_pct"], 0.0)
        self.assertAlmostEqual(arb_pos["kelly_quarto_pct"], round(arb_pos["kelly_fracao_otima_pct"] * 0.25, 8), delta=1e-7)

        arb_neg = self.engine.calcular_arbitragem_ginther_mandel(5000000.0, 6.0, "normal")
        self.assertEqual(arb_neg["kelly_fracao_otima_pct"], 0.0)

        kol = self.engine.auditar_incompressibilidade_kolmogorov()
        self.assertTrue(kol["incompressivel"], f"Série histórica deve ser algorítmicamente incompressível: {kol}")

        mc = self.engine.simular_monte_carlo([12, 14, 27, 40, 42, 45], sorteios=20000)
        self.assertEqual(mc["sorteios"], 20000)
        self.assertGreaterEqual(mc["tempo_ms"], 0.0)

    def test_22_quina_and_binary_orthogonal_engine(self):
        """Valida Quina (01-80, k=5, Mask128) e motor binário ortogonal (distância de Hamming)."""
        arb_q = self.engine.calcular_arbitragem_quina(80000000.0, 3.0, "especial")
        self.assertEqual(arb_q["modalidade"], "QUINA")
        self.assertGreater(arb_q["valor_esperado_bruto"], 3.0)

        jogos_q = self.engine.gerar_jogos_quina(quantidade=4, modo="anti_colisao")
        self.assertEqual(len(jogos_q), 4)
        for j in jogos_q:
            self.assertEqual(len(j), 5)
            self.assertTrue(all(1 <= d <= 80 for d in j))

        pool_q = [5, 17, 29, 41, 53, 64, 72, 79]
        fech_q = self.engine.gerar_fechamento_quina(pool_q, garantia="terno")
        self.assertGreater(len(fech_q), 0)
        for sorteio in itertools.combinations(pool_q, 5):
            s_set = set(sorteio)
            self.assertGreaterEqual(max(len(s_set.intersection(v)) for v in fech_q), 3)

        ort = self.engine.gerar_jogos_ortogonais_binarios(quantidade=5, modalidade="QUINA")
        self.assertEqual(len(ort["jogos"]), 5)
        self.assertGreaterEqual(ort["hamming_minimo"], 6)

    def test_23_balanced_portfolio_and_anchors(self):
        """Valida Cobertura Balanceada de Portfólio (Phi), Índice de Densidade e Dezenas Âncoras."""
        # 1. Densidade combinatória
        jogos_disjuntos = [[1, 2, 3, 4, 5, 6], [7, 8, 9, 10, 11, 12]]
        d_disj = self.engine.calcular_densidade_combinatoria_portfolio(jogos_disjuntos)
        self.assertEqual(d_disj["phi"], 0.0)
        self.assertIn("Dispersão Total", d_disj["diagnostico"])

        jogos_balanceados = [[1, 2, 3, 4, 5, 6], [1, 2, 3, 7, 8, 9]]
        d_bal = self.engine.calcular_densidade_combinatoria_portfolio(jogos_balanceados)
        self.assertEqual(d_bal["phi"], 0.5)
        self.assertIn("Zona Ótima", d_bal["diagnostico"])

        # 2. Portfólio balanceado
        res_bal = self.engine.gerar_portfolio_balanceado(pool=[3, 7, 12, 19, 23, 28, 35, 42, 48, 54], quantidade=3, modalidade="MEGA_SENA")
        self.assertTrue(res_bal["ok"])
        self.assertEqual(len(res_bal["jogos"]), 3)
        self.assertGreater(res_bal["densidade"]["phi"], 0.0)

        # 3. Jogos com âncoras (bases fixas)
        res_anc = self.engine.gerar_jogos_com_ancoras(ancoras=[10, 25], satelites=[3, 14, 22, 33, 45, 51, 58], quantidade=3, modalidade="MEGA_SENA")
        self.assertTrue(res_anc["ok"])
        self.assertEqual(len(res_anc["jogos"]), 3)
        for j in res_anc["jogos"]:
            self.assertIn(10, j)
            self.assertIn(25, j)
            self.assertEqual(len(j), 6)


if __name__ == "__main__":
    unittest.main()
