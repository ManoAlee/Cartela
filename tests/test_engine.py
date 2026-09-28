import os
import sys
import unittest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC = os.path.join(ROOT, "app_files", "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from core.engine import get_engine


class TestMegaSenaEngine(unittest.TestCase):
    def setUp(self):
        self.engine = get_engine()

    def test_database_loaded_real(self):
        self.assertGreaterEqual(len(self.engine.concursos), 3000, "Base de dados real deve ter pelo menos 3000 concursos.")

    def test_chi_square_goodness_of_fit(self):
        audit = self.engine.teste_qui_quadrado()
        self.assertIn("estatistica_qui_quadrado", audit)
        self.assertIn("p_valor", audit)
        self.assertGreater(audit["p_valor"], 0.01, "P-valor deve ser consistente com aleatoriedade estatística.")

    def test_anti_collision_scoring(self):
        # Aposta típica de aniversário (datas de 1 a 31)
        jogo_aniversario = [2, 5, 12, 19, 25, 30]
        score_aniv = self.engine.calcular_indice_anti_colisao(jogo_aniversario)["score_anti_colisao"]

        # Aposta otimizada anti-colisão (dezenas altas, bem dispersas)
        jogo_anti_colisao = [14, 34, 42, 49, 53, 58]
        score_otimo = self.engine.calcular_indice_anti_colisao(jogo_anti_colisao)["score_anti_colisao"]

        self.assertGreater(score_otimo, score_aniv, "Aposta dispersa deve ter score anti-colisão maior que aniversário.")

    def test_covering_designs(self):
        pool = [5, 10, 15, 23, 34, 42, 48, 55, 59]  # 9 dezenas
        fechamento = self.engine.gerar_fechamento_combinatorio(pool, garantia="quadra")
        self.assertGreater(len(fechamento), 0)
        for j in fechamento:
            self.assertEqual(len(j), 6)
            self.assertTrue(set(j).issubset(set(pool)))

    def test_mahalanobis_distance(self):
        jogo_equilibrado = [5, 18, 27, 36, 45, 54]
        dm = self.engine.distancia_mahalanobis(jogo_equilibrado)
        self.assertGreater(dm, 0.0)
        self.assertLess(dm, 15.0)

    def test_backtest_execution(self):
        res = self.engine.backtest_jogo([5, 10, 20, 30, 40, 50])
        self.assertIn("quadras", res)
        self.assertIn("quinas", res)
        self.assertIn("senas", res)


if __name__ == "__main__":
    unittest.main()
