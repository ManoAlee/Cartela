# 🏛 Arquitetura de Software & Design System

Este documento detalha as decisões arquiteturais, padrões de engenharia e diretrizes de concorrência implementadas no **Cartela**.

---

## 1. Visão Modular C4 (Level 2 — Containers)

```mermaid
graph TB
    subgraph Client Application
        GUI["Presentation Layer<br/>Tkinter Dark Slate GUI<br/>(gui.py)"]
        CLI["CLI Layer<br/>Standalone Scripts<br/>(run_app.py / examples)"]
    end

    subgraph Core Mathematical Engine
        Engine["MegaSenaEngine<br/>Singleton Thread-Safe<br/>(engine.py)"]
        RLock["Reentrant Lock<br/>(threading.RLock)"]
        Engine --- RLock
    end

    subgraph Data & Persistence Layer
        CacheFile[("JSON Cache<br/>mega_cache.json<br/>(3.063 concursos)")]
        CSVFile[("Tabular Export<br/>mega_history.csv")]
        CaixaAPI["External Service<br/>Caixa REST API"]
    end

    GUI -->|Calls Engine Methods| Engine
    CLI -->|Calls Engine Methods| Engine
    Engine -->|Reads / Updates| CacheFile
    Engine -->|Synchronizes with Fallback| CaixaAPI
    Engine -->|Exports| CSVFile
```

---

## 2. Padrões de Concorrência & Thread-Safety

A interface gráfica executa operações pesadas (como requisições HTTP à API da Caixa e cálculos de cobertura combinatória) em segundo plano através de instâncias de `threading.Thread(daemon=True)`.

### Blindagem de Concorrência:
- O motor `MegaSenaEngine` utiliza um **Reentrant Lock (`threading.RLock`)** interno.
- Leituras aos arrays de concursos, recalibração da matriz de covariância e escritas no arquivo de cache local são atomicamente protegidas.
- A interface de usuário agenda mutações visuais de forma segura e síncrona.

---

## 3. Estrutura de Diretórios Padronizada

```text
Cartela/
├── run_app.py                   # Ponto de entrada canônico
├── pyproject.toml               # Padrão PEP 517/518/621
├── requirements.txt             # Dependências de produção
├── LICENSE                      # Licença MIT
├── CITATION.cff                 # Metadados para citação científica
├── README.md                    # Documentação principal
├── docs/
│   ├── MATHEMATICAL_SPECIFICATION.md # Whitepaper matemático formal
│   ├── ARCHITECTURE.md          # Arquitetura e concorrência
│   ├── CONTRIBUTING.md          # Guia de contribuição e TDD
│   └── SECURITY.md              # Política de segurança
├── .github/
│   └── workflows/
│       └── ci.yml               # CI Pipeline multiplataforma
├── tests/
│   └── test_engine.py           # 12 testes unitários formais
├── examples/
│   └── quickstart_analysis.py   # Script rápido de demonstração
└── app_files/
    ├── data/                    # Base de dados oficial da Caixa
    └── src/
        ├── app/                 # Camada gráfica (Tkinter)
        └── core/                # Motor estatístico e combinatório
```
