@echo off
REM QuickCommerce India launcher (Windows). First run sets up a venv + deps.
setlocal

cd /d "%~dp0"

if not exist ".venv\" (
  echo [setup] Creating virtual environment...
  python -m venv .venv
  call .venv\Scripts\activate.bat
  echo [setup] Installing dependencies...
  python -m pip install --upgrade pip >nul
  pip install -r requirements.txt
) else (
  call .venv\Scripts\activate.bat
)

if not exist ".env" (
  echo [info] No .env found - copying .env.example. App runs with rule-based
  echo        explanations until you add QC_ANTHROPIC_API_KEY.
  copy /y ".env.example" ".env" >nul
)

echo [run] Starting on http://127.0.0.1:8000  (Ctrl+C to stop)
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload

endlocal
