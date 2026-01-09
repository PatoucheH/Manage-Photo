@echo off
echo ================================
echo   Photo Manager - Demarrage
echo ================================
echo.

REM Verifier si Python est installe
python --version >nul 2>&1
if errorlevel 1 (
    echo ERREUR: Python n'est pas installe ou n'est pas dans le PATH.
    echo Veuillez installer Python depuis https://www.python.org/downloads/
    pause
    exit /b 1
)

REM Verifier si l'environnement virtuel existe
if exist "venv\Scripts\activate.bat" (
    echo Activation de l'environnement virtuel...
    call venv\Scripts\activate.bat
) else (
    echo Creation de l'environnement virtuel...
    python -m venv venv
    call venv\Scripts\activate.bat

    echo Installation des dependances...
    pip install -r requirements.txt
)

echo.
echo Lancement de Photo Manager...
echo.
python photo_manager.py

pause
