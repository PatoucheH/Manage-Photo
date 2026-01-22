"""Configuration and constants for the application"""

# Supported image formats
SUPPORTED_FORMATS = ('.jpg', '.jpeg', '.png', '.JPG', '.JPEG', '.PNG')

# Thumbnail size in pixels
THUMB_SIZE = (100, 100)


class WordExportConfig:
    """Word export configuration"""
    PAGE_MARGIN_MM = 10  # Page margin in millimeters
    GAP_MM = 3  # Gap between photos in millimeters (same horizontal and vertical)
    DPI = 150  # Resolution for composite image
    JPEG_QUALITY = 95  # JPEG quality

    # Available layouts: (columns, rows)
    LAYOUTS = {
        4: (2, 2),
        6: (2, 3),
        9: (3, 3)
    }

    # Image size options (percentage of cell size, gap stays fixed)
    IMAGE_SIZES = {
        'half': 0.50,           # Demi page (50%)
        'three_quarter': 0.75,  # 3/4 de page (75%)
        'full': 0.90            # Page complète (90% max pour ne jamais dépasser)
    }
