#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gui.py - Interface Gráfica Moderna (Dark Theme / Glassmorphic) para CartelaApp
Incorpora a Teoria dos Jogos, Covering Designs C(v, k, t), Teste Chi-Quadrado NIST
e sincronização em tempo real com a Caixa Econômica Federal.
"""

import sys
import os
import threading
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from typing import List, Optional

# Garante resolução de imports
SRC_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from core.engine import get_engine, MegaSenaEngine


class CartelaApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Cartela - Advanced Lottery Analytics & Mathematical Engine")
        self.geometry("1150x780")
        self.minsize(1020, 700)

        # Paleta Dark Mode / Glassmorphism
        self.c_bg = "#0b0f19"          # Deep Space Navy
        self.c_card = "#151d30"        # Glass Card Navy
        self.c_card_light = "#222f4c"  # Card Hover/Input
        self.c_accent = "#06b6d4"      # Cyan 500
        self.c_emerald = "#10b981"     # Emerald 500
        self.c_purple = "#a855f7"      # Purple 500 (Covering Designs)
        self.c_amber = "#f59e0b"       # Amber 500
        self.c_text = "#f8fafc"        # Slate 50
        self.c_muted = "#94a3b8"       # Slate 400
        self.c_highlight = "#38bdf8"   # Sky 400

        self.configure(bg=self.c_bg)

        self.engine = get_engine()
        self.jogos_gerados: List[List[int]] = []

        self._configurar_estilos()
        self._construir_ui()
        self._carregar_resumo_caixa()

    def _configurar_estilos(self):
        style = ttk.Style(self)
        style.theme_use("clam")

        style.configure("TNotebook", background=self.c_bg, borderwidth=0)
        style.configure("TNotebook.Tab",
                        background=self.c_card,
                        foreground=self.c_muted,
                        padding=[16, 9],
                        font=("Helvetica", 10, "bold"),
                        borderwidth=0)
        style.map("TNotebook.Tab",
                  background=[("selected", self.c_accent)],
                  foreground=[("selected", "#000000")])

        style.configure("TFrame", background=self.c_bg)
        style.configure("Card.TFrame", background=self.c_card)

        # Botões estilizados
        style.configure("Accent.TButton",
                        background=self.c_accent,
                        foreground="#000000",
                        font=("Helvetica", 10, "bold"),
                        padding=[14, 8],
                        borderwidth=0)
        style.map("Accent.TButton",
                  background=[("active", self.c_highlight), ("pressed", "#0891b2")])

        style.configure("Purple.TButton",
                        background=self.c_purple,
                        foreground="#ffffff",
                        font=("Helvetica", 10, "bold"),
                        padding=[14, 8],
                        borderwidth=0)
        style.map("Purple.TButton",
                  background=[("active", "#c084fc"), ("pressed", "#9333ea")])

        style.configure("Emerald.TButton",
                        background=self.c_emerald,
                        foreground="#000000",
                        font=("Helvetica", 10, "bold"),
                        padding=[12, 7],
                        borderwidth=0)
        style.map("Emerald.TButton",
                  background=[("active", "#34d399"), ("pressed", "#059669")])

        style.configure("Secondary.TButton",
                        background=self.c_card_light,
                        foreground=self.c_text,
                        font=("Helvetica", 9),
                        padding=[10, 6],
                        borderwidth=0)
        style.map("Secondary.TButton",
                  background=[("active", "#334155")])

        # Tabela Treeview
        style.configure("Treeview",
                        background=self.c_card,
                        foreground=self.c_text,
                        fieldbackground=self.c_card,
                        rowheight=28,
                        font=("Helvetica", 10),
                        borderwidth=0)
        style.configure("Treeview.Heading",
                        background=self.c_card_light,
                        foreground=self.c_text,
                        font=("Helvetica", 9, "bold"),
                        borderwidth=1)
        style.map("Treeview",
                  background=[("selected", "#0284c7")],
                  foreground=[("selected", "#ffffff")])

    def _construir_ui(self):
        # Header Superior
        header = tk.Frame(self, bg=self.c_card, height=80)
        header.pack(fill="x", side="top")

        title_box = tk.Frame(header, bg=self.c_card)
        title_box.pack(side="left", padx=22, pady=12)

        lbl_logo = tk.Label(title_box, text="⚡ CARTELA MATEMÁTICA", bg=self.c_card, fg=self.c_accent, font=("Helvetica", 18, "bold"))
        lbl_logo.pack(anchor="w")
        lbl_desc = tk.Label(title_box, text="Teoria dos Jogos (E[X]) • Covering Designs C(v,k,t) • Teste Qui-Quadrado NIST",
                            bg=self.c_card, fg=self.c_muted, font=("Helvetica", 9))
        lbl_desc.pack(anchor="w")

        # Caixa Info Box
        self.box_caixa = tk.Frame(header, bg=self.c_card_light, padx=14, pady=6)
        self.box_caixa.pack(side="right", padx=22, pady=10)

        self.lbl_caixa_concurso = tk.Label(self.box_caixa, text="Consultando Caixa...", bg=self.c_card_light, fg=self.c_text, font=("Helvetica", 10, "bold"))
        self.lbl_caixa_concurso.pack(anchor="e")
        self.lbl_caixa_status = tk.Label(self.box_caixa, text=f"🟢 Base: {len(self.engine.concursos)} Concursos Reais", bg=self.c_card_light, fg=self.c_emerald, font=("Helvetica", 8, "bold"))
        self.lbl_caixa_status.pack(anchor="e")

        # Tabs
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True, padx=16, pady=12)

        # Tab 1: Gerador Anti-Colisão & Valor Esperado
        self.tab_gerador = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_gerador, text="  🎯 Teoria dos Jogos & E[X]  ")
        self._construir_tab_gerador()

        # Tab 2: Fechamentos Combinatórios
        self.tab_fechamento = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_fechamento, text="  🧩 Fechamentos C(v,k,t)  ")
        self._construir_tab_fechamentos()

        # Tab 3: Auditoria Qui-Quadrado NIST
        self.tab_audit = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_audit, text="  🔬 Auditoria Chi-Quadrado (NIST)  ")
        self._construir_tab_audit()

        # Tab 4: Backtesting
        self.tab_backtest = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_backtest, text="  🧪 Backtest Histórico Real  ")
        self._construir_tab_backtest()

        # Tab 5: Sincronizador Caixa
        self.tab_sync = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_sync, text="  🔄 Sincronizador Oficial  ")
        self._construir_tab_sync()

    # -------------------------------------------------------------
    # TAB 1: GERADOR TEORIA DOS JOGOS & E[X]
    # -------------------------------------------------------------
    def _construir_tab_gerador(self):
        pane = tk.PanedWindow(self.tab_gerador, orient="horizontal", bg=self.c_bg, bd=0, sashwidth=4)
        pane.pack(fill="both", expand=True, padx=4, pady=4)

        # Controles Esquerda
        left = tk.Frame(pane, bg=self.c_card, width=330, padx=16, pady=16)
        pane.add(left, minsize=320)

        tk.Label(left, text="Estratégia de Otimização", bg=self.c_card, fg=self.c_text, font=("Helvetica", 12, "bold")).pack(anchor="w", pady=(0, 10))

        tk.Label(left, text="Quantidade de Jogos:", bg=self.c_card, fg=self.c_muted, font=("Helvetica", 9)).pack(anchor="w")
        self.spin_qtd = tk.Spinbox(left, from_=1, to=100, font=("Helvetica", 10), bg=self.c_card_light, fg=self.c_text, insertbackground="white", bd=0)
        self.spin_qtd.delete(0, "end")
        self.spin_qtd.insert(0, "10")
        self.spin_qtd.pack(fill="x", pady=(2, 10))

        tk.Label(left, text="Abordagem Matemática:", bg=self.c_card, fg=self.c_muted, font=("Helvetica", 9)).pack(anchor="w")
        self.combo_modelo = ttk.Combobox(left, values=[
            "Anti-Colisão (Maximização E[X] / Fuga de Aniversário)",
            "Baricentro de Mahalanobis (Gaussiana Multivariada)",
            "Distribuição de Poisson Ponderada",
            "Amostragem Monte Carlo Uniforme"
        ], state="readonly", font=("Helvetica", 9))
        self.combo_modelo.current(0)
        self.combo_modelo.pack(fill="x", pady=(2, 12))

        tk.Label(left, text="Filtros Estatísticos Gaussianos", bg=self.c_card, fg=self.c_text, font=("Helvetica", 10, "bold")).pack(anchor="w", pady=(4, 6))

        soma_box = tk.Frame(left, bg=self.c_card)
        soma_box.pack(fill="x", pady=(2, 6))
        tk.Label(soma_box, text="Soma:", bg=self.c_card, fg=self.c_muted).pack(side="left")
        self.ent_min_soma = tk.Entry(soma_box, width=6, bg=self.c_card_light, fg=self.c_text, font=("Helvetica", 9), bd=0)
        self.ent_min_soma.insert(0, "140")
        self.ent_min_soma.pack(side="left", padx=4)
        tk.Label(soma_box, text="a", bg=self.c_card, fg=self.c_muted).pack(side="left")
        self.ent_max_soma = tk.Entry(soma_box, width=6, bg=self.c_card_light, fg=self.c_text, font=("Helvetica", 9), bd=0)
        self.ent_max_soma.insert(0, "225")
        self.ent_max_soma.pack(side="left", padx=4)

        self.var_forcar = tk.BooleanVar(value=False)
        chk = tk.Checkbutton(left, text="Ignorar Filtros (Gerar sem Restrições)", variable=self.var_forcar,
                             bg=self.c_card, fg=self.c_muted, activebackground=self.c_card, selectcolor=self.c_card_light)
        chk.pack(anchor="w", pady=(4, 14))

        btn_gerar = ttk.Button(left, text="⚡ GERAR VOLANTES ESTRATÉGICOS", style="Accent.TButton", command=self._acao_gerar_jogos)
        btn_gerar.pack(fill="x", pady=(4, 14))

        tk.Label(left, text="Exportação e Relatórios", bg=self.c_card, fg=self.c_muted, font=("Helvetica", 9)).pack(anchor="w", pady=(6, 4))
        btn_pdf = ttk.Button(left, text="📄 Gerar Relatório PDF Vetorial", style="Emerald.TButton", command=self._acao_exportar_pdf)
        btn_pdf.pack(fill="x", pady=3)

        btn_csv = ttk.Button(left, text="📊 Exportar CSV Estruturado", style="Secondary.TButton", command=self._acao_exportar_csv)
        btn_csv.pack(fill="x", pady=3)

        # Painel Direito (Grid / Resultados)
        right = tk.Frame(pane, bg=self.c_bg, padx=12, pady=12)
        pane.add(right, minsize=550)

        header_tbl = tk.Frame(right, bg=self.c_bg)
        header_tbl.pack(fill="x", pady=(0, 8))
        self.lbl_qtd_resultado = tk.Label(header_tbl, text="Volantes Otimizados: 0", bg=self.c_bg, fg=self.c_text, font=("Helvetica", 11, "bold"))
        self.lbl_qtd_resultado.pack(side="left")

        btn_copiar = ttk.Button(header_tbl, text="📋 Copiar Jogos", style="Secondary.TButton", command=self._acao_copiar_jogos)
        btn_copiar.pack(side="right")

        cols = ("num", "dezenas", "soma", "pares", "anticolisao", "status")
        self.tree_jogos = ttk.Treeview(right, columns=cols, show="headings", selectmode="browse")
        self.tree_jogos.heading("num", text="#")
        self.tree_jogos.heading("dezenas", text="Dezenas do Volante")
        self.tree_jogos.heading("soma", text="Soma")
        self.tree_jogos.heading("pares", text="Paridade")
        self.tree_jogos.heading("anticolisao", text="Score Anti-Colisão")
        self.tree_jogos.heading("status", text="Avaliação E[X]")

        self.tree_jogos.column("num", width=40, anchor="center")
        self.tree_jogos.column("dezenas", width=230, anchor="center")
        self.tree_jogos.column("soma", width=60, anchor="center")
        self.tree_jogos.column("pares", width=70, anchor="center")
        self.tree_jogos.column("anticolisao", width=120, anchor="center")
        self.tree_jogos.column("status", width=180, anchor="w")

        scroll = ttk.Scrollbar(right, orient="vertical", command=self.tree_jogos.yview)
        self.tree_jogos.configure(yscrollcommand=scroll.set)

        self.tree_jogos.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")

    def _acao_gerar_jogos(self):
        try:
            qtd = int(self.spin_qtd.get().strip())
        except ValueError:
            messagebox.showerror("Erro", "Quantidade inválida.")
            return

        try:
            min_soma = int(self.ent_min_soma.get().strip())
            max_soma = int(self.ent_max_soma.get().strip())
        except ValueError:
            min_soma, max_soma = 140, 225

        mapa_modo = {
            0: "anti_colisao",
            1: "mahalanobis",
            2: "frequencia",
            3: "aleatorio"
        }
        modo = mapa_modo.get(self.combo_modelo.current(), "anti_colisao")
        forcar = self.var_forcar.get()

        self.jogos_gerados = self.engine.gerar_jogos(
            quantidade=qtd,
            modo=modo,
            min_soma=min_soma,
            max_soma=max_soma,
            forcar_filtros=forcar
        )

        for item in self.tree_jogos.get_children():
            self.tree_jogos.delete(item)

        for idx, j in enumerate(self.jogos_gerados, 1):
            soma = sum(j)
            pares = sum(1 for d in j if d % 2 == 0)
            ac_info = self.engine.calcular_indice_anti_colisao(j)
            dezenas_format = " - ".join(f"{d:02d}" for d in j)

            self.tree_jogos.insert("", "end", values=(
                f"{idx:02d}",
                dezenas_format,
                str(soma),
                f"{pares}P / {6 - pares}I",
                f"{ac_info['score_anti_colisao']:.0f}%",
                ac_info["classificacao"]
            ))

        self.lbl_qtd_resultado.config(text=f"Volantes Otimizados: {len(self.jogos_gerados)}")

    def _acao_copiar_jogos(self):
        if not self.jogos_gerados:
            messagebox.showinfo("Aviso", "Gere jogos primeiro.")
            return
        texto = "\n".join(" ".join(f"{d:02d}" for d in j) for j in self.jogos_gerados)
        self.clipboard_clear()
        self.clipboard_append(texto)
        messagebox.showinfo("Copiado", f"{len(self.jogos_gerados)} volantes copiados para a Área de Transferência!")

    def _acao_exportar_pdf(self):
        if not self.jogos_gerados:
            messagebox.showinfo("Aviso", "Gere jogos primeiro.")
            return
        caminho = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF Documents", "*.pdf")], title="Salvar Relatório PDF")
        if caminho:
            try:
                self.engine.exportar_pdf(self.jogos_gerados, caminho)
                messagebox.showinfo("Sucesso", f"PDF gerado com sucesso:\n{caminho}")
            except Exception as e:
                messagebox.showerror("Erro ao exportar PDF", str(e))

    def _acao_exportar_csv(self):
        if not self.jogos_gerados:
            messagebox.showinfo("Aviso", "Gere jogos primeiro.")
            return
        caminho = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV Files", "*.csv")], title="Salvar Volantes CSV")
        if caminho:
            try:
                self.engine.exportar_csv(self.jogos_gerados, caminho)
                messagebox.showinfo("Sucesso", f"CSV exportado com sucesso:\n{caminho}")
            except Exception as e:
                messagebox.showerror("Erro ao exportar CSV", str(e))

    # -------------------------------------------------------------
    # TAB 2: FECHAMENTOS COMBINATÓRIOS C(v, k, t)
    # -------------------------------------------------------------
    def _construir_tab_fechamentos(self):
        frame = tk.Frame(self.tab_fechamento, bg=self.c_bg, padx=16, pady=16)
        frame.pack(fill="both", expand=True)

        tk.Label(frame, text="Covering Designs C(v, k, t) - Fechamento Matemático", bg=self.c_bg, fg=self.c_purple, font=("Helvetica", 14, "bold")).pack(anchor="w")
        tk.Label(frame, text="Reduz centenas de combinações em um número mínimo de volantes, garantindo matematicamente Quadra ou Quina.",
                 bg=self.c_bg, fg=self.c_muted, font=("Helvetica", 9)).pack(anchor="w", pady=(2, 12))

        ctrl_box = tk.Frame(frame, bg=self.c_card, padx=14, pady=14)
        ctrl_box.pack(fill="x", pady=(0, 12))

        tk.Label(ctrl_box, text="Pool de Dezenas Escolhidas (8 a 15 números separados por espaço):", bg=self.c_card, fg=self.c_text, font=("Helvetica", 10, "bold")).pack(anchor="w")
        self.ent_pool_fechamento = tk.Entry(ctrl_box, font=("Helvetica", 11), bg=self.c_card_light, fg=self.c_accent, bd=0)
        self.ent_pool_fechamento.insert(0, "04 11 18 25 32 39 44 49 53 58")
        self.ent_pool_fechamento.pack(fill="x", pady=(4, 10))

        opt_row = tk.Frame(ctrl_box, bg=self.c_card)
        opt_row.pack(fill="x")

        tk.Label(opt_row, text="Garantia Matemática:", bg=self.c_card, fg=self.c_muted, font=("Helvetica", 10)).pack(side="left")
        self.combo_garantia = ttk.Combobox(opt_row, values=["Garantia de Quadra (t=4 se 6 no pool)", "Garantia de Quina (t=5 se 6 no pool)"], state="readonly", width=34)
        self.combo_garantia.current(0)
        self.combo_garantia.pack(side="left", padx=8)

        btn_gerar_fechamento = ttk.Button(opt_row, text="🧩 CALCULAR FECHAMENTO ÓTIMO", style="Purple.TButton", command=self._acao_calcular_fechamento)
        btn_gerar_fechamento.pack(side="right")

        # Tabela de Jogos do Fechamento
        res_box = tk.Frame(frame, bg=self.c_card, padx=14, pady=12)
        res_box.pack(fill="both", expand=True)

        self.lbl_fechamento_info = tk.Label(res_box, text="Nenhum fechamento calculado ainda.", bg=self.c_card, fg=self.c_text, font=("Helvetica", 10, "bold"))
        self.lbl_fechamento_info.pack(anchor="w", pady=(0, 8))

        cols = ("num", "dezenas", "soma", "anticolisao")
        self.tree_fechamento = ttk.Treeview(res_box, columns=cols, show="headings", selectmode="browse")
        self.tree_fechamento.heading("num", text="#")
        self.tree_fechamento.heading("dezenas", text="Volante Gerado")
        self.tree_fechamento.heading("soma", text="Soma")
        self.tree_fechamento.heading("anticolisao", text="Score Anti-Colisão")

        self.tree_fechamento.column("num", width=50, anchor="center")
        self.tree_fechamento.column("dezenas", width=300, anchor="center")
        self.tree_fechamento.column("soma", width=90, anchor="center")
        self.tree_fechamento.column("anticolisao", width=140, anchor="center")

        self.tree_fechamento.pack(fill="both", expand=True)

    def _acao_calcular_fechamento(self):
        txt = self.ent_pool_fechamento.get().strip()
        try:
            dezenas = sorted(list(set([int(x) for x in txt.replace(",", " ").replace("-", " ").split() if x])))
            if len(dezenas) < 6:
                raise ValueError("Insira pelo menos 6 dezenas no pool.")
            if len(dezenas) > 16:
                raise ValueError("Máximo recomendado de 16 dezenas para cálculo instantâneo.")
            if any(d < 1 or d > 60 for d in dezenas):
                raise ValueError("Dezenas devem ser de 01 a 60.")
        except Exception as e:
            messagebox.showerror("Erro de Entrada", str(e))
            return

        garantia = "quadra" if self.combo_garantia.current() == 0 else "quina"
        jogos = self.engine.gerar_fechamento_combinatorio(dezenas, garantia=garantia)

        total_combinacoes_brutas = math.comb(len(dezenas), 6)
        economia = (1.0 - (len(jogos) / total_combinacoes_brutas)) * 100

        self.lbl_fechamento_info.config(
            text=f"Pool de {len(dezenas)} Dezenas | Combinações Brutas: {total_combinacoes_brutas} -> Fechamento Mínimo: Apenas {len(jogos)} Volantes (Economia de {economia:.1f}%)"
        )

        for item in self.tree_fechamento.get_children():
            self.tree_fechamento.delete(item)

        for idx, j in enumerate(jogos, 1):
            ac = self.engine.calcular_indice_anti_colisao(j)["score_anti_colisao"]
            self.tree_fechamento.insert("", "end", values=(
                f"#{idx:02d}",
                " - ".join(f"{d:02d}" for d in j),
                str(sum(j)),
                f"{ac:.0f}%"
            ))

        self.jogos_gerados = jogos

    # -------------------------------------------------------------
    # TAB 3: AUDITORIA CIENTÍFICA & TESTE QUI-QUADRADO
    # -------------------------------------------------------------
    def _construir_tab_audit(self):
        frame = tk.Frame(self.tab_audit, bg=self.c_bg, padx=16, pady=16)
        frame.pack(fill="both", expand=True)

        tk.Label(frame, text="Auditoria Estatística Formal (NIST SP 800-22 / Dieharder)", bg=self.c_bg, fg=self.c_accent, font=("Helvetica", 14, "bold")).pack(anchor="w")
        tk.Label(frame, text="Teste de Aderência Qui-Quadrado (Goodness-of-Fit) calculado sobre os 3063+ concursos reais da história.",
                 bg=self.c_bg, fg=self.c_muted, font=("Helvetica", 9)).pack(anchor="w", pady=(2, 14))

        audit = self.engine.teste_qui_quadrado()

        cards_box = tk.Frame(frame, bg=self.c_bg)
        cards_box.pack(fill="x", pady=(0, 14))

        # Card Estatística
        c1 = tk.Frame(cards_box, bg=self.c_card, padx=14, pady=12)
        c1.pack(side="left", fill="both", expand=True, padx=4)
        tk.Label(c1, text="Estatística Qui-Quadrado (χ²)", bg=self.c_card, fg=self.c_muted, font=("Helvetica", 9)).pack(anchor="w")
        tk.Label(c1, text=f"{audit['estatistica_qui_quadrado']}", bg=self.c_card, fg=self.c_accent, font=("Helvetica", 18, "bold")).pack(anchor="w", pady=2)
        tk.Label(c1, text=f"Graus de Liberdade: {audit['graus_liberdade']}", bg=self.c_card, fg=self.c_muted, font=("Helvetica", 8)).pack(anchor="w")

        # Card P-Valor
        c2 = tk.Frame(cards_box, bg=self.c_card, padx=14, pady=12)
        c2.pack(side="left", fill="both", expand=True, padx=4)
        tk.Label(c2, text="P-Valor (Nível de Significância)", bg=self.c_card, fg=self.c_muted, font=("Helvetica", 9)).pack(anchor="w")
        tk.Label(c2, text=f"{audit['p_valor']}", bg=self.c_card, fg=self.c_emerald, font=("Helvetica", 18, "bold")).pack(anchor="w", pady=2)
        tk.Label(c2, text="Critério de Aceitação: p > 0.05", bg=self.c_card, fg=self.c_muted, font=("Helvetica", 8)).pack(anchor="w")

        # Card Conclusão
        c3 = tk.Frame(cards_box, bg=self.c_card, padx=14, pady=12)
        c3.pack(side="left", fill="both", expand=True, padx=4)
        tk.Label(c3, text="Veredito Científico", bg=self.c_card, fg=self.c_muted, font=("Helvetica", 9)).pack(anchor="w")
        tk.Label(c3, text=f"{audit['conclusao_cientifica']}", bg=self.c_card, fg=self.c_emerald, font=("Helvetica", 14, "bold")).pack(anchor="w", pady=4)
        tk.Label(c3, text="Processo Estocástico sem Memória", bg=self.c_card, fg=self.c_muted, font=("Helvetica", 8)).pack(anchor="w")

        # Caixa com Explicação Acadêmica
        expl_box = tk.Frame(frame, bg=self.c_card, padx=16, pady=16)
        expl_box.pack(fill="both", expand=True)

        tk.Label(expl_box, text="Fundamentação na Literatura Acadêmica:", bg=self.c_card, fg=self.c_text, font=("Helvetica", 11, "bold")).pack(anchor="w", pady=(0, 6))
        txt_expl = tk.Text(expl_box, bg=self.c_bg, fg=self.c_text, font=("Helvetica", 10), bd=0, wrap="word", padx=10, pady=10)
        txt_expl.pack(fill="both", expand=True)

        conteudo_academico = (
            f"1. ALEATORIEDADE E COMPLEXIDADE DE KOLMOGOROV:\n"
            f"   A sequência de sorteios da Mega-Sena atinge a Entropia de Shannon máxima H(X) ≈ 25,57 bits por concurso.\n"
            f"   Nenhum algoritmo ou modelo preditivo (LSTM, Transformers, XGBoost) consegue prever o próximo sorteio,\n"
            f"   pois a perda converge exatamente para a entropia teórica uniforme do ruído branco.\n\n"
            f"2. FALÁCIA DO APOSTADOR DESMISTIFICADA:\n"
            f"   O teste Chi-Quadrado com p-valor={audit['p_valor']} demonstra que dezenas que saíram mais vezes ou que\n"
            f"   estão em atraso não possuem probabilidade alterada. Cada dezena mantém Rigorosamente p = 1/60 (≈ 1,67%).\n\n"
            f"3. ONDE A MATEMÁTICA REALMENTE GERA VANTAGEM:\n"
            f"   A) TEORIA DOS JOGOS (MAXIMIZAÇÃO DE E[X]):\n"
            f"      Como todas as dezenas têm a mesma chance, você deve apostar em combinações que outros NÃO jogam\n"
            f"      (fuga de datas de aniversário de 1 a 31 e padrões geométricos). Isso evita dividir prêmios milionários!\n\n"
            f"   B) COVERING DESIGNS C(v, k, t):\n"
            f"      Sistemas de fechamento que garantem prêmios matemáticos com a menor quantidade de bilhetes possível."
        )
        txt_expl.insert("end", conteudo_academico)
        txt_expl.config(state="disabled")

    # -------------------------------------------------------------
    # TAB 4: BACKTEST HISTÓRICO REAL
    # -------------------------------------------------------------
    def _construir_tab_backtest(self):
        frame = tk.Frame(self.tab_backtest, bg=self.c_bg, padx=16, pady=16)
        frame.pack(fill="both", expand=True)

        tk.Label(frame, text="Simulação de Desempenho Histórico Real", bg=self.c_bg, fg=self.c_text, font=("Helvetica", 14, "bold")).pack(anchor="w")
        tk.Label(frame, text=f"Audita qualquer aposta contra todos os {len(self.engine.concursos)} concursos realizados desde 1996.",
                 bg=self.c_bg, fg=self.c_muted, font=("Helvetica", 9)).pack(anchor="w", pady=(2, 12))

        in_card = tk.Frame(frame, bg=self.c_card, padx=14, pady=14)
        in_card.pack(fill="x", pady=(0, 14))

        tk.Label(in_card, text="Informe as 6 dezenas (ex: 05 13 21 32 33 59):", bg=self.c_card, fg=self.c_text, font=("Helvetica", 10, "bold")).pack(anchor="w")

        row = tk.Frame(in_card, bg=self.c_card)
        row.pack(fill="x", pady=(4, 0))
        self.ent_backtest = tk.Entry(row, font=("Helvetica", 12, "bold"), bg=self.c_card_light, fg=self.c_accent, bd=0)
        self.ent_backtest.insert(0, "05 13 21 32 33 59")
        self.ent_backtest.pack(side="left", fill="x", expand=True, padx=(0, 10))

        btn = ttk.Button(row, text="🔬 SIMULAR CONTRA 3063+ CONCURSOS", style="Accent.TButton", command=self._acao_simular_backtest)
        btn.pack(side="right")

        res_card = tk.Frame(frame, bg=self.c_card, padx=16, pady=16)
        res_card.pack(fill="both", expand=True)

        self.lbl_quadras = tk.Label(res_card, text="Quadras: --", bg=self.c_card, fg=self.c_text, font=("Helvetica", 12, "bold"))
        self.lbl_quadras.pack(anchor="w", pady=3)

        self.lbl_quinas = tk.Label(res_card, text="Quinas: --", bg=self.c_card, fg=self.c_emerald, font=("Helvetica", 12, "bold"))
        self.lbl_quinas.pack(anchor="w", pady=3)

        self.lbl_senas = tk.Label(res_card, text="Senas (Prêmio Máximo): --", bg=self.c_card, fg=self.c_accent, font=("Helvetica", 12, "bold"))
        self.lbl_senas.pack(anchor="w", pady=3)

        self.txt_detalhes_backtest = tk.Text(res_card, bg=self.c_bg, fg=self.c_text, font=("Courier New", 9), bd=0, height=9)
        self.txt_detalhes_backtest.pack(fill="both", expand=True, pady=(8, 0))

    def _acao_simular_backtest(self):
        txt = self.ent_backtest.get().strip()
        try:
            dezenas = sorted([int(x) for x in txt.replace(",", " ").replace("-", " ").split() if x])
            if len(dezenas) != 6:
                raise ValueError("Insira exatamente 6 dezenas.")
            if any(d < 1 or d > 60 for d in dezenas):
                raise ValueError("Dezenas devem estar entre 01 e 60.")
            if len(set(dezenas)) != 6:
                raise ValueError("Não repita dezenas.")
        except Exception as e:
            messagebox.showerror("Erro", str(e))
            return

        res = self.engine.backtest_jogo(dezenas)
        self.lbl_quadras.config(text=f"Quadras (4 acertos): {res['quadras']} vezes")
        self.lbl_quinas.config(text=f"Quinas (5 acertos): {res['quinas']} vezes")
        self.lbl_senas.config(text=f"Senas (6 acertos): {res['senas']} vezes")

        self.txt_detalhes_backtest.delete("1.0", "end")
        if res["detalhes"]:
            self.txt_detalhes_backtest.insert("end", f"Concursos históricos onde essa aposta pontuou:\n")
            for d in res["detalhes"]:
                self.txt_detalhes_backtest.insert("end", f"Concurso #{d['concurso']:04d} -> {d['acertos']} Acertos | Sorteio: {d['sorteio']}\n")
        else:
            self.txt_detalhes_backtest.insert("end", "Essa combinação específica nunca atingiu Quadra, Quina ou Sena na história da Caixa.\n")

    # -------------------------------------------------------------
    # TAB 5: SINCRONIZADOR CAIXA OFICIAL
    # -------------------------------------------------------------
    def _construir_tab_sync(self):
        frame = tk.Frame(self.tab_sync, bg=self.c_bg, padx=16, pady=16)
        frame.pack(fill="both", expand=True)

        tk.Label(frame, text="Sincronizador Automático com Loterias Caixa", bg=self.c_bg, fg=self.c_text, font=("Helvetica", 14, "bold")).pack(anchor="w")
        tk.Label(frame, text="Conexão direta com a API REST oficial da Caixa Econômica Federal.",
                 bg=self.c_bg, fg=self.c_muted, font=("Helvetica", 9)).pack(anchor="w", pady=(2, 14))

        box = tk.Frame(frame, bg=self.c_card, padx=16, pady=16)
        box.pack(fill="x", pady=(0, 14))

        self.btn_sincronizar_agora = ttk.Button(box, text="🔄 Sincronizar Novos Concursos Agora", style="Accent.TButton", command=self._acao_sincronizar_online)
        self.btn_sincronizar_agora.pack(side="left")

        self.prog_sync = ttk.Progressbar(box, orient="horizontal", mode="determinate", length=320)
        self.prog_sync.pack(side="right", padx=10)

        self.txt_sync_log = tk.Text(frame, bg=self.c_card, fg=self.c_emerald, font=("Courier New", 9), bd=0, height=14)
        self.txt_sync_log.pack(fill="both", expand=True)
        self.txt_sync_log.insert("end", f"[{self._hora_atual()}] Base local carregada com {len(self.engine.concursos)} concursos reais.\n")

    def _acao_sincronizar_online(self):
        self.btn_sincronizar_agora.config(state="disabled")
        self.txt_sync_log.insert("end", f"[{self._hora_atual()}] Consultando servidor Caixa...\n")

        def task():
            def progresso(idx, total, num):
                self.prog_sync["maximum"] = total
                self.prog_sync["value"] = idx
                self.txt_sync_log.insert("end", f"[{self._hora_atual()}] Baixando concurso #{num}...\n")
                self.txt_sync_log.see("end")

            try:
                concursos = self.engine.sincronizar_dados_oficiais(progress_callback=progresso)
                self.txt_sync_log.insert("end", f"[{self._hora_atual()}] Sincronização 100% concluída! Base total: {len(concursos)} concursos.\n")
                self.lbl_caixa_status.config(text=f"🟢 Base: {len(concursos)} Concursos Reais")
            except Exception as e:
                self.txt_sync_log.insert("end", f"[{self._hora_atual()}] Erro na conexão: {e}\n")
            finally:
                self.btn_sincronizar_agora.config(state="normal")
                self.prog_sync["value"] = 0

        threading.Thread(target=task, daemon=True).start()

    def _carregar_resumo_caixa(self):
        def task():
            info = self.engine.obter_ultimo_resultado_online()
            if info:
                self.lbl_caixa_concurso.config(
                    text=f"Concurso #{info['numero']} ({info['data']}): {' - '.join(f'{d:02d}' for d in info['dezenas'])}"
                )
                if info.get("acumulado"):
                    self.lbl_caixa_status.config(
                        text=f"🔥 ACUMULADO! Estimativa: R$ {info['premio_estimado']/1e6:.1f}M ({len(self.engine.concursos)} Concursos)"
                    )
        threading.Thread(target=task, daemon=True).start()

    def _hora_atual(self) -> str:
        import time
        return time.strftime("%H:%M:%S")


if __name__ == "__main__":
    app = CartelaApp()
    app.mainloop()
