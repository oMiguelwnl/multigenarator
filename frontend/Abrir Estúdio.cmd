@echo off
setlocal
cd /d "%~dp0.."
if not exist ".venv-studio-win\Scripts\python.exe" (
  echo Ambiente Python nao encontrado. Instale as dependencias conforme frontend/README.md.
  pause
  exit /b 1
)
if not exist "frontend\dist\index.html" (
  echo Compile a interface primeiro: npm --prefix frontend run build
  pause
  exit /b 1
)
set "PYTHONPATH=%CD%\src"
set "MULTILANG_STUDIO_CONNECTIONS_ENABLED=1"
echo O link de acesso sera exibido abaixo. Mantenha esta janela aberta.
".venv-studio-win\Scripts\python.exe" -m multilang.studio.server
pause
