#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
engine_cli.py - Ponte JSON assíncrona entre a interface nativa C# WPF (CartelaUI.exe)
e o motor matemático MegaSenaEngine.
"""

import json
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stdin, "reconfigure"):
    sys.stdin.reconfigure(encoding="utf-8")

SRC_DIR = Path(__file__).resolve().parent.parent
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from core.engine import get_engine  # noqa: E402


def main() -> int:
    if len(sys.argv) < 2:
        print(json.dumps({"ok": False, "error": "Comando ausente"}))
        return 1

    cmd = sys.argv[1]
    payload = {}
    if len(sys.argv) >= 3 and sys.argv[2].strip():
        if sys.argv[2].strip() == "-":
            raw_in = sys.stdin.read().strip()
            if raw_in:
                payload = json.loads(raw_in)
        else:
            payload = json.loads(sys.argv[2])

    engine = get_engine()

    try:
        if cmd == "status":
            ultimo = engine.obter_ultimo_resultado_online()
            params = engine.obter_parametros_oficiais_ao_vivo()
            out = {
                "ok": True,
                "total_concursos": len(engine.concursos),
                "ultimo": ultimo,
                "params": params,
            }
        elif cmd == "gerar":
            qtd = int(payload.get("quantidade", 6))
            modo = str(payload.get("modo", "anti_colisao"))
            min_soma = int(payload.get("min_soma", 140))
            max_soma = int(payload.get("max_soma", 225))
            jogos = engine.gerar_jogos(quantidade=qtd, modo=modo, min_soma=min_soma, max_soma=max_soma)
            itens = []
            for j in jogos:
                ac = engine.calcular_indice_anti_colisao(j)["score_anti_colisao"]
                dm = engine.distancia_mahalanobis(j)
                ent = engine.entropia_shannon(j)
                itens.append({
                    "dezenas": j,
                    "soma": sum(j),
                    "score": round(ac, 1),
                    "mahalanobis": round(dm, 2),
                    "entropia": round(ent, 2),
                })
            lote = engine.calcular_custo_lote(jogos)
            out = {"ok": True, "jogos": itens, "lote": lote}
        elif cmd == "fechamento":
            pool = [int(x) for x in payload.get("pool", [])]
            garantia = str(payload.get("garantia", "quadra"))
            jogos = engine.gerar_fechamento_combinatorio(pool, garantia=garantia)
            itens = [
                {
                    "dezenas": j,
                    "soma": sum(j),
                    "score": round(engine.calcular_indice_anti_colisao(j)["score_anti_colisao"], 1),
                }
                for j in jogos
            ]
            lote = engine.calcular_custo_lote(jogos)
            out = {"ok": True, "jogos": itens, "lote": lote}
        elif cmd == "arbitragem":
            premio = float(payload.get("premio", 1000000000.0))
            res = engine.calcular_arbitragem_ginther_mandel(premio)
            out = {"ok": True, "resultado": res}
        elif cmd == "backtest":
            jogo = sorted([int(x) for x in payload.get("jogo", [])])
            res = engine.backtest_jogo(jogo)
            out = {"ok": True, "resultado": res}
        elif cmd == "sync":
            concursos = engine.sincronizar_dados_oficiais()
            ultimo = engine.obter_ultimo_resultado_online()
            params = engine.obter_parametros_oficiais_ao_vivo()
            out = {
                "ok": True,
                "total_concursos": len(concursos),
                "ultimo": ultimo,
                "params": params,
            }
        elif cmd == "export_csv":
            jogos = payload.get("jogos", [])
            filepath = str(payload.get("filepath", ""))
            engine.exportar_csv(jogos, filepath)
            out = {"ok": True, "filepath": filepath}
        elif cmd == "export_pdf":
            jogos = payload.get("jogos", [])
            filepath = str(payload.get("filepath", ""))
            res_path = engine.exportar_pdf(jogos, filepath)
            out = {"ok": True, "filepath": res_path}
        elif cmd == "heatmap":
            freq = engine.calcular_frequencias()
            atrasos = engine.calcular_atrasos()
            chi = engine.teste_qui_quadrado()
            out = {
                "ok": True,
                "frequencias": {str(k): v for k, v in freq.items()},
                "atrasos": {str(k): v for k, v in atrasos.items()},
                "chi2": chi,
            }
        elif cmd == "bolao":
            orcamento = float(payload.get("orcamento", 150.0))
            res = engine.planejar_bolao_sindicato(orcamento)
            out = {"ok": True, "resultado": res}
        elif cmd == "montecarlo":
            jogo = [int(x) for x in payload.get("jogo", [12, 14, 27, 40, 42, 45])]
            sorteios = int(payload.get("sorteios", 100000))
            res = engine.simular_monte_carlo(jogo, sorteios=sorteios)
            out = {"ok": True, "resultado": res}
        elif cmd == "kolmogorov":
            res = engine.auditar_incompressibilidade_kolmogorov()
            out = {"ok": True, "resultado": res}
        elif cmd == "ortogonal":
            qtd = int(payload.get("quantidade", 6))
            mod = str(payload.get("modalidade", "MEGA_SENA"))
            res = engine.gerar_jogos_ortogonais_binarios(quantidade=qtd, modalidade=mod)
            out = {"ok": True, "resultado": res}
        elif cmd == "quina_status":
            ultimo = engine.obter_ultimo_resultado_online("QUINA")
            out = {"ok": True, "ultimo": ultimo}
        elif cmd == "quina_gerar":
            qtd = int(payload.get("quantidade", 6))
            modo = str(payload.get("modo", "anti_colisao"))
            jogos = engine.gerar_jogos_quina(quantidade=qtd, modo=modo)
            out = {"ok": True, "jogos": jogos}
        elif cmd == "quina_fechamento":
            pool = [int(x) for x in payload.get("pool", [])]
            gar = str(payload.get("garantia", "terno"))
            jogos = engine.gerar_fechamento_quina(pool, garantia=gar)
            out = {"ok": True, "jogos": jogos}
        elif cmd == "quina_arbitragem":
            premio = float(payload.get("premio", 14500000.0))
            res = engine.calcular_arbitragem_quina(premio)
            out = {"ok": True, "resultado": res}
        else:
            out = {"ok": False, "error": f"Comando desconhecido: {cmd}"}
    except Exception as exc:
        out = {"ok": False, "error": str(exc)}

    print(json.dumps(out, ensure_ascii=False))
    return 0 if out.get("ok") else 1


if __name__ == "__main__":
    sys.exit(main())
