"""Export photos to Word document"""

import io
import math
from typing import List

from PIL import Image
from PyQt5.QtCore import QThread, pyqtSignal
from docx import Document
from docx.shared import Mm
from docx.enum.text import WD_ALIGN_PARAGRAPH

from ..models import PhotoItem
from ..config import WordExportConfig


class WordExporter(QThread):
    """Thread for Word export"""
    progress = pyqtSignal(int)
    finished = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, photos: List[PhotoItem], path: str, photos_per_page: int, image_size: str = 'full'):
        super().__init__()
        self.photos = photos
        self.path = path
        self.ppp = photos_per_page
        self.image_size = image_size
        self.config = WordExportConfig()

    def run(self) -> None:
        try:
            self._generate_word()
            self.finished.emit(self.path)
        except Exception as e:
            self.error.emit(str(e))

    def _generate_word(self) -> None:
        doc = Document()

        # Page margins
        page_margin = self.config.PAGE_MARGIN_MM
        for section in doc.sections:
            section.top_margin = Mm(page_margin)
            section.bottom_margin = Mm(page_margin)
            section.left_margin = Mm(page_margin)
            section.right_margin = Mm(page_margin)

        cols, rows = self.config.LAYOUTS.get(self.ppp, (2, 3))
        available_w_mm = 210 - page_margin * 2
        available_h_mm = 297 - page_margin * 2
        gap_mm = self.config.GAP_MM
        size_factor = self.config.IMAGE_SIZES.get(self.image_size, 1.0)

        # Taille max d’une image
        cell_w_mm = (available_w_mm - gap_mm * (cols - 1)) / cols * size_factor
        cell_h_mm = (available_h_mm - gap_mm * (rows - 1)) / rows * size_factor

        # Composite size including margin = gap on all sides
        composite_w_mm = cell_w_mm * cols + gap_mm * (cols + 1)
        composite_h_mm = cell_h_mm * rows + gap_mm * (rows + 1)

        mm_to_px = self.config.DPI / 25.4
        cell_w_px = int(cell_w_mm * mm_to_px)
        cell_h_px = int(cell_h_mm * mm_to_px)
        gap_px = int(gap_mm * mm_to_px)
        composite_w_px = int(composite_w_mm * mm_to_px)
        composite_h_px = int(composite_h_mm * mm_to_px)

        total = len(self.photos)
        num_pages = math.ceil(total / self.ppp)

        for page_idx in range(num_pages):
            if page_idx > 0:
                doc.add_page_break()

            # White background composite
            composite = Image.new("RGB", (composite_w_px, composite_h_px), (255, 255, 255))
            start = page_idx * self.ppp

            for i in range(rows):
                for j in range(cols):
                    idx = start + i * cols + j
                    if idx >= total:
                        continue

                    x = gap_px + j * (cell_w_px + gap_px)
                    y = gap_px + i * (cell_h_px + gap_px)

                    self._place_photo(composite, self.photos[idx], x, y, cell_w_px, cell_h_px)
                    self.progress.emit(int((idx + 1) / total * 100))

            self._insert_composite(doc, composite, composite_w_mm, composite_h_mm)

        doc.save(self.path)

    def _place_photo(
        self,
        composite: Image.Image,
        photo: PhotoItem,
        x: int,
        y: int,
        max_w: int,
        max_h: int
    ) -> None:
        """Place a photo inside a cell (fit entirely, no crop, centered horizontally, top-aligned)"""
        try:
            with Image.open(photo.path) as img:
                if photo.rotation:
                    img = img.rotate(-photo.rotation, expand=True)

                if img.mode != "RGB":
                    img = img.convert("RGB")

                img_w, img_h = img.size
                scale = min(max_w / img_w, max_h / img_h)

                new_w = int(img_w * scale)
                new_h = int(img_h * scale)

                img_resized = img.resize(
                    (new_w, new_h),
                    Image.LANCZOS if hasattr(Image, "LANCZOS") else Image.ANTIALIAS
                )

                # Horizontal centering
                offset_x = x + (max_w - new_w) // 2
                # Vertical: top-aligned
                offset_y = y

                composite.paste(img_resized, (offset_x, offset_y))

        except Exception as e:
            print(f"Error placing photo {photo.path}: {e}")

    def _insert_composite(
        self,
        doc: Document,
        composite: Image.Image,
        width_mm: float,
        height_mm: float
    ) -> None:
        buf = io.BytesIO()
        composite.save(buf, format="JPEG", quality=self.config.JPEG_QUALITY)
        buf.seek(0)

        para = doc.add_paragraph()
        para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        para.paragraph_format.space_before = Mm(0)
        para.paragraph_format.space_after = Mm(0)
        para.add_run().add_picture(buf, width=Mm(width_mm), height=Mm(height_mm))
