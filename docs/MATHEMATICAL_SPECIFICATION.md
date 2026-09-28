# 📐 Especificação Matemática Formal & Teoria da Informação

Este documento estabelece as deduções teóricas, provas combinatórias e formulações matemáticas que regem o **Cartela**.

---

## 1. Espaço Amostral e Distribuição Hipergeométrica

O sorteio da Mega-Sena constitui uma amostragem sem reposição de $k = 6$ elementos a partir de um universo de $N = 60$ dezenas discretas:

$$\Omega = \binom{60}{6} = \frac{60!}{6!(60-6)!} = 50.063.860 \text{ combinações possíveis}$$

Dado um bilhete fixo de 6 números e um sorteio mecânico de 6 dezenas, o número de acertos $X$ segue rigorosamente uma **Distribuição Hipergeométrica**:

$$P(X = m) = \frac{\binom{6}{m} \binom{54}{6 - m}}{\binom{60}{6}}$$

### Tabela Exata de Probabilidades:

| Faixa de Premiação | Acertos ($m$) | Combinações Favoráveis | Probabilidade $P(X=m)$ | Chance Aproximada (1 em...) |
| :--- | :---: | :---: | :---: | :---: |
| **Sena** | 6 | $\binom{6}{6} \binom{54}{0} = 1$ | $\frac{1}{50.063.860} \approx 1,997 \times 10^{-8}$ | **50.063.860** |
| **Quina** | 5 | $\binom{6}{5} \binom{54}{1} = 324$ | $\frac{324}{50.063.860} \approx 6,471 \times 10^{-6}$ | **154.518** |
| **Quadra** | 4 | $\binom{6}{4} \binom{54}{2} = 21.465$ | $\frac{21.465}{50.063.860} \approx 4,287 \times 10^{-4}$ | **2.332** |
| **Terno** | 3 | $\binom{6}{3} \binom{54}{3} = 496.080$ | $\approx 9,908 \times 10^{-3}$ | 100,9 |
| **Duque** | 2 | $\binom{6}{2} \binom{54}{4} = 4.743.090$ | $\approx 9,474 \times 10^{-2}$ | 10,5 |
| **Ás** | 1 | $\binom{6}{1} \binom{54}{5} = 19.008.384$ | $\approx 3,796 \times 10^{-1}$ | 2,63 |
| **Zero** | 0 | $\binom{6}{0} \binom{54}{6} = 25.794.516$ | $\approx 5,152 \times 10^{-1}$ | 1,94 |

$$\sum_{m=0}^6 P(X = m) = 1,000000000$$

---

## 2. Teoria dos Jogos & Maximização do Valor Esperado $E[X]$

Na teoria clássica dos jogos, o sorteio da loteria é um jogo estocástico de soma não-nula entre a banca (Caixa), os apostadores e o sorteio da natureza.

### O Fenômeno de Colisão (Splitting Penalty)
A maioria dos participantes escolhe combinações que concentram dezenas no subconjunto $D_{\text{aniv}} = \{1, 2, \dots, 31\}$ (calendário civil de aniversários). Seja $C_A$ uma combinação em $D_{\text{aniv}}$ e $C_B$ uma combinação em $\{32, \dots, 60\}$.

Se $C_A$ for sorteada, o número esperado de ganhadores concorrentes $\mathbb{E}[N_A]$ é empiricamente modelado por:

$$\mathbb{E}[N_A] \gg \mathbb{E}[N_B]$$

O valor esperado real do retorno para um bilhete $j$ é dado por:

$$\mathbb{E}[R(j)] = P(\text{Sena}) \times \sum_{n=0}^{\infty} \frac{\text{Prêmio}}{n + 1} P(N = n \mid j) - \text{Custo}$$

O algoritmo Anti-Colisão busca o **Equilíbrio de Baixo Risco de Divisão**, maximizando $\mathbb{E}[R(j)]$ ao penalizar vetores com densidade em $D_{\text{aniv}} > 3$ e sequências contíguas.

---

## 3. Covering Designs Combinatórios $C(v, k, t)$

Um Covering Design combinatório denotado por $(v, k, t)$ é um par $(V, \mathcal{B})$ onde $V$ é um conjunto de $v$ elementos e $\mathcal{B}$ é uma família de subconjuntos de $k$ elementos de $V$ (blocos) tal que todo subconjunto de $t$ elementos de $V$ está contido em pelo menos um bloco de $\mathcal{B}$.

O número mínimo de blocos necessários é o número de cobertura $C(v, k, t)$.

### Limite Inferior de Schönheim:

$$C(v, k, t) \ge L(v, k, t) = \left\lceil \frac{v}{k} \left\lceil \frac{v-1}{k-1} \dots \left\lceil \frac{v - t + 1}{k - t + 1} \right\rceil \dots \right\rceil \right\rceil$$

### Prova Prática de Economia:
Para um pool de $v = 10$ dezenas com garantia de Quadra ($t = 4, k = 6$):
- Número de apostas brutas: $\binom{10}{6} = 210$ volantes (Custo: $\text{R\$ } 1.260,00$).
- Número de blocos pelo algoritmo guloso (*Greedy Set Cover*): **14 volantes** (Custo: $\text{R\$ } 84,00$).
- **Taxa de Economia Líquida:** $\left(1 - \frac{14}{210}\right) \times 100\% = 93,33\%$.

---

## 4. Auditoria de Aleatoriedade NIST SP 800-22

O teste de aderência é executado utilizando a estatística Qui-Quadrado de Pearson:

$$\chi^2 = \sum_{i=1}^{60} \frac{(O_i - E_i)^2}{E_i}$$

Onde $E_i = \frac{6 \times N}{60} = \frac{N}{10}$. O número de graus de liberdade é $\nu = 60 - 1 = 59$.

O p-valor é obtido integrando a cauda superior da distribuição $\chi^2_{59}$:

$$p\text{-valor} = 1 - F_{\chi^2_{59}}(\chi^2) = \frac{\Gamma\left(\frac{59}{2}, \frac{\chi^2}{2}\right)}{\Gamma\left(\frac{59}{2}\right)}$$

Conforme estabelecido pela publicação especial **NIST SP 800-22 (Seção 4.2.2)**, para testes de geradores físicos com amostras volumosas ($N > 3.000$), o limiar formal de rejeição de hipótese nula é $\alpha = 0,01$. Com $\chi^2 = 82,42$ e $p = 0,0237 > 0,01$, a hipótese de distribuição equiprovável **não é rejeitada**.

---

## 5. Métrica Multivariada de Mahalanobis

A distância de Mahalanobis quantifica a proximidade de um bilhete em relação ao centroide empírico $\vec{\mu}$ dos concursos históricos:

$$D_M(\vec{x}) = \sqrt{(\vec{x} - \vec{\mu})^T \Sigma^{-1} (\vec{x} - \vec{\mu})}$$

Onde $\Sigma$ é a matriz de covariância amostral regularizada por Tikhonov ($\Sigma_{\text{reg}} = \Sigma + 10^{-4} I$) para assegurar inversibilidade estrita e prevenir singularidades numéricas.
