#!/bin/bash

echo "================================"
echo "  Photo Manager - Démarrage"
echo "================================"
echo

# Vérifier si Python est installé
if ! command -v python3 &> /dev/null; then
    echo "ERREUR: Python 3 n'est pas installé."
    echo "Installez Python via: brew install python"
    exit 1
fi

# Se placer dans le répertoire du script
cd "$(dirname "$0")"

# Vérifier si l'environnement virtuel existe
if [ -d "venv" ]; then
    echo "Activation de l'environnement virtuel..."
    source venv/bin/activate
else
    echo "Création de l'environnement virtuel..."
    python3 -m venv venv
    source venv/bin/activate

    echo "Installation des dépendances..."
    pip install -r requirements.txt
fi

echo
echo "Lancement de Photo Manager..."
echo

python photo_manager.py
