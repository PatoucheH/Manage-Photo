"""Photo data model"""

import os
from dataclasses import dataclass, field
from typing import Optional

from PIL import Image
from PyQt5.QtGui import QPixmap, QImage

from ..config import THUMB_SIZE


@dataclass
class PhotoItem:
    """Represents a photo with its metadata"""
    path: str
    rotation: int = 0
    _pixmap: Optional[QPixmap] = field(default=None, repr=False)

    @property
    def filename(self) -> str:
        """Returns the filename"""
        return os.path.basename(self.path)

    def rotate(self) -> None:
        """Rotate 90 degrees clockwise"""
        self.rotation = (self.rotation + 90) % 360
        self._pixmap = None

    def get_pixmap(self) -> Optional[QPixmap]:
        """Returns the thumbnail as QPixmap"""
        if self._pixmap:
            return self._pixmap
        try:
            with Image.open(self.path) as img:
                # Apply rotation
                if self.rotation:
                    img = img.rotate(-self.rotation, expand=True)

                # Convert to RGB
                if img.mode != 'RGB':
                    img = img.convert('RGB')

                # Use appropriate resampling method
                resample = Image.LANCZOS if hasattr(Image, 'LANCZOS') else Image.ANTIALIAS
                img.thumbnail(THUMB_SIZE, resample)

                # Convert to QPixmap
                data = img.tobytes("raw", "RGB")
                qimg = QImage(data, img.width, img.height, 3 * img.width, QImage.Format_RGB888)
                self._pixmap = QPixmap.fromImage(qimg)
                return self._pixmap
        except Exception as e:
            print(f"Error loading {self.path}: {e}")
            return None

    def get_full_image(self, max_width: int, max_height: int) -> Optional[QPixmap]:
        """Returns the full-size image scaled to fit within max dimensions"""
        try:
            with Image.open(self.path) as img:
                # Apply rotation
                if self.rotation:
                    img = img.rotate(-self.rotation, expand=True)

                # Convert to RGB
                if img.mode != 'RGB':
                    img = img.convert('RGB')

                # Calculate scale factor
                img_w, img_h = img.size
                scale = min(max_width / img_w, max_height / img_h, 1.0)
                new_w = int(img_w * scale)
                new_h = int(img_h * scale)

                # Resize with high quality
                resample = Image.LANCZOS if hasattr(Image, 'LANCZOS') else Image.ANTIALIAS
                img = img.resize((new_w, new_h), resample)

                # Convert to QPixmap
                data = img.tobytes("raw", "RGB")
                qimg = QImage(data, img.width, img.height, 3 * img.width, QImage.Format_RGB888)
                return QPixmap.fromImage(qimg)
        except Exception:
            return None

    def clear(self) -> None:
        """Free memory"""
        self._pixmap = None
