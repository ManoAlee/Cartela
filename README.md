````markdown
# Gerador Mega & Tele

Pequeno conjunto de scripts para gerar jogos da Mega da Virada e ranquear cartelas da Tele Sena usando distância de Mahalanobis.

Arquivos:
- `mega_da_virada.py` — motor do gerador Mega (CLI + PDF).
- `tele_sena_math.py` — motor Mahalanobis para Tele Sena (top-k cartelas semelhantes).
- `mega_gui.py` — interface gráfica (Tkinter) para gerar jogos e salvar resultados.
- `requirements.txt` — dependências opcional: `numpy`, `fpdf`.

Instalação:

```bash
python -m pip install -r requirements.txt
```

Uso CLI:

```bash
# Mega: gera 20 jogos
python mega_da_virada.py 20

# Mega: gera 50 e salva PDF
python mega_da_virada.py 50 --pdf volantes.pdf

# Mega: força baixar histórico e salva CSV
python mega_da_virada.py 30 --update --csv volantes.csv

# Tele Sena: top 10 (padrão 50k candidatos)
Cartela — Distribuição

Arquivos na raiz:
- `Cartela.exe` — executável principal (onefile). Este é o único binário fora de pastas.
- `README.md` — este arquivo.

Todo o restante do projeto foi organizado dentro da pasta `app_files/` para manter a raiz limpa.

Estrutura gerada:
- app_files/
	- src/ (código fonte)
	- data/ (dados, incluindo `mega_cache.json`)
	- resources/ (ícone `bingo.ico` etc.)
	- scripts/ (scripts de build e utilitários)
	- tests/
	- build/ (artefatos de build anteriores)
	- outros arquivos e configurações do projeto
- dist/Cartela.exe

Como usar
1. Executar localmente (Windows): clique em `Cartela.exe` na raiz. O exe é "onefile" e contém os arquivos necessários.
2. Se precisar atualizar o histórico: abra `app_files\scripts\update_cache_from_csv.py` e rode com Python para regenerar `app_files\data\mega_cache.json`.
3. Para rebuild: ative o venv e rode `app_files\scripts\build_exe.ps1` (PowerShell) ou `app_files\scripts\build_exe.bat`.

Notas
- A pasta `.venv` foi mantida na raiz para o ambiente de desenvolvimento; se preferir movê-la, faça antes de distribuir.
- O `Cartela.exe` é empacotado para Windows x64; para garantir portabilidade em outras máquinas, instale o `Microsoft Visual C++ Redistributable` compatível ou gere um build em uma máquina alvo.
- Verifique `app_files\scripts\README_packaging.md` para instruções detalhadas de empacotamento.

Contato
- Se quiser que eu gere um instalador/zip final contendo apenas `Cartela.exe` e uma licença/README, diga e eu preparo.
````