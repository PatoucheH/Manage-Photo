"""Configuration and constants for the application"""

# Supported image formats
SUPPORTED_FORMATS = ('.jpg', '.jpeg', '.png', '.JPG', '.JPEG', '.PNG')

# Thumbnail size in pixels
THUMB_SIZE = (100, 100)


class WordExportConfig:
    """Word export configuration"""
    PAGE_MARGIN_MM = 10  # Page margin in millimeters
    GAP_MM = 2  # Gap between photos in millimeters
    SAFE_FACTOR = 0.85  # Safety factor (85% of available space)
    DPI = 150  # Resolution for composite image
    JPEG_QUALITY = 95  # JPEG quality

    # Available layouts: (columns, rows)
    LAYOUTS = {
        4: (2, 2),
        6: (2, 3),
        9: (3, 3)
    }

    # Image size options (percentage of page)
    # Full page is 95% max to ensure it never exceeds page bounds
    IMAGE_SIZES = {
        'half': 0.50,           # Demi page (50%)
        'three_quarter': 0.75,  # 3/4 de page (75%)
        'full': 0.95            # Page complète (95% max)
    }
