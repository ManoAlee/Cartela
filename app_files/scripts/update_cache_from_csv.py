```python
import csv
import json
import shutil
import os
import datetime

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
DATA_DIR = os.path.join(BASE, 'data')
SRC = os.path.join(DATA_DIR, 'mega_full_from_local.csv')
CACHE = os.path.join(DATA_DIR, 'mega_cache.json')

now = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
BAK = CACHE + '.bak.' + now

if os.path.exists(CACHE):
    shutil.copy(CACHE, BAK)
    print('Backup criado:', BAK)
else:
    print('Arquivo de cache não existe, nenhum backup criado.')

out = []
with open(SRC, newline='', encoding='utf-8') as f:
    sample = f.readline()
    delim = ';' if ';' in sample else ','
    f.seek(0)
    reader = csv.reader(f, delimiter=delim)
    try:
        headers = next(reader)
    except StopIteration:
        print('CSV vazio')
        headers = []

    bola_idx = [i for i,h in enumerate(headers) if 'bola' in h.lower()]
    if not bola_idx:
        # assume columns: Num, bola 1..6 -> bolas at indices 1..6
        bola_idx = list(range(1,7))

    for row in reader:
        if len(row) <= max(bola_idx):
            continue
        try:
            nums = [int(row[i]) for i in bola_idx]
        except Exception:
            continue
        out.append(nums)

os.makedirs(DATA_DIR, exist_ok=True)
with open(CACHE, 'w', encoding='utf-8') as g:
    json.dump(out, g, ensure_ascii=False)

print('Escreveu', len(out), 'entradas em', CACHE)

```