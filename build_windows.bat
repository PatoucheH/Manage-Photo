@echo off
chcp 65001 >nul
echo.
echo ╔═══════════════════════════════════════════════════════════╗
echo ║     Photo Manager - Build Windows Executable              ║
echo ╚═══════════════════════════════════════════════════════════╝
echo.

REM Vérifier Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERREUR] Python n'est pas installé ou n'est pas dans le PATH.
    echo          Téléchargez Python: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo [1/4] Création de l'environnement virtuel...
if not exist "build_env" (
    python -m venv build_env
)
call build_env\Scripts\activate.bat

echo.
echo [2/4] Installation des dépendances...
pip install --upgrade pip >nul 2>&1
pip install pyinstaller customtkinter python-docx Pillow

echo.
echo [3/4] Génération de l'exécutable Windows...
echo       Cela peut prendre quelques minutes...
echo.

pyinstaller --noconfirm --onefile --windowed ^
    --name "PhotoManager" ^
    --add-data "build_env\Lib\site-packages\customtkinter;customtkinter" ^
    --hidden-import "PIL._tkinter_finder" ^
    --hidden-import "customtkinter" ^
    --hidden-import "docx" ^
    --hidden-import "docx.parts.image" ^
    --hidden-import "lxml.etree" ^
    --hidden-import "lxml._elementpath" ^
    photo_manager.py

echo.
if exist "dist\PhotoManager.exe" (
    echo ╔═══════════════════════════════════════════════════════════╗
    echo ║                    BUILD RÉUSSI !                         ║
    echo ╚═══════════════════════════════════════════════════════════╝
    echo.
    echo [4/4] Exécutable créé avec succès !
    echo.
    echo       Fichier: dist\PhotoManager.exe
    echo.
    echo       Vous pouvez copier ce fichier n'importe où et
    echo       double-cliquer dessus pour lancer l'application.
    echo.

    REM Copier dans le dossier principal pour plus de visibilité
    copy "dist\PhotoManager.exe" "PhotoManager.exe" >nul 2>&1
    echo       Une copie a été placée dans le dossier actuel.
) else (
    echo [ERREUR] La génération a échoué.
    echo          Vérifiez les messages d'erreur ci-dessus.
)

echo.
pause
