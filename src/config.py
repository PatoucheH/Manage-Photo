"""Configuration et constantes de l'application"""

# Formats d'images supportes
SUPPORTED_FORMATS = ('.jpg', '.jpeg', '.png', '.JPG', '.JPEG', '.PNG')

# Taille des miniatures
THUMB_SIZE = (100, 100)

# Nombre de photos par vue (pagination)
PHOTOS_PER_VIEW = 50

# Configuration de l'export Word
class WordExportConfig:
    PAGE_MARGIN_MM = 10  # Marge de page en mm
    GAP_MM = 2  # Espace entre les photos en mm
    SAFE_FACTOR = 0.85  # Facteur de securite (85% de la zone disponible)
    DPI = 150  # Resolution pour l'image composite
    JPEG_QUALITY = 95  # Qualite JPEG

    # Layouts disponibles: (colonnes, lignes)
    LAYOUTS = {
        4: (2, 2),
        6: (2, 3),
        9: (3, 3)
    }
