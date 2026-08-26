@echo off
cd /d %~dp0
where docker >nul 2>nul
if %ERRORLEVEL%==0 (
  docker compose up --build -d
  echo.
  echo Ortho Aux iniciado.
  echo Docs:    http://127.0.0.1:8000/docs
  echo OpenAPI: http://127.0.0.1:8000/openapi.json
  echo Health:  http://127.0.0.1:8000/health
  exit /b 0
)

where py >nul 2>nul
if %ERRORLEVEL% neq 0 (
  echo Docker ou Python 3 e necessario.
  exit /b 1
)

py -m venv .venv
call .venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
if not exist data mkdir data
set ORTHO_AUX_DB=%CD%\data\ortho_aux.sqlite3
uvicorn app.main:app --host 0.0.0.0 --port 8000
