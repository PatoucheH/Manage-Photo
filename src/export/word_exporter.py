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

        # Calcul de la largeur max d'une image
        cell_w_mm = (available_w_mm - gap_mm * (cols - 1)) / cols * size_factor

        # Conversion mm -> px
        mm_to_px = self.config.DPI / 25.4
        cell_w_px = int(cell_w_mm * mm_to_px)
        gap_px = int(gap_mm * mm_to_px)

        total = len(self.photos)
        num_pages = math.ceil(total / self.ppp)

        for page_idx in range(num_pages):
            if page_idx > 0:
                doc.add_page_break()

            # Création composite
            # On initialise un composite provisoire, taille suffisante (sera ajustée)
            composite = Image.new("RGB", (int(available_w_mm * mm_to_px), int(available_h_mm * mm_to_px)), (255, 255, 255))

            # Positionnement initial
            start = page_idx * self.ppp
            y_cursor = gap_px  # début du premier rang

            for i in range(rows):
                x_cursor = gap_px  # début de la première colonne
                row_height = 0  # calcul dynamique de la hauteur du rang

                for j in range(cols):
                    idx = start + i * cols + j
                    if idx >= total:
                        continue

                    photo = self.photos[idx]

                    with Image.open(photo.path) as img:
                        if photo.rotation:
                            img = img.rotate(-photo.rotation, expand=True)
                        if img.mode != "RGB":
                            img = img.convert("RGB")

                        img_w, img_h = img.size
                        scale = min(cell_w_px / img_w, 1.0)  # on ne grossit pas
                        new_w = int(img_w * scale)
                        new_h = int(img_h * scale)

                        img_resized = img.resize(new_w, new_h, Image.LANCZOS if hasattr(Image, "LANCZOS") else Image.ANTIALIAS)

                        # paste avec centrage horizontal, top aligné verticalement
                        offset_x = x_cursor + (cell_w_px - new_w) // 2
                        offset_y = y_cursor
                        composite.paste(img_resized, (offset_x, offset_y))

                        x_cursor += cell_w_px + gap_px
                        row_height = max(row_height, new_h)

                y_cursor += row_height + gap_px  # le rang suivant commence juste après l'image la plus haute du rang

            # Ajuster la taille finale du composite
            final_w = min(composite.width, cols * cell_w_px + (cols + 1) * gap_px)
            final_h = y_cursor
            composite = composite.crop((0, 0, final_w, final_h))

            self._insert_composite(doc, composite, final_w / mm_to_px, final_h / mm_to_px)

            self.progress.emit(int((min((page_idx + 1) * self.ppp, total)) / total * 100))

        doc.save(self.path)

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
