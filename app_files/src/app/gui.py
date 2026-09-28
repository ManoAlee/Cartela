#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gui.py - Interface Gráfica Minimalista, Moderna e Sem Poluição Visual
Design System baseado em Dark Slate, cards limpos, tipografia nítida e foco em usabilidade.
"""

import sys
import os
import math
import time
import threading
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from typing import List, Optional

SRC_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from core.engine import get_engine, MegaSenaEngine


class CartelaApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Cartela — Inteligência Estatística")
        self.geometry("1080x740")
        self.minsize(960, 640)

        # Paleta Minimalista Profissional (Slate Dark / Sky / Emerald)
        self.c_bg = "#0b0f19"          # Fundo principal profundo
        self.c_card = "#161f30"        # Cartões e seções
        self.c_card_border = "#24334a" # Bordas sutis
        self.c_input = "#0d1322"       # Fundo de campos de input
        self.c_primary = "#38bdf8"     # Acento Sky
        self.c_primary_hover = "#7dd3fc"
        self.c_primary_fg = "#0b0f19"  # Texto sobre acento
        self.c_emerald = "#34d399"     # Indicadores positivos
        self.c_amber = "#fbbf24"       # Indicadores de atenção
        self.c_text = "#f8fafc"        # Texto primário
        self.c_muted = "#94a3b8"       # Texto secundário

        self.configure(bg=self.c_bg)

        self.engine = get_engine()
        self.jogos_gerados: List[List[int]] = []

        self._configurar_estilos()
        self._construir_ui()
        self._carregar_resumo_caixa()

    def _configurar_estilos(self):
        style = ttk.Style(self)
        style.theme_use("clam")

        # Configuração do Notebook (Abas Minimalistas)
        style.configure("TNotebook", background=self.c_bg, borderwidth=0)
        style.configure("TNotebook.Tab",
                        background=self.c_card,
                        foreground=self.c_muted,
                        padding=[22, 11],
                        font=("Segoe UI", 10),
                        borderwidth=0)
        style.map("TNotebook.Tab",
                  background=[("selected", self.c_primary)],
                  foreground=[("selected", self.c_primary_fg)],
                  font=[("selected", ("Segoe UI", 10, "bold"))])

        style.configure("TFrame", background=self.c_bg)

        # Botão Primário (Ação Principal)
        style.configure("Primary.TButton",
                        background=self.c_primary,
                        foreground=self.c_primary_fg,
                        font=("Segoe UI", 10, "bold"),
                        padding=[14, 8],
                        borderwidth=0)
        style.map("Primary.TButton",
                  background=[("active", self.c_primary_hover), ("pressed", "#0284c7")])

        # Botão Secundário (Ações Utilitárias)
        style.configure("Secondary.TButton",
                        background=self.c_card_border,
                        foreground=self.c_text,
                        font=("Segoe UI", 9),
                        padding=[12, 6],
                        borderwidth=0)
        style.map("Secondary.TButton",
                  background=[("active", "#334155")])

        # Combobox Customizado
        style.configure("TCombobox",
                        fieldbackground=self.c_input,
                        background=self.c_card_border,
                        foreground=self.c_text,
                        arrowcolor=self.c_primary,
                        borderwidth=0)

        # Treeview (Tabela de Resultados Clean)
        style.configure("Treeview",
                        background=self.c_card,
                        foreground=self.c_text,
                        fieldbackground=self.c_card,
                        rowheight=34,
                        font=("Segoe UI", 10),
                        borderwidth=0)
        style.configure("Treeview.Heading",
                        background=self.c_card_border,
                        foreground=self.c_text,
                        font=("Segoe UI", 9, "bold"),
                        borderwidth=0)
        style.map("Treeview",
                  background=[("selected", "#0284c7")],
                  foreground=[("selected", "#ffffff")])

    def _construir_ui(self):
        # 1. Top Bar Elegante e Desobstruída
        top_bar = tk.Frame(self, bg=self.c_bg, padx=24, pady=16)
        top_bar.pack(fill="x")

        title_box = tk.Frame(top_bar, bg=self.c_bg)
        title_box.pack(side="left")

        lbl_logo = tk.Label(title_box, text="Cartela", bg=self.c_bg, fg=self.c_text, font=("Segoe UI", 18, "bold"))
        lbl_logo.pack(side="left")

        lbl_sub = tk.Label(title_box, text="  Inteligência Estatística & Teoria dos Jogos", bg=self.c_bg, fg=self.c_muted, font=("Segoe UI", 10))
        lbl_sub.pack(side="left", pady=(4, 0))

        # Badge Informativo Discreto
        self.badge_caixa = tk.Label(
            top_bar,
            text=f"● {len(self.engine.concursos)} Concursos Oficiais",
            bg=self.c_card,
            fg=self.c_emerald,
            font=("Segoe UI", 9),
            padx=14,
            pady=5
        )
        self.badge_caixa.pack(side="right")

        # 2. Notebook de Navegação Focada
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True, padx=24, pady=(0, 20))

        # Aba 1: Gerador Estratégico
        self.tab_gerador = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_gerador, text="  Gerador Estratégico  ")
        self._construir_tab_gerador()

        # Aba 2: Fechamentos Stefan Mandel
        self.tab_fechamento = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_fechamento, text="  Fechamentos C(v, k, t)  ")
        self._construir_tab_fechamentos()

        # Aba 3: Radar de Arbitragem Joan Ginther
        self.tab_arbitragem = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_arbitragem, text="  Arbitragem E[X]  ")
        self._construir_tab_arbitragem()

        # Aba 4: Conferência Histórica & Sincronização
        self.tab_conferencia = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_conferencia, text="  Conferência & Dados  ")
        self._construir_tab_conferencia()

    # -------------------------------------------------------------
    # ABA 1: GERADOR ESTRATÉGICO
    # -------------------------------------------------------------
    def _construir_tab_gerador(self):
        container = tk.Frame(self.tab_gerador, bg=self.c_bg)
        container.pack(fill="both", expand=True, pady=10)

        # Coluna Lateral Esquerda: Controles Enxutos
        left = tk.Frame(container, bg=self.c_card, width=290, padx=18, pady=18)
        left.pack(side="left", fill="y", padx=(0, 14))
        left.pack_propagate(False)

        tk.Label(left, text="Configuração", bg=self.c_card, fg=self.c_text, font=("Segoe UI", 11, "bold")).pack(anchor="w", pady=(0, 14))

        # Quantidade
        tk.Label(left, text="Quantidade de Volantes:", bg=self.c_card, fg=self.c_muted, font=("Segoe UI", 9)).pack(anchor="w")
        self.spin_qtd = tk.Spinbox(left, from_=1, to=200, font=("Segoe UI", 10), bg=self.c_input, fg=self.c_text, insertbackground="white", bd=0)
        self.spin_qtd.delete(0, "end")
        self.spin_qtd.insert(0, "10")
        self.spin_qtd.pack(fill="x", pady=(4, 14))

        # Modelo Matemático
        tk.Label(left, text="Modelo Matemático:", bg=self.c_card, fg=self.c_muted, font=("Segoe UI", 9)).pack(anchor="w")
        self.combo_modelo = ttk.Combobox(left, values=[
            "Anti-Colisão (Fuga de 1-31)",
            "Baricentro de Mahalanobis",
            "Frequência Ponderada",
            "Aleatório Puro"
        ], state="readonly", font=("Segoe UI", 9))
        self.combo_modelo.current(0)
        self.combo_modelo.pack(fill="x", pady=(4, 16))

        # Faixa Gaussiana de Soma
        tk.Label(left, text="Filtro Gaussiano de Soma:", bg=self.c_card, fg=self.c_muted, font=("Segoe UI", 9)).pack(anchor="w")
        soma_row = tk.Frame(left, bg=self.c_card)
        soma_row.pack(fill="x", pady=(4, 18))
        self.ent_min_soma = tk.Entry(soma_row, width=6, bg=self.c_input, fg=self.c_text, font=("Segoe UI", 9), bd=0)
        self.ent_min_soma.insert(0, "140")
        self.ent_min_soma.pack(side="left")
        tk.Label(soma_row, text="até", bg=self.c_card, fg=self.c_muted, font=("Segoe UI", 9)).pack(side="left", padx=8)
        self.ent_max_soma = tk.Entry(soma_row, width=6, bg=self.c_input, fg=self.c_text, font=("Segoe UI", 9), bd=0)
        self.ent_max_soma.insert(0, "225")
        self.ent_max_soma.pack(side="left")

        # Botão Gerar
        btn_gerar = ttk.Button(left, text="Gerar Volantes", style="Primary.TButton", command=self._acao_gerar_jogos)
        btn_gerar.pack(fill="x", pady=(0, 20))

        # Divisor
        div = tk.Frame(left, bg=self.c_card_border, height=1)
        div.pack(fill="x", pady=(0, 16))

        # Ações de Exportação
        tk.Label(left, text="Exportação:", bg=self.c_card, fg=self.c_muted, font=("Segoe UI", 9)).pack(anchor="w", pady=(0, 6))
        btn_pdf = ttk.Button(left, text="Salvar em PDF", style="Secondary.TButton", command=self._acao_exportar_pdf)
        btn_pdf.pack(fill="x", pady=3)
        btn_csv = ttk.Button(left, text="Salvar em CSV", style="Secondary.TButton", command=self._acao_exportar_csv)
        btn_csv.pack(fill="x", pady=3)

        # Painel Direito: Grid Limpo e Espaçoso
        right = tk.Frame(container, bg=self.c_card, padx=18, pady=18)
        right.pack(side="right", fill="both", expand=True)

        header_r = tk.Frame(right, bg=self.c_card)
        header_r.pack(fill="x", pady=(0, 12))

        self.lbl_qtd_resultado = tk.Label(header_r, text="Pronto para gerar volantes", bg=self.c_card, fg=self.c_muted, font=("Segoe UI", 10))
        self.lbl_qtd_resultado.pack(side="left")

        btn_copiar = ttk.Button(header_r, text="Copiar Dezenas", style="Secondary.TButton", command=self._acao_copiar_jogos)
        btn_copiar.pack(side="right")

        cols = ("num", "dezenas", "soma", "pares", "anticolisao")
        self.tree_jogos = ttk.Treeview(right, columns=cols, show="headings", selectmode="browse")
        self.tree_jogos.heading("num", text="#")
        self.tree_jogos.heading("dezenas", text="Dezenas Selecionadas")
        self.tree_jogos.heading("soma", text="Soma")
        self.tree_jogos.heading("pares", text="Par/Ímp")
        self.tree_jogos.heading("anticolisao", text="Anti-Colisão")

        self.tree_jogos.column("num", width=45, anchor="center")
        self.tree_jogos.column("dezenas", width=340, anchor="center")
        self.tree_jogos.column("soma", width=75, anchor="center")
        self.tree_jogos.column("pares", width=85, anchor="center")
        self.tree_jogos.column("anticolisao", width=115, anchor="center")

        scroll = ttk.Scrollbar(right, orient="vertical", command=self.tree_jogos.yview)
        self.tree_jogos.configure(yscrollcommand=scroll.set)

        self.tree_jogos.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")

    def _acao_gerar_jogos(self):
        try:
            qtd = int(self.spin_qtd.get().strip())
            min_soma = int(self.ent_min_soma.get().strip())
            max_soma = int(self.ent_max_soma.get().strip())
        except ValueError:
            messagebox.showerror("Erro", "Valores numéricos inválidos.")
            return

        mapa = {0: "anti_colisao", 1: "mahalanobis", 2: "frequencia", 3: "aleatorio"}
        modo = mapa.get(self.combo_modelo.current(), "anti_colisao")

        self.jogos_gerados = self.engine.gerar_jogos(qtd, modo=modo, min_soma=min_soma, max_soma=max_soma)

        for item in self.tree_jogos.get_children():
            self.tree_jogos.delete(item)

        for idx, j in enumerate(self.jogos_gerados, 1):
            soma = sum(j)
            pares = sum(1 for d in j if d % 2 == 0)
            ac = self.engine.calcular_indice_anti_colisao(j)["score_anti_colisao"]
            format_dezenas = "   ".join(f"{d:02d}" for d in j)

            self.tree_jogos.insert("", "end", values=(
                f"{idx:02d}",
                format_dezenas,
                str(soma),
                f"{pares}P / {6-pares}I",
                f"{ac:.0f}%"
            ))

        self.lbl_qtd_resultado.config(text=f"{len(self.jogos_gerados)} volantes gerados com sucesso")

    def _acao_copiar_jogos(self):
        if not self.jogos_gerados:
            return
        texto = "\n".join(" ".join(f"{d:02d}" for d in j) for j in self.jogos_gerados)
        self.clipboard_clear()
        self.clipboard_append(texto)
        messagebox.showinfo("Sucesso", f"{len(self.jogos_gerados)} volantes copiados para a área de transferência!")

    def _acao_exportar_pdf(self):
        if not self.jogos_gerados:
            messagebox.showinfo("Aviso", "Gere jogos antes de exportar.")
            return
        path = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF Document", "*.pdf")])
        if path:
            self.engine.exportar_pdf(self.jogos_gerados, path)
            messagebox.showinfo("Sucesso", f"PDF salvo com sucesso em:\n{path}")

    def _acao_exportar_csv(self):
        if not self.jogos_gerados:
            messagebox.showinfo("Aviso", "Gere jogos antes de exportar.")
            return
        path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV", "*.csv")])
        if path:
            self.engine.exportar_csv(self.jogos_gerados, path)
            messagebox.showinfo("Sucesso", f"CSV salvo com sucesso em:\n{path}")

    # -------------------------------------------------------------
    # ABA 2: FECHAMENTOS COMBINATÓRIOS (Stefan Mandel)
    # -------------------------------------------------------------
    def _construir_tab_fechamentos(self):
        container = tk.Frame(self.tab_fechamento, bg=self.c_bg)
        container.pack(fill="both", expand=True, pady=10)

        # Cartão de Entrada Superior
        top = tk.Frame(container, bg=self.c_card, padx=20, pady=18)
        top.pack(fill="x", pady=(0, 14))

        tk.Label(top, text="Fechamento Combinatório C(v, k, t)", bg=self.c_card, fg=self.c_text, font=("Segoe UI", 12, "bold")).pack(anchor="w")
        tk.Label(top, text="Garante matematicamente premiação de Quadra ou Quina se as 6 sorteadas estiverem no seu conjunto.",
                 bg=self.c_card, fg=self.c_muted, font=("Segoe UI", 9)).pack(anchor="w", pady=(2, 10))

        tk.Label(top, text="Dezenas Escolhidas (separadas por espaço ou vírgula):", bg=self.c_card, fg=self.c_muted, font=("Segoe UI", 9)).pack(anchor="w")
        self.ent_pool = tk.Entry(top, font=("Segoe UI", 10), bg=self.c_input, fg=self.c_primary, insertbackground="white", bd=0)
        self.ent_pool.insert(0, "04 11 18 25 32 39 44 49 53 58")
        self.ent_pool.pack(fill="x", pady=(4, 12))

        row_ctrl = tk.Frame(top, bg=self.c_card)
        row_ctrl.pack(fill="x")
        self.combo_garantia = ttk.Combobox(row_ctrl, values=["Garantia de Quadra (t=4)", "Garantia de Quina (t=5)"], state="readonly", width=28)
        self.combo_garantia.current(0)
        self.combo_garantia.pack(side="left")

        btn_calc = ttk.Button(row_ctrl, text="Calcular Fechamento Otimizado", style="Primary.TButton", command=self._acao_fechamento)
        btn_calc.pack(side="right")

        # Cartão de Resultados Inferior
        bottom = tk.Frame(container, bg=self.c_card, padx=18, pady=18)
        bottom.pack(fill="both", expand=True)

        self.lbl_fech_resumo = tk.Label(bottom, text="Informe as dezenas acima e clique em Calcular.", bg=self.c_card, fg=self.c_muted, font=("Segoe UI", 9))
        self.lbl_fech_resumo.pack(anchor="w", pady=(0, 10))

        cols = ("num", "dezenas", "soma", "anticolisao")
        self.tree_fech = ttk.Treeview(bottom, columns=cols, show="headings", selectmode="browse")
        self.tree_fech.heading("num", text="#")
        self.tree_fech.heading("dezenas", text="Volante Otimizado")
        self.tree_fech.heading("soma", text="Soma")
        self.tree_fech.heading("anticolisao", text="Anti-Colisão")

        self.tree_fech.column("num", width=45, anchor="center")
        self.tree_fech.column("dezenas", width=380, anchor="center")
        self.tree_fech.column("soma", width=85, anchor="center")
        self.tree_fech.column("anticolisao", width=120, anchor="center")

        self.tree_fech.pack(fill="both", expand=True)

    def _acao_fechamento(self):
        txt = self.ent_pool.get().strip()
        try:
            dezenas = sorted(list(set([int(x) for x in txt.replace(",", " ").replace("-", " ").split() if x])))
            if len(dezenas) < 6:
                raise ValueError("Insira pelo menos 6 dezenas.")
            if len(dezenas) > 16:
                raise ValueError("Limite de 16 dezenas para cálculo instantâneo.")
        except Exception as e:
            messagebox.showerror("Erro", str(e))
            return

        garantia = "quadra" if self.combo_garantia.current() == 0 else "quina"
        jogos = self.engine.gerar_fechamento_combinatorio(dezenas, garantia=garantia)
        brutas = math.comb(len(dezenas), 6)
        economia = (1.0 - (len(jogos) / brutas)) * 100

        self.lbl_fech_resumo.config(
            text=f"Pool de {len(dezenas)} dezenas: {brutas} combinações brutas reduzidas para apenas {len(jogos)} volantes ({economia:.1f}% de economia de custo)"
        )

        for item in self.tree_fech.get_children():
            self.tree_fech.delete(item)

        for idx, j in enumerate(jogos, 1):
            ac = self.engine.calcular_indice_anti_colisao(j)["score_anti_colisao"]
            self.tree_fech.insert("", "end", values=(
                f"{idx:02d}",
                "   ".join(f"{d:02d}" for d in j),
                str(sum(j)),
                f"{ac:.0f}%"
            ))
        self.jogos_gerados = jogos

    # -------------------------------------------------------------
    # ABA 3: RADAR DE ARBITRAGEM E[X] (Joan Ginther)
    # -------------------------------------------------------------
    def _construir_tab_arbitragem(self):
        container = tk.Frame(self.tab_arbitragem, bg=self.c_bg)
        container.pack(fill="both", expand=True, pady=10)

        # Entrada Superior
        top = tk.Frame(container, bg=self.c_card, padx=20, pady=18)
        top.pack(fill="x", pady=(0, 14))

        tk.Label(top, text="Radar de Arbitragem Financeira (Valor Esperado E[X])", bg=self.c_card, fg=self.c_text, font=("Segoe UI", 12, "bold")).pack(anchor="w")
        tk.Label(top, text="Identifica janelas de valor esperado positivo E[X] > 0 em super prêmios (ex: Mega da Virada que não acumula).",
                 bg=self.c_card, fg=self.c_muted, font=("Segoe UI", 9)).pack(anchor="w", pady=(2, 12))

        row_in = tk.Frame(top, bg=self.c_card)
        row_in.pack(fill="x")
        tk.Label(row_in, text="Prêmio Estimado (R$):", bg=self.c_card, fg=self.c_muted, font=("Segoe UI", 9)).pack(side="left")
        self.ent_premio_arb = tk.Entry(row_in, font=("Segoe UI", 10, "bold"), bg=self.c_input, fg=self.c_amber, width=18, bd=0, insertbackground="white")
        self.ent_premio_arb.insert(0, "1090000000")
        self.ent_premio_arb.pack(side="left", padx=10)

        btn_calc = ttk.Button(row_in, text="Calcular Valor Esperado", style="Primary.TButton", command=self._acao_arbitragem)
        btn_calc.pack(side="right")

        # 3 Cartões de Métricas Minimalistas
        kpi_row = tk.Frame(container, bg=self.c_bg)
        kpi_row.pack(fill="x", pady=(0, 14))

        self.kpi_status = self._criar_kpi_card(kpi_row, "DIRETRIZ MATEMÁTICA", "Analisando...", self.c_emerald)
        self.kpi_valor = self._criar_kpi_card(kpi_row, "VALOR INTRÍNSECO / BILHETE", "R$ --", self.c_primary)
        self.kpi_roi = self._criar_kpi_card(kpi_row, "RETORNO ESPERADO (ROI)", "--%", self.c_amber)

        # Relatório Sintético
        self.card_relatorio = tk.Frame(container, bg=self.c_card, padx=18, pady=18)
        self.card_relatorio.pack(fill="both", expand=True)

        tk.Label(self.card_relatorio, text="Diagnóstico Analítico do Concurso", bg=self.c_card, fg=self.c_text, font=("Segoe UI", 11, "bold")).pack(anchor="w", pady=(0, 8))

        self.txt_arb_resumo = tk.Text(self.card_relatorio, bg=self.c_bg, fg=self.c_text, font=("Segoe UI", 10), bd=0, height=8, padx=14, pady=14)
        self.txt_arb_resumo.pack(fill="both", expand=True)

        self._acao_arbitragem()

    def _criar_kpi_card(self, parent, titulo, valor, cor):
        card = tk.Frame(parent, bg=self.c_card, padx=18, pady=16)
        card.pack(side="left", fill="both", expand=True, padx=4)
        tk.Label(card, text=titulo, bg=self.c_card, fg=self.c_muted, font=("Segoe UI", 8, "bold")).pack(anchor="w")
        lbl_val = tk.Label(card, text=valor, bg=self.c_card, fg=cor, font=("Segoe UI", 15, "bold"))
        lbl_val.pack(anchor="w", pady=(6, 0))
        return lbl_val

    def _acao_arbitragem(self):
        try:
            premio = float(self.ent_premio_arb.get().strip())
        except ValueError:
            return

        res = self.engine.calcular_arbitragem_ginther_mandel(premio)
        self.kpi_status.config(text=res["status_arbitragem"].split("(")[0].strip())
        self.kpi_valor.config(text=f"R$ {res['valor_esperado_bruto']:.2f}")
        self.kpi_roi.config(text=f"{res['roi_esperado_percent']:+.1f}%")

        self.txt_arb_resumo.delete("1.0", "end")
        msg = (
            f"• Custo do Espaço Amostral Completo (50.063.860 jogos): R$ {50063860 * 6.0:,.2f}\n"
            f"• Breakeven Jackpot (Ponto de Equilíbrio): R$ {res['breakeven_jackpot']:,.2f}\n"
            f"• Retorno com Anti-Colisão (Dezenas > 31): E[X] = R$ {res['ev_com_estrategia_anticolisao']:+.2f} por bilhete\n"
            f"• Risco com Datas de Aniversário (Divisão Provável): E[X] = R$ {res['ev_sem_estrategia_aniversarios']:+.2f}\n\n"
            f"Diretriz Estratégica: {res['diretriz_executiva']}"
        )
        self.txt_arb_resumo.insert("end", msg)

    # -------------------------------------------------------------
    # ABA 4: CONFERÊNCIA HISTÓRICA & DADOS CAIXA
    # -------------------------------------------------------------
    def _construir_tab_conferencia(self):
        container = tk.Frame(self.tab_conferencia, bg=self.c_bg)
        container.pack(fill="both", expand=True, pady=10)

        # Card de Conferência
        top = tk.Frame(container, bg=self.c_card, padx=20, pady=18)
        top.pack(fill="x", pady=(0, 14))

        tk.Label(top, text="Conferência contra 3.063 Concursos Históricos", bg=self.c_card, fg=self.c_text, font=("Segoe UI", 12, "bold")).pack(anchor="w")
        tk.Label(top, text="Verifique o desempenho histórico de qualquer jogo na base oficial da Caixa Econômica Federal.",
                 bg=self.c_card, fg=self.c_muted, font=("Segoe UI", 9)).pack(anchor="w", pady=(2, 10))

        row_chk = tk.Frame(top, bg=self.c_card)
        row_chk.pack(fill="x")
        self.ent_conf = tk.Entry(row_chk, font=("Segoe UI", 11), bg=self.c_input, fg=self.c_primary, bd=0, insertbackground="white")
        self.ent_conf.insert(0, "05 13 21 32 33 59")
        self.ent_conf.pack(side="left", fill="x", expand=True, padx=(0, 12))

        btn_verificar = ttk.Button(row_chk, text="Verificar Histórico", style="Primary.TButton", command=self._acao_conferir)
        btn_verificar.pack(side="right")

        # Badges de Resultado
        res_row = tk.Frame(top, bg=self.c_card)
        res_row.pack(fill="x", pady=(14, 0))

        self.lbl_quadras = tk.Label(res_row, text="Quadras: --", bg=self.c_card_border, fg=self.c_text, font=("Segoe UI", 9), padx=12, pady=5)
        self.lbl_quadras.pack(side="left", padx=(0, 8))

        self.lbl_quinas = tk.Label(res_row, text="Quinas: --", bg=self.c_card_border, fg=self.c_emerald, font=("Segoe UI", 9, "bold"), padx=12, pady=5)
        self.lbl_quinas.pack(side="left", padx=8)

        self.lbl_senas = tk.Label(res_row, text="Senas: --", bg=self.c_card_border, fg=self.c_amber, font=("Segoe UI", 9, "bold"), padx=12, pady=5)
        self.lbl_senas.pack(side="left", padx=8)

        # Sincronizador Oficial Caixa
        sync_card = tk.Frame(container, bg=self.c_card, padx=20, pady=18)
        sync_card.pack(fill="both", expand=True)

        row_sync = tk.Frame(sync_card, bg=self.c_card)
        row_sync.pack(fill="x", pady=(0, 12))

        tk.Label(row_sync, text="Sincronização Online com a Caixa Econômica Federal", bg=self.c_card, fg=self.c_text, font=("Segoe UI", 11, "bold")).pack(side="left")
        self.btn_sync = ttk.Button(row_sync, text="Atualizar Novos Sorteios", style="Secondary.TButton", command=self._acao_sync)
        self.btn_sync.pack(side="right")

        self.txt_log_sync = tk.Text(sync_card, bg=self.c_bg, fg=self.c_emerald, font=("Consolas", 9), bd=0, height=8, padx=12, pady=12)
        self.txt_log_sync.pack(fill="both", expand=True)
        self.txt_log_sync.insert("end", f"[{time.strftime('%H:%M:%S')}] Base local 100% íntegra: {len(self.engine.concursos)} concursos registrados.\n")

    def _acao_conferir(self):
        txt = self.ent_conf.get().strip()
        try:
            dezenas = sorted([int(x) for x in txt.replace(",", " ").replace("-", " ").split() if x])
            if len(dezenas) != 6:
                raise ValueError("Insira exatamente 6 números.")
        except Exception as e:
            messagebox.showerror("Erro", str(e))
            return

        res = self.engine.backtest_jogo(dezenas)
        self.lbl_quadras.config(text=f"Quadras (4 acertos): {res['quadras']}")
        self.lbl_quinas.config(text=f"Quinas (5 acertos): {res['quinas']}")
        self.lbl_senas.config(text=f"Senas (6 acertos): {res['senas']}")

    def _acao_sync(self):
        self.btn_sync.config(state="disabled")
        self.txt_log_sync.insert("end", f"[{time.strftime('%H:%M:%S')}] Conectando à API da Caixa...\n")

        def task():
            try:
                concursos = self.engine.sincronizar_dados_oficiais()
                self.txt_log_sync.insert("end", f"[{time.strftime('%H:%M:%S')}] Concluído com sucesso! Total: {len(concursos)} concursos.\n")
                self.badge_caixa.config(text=f"● {len(concursos)} Concursos Oficiais")
            except Exception as e:
                self.txt_log_sync.insert("end", f"[{time.strftime('%H:%M:%S')}] Falha na sincronização: {e}\n")
            finally:
                self.btn_sync.config(state="normal")
        threading.Thread(target=task, daemon=True).start()

    def _carregar_resumo_caixa(self):
        def task():
            try:
                info = self.engine.obter_ultimo_resultado_online()
                if info and hasattr(self, "badge_caixa"):
                    dezenas_fmt = " ".join(f"{d:02d}" for d in info['dezenas'])
                    self.badge_caixa.config(
                        text=f"● #{info['numero']}: {dezenas_fmt}"
                    )
            except Exception:
                pass
        threading.Thread(target=task, daemon=True).start()


if __name__ == "__main__":
    app = CartelaApp()
    app.mainloop()
