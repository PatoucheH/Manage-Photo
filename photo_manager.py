#!/usr/bin/env python3
"""
Photo Manager - Application de gestion de photos pour générer des documents Word
Compatible Windows et macOS
Ultra-optimisé pour traiter des milliers de photos
"""

import customtkinter as ctk
from tkinter import filedialog, messagebox
from PIL import Image
import os
import sys
from typing import List, Tuple, Optional, Callable
from dataclasses import dataclass, field
from docx import Document
from docx.shared import Cm, Mm
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
import io
import math
import threading

# Configuration
ctk.set_appearance_mode("system")
ctk.set_default_color_theme("blue")

SUPPORTED_FORMATS = ('.jpg', '.jpeg', '.png')
THUMB_SIZE = (100, 100)
PHOTOS_PER_VIEW = 50  # Photos affichées par "page" de prévisualisation


@dataclass
class PhotoItem:
    """Photo avec métadonnées"""
    path: str
    rotation: int = 0
    _thumb: Optional[ctk.CTkImage] = field(default=None, repr=False)

    def rotate(self):
        self.rotation = (self.rotation + 90) % 360
        self._thumb = None

    def get_thumb(self) -> Optional[ctk.CTkImage]:
        if self._thumb:
            return self._thumb
        try:
            with Image.open(self.path) as img:
                if self.rotation:
                    img = img.rotate(-self.rotation, expand=True)
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                img.thumbnail(THUMB_SIZE, Image.Resampling.LANCZOS)
                self._thumb = ctk.CTkImage(img, img, img.size)
                return self._thumb
        except:
            return None

    def clear(self):
        self._thumb = None


class PhotoCard(ctk.CTkFrame):
    """Carte photo compacte"""

    def __init__(self, master, photo: PhotoItem, index: int, on_delete: Callable, **kw):
        super().__init__(master, width=130, height=160, **kw)
        self.pack_propagate(False)

        self.photo = photo
        self.index = index
        self.on_delete = on_delete

        # Image
        self.img_label = ctk.CTkLabel(self, text="...", width=100, height=100)
        self.img_label.pack(pady=(5,2))

        # Boutons
        bf = ctk.CTkFrame(self, fg_color="transparent")
        bf.pack()
        ctk.CTkButton(bf, text="↻", width=30, height=22, command=self._rotate).pack(side="left", padx=1)
        ctk.CTkButton(bf, text="✕", width=30, height=22, fg_color="#c0392b",
                     hover_color="#a93226", command=self._delete).pack(side="left", padx=1)

        # Nom
        name = os.path.basename(photo.path)
        ctk.CTkLabel(self, text=name[:16] + "..." if len(name) > 16 else name,
                    font=("Arial", 8)).pack()

        # Charger image après
        self.after(1, self._load)

    def _load(self):
        thumb = self.photo.get_thumb()
        if thumb:
            self.img_label.configure(image=thumb, text="")
        else:
            self.img_label.configure(text="Err")

    def _rotate(self):
        self.photo.rotate()
        self._load()

    def _delete(self):
        self.on_delete(self.index)


