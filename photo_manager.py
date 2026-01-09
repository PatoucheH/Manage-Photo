#!/usr/bin/env python3
"""
Photo Manager - Application de gestion de photos pour générer des documents Word
Compatible Windows et macOS (fonctionne avec Tcl/Tk 8.5+)
Ultra-optimisé pour traiter des milliers de photos
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk
import os
import sys
from typing import List, Optional, Callable
from dataclasses import dataclass, field
from docx import Document
from docx.shared import Mm
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
import io
import math
import threading

SUPPORTED_FORMATS = ('.jpg', '.jpeg', '.png')
THUMB_SIZE = (100, 100)
PHOTOS_PER_VIEW = 50


@dataclass
class PhotoItem:
    """Photo avec métadonnées"""
    path: str
    rotation: int = 0
    _thumb: Optional[ImageTk.PhotoImage] = field(default=None, repr=False)
    _pil_img: Optional[Image.Image] = field(default=None, repr=False)

    def rotate(self):
        self.rotation = (self.rotation + 90) % 360
        self._thumb = None
        self._pil_img = None

    def get_thumb(self) -> Optional[ImageTk.PhotoImage]:
        if self._thumb:
            return self._thumb
        try:
            with Image.open(self.path) as img:
                if self.rotation:
                    img = img.rotate(-self.rotation, expand=True)
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                img.thumbnail(THUMB_SIZE, Image.Resampling.LANCZOS)
                self._pil_img = img.copy()
                self._thumb = ImageTk.PhotoImage(self._pil_img)
                return self._thumb
        except:
            return None

    def clear(self):
        self._thumb = None
        self._pil_img = None


class PhotoCard(ttk.Frame):
    """Carte photo compacte"""

    def __init__(self, master, photo: PhotoItem, index: int, on_delete: Callable, **kw):
        super().__init__(master, **kw)

        self.photo = photo
        self.index = index
        self.on_delete = on_delete

        # Container avec bordure
        self.configure(relief="solid", borderwidth=1)

        # Image
        self.img_label = ttk.Label(self, text="...", width=12)
        self.img_label.pack(pady=(5, 2))

        # Boutons
        bf = ttk.Frame(self)
        bf.pack()

        rotate_btn = ttk.Button(bf, text="↻", width=3, command=self._rotate)
        rotate_btn.pack(side="left", padx=1)

        delete_btn = ttk.Button(bf, text="✕", width=3, command=self._delete)
        delete_btn.pack(side="left", padx=1)

        # Nom
        name = os.path.basename(photo.path)
        display_name = name[:16] + "..." if len(name) > 16 else name
        ttk.Label(self, text=display_name, font=("Arial", 8)).pack()

        # Charger image après
        self.after(10, self._load)

    def _load(self):
        thumb = self.photo.get_thumb()
        if thumb:
            self.img_label.configure(image=thumb, text="")
            self.img_label.image = thumb  # Keep reference
        else:
            self.img_label.configure(text="Err")

    def _rotate(self):
        self.photo.rotate()
        self._load()

    def _delete(self):
        self.on_delete(self.index)


class ScrollableFrame(ttk.Frame):
    """Frame scrollable compatible Tk 8.5+"""

    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)

        # Canvas avec scrollbar
        self.canvas = tk.Canvas(self, highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = ttk.Frame(self.canvas)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        self.canvas_frame = self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")

        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        # Bind mouse wheel
        self.canvas.bind("<Enter>", self._bind_mousewheel)
        self.canvas.bind("<Leave>", self._unbind_mousewheel)

        # Resize handling
        self.canvas.bind("<Configure>", self._on_canvas_configure)

    def _on_canvas_configure(self, event):
        self.canvas.itemconfig(self.canvas_frame, width=event.width)

    def _bind_mousewheel(self, event):
        if sys.platform == 'darwin':
            self.canvas.bind_all("<MouseWheel>", self._on_mousewheel_mac)
        else:
            self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)
            self.canvas.bind_all("<Button-4>", self._on_mousewheel_linux)
            self.canvas.bind_all("<Button-5>", self._on_mousewheel_linux)

    def _unbind_mousewheel(self, event):
        self.canvas.unbind_all("<MouseWheel>")
        if sys.platform != 'darwin':
            self.canvas.unbind_all("<Button-4>")
            self.canvas.unbind_all("<Button-5>")

    def _on_mousewheel(self, event):
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def _on_mousewheel_mac(self, event):
        self.canvas.yview_scroll(int(-1 * event.delta), "units")

    def _on_mousewheel_linux(self, event):
        if event.num == 4:
            self.canvas.yview_scroll(-1, "units")
        elif event.num == 5:
            self.canvas.yview_scroll(1, "units")


class PhotoManagerApp(tk.Tk):
    """Application principale compatible Tk 8.5+"""

    def __init__(self):
        super().__init__()
        self.title("Photo Manager")
        self.geometry("1200x800")
        self.minsize(900, 600)

        # Style
        self._setup_style()

        self.photos: List[PhotoItem] = []
        self.current_page = 0
        self._cards: List[PhotoCard] = []

        self._build_ui()

    def _setup_style(self):
        """Configure ttk style"""
        style = ttk.Style()

        # Use native theme
        if sys.platform == 'darwin':
            style.theme_use('aqua')
        elif sys.platform == 'win32':
            style.theme_use('vista')
        else:
            style.theme_use('clam')

        # Custom button styles
        style.configure("Green.TButton", background="#27ae60")
        style.configure("Red.TButton", background="#e74c3c")

    def _build_ui(self):
        # Main container
        main_frame = ttk.Frame(self)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Panneau gauche
        left = ttk.Frame(main_frame, width=240)
        left.pack(side="left", fill="y", padx=(0, 10))
        left.pack_propagate(False)

        ttk.Label(left, text="Photo Manager", font=("Arial", 18, "bold")).pack(pady=(15, 3))
        ttk.Label(left, text="Export Word", font=("Arial", 10)).pack(pady=(0, 15))

        ttk.Separator(left, orient="horizontal").pack(fill="x", padx=10, pady=5)

        ttk.Label(left, text="Ajouter", font=("Arial", 11, "bold")).pack(anchor="w", padx=15, pady=(10, 5))
        ttk.Button(left, text="+ Dossier", command=self._add_folder).pack(fill="x", padx=15, pady=2)
        ttk.Button(left, text="+ Fichiers", command=self._add_files).pack(fill="x", padx=15, pady=2)

        self.count_lbl = ttk.Label(left, text="0 photos", font=("Arial", 10, "bold"))
        self.count_lbl.pack(pady=8)

        ttk.Separator(left, orient="horizontal").pack(fill="x", padx=10, pady=5)

        ttk.Label(left, text="Photos/page", font=("Arial", 11, "bold")).pack(anchor="w", padx=15, pady=(10, 5))
        self.ppp = tk.StringVar(value="6")
        for v, t in [("4", "4 (2x2)"), ("6", "6 (2x3)"), ("9", "9 (3x3)")]:
            ttk.Radiobutton(left, text=t, variable=self.ppp, value=v).pack(anchor="w", padx=25, pady=1)

        ttk.Separator(left, orient="horizontal").pack(fill="x", padx=10, pady=10)

        export_btn = ttk.Button(left, text="EXPORTER WORD", command=self._export)
        export_btn.pack(fill="x", padx=15, pady=5)

        clear_btn = ttk.Button(left, text="Tout effacer", command=self._clear)
        clear_btn.pack(fill="x", padx=15, pady=5)

        # Spacer
        ttk.Frame(left).pack(fill="both", expand=True)
        ttk.Label(left, text="JPG, PNG", font=("Arial", 9), foreground="gray").pack(pady=5)

        # Panneau droit
        right = ttk.Frame(main_frame)
        right.pack(side="left", fill="both", expand=True)

        # Header avec navigation
        header = ttk.Frame(right)
        header.pack(fill="x", pady=(0, 5))

        ttk.Label(header, text="Aperçu", font=("Arial", 13, "bold")).pack(side="left")

        # Navigation
        nav = ttk.Frame(header)
        nav.pack(side="right")

        self.prev_btn = ttk.Button(nav, text="<", width=3, command=self._prev_page)
        self.prev_btn.pack(side="left", padx=2)

        self.page_lbl = ttk.Label(nav, text="0/0", width=10, anchor="center")
        self.page_lbl.pack(side="left", padx=5)

        self.next_btn = ttk.Button(nav, text=">", width=3, command=self._next_page)
        self.next_btn.pack(side="left", padx=2)

        # Zone photos scrollable
        self.scroll = ScrollableFrame(right)
        self.scroll.pack(fill="both", expand=True)

        # Grid container
        self.grid_frame = self.scroll.scrollable_frame

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

        # Colonnes
        cols = 6

        for i, idx in enumerate(range(start, end)):
            card = PhotoCard(self.grid_frame, self.photos[idx], idx, self._delete_photo)
            card.grid(row=i // cols, column=i % cols, padx=3, pady=3, sticky="nsew")
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

        # Progress window
        prog = tk.Toplevel(self)
        prog.title("Export...")
        prog.geometry("350x120")
        prog.transient(self)
        prog.grab_set()

        ttk.Label(prog, text="Génération du document Word...", font=("Arial", 12)).pack(pady=15)

        bar = ttk.Progressbar(prog, length=300, mode='determinate')
        bar.pack(pady=10)

        status = ttk.Label(prog, text="0%", font=("Arial", 10))
        status.pack()

        def update_progress(p):
            bar['value'] = p * 100
            status.configure(text=f"{int(p * 100)}%")
            prog.update_idletasks()

        def gen():
            try:
                self._generate_word(path, lambda p: self.after(0, lambda: update_progress(p)))
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
        page_w_mm = 210 - 10
        page_h_mm = 297 - 10

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
                                final_w = cell_w
                                final_h = cell_w / ratio
                            else:
                                final_h = cell_h
                                final_w = cell_h * ratio

                            para.add_run().add_picture(buf, width=Mm(final_w), height=Mm(final_h))

                    except Exception:
                        para.add_run("[Err]")

                    if progress:
                        progress((idx + 1) / total)

        doc.save(path)


def main():
    app = PhotoManagerApp()
    app.mainloop()


if __name__ == "__main__":
    main()
