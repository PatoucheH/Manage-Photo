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

# Supprimer ancien venv si besoin
if [ -d "venv" ]; then
    echo "Activation de l environnement virtuel..."
    source venv/bin/activate
else
    echo "Creation de l environnement virtuel..."
    python3 -m venv venv
    source venv/bin/activate

    echo "Installation des dependances..."
    pip install -r requirements.txt
fi

echo
echo "Lancement de Photo Manager..."
echo

# Suppress Tk deprecation warning
export TK_SILENCE_DEPRECATION=1

python3 photo_manager.py
