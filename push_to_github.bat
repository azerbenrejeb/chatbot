@echo off
echo ============================================================
echo   ENREGISTREMENT ET PUSH DES MODIFICATIONS SUR GITHUB
echo ============================================================
echo.

git add .
set /p commit_msg="Entrez le message de commit (ou appuyez sur Entrée): "
if "%commit_msg%"=="" set commit_msg="Sauvegarde automatique du projet Chatbot ESG"

git commit -m "%commit_msg%"
echo.
echo Envoi vers GitHub...
git push -u origin main

echo.
echo ============================================================
echo   OPERATION TERMINEE !
echo ============================================================
pause
