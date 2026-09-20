@echo off
title Lancement - Chatbot ESG RSE Time
echo ============================================================
echo   DEMARRAGE DE L'APPLICATION CHATBOT ESG (IA & RSE)
echo ============================================================
echo.

cd /d "%~dp0"

echo [1/3] Verification d'Ollama (Mistral 7B)...
netstat -ano | findstr 11434 >nul
if %errorlevel% neq 0 (
    echo [INFO] Demarrage d'Ollama en arriere-plan...
    start "" ollama serve
    timeout /t 3 /nobreak >nul
) else (
    echo [OK] Ollama est actif.
)

echo [2/3] Lancement du Backend FastAPI (port 8000)...
start "FastAPI Backend ESG" /min cmd /c "python -m uvicorn app.main:app --host 127.0.0.1 --port 8000"
timeout /t 2 /nobreak >nul

echo [3/3] Lancement de l'Interface Streamlit (port 8501)...
python -m streamlit run modules/module4_chatbot/chatbot_app.py

pause
