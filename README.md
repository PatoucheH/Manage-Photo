# Photo Manager - Générateur de Document Word

Application desktop cross-platform pour organiser vos photos et les exporter vers un document Word.

## Fonctionnalités

- **Sélection de photos** : Choisissez un dossier complet ou sélectionnez des fichiers individuels
- **Mise en page flexible** : 4, 6 ou 9 photos par page
- **Prévisualisation** : Visualisez vos pages avant l'export
- **Rotation des photos** : Pivotez chaque photo de 90° directement dans l'aperçu
- **Export Word** : Générez un document .docx professionnel prêt à imprimer

## Formats supportés

- JPG / JPEG
- PNG

---

## Installation Rapide (Exécutables)

### Pour les utilisateurs finaux

**Aucune installation requise !** Téléchargez simplement l'exécutable correspondant à votre système :

| Système | Fichier | Action |
|---------|---------|--------|
| Windows | `PhotoManager.exe` | Double-cliquez pour lancer |
| macOS | `PhotoManager.app` | Double-cliquez pour lancer |

---

## Création des Exécutables (Pour développeurs)

### Prérequis pour le build

- Python 3.8 ou supérieur installé sur la machine de build
- Connexion internet (pour télécharger les dépendances)

### Windows - Créer le .exe

1. **Double-cliquez sur `build_windows.bat`**

   Ou exécutez dans un terminal :
   ```cmd
   build_windows.bat
   ```

2. **Attendez la fin du build** (2-5 minutes)

3. **Récupérez l'exécutable** : `PhotoManager.exe` sera créé dans le dossier

**Résultat** : Un fichier `PhotoManager.exe` autonome (~50-80 MB) qui fonctionne sur n'importe quel PC Windows sans Python.

### macOS - Créer le .app

1. **Ouvrez Terminal** et naviguez vers le dossier du projet

2. **Rendez le script exécutable** (une seule fois) :
   ```bash
   chmod +x build_macos.sh
   ```

3. **Lancez le build** :
   ```bash
   ./build_macos.sh
   ```

4. **Attendez la fin du build** (2-5 minutes)

5. **Récupérez l'application** : `PhotoManager.app` sera créé

**Résultat** : Une application `PhotoManager.app` que vous pouvez glisser dans `/Applications` et lancer d'un double-clic.

---

## Utilisation

### 1. Sélectionner des photos

- **Dossier complet** : Cliquez sur "📁 Sélectionner un dossier" pour charger toutes les photos d'un dossier
- **Fichiers individuels** : Cliquez sur "🖼️ Sélectionner des fichiers" pour choisir des photos spécifiques

### 2. Configurer la mise en page

Choisissez le nombre de photos par page :
- **4 photos (2x2)** : Grandes photos, idéal pour des images détaillées
- **6 photos (2x3)** : Bon compromis taille/quantité
- **9 photos (3x3)** : Plus de photos par page

### 3. Prévisualiser et ajuster

- La prévisualisation s'affiche automatiquement à droite
- Cliquez sur "↻ Pivoter" sous une photo pour la faire pivoter de 90°
- Les rotations sont conservées lors de l'export

### 4. Exporter en Word

- Cliquez sur "💾 Enregistrer le Word"
- Choisissez l'emplacement et le nom du fichier
- Le document .docx est créé avec toutes vos photos disposées en grille

---

## Structure du projet

```
Manage-photo/
├── photo_manager.py      # Application principale (code source)
├── requirements.txt      # Dépendances Python
├── README.md             # Ce fichier
├── build_windows.bat     # Script pour créer l'exécutable Windows
├── build_macos.sh        # Script pour créer l'application macOS
├── PhotoManager.spec     # Configuration PyInstaller
├── run_windows.bat       # Lancer avec Python (développement)
└── run_macos.sh          # Lancer avec Python (développement)
```

---

## Mode Développement (avec Python)

Si vous préférez exécuter depuis le code source :

### Windows

```cmd
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python photo_manager.py
```

### macOS / Linux

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python photo_manager.py
```

---

## Dépannage

### Le build échoue

1. Vérifiez que Python est installé : `python --version`
2. Vérifiez votre connexion internet
3. Supprimez les dossiers `build/`, `dist/`, `build_env/` et relancez

### L'exécutable ne démarre pas (Windows)

- Certains antivirus peuvent bloquer les exécutables PyInstaller
- Ajoutez une exception pour `PhotoManager.exe`

### L'app ne s'ouvre pas (macOS)

- Clic droit → "Ouvrir" pour contourner Gatekeeper la première fois
- Ou : Préférences Système → Sécurité → "Ouvrir quand même"

### Erreur "tkinter not found" (build macOS)

```bash
brew install python-tk
```

---

## Licence

Ce projet est libre d'utilisation.
