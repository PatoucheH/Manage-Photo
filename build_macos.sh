#!/bin/bash

echo ""
echo "========================================"
echo "  Photo Manager - Build macOS"
echo "  (Compatible Tk 8.5+)"
echo "========================================"
echo ""

# Se placer dans le répertoire du script
cd "$(dirname "$0")"

# Vérifier Python
if ! command -v python3 &> /dev/null; then
    echo "[ERREUR] Python 3 n'est pas installé."
    echo "         Installez Python via: brew install python"
    exit 1
fi

echo "[1/4] Création de l'environnement virtuel..."
if [ ! -d "build_env" ]; then
    python3 -m venv build_env
fi
source build_env/bin/activate

echo ""
echo "[2/4] Installation des dépendances..."
pip install --upgrade pip > /dev/null 2>&1
pip install pyinstaller python-docx Pillow

echo ""
echo "[3/4] Génération de l'application macOS..."
echo "      Cela peut prendre quelques minutes..."
echo ""

pyinstaller --noconfirm --onefile --windowed \
    --name "PhotoManager" \
    --hidden-import "PIL._tkinter_finder" \
    --hidden-import "docx" \
    --hidden-import "docx.parts.image" \
    --hidden-import "lxml.etree" \
    --hidden-import "lxml._elementpath" \
    --osx-bundle-identifier "com.photomanager.app" \
    photo_manager.py

echo ""

# Créer le bundle .app manuellement si nécessaire
if [ -f "dist/PhotoManager" ]; then
    echo "[3.5/4] Création du bundle .app..."

    APP_DIR="dist/PhotoManager.app"
    CONTENTS_DIR="${APP_DIR}/Contents"
    MACOS_DIR="${CONTENTS_DIR}/MacOS"
    RESOURCES_DIR="${CONTENTS_DIR}/Resources"

    # Créer la structure
    mkdir -p "${MACOS_DIR}"
    mkdir -p "${RESOURCES_DIR}"

    # Copier l'exécutable
    cp "dist/PhotoManager" "${MACOS_DIR}/PhotoManager"
    chmod +x "${MACOS_DIR}/PhotoManager"

    # Créer Info.plist
    cat > "${CONTENTS_DIR}/Info.plist" << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleName</key>
    <string>Photo Manager</string>
    <key>CFBundleDisplayName</key>
    <string>Photo Manager</string>
    <key>CFBundleIdentifier</key>
    <string>com.photomanager.app</string>
    <key>CFBundleVersion</key>
    <string>1.0.0</string>
    <key>CFBundleShortVersionString</key>
    <string>1.0.0</string>
    <key>CFBundleExecutable</key>
    <string>PhotoManager</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>NSHighResolutionCapable</key>
    <true/>
    <key>NSRequiresAquaSystemAppearance</key>
    <false/>
    <key>LSMinimumSystemVersion</key>
    <string>10.13</string>
</dict>
</plist>
EOF
fi

if [ -d "dist/PhotoManager.app" ]; then
    echo ""
    echo "========================================"
    echo "         BUILD REUSSI !"
    echo "========================================"
    echo ""
    echo "[4/4] Application créée avec succès !"
    echo ""
    echo "      Application: dist/PhotoManager.app"
    echo ""
    echo "      Vous pouvez glisser cette application dans votre"
    echo "      dossier Applications et double-cliquer pour lancer."
    echo ""

    # Copier dans le dossier principal
    cp -R "dist/PhotoManager.app" "PhotoManager.app" 2>/dev/null
    echo "      Une copie a été placée dans le dossier actuel."
elif [ -f "dist/PhotoManager" ]; then
    echo ""
    echo "========================================"
    echo "         BUILD REUSSI !"
    echo "========================================"
    echo ""
    echo "[4/4] Exécutable créé: dist/PhotoManager"
    echo ""
    echo "      Double-cliquez dessus pour lancer l'application."
else
    echo "[ERREUR] La génération a échoué."
    echo "         Vérifiez les messages d'erreur ci-dessus."
    exit 1
fi

echo ""
