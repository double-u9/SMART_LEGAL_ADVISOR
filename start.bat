@echo off
echo ===============================================
echo   Smart Legal Advisor — Startup Script
echo   المستشار القانوني الذكي
echo ===============================================
echo.

REM --- 1. Check Ollama ---
echo [1/7] Checking Ollama...
where ollama >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Ollama not found! Install from: https://ollama.com
    echo After installing, run: ollama pull llama3.1
    pause
    exit /b 1
)
echo [OK] Ollama found

REM --- 2. Check/Pull Model ---
echo [2/7] Checking Ollama model...
ollama list | findstr /i "llama3.1" >nul 2>&1
if %errorlevel% neq 0 (
    echo [INFO] Pulling llama3.1 model, this may take a while...
    ollama pull llama3.1
)
echo [OK] Model ready

REM --- 3. Start Qdrant ---
echo [3/7] Starting Qdrant...
docker compose up -d qdrant 2>nul
if %errorlevel% neq 0 (
    echo [WARN] Docker not available. Attempting to start Qdrant directly...
    echo [INFO] Please start Qdrant manually: docker compose up -d
)
echo [OK] Qdrant started

REM --- 4. Setup Python Virtual Environment ---
echo [4/7] Setting up Python virtual environment...
cd /d "%~dp0"
if not exist venv (
    echo [INFO] Creating virtual environment...
    python -m venv venv
)
echo [INFO] Installing Python dependencies...
call venv\Scripts\activate
pip install -r requirements.txt >nul
echo [OK] Python dependencies ready

REM --- 5. Install Frontend Dependencies ---
echo [5/7] Checking Frontend dependencies...
cd /d "%~dp0frontend"
if not exist node_modules (
    echo [INFO] Installing frontend dependencies...
    call npm install >nul
)
echo [OK] Frontend dependencies ready

REM --- 6. Start Backend ---
echo [6/7] Starting Backend...
cd /d "%~dp0"
set HF_HOME=./.models_cache
start "Smart Legal Advisor - Backend" cmd /c "call venv\Scripts\activate && python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload"
echo [OK] Backend starting on http://localhost:8000

REM --- 7. Start Frontend ---
echo [7/7] Starting Frontend...
cd /d "%~dp0frontend"
start "Smart Legal Advisor - Frontend" cmd /c "npm run dev"
echo [OK] Frontend starting on http://localhost:3000

echo.
echo ===============================================
echo   All services started!
echo   Backend:  http://localhost:8000
echo   Frontend: http://localhost:3000
echo   Qdrant:   http://localhost:6333
echo   API Docs: http://localhost:8000/docs
echo ===============================================
echo.
echo Press any key to open the app in your browser...
pause >nul
start http://localhost:3000
