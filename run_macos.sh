#!/bin/bash

echo "================================"
echo "  Photo Manager - Demarrage"
echo "================================"
echo

# Verifier si Python est installe
if ! command -v python3 &> /dev/null; then
    echo "ERREUR: Python 3 n est pas installe."
    echo "Installez Python via: brew install python"
    exit 1
fi

# Se placer dans le repertoire du script
cd "$(dirname "$0")"

# Creer venv si necessaire
if [ ! -d "venv" ]; then
    echo "Creation de l environnement virtuel..."
    python3 -m venv venv
fi

echo "Activation de l environnement virtuel..."
source venv/bin/activate

# Verifier et installer les dependances si manquantes
if ! python3 -c "import PyQt5" 2>/dev/null; then
    echo "Installation des dependances..."
    pip install --quiet -r requirements.txt
fi

echo
echo "Lancement de Photo Manager..."
echo

# Suppress Tk deprecation warning
export TK_SILENCE_DEPRECATION=1

python3 photo_manager.py
