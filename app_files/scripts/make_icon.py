```python
from PIL import Image
import os

SRC = os.path.join('bingo.png')
OUT_DIR = os.path.join('resources')
OUT = os.path.join(OUT_DIR, 'bingo.ico')

os.makedirs(OUT_DIR, exist_ok=True)

if not os.path.exists(SRC):
    raise SystemExit('Arquivo bingo.png não encontrado no diretório do projeto.')

img = Image.open(SRC).convert('RGBA')
# Typical Windows icons contain multiple sizes; Pillow will save multiple sizes if provided
sizes = [(256,256),(128,128),(64,64),(48,48),(32,32),(16,16)]
icon_sizes = [s for s in sizes]
img.save(OUT, format='ICO', sizes=icon_sizes)
print('Ícone gerado em', OUT)

```