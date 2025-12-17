```python
import sys
import os

# When PyInstaller bundles the app as onefile, it extracts resources to a
# temporary folder available at `sys._MEIPASS`. Many parts of the project
# expect to open files like `mega_cache.json` using relative paths, so when
# frozen we change the current working directory to the extracted folder so
# relative file accesses continue to work.
ROOT = os.path.dirname(os.path.abspath(__file__))
if getattr(sys, 'frozen', False) and getattr(sys, '_MEIPASS', None):
    os.chdir(sys._MEIPASS)
else:
    # when running from source, ensure working directory is the app_files folder
    try:
        os.chdir(ROOT)
    except Exception:
        pass

# Ensure project src is importable when running from source
SRC = os.path.join(ROOT, 'src')
if SRC not in sys.path:
    sys.path.insert(0, SRC)

try:
    from src.app.gui import CartelaApp
except Exception as e:
    print('Erro ao importar GUI:', e)
    raise

if __name__ == '__main__':
    app = CartelaApp()
    app.mainloop()

```