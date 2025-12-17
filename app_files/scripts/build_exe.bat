```bat
@echo off
REM Build .exe usando PyInstaller (Windows)
@echo off
REM Build .exe usando PyInstaller (Windows)
SET SCRIPT_DIR=%~dp0
cd /d %SCRIPT_DIR%..
cd /d %SCRIPT_DIR%..\..
if exist .venv\Scripts\activate.bat (
  call .venv\Scripts\activate.bat
) else (
  echo Venv não encontrado ou não ativado. Continue mesmo assim se o pyinstaller estiver global.
)
pyinstaller --noconfirm --onefile --name Cartela --windowed --icon "app_files\resources\bingo.ico" --add-data "app_files\\data\\mega_cache.json;." --add-data "app_files;app_files" --add-data "app_files\\resources;resources" app_files\run_app.py
if %errorlevel% equ 0 (
  echo Build concluido. Arquivo em dist\Cartela.exe
) else (
  echo Build falhou com codigo %errorlevel%
)
if %errorlevel% equ 0 (
  echo Build concluido. Arquivo em dist\Cartela.exe
) else (
  echo Build falhou com codigo %errorlevel%
)
```