class PhotoManagerApp(ctk.CTk):
    """Application principale ultra-optimisée"""

    def __init__(self):
        super().__init__()
        self.title("Photo Manager")
        self.geometry("1200x800")
        self.minsize(900, 600)

        self.photos: List[PhotoItem] = []
        self.current_page = 0
        self._cards: List[PhotoCard] = []

        self._build_ui()

        # Fix macOS black screen issue with deprecated Tk
        if sys.platform == 'darwin':
            self.update()
            self.update_idletasks()
            self.lift()
            self.focus_force()
            # Force window to refresh by toggling visibility
            self.after(100, self._macos_refresh)

    def _macos_refresh(self):
        """Force refresh on macOS to fix black screen with deprecated Tk"""
        self.withdraw()
        self.update()
        self.deiconify()
        self.update()
        self.lift()

    def _build_ui(self):
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Panneau gauche
        left = ctk.CTkFrame(self, width=240)
        left.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        left.grid_propagate(False)

        ctk.CTkLabel(left, text="Photo Manager", font=("Arial", 18, "bold")).pack(pady=(15,3))
        ctk.CTkLabel(left, text="Export Word", font=("Arial", 10)).pack(pady=(0,15))

        ctk.CTkFrame(left, height=1, fg_color="gray50").pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(left, text="Ajouter", font=("Arial", 11, "bold")).pack(anchor="w", padx=15, pady=(10,5))
        ctk.CTkButton(left, text="+ Dossier", command=self._add_folder, height=30).pack(fill="x", padx=15, pady=2)
        ctk.CTkButton(left, text="+ Fichiers", command=self._add_files, height=30).pack(fill="x", padx=15, pady=2)

        self.count_lbl = ctk.CTkLabel(left, text="0 photos", font=("Arial", 10, "bold"))
        self.count_lbl.pack(pady=8)

        ctk.CTkFrame(left, height=1, fg_color="gray50").pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(left, text="Photos/page", font=("Arial", 11, "bold")).pack(anchor="w", padx=15, pady=(10,5))
        self.ppp = ctk.StringVar(value="6")
        for v, t in [("4", "4 (2×2)"), ("6", "6 (2×3)"), ("9", "9 (3×3)")]:
            ctk.CTkRadioButton(left, text=t, variable=self.ppp, value=v).pack(anchor="w", padx=25, pady=1)

        ctk.CTkFrame(left, height=1, fg_color="gray50").pack(fill="x", padx=10, pady=10)

        ctk.CTkButton(left, text="EXPORTER WORD", command=self._export, height=40,
                     fg_color="#27ae60", hover_color="#1e8449",
                     font=("Arial", 12, "bold")).pack(fill="x", padx=15, pady=5)

        ctk.CTkButton(left, text="Tout effacer", command=self._clear, height=28,
                     fg_color="#e74c3c", hover_color="#c0392b").pack(fill="x", padx=15, pady=5)

        ctk.CTkFrame(left, fg_color="transparent").pack(fill="both", expand=True)
        ctk.CTkLabel(left, text="JPG, PNG", font=("Arial", 9), text_color="gray").pack(pady=5)

        # Panneau droit
        right = ctk.CTkFrame(self)
        right.grid(row=0, column=1, sticky="nsew", padx=(0,10), pady=10)
        right.grid_columnconfigure(0, weight=1)
        right.grid_rowconfigure(1, weight=1)

        # Header avec navigation
        header = ctk.CTkFrame(right, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=10, pady=5)

        ctk.CTkLabel(header, text="Aperçu", font=("Arial", 13, "bold")).pack(side="left")

        # Navigation
        nav = ctk.CTkFrame(header, fg_color="transparent")
        nav.pack(side="right")

        self.prev_btn = ctk.CTkButton(nav, text="◀", width=30, command=self._prev_page)
        self.prev_btn.pack(side="left", padx=2)

        self.page_lbl = ctk.CTkLabel(nav, text="0/0", width=80)
        self.page_lbl.pack(side="left", padx=5)

        self.next_btn = ctk.CTkButton(nav, text="▶", width=30, command=self._next_page)
        self.next_btn.pack(side="left", padx=2)

        # Zone photos scrollable
        self.scroll = ctk.CTkScrollableFrame(right, fg_color=("gray90", "gray20"))
        self.scroll.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)

        # Grid container
        self.grid_frame = ctk.CTkFrame(self.scroll, fg_color="transparent")
        self.grid_frame.pack(fill="both", expand=True)

    def _add_folder(self):
        folder = filedialog.askdirectory(title="Dossier")
        if folder:
            files = sorted([os.path.join(folder, f) for f in os.listdir(folder)
                          if f.lower().endswith(SUPPORTED_FORMATS)])
            if files:
                self._add_photos(files)

    def _add_files(self):
        files = filedialog.askopenfilenames(title="Photos",
            filetypes=[("Images", "*.jpg *.jpeg *.png")])
        if files:
            self._add_photos(list(files))

    def _add_photos(self, files: List[str]):
        existing = {p.path for p in self.photos}
        new = [PhotoItem(f) for f in files if f not in existing]
        self.photos.extend(new)
        self._update()

    def _delete_photo(self, index: int):
        if 0 <= index < len(self.photos):
            self.photos[index].clear()
            del self.photos[index]
            # Ajuster la page si nécessaire
            max_page = max(0, (len(self.photos) - 1) // PHOTOS_PER_VIEW)
            if self.current_page > max_page:
                self.current_page = max_page
            self._update()

    def _clear(self):
        for p in self.photos:
            p.clear()
        self.photos.clear()
        self.current_page = 0
        self._update()

    def _prev_page(self):
        if self.current_page > 0:
            self.current_page -= 1
            self._refresh_grid()

    def _next_page(self):
        max_page = max(0, (len(self.photos) - 1) // PHOTOS_PER_VIEW)
        if self.current_page < max_page:
            self.current_page += 1
            self._refresh_grid()

    def _update(self):
        self.count_lbl.configure(text=f"{len(self.photos)} photos")
        self._refresh_grid()

    def _refresh_grid(self):
        # Détruire anciennes cartes
        for c in self._cards:
            c.destroy()
        self._cards.clear()

        if not self.photos:
            self.page_lbl.configure(text="0/0")
            return

        # Pagination
        total_pages = math.ceil(len(self.photos) / PHOTOS_PER_VIEW)
        self.page_lbl.configure(text=f"{self.current_page + 1}/{total_pages}")

        # Photos de cette page
        start = self.current_page * PHOTOS_PER_VIEW
        end = min(start + PHOTOS_PER_VIEW, len(self.photos))

        # Calculer colonnes selon largeur
        cols = 6

        for i, idx in enumerate(range(start, end)):
            card = PhotoCard(self.grid_frame, self.photos[idx], idx,
                           self._delete_photo, fg_color=("white", "gray30"))
            card.grid(row=i // cols, column=i % cols, padx=3, pady=3)
            self._cards.append(card)

    def _export(self):
        if not self.photos:
            messagebox.showwarning("Attention", "Aucune photo.")
            return

        path = filedialog.asksaveasfilename(
            title="Enregistrer",
            defaultextension=".docx",
            filetypes=[("Word", "*.docx")],
            initialfile="photos.docx"
        )
        if not path:
            return

        # Progress
        prog = ctk.CTkToplevel(self)
        prog.title("Export...")
        prog.geometry("350x120")
        prog.transient(self)
        prog.grab_set()

        ctk.CTkLabel(prog, text="Génération du document Word...",
                    font=("Arial", 12)).pack(pady=15)
        bar = ctk.CTkProgressBar(prog, width=300)
        bar.pack(pady=10)
        bar.set(0)

        status = ctk.CTkLabel(prog, text="0%", font=("Arial", 10))
        status.pack()

        def gen():
            try:
                self._generate_word(path, lambda p: self.after(0, lambda: (
                    bar.set(p), status.configure(text=f"{int(p*100)}%"))))
                self.after(0, lambda: self._done(prog, path, None))
            except Exception as e:
                self.after(0, lambda: self._done(prog, path, str(e)))

        threading.Thread(target=gen, daemon=True).start()

    def _done(self, prog, path, err):
        prog.destroy()
        if err:
            messagebox.showerror("Erreur", err)
        else:
            messagebox.showinfo("Succès", f"Exporté:\n{path}")

    def _generate_word(self, path: str, progress: Callable = None):
        """Génère Word avec images MAXIMUM"""
        doc = Document()

        # Marges minimales (5mm)
        for section in doc.sections:
            section.top_margin = Mm(5)
            section.bottom_margin = Mm(5)
            section.left_margin = Mm(5)
            section.right_margin = Mm(5)

        ppp = int(self.ppp.get())
        cols, rows = {4: (2, 2), 6: (2, 3), 9: (3, 3)}[ppp]

        # Dimensions page A4 - marges (en mm)
        page_w_mm = 210 - 10  # 200mm utilisable
        page_h_mm = 297 - 10  # 287mm utilisable

        # Espacement minimal entre images (2mm)
        gap = 2

        # Taille max par cellule
        cell_w = (page_w_mm - gap * (cols - 1)) / cols
        cell_h = (page_h_mm - gap * (rows - 1)) / rows

        total = len(self.photos)
        num_pages = math.ceil(total / ppp)

        for page_idx in range(num_pages):
            if page_idx > 0:
                doc.add_page_break()

            table = doc.add_table(rows=rows, cols=cols)
            table.alignment = WD_TABLE_ALIGNMENT.CENTER

            # Supprimer les bordures et marges de table
            tbl = table._tbl
            tblPr = tbl.tblPr if tbl.tblPr is not None else OxmlElement('w:tblPr')

            # Marges cellules à 0
            tblCellMar = OxmlElement('w:tblCellMar')
            for side in ['top', 'left', 'bottom', 'right']:
                node = OxmlElement(f'w:{side}')
                node.set(qn('w:w'), '0')
                node.set(qn('w:type'), 'dxa')
                tblCellMar.append(node)
            tblPr.append(tblCellMar)

            start = page_idx * ppp

            for i in range(rows):
                for j in range(cols):
                    idx = start + i * cols + j
                    if idx >= total:
                        continue

                    photo = self.photos[idx]
                    cell = table.cell(i, j)
                    para = cell.paragraphs[0]
                    para.alignment = WD_ALIGN_PARAGRAPH.CENTER

                    # Marges paragraphe à 0
                    para.paragraph_format.space_before = Mm(0)
                    para.paragraph_format.space_after = Mm(0)

                    try:
                        with Image.open(photo.path) as img:
                            if photo.rotation:
                                img = img.rotate(-photo.rotation, expand=True)

                            if img.mode != 'RGB':
                                if img.mode in ('RGBA', 'LA', 'P'):
                                    bg = Image.new('RGB', img.size, (255, 255, 255))
                                    if img.mode == 'P':
                                        img = img.convert('RGBA')
                                    if 'A' in img.getbands():
                                        bg.paste(img, mask=img.split()[-1])
                                    else:
                                        bg.paste(img)
                                    img = bg
                                else:
                                    img = img.convert('RGB')

                            buf = io.BytesIO()
                            img.save(buf, format='JPEG', quality=90)
                            buf.seek(0)

                            # Calculer taille pour remplir la cellule
                            w, h = img.size
                            ratio = w / h

                            # Adapter à la cellule en gardant ratio
                            if ratio > (cell_w / cell_h):
                                # Image plus large : limiter par largeur
                                final_w = cell_w
                                final_h = cell_w / ratio
                            else:
                                # Image plus haute : limiter par hauteur
                                final_h = cell_h
                                final_w = cell_h * ratio

                            para.add_run().add_picture(buf, width=Mm(final_w), height=Mm(final_h))

                    except Exception as e:
                        para.add_run(f"[Err]")

                    if progress:
                        progress((idx + 1) / total)

        doc.save(path)


def main():
    app = PhotoManagerApp()
    app.mainloop()


if __name__ == "__main__":
    main()
