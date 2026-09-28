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


if __name__ == "__main__":
    unittest.main()
