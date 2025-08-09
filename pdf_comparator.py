import tkinter as tk
from tkinter import filedialog, messagebox
import fitz  # PyMuPDF
from PIL import Image, ImageChops, ImageDraw
import os
import io
import base64
import difflib

class PDFComparator:
    def __init__(self, root):
        self.root = root
        self.root.title("PDF Comparator")
        self.root.geometry("1200x800")

        self.file1 = None
        self.file2 = None
        self.doc1 = None
        self.doc2 = None
        self.page_num = 0
        self.book_diffs = []
        self.current_diff_index = -1
        self.view_mode = 'continuous'  # 'page' or 'continuous'

        # Create main frame
        self.main_frame = tk.Frame(root)
        self.main_frame.pack(fill=tk.BOTH, expand=1)

        # Create tool bar
        self.toolbar = tk.Frame(self.main_frame, bd=1, relief=tk.RAISED)
        self.toolbar.pack(side=tk.TOP, fill=tk.X)

        self.btn_open1 = tk.Button(self.toolbar, text="Open PDF 1", command=self.open_file1)
        self.btn_open1.pack(side=tk.LEFT, padx=5, pady=2)

        self.btn_open2 = tk.Button(self.toolbar, text="Open PDF 2", command=self.open_file2)
        self.btn_open2.pack(side=tk.LEFT, padx=5, pady=2)

        tk.Label(self.toolbar, text="  |  View:").pack(side=tk.LEFT)
        self.btn_toggle_view = tk.Button(self.toolbar, text="Switch to Continuous View", command=self.toggle_view_mode)
        self.btn_toggle_view.pack(side=tk.LEFT, padx=5)

        tk.Label(self.toolbar, text="  |  Navigate:").pack(side=tk.LEFT)
        self.nav_frame = tk.Frame(self.toolbar)
        self.nav_frame.pack(side=tk.LEFT)
        self.btn_prev_sync = tk.Button(self.nav_frame, text="<< Prev", command=self.prev_page)
        self.btn_prev_sync.pack(side=tk.LEFT, padx=5)
        self.lbl_page = tk.Label(self.nav_frame, text="Page -/-")
        self.lbl_page.pack(side=tk.LEFT, padx=5)
        self.btn_next_sync = tk.Button(self.nav_frame, text="Next >>", command=self.next_page)
        self.btn_next_sync.pack(side=tk.LEFT, padx=5)

        tk.Label(self.toolbar, text="  |").pack(side=tk.LEFT)
        self.btn_compare_page = tk.Button(self.toolbar, text="Compare Page", command=self.compare_pdfs)
        self.btn_compare_page.pack(side=tk.LEFT, padx=5, pady=2)
        self.btn_compare_book = tk.Button(self.toolbar, text="Compare Book", command=self.compare_book)
        self.btn_compare_book.pack(side=tk.LEFT, padx=5, pady=2)

        tk.Label(self.toolbar, text="  |").pack(side=tk.LEFT)
        self.btn_prev_diff = tk.Button(self.toolbar, text="<- Prev Diff", command=lambda: self.navigate_diff(-1))
        self.btn_prev_diff.pack(side=tk.LEFT)
        self.btn_next_diff = tk.Button(self.toolbar, text="Next Diff ->", command=lambda: self.navigate_diff(1))
        self.btn_next_diff.pack(side=tk.LEFT, padx=5)

        # Create canvas for PDF display
        self.canvas_frame = tk.Frame(self.main_frame)
        self.canvas_frame.pack(fill=tk.BOTH, expand=1)

        self.canvas1 = tk.Canvas(self.canvas_frame, bg="white")
        self.canvas1.pack(side=tk.LEFT, fill=tk.BOTH, expand=1)

        self.canvas2 = tk.Canvas(self.canvas_frame, bg="white")
        self.canvas2.pack(side=tk.RIGHT, fill=tk.BOTH, expand=1)

        self.vsb1 = tk.Scrollbar(self.canvas1, orient="vertical", command=self.on_scroll_y)
        self.vsb1.pack(side=tk.RIGHT, fill="y")
        self.canvas1.configure(yscrollcommand=self.vsb1.set)

        self.hsb1 = tk.Scrollbar(self.canvas1, orient="horizontal", command=self.on_scroll_x)
        self.hsb1.pack(side=tk.BOTTOM, fill="x")
        self.canvas1.configure(xscrollcommand=self.hsb1.set)

        self.vsb2 = tk.Scrollbar(self.canvas2, orient="vertical", command=self.on_scroll_y)
        self.vsb2.pack(side=tk.RIGHT, fill="y")
        self.canvas2.configure(yscrollcommand=self.vsb2.set)

        self.hsb2 = tk.Scrollbar(self.canvas2, orient="horizontal", command=self.on_scroll_x)
        self.hsb2.pack(side=tk.BOTTOM, fill="x")
        self.canvas2.configure(xscrollcommand=self.hsb2.set)

        self.canvas1.bind("<MouseWheel>", self.on_mouse_wheel)
        self.canvas2.bind("<MouseWheel>", self.on_mouse_wheel)

        self.images1 = []
        self.images2 = []

        # Status Bar
        self.status_bar = tk.Label(root, text="Ready", bd=1, relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

        self._update_ui_for_view_mode()

    def _pil_to_tk_image(self, pil_image):
        """Converts a Pillow image to a Tkinter PhotoImage object using an in-memory GIF workaround."""
        with io.BytesIO() as buffer:
            pil_image.save(buffer, format="GIF")
            b64_data = base64.b64encode(buffer.getvalue())
        return tk.PhotoImage(data=b64_data)

    def open_file1(self):
        filepath = filedialog.askopenfilename(filetypes=[("PDF files", "*.pdf")])
        if not filepath:
            return
        self.file1 = filepath
        self.doc1 = fitz.open(self.file1)
        self.page_num = 0
        self.update_view()

    def open_file2(self):
        filepath = filedialog.askopenfilename(filetypes=[("PDF files", "*.pdf")])
        if not filepath:
            return
        self.file2 = filepath
        self.doc2 = fitz.open(self.file2)
        if self.doc1:
            self.page_num = min(self.page_num, len(self.doc2) - 1 if len(self.doc2) > 0 else 0)
        else:
            self.page_num = 0
        self.update_view()

    def update_view(self):
        """A central method to refresh both PDF views."""
        self.current_diff_index = -1
        if self.view_mode == 'page':
            if self.doc1: self.show_page(1)
            if self.doc2: self.show_page(2)
        else: # continuous
            if self.doc1: self.display_continuous_view(1)
            if self.doc2: self.display_continuous_view(2)

        if self.doc1 and self.doc2:
            num_pages = min(len(self.doc1), len(self.doc2))
            self.lbl_page.config(text=f"Page {self.page_num + 1} / {num_pages}")
        elif self.doc1:
            self.lbl_page.config(text=f"Page {self.page_num + 1} / {len(self.doc1)}")
        elif self.doc2:
            self.lbl_page.config(text=f"Page {self.page_num + 1} / {len(self.doc2)}")
        else:
            self.lbl_page.config(text="Page -/-")

    def display_continuous_view(self, pdf_num):
        if pdf_num == 1:
            doc, canvas, images_list = self.doc1, self.canvas1, self.images1
        else:
            doc, canvas, images_list = self.doc2, self.canvas2, self.images2

        if not doc: return
        canvas.delete("all")
        images_list.clear()
        y_offset = 0
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            pix = page.get_pixmap(alpha=False)
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            tk_img = self._pil_to_tk_image(img)
            images_list.append(tk_img)
            canvas.create_image(0, y_offset, anchor="nw", image=tk_img)
            y_offset += img.height
        canvas.config(scrollregion=canvas.bbox("all"))

    def show_page(self, pdf_num, img=None, highlight_rect=None):
        if pdf_num == 1:
            doc, canvas, images_list = self.doc1, self.canvas1, self.images1
        else:
            doc, canvas, images_list = self.doc2, self.canvas2, self.images2

        if doc is None or self.page_num >= len(doc):
            canvas.delete("all")
            return

        canvas.delete("all")
        images_list.clear()

        if img is None:
            page = doc.load_page(self.page_num)
            pix = page.get_pixmap()
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

        if img.mode != "RGBA":
            img = img.convert("RGBA")

        if highlight_rect:
            highlight = Image.new("RGBA", img.size, (255, 255, 255, 0))
            draw_highlight = ImageDraw.Draw(highlight)
            draw_highlight.rectangle(highlight_rect, outline="yellow", width=3)
            img = Image.alpha_composite(img, highlight)

        tk_img = self._pil_to_tk_image(img)
        images_list.append(tk_img)
        canvas.create_image(0, 0, anchor="nw", image=tk_img)
        canvas.config(scrollregion=canvas.bbox("all"))

    def prev_page(self):
        if self.page_num > 0:
            self.page_num -= 1
            self.update_view()

    def next_page(self):
        can_go_next = True
        if not self.doc1 or self.page_num >= len(self.doc1) - 1: can_go_next = False
        if not self.doc2 or self.page_num >= len(self.doc2) - 1: can_go_next = False
        if can_go_next:
            self.page_num += 1
            self.update_view()

    def compare_pdfs(self):
        if not self.doc1 or not self.doc2:
            messagebox.showerror("Error", "Please open both PDF files.")
            return
        if self.page_num >= len(self.doc1) or self.page_num >= len(self.doc2):
            messagebox.showerror("Error", "Page number is out of bounds for one of the documents.")
            return

        self.status_bar.config(text="Comparing current page...")
        self.root.update_idletasks()

        page1 = self.doc1.load_page(self.page_num)
        page2 = self.doc2.load_page(self.page_num)

        words1 = page1.get_text("words")
        words2 = page2.get_text("words")
        word_list1 = [w[4] for w in words1]
        word_list2 = [w[4] for w in words2]

        matcher = difflib.SequenceMatcher(None, word_list1, word_list2, autojunk=False)

        rects1_to_highlight = []
        rects2_to_highlight = []
        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == 'replace' or tag == 'delete':
                for i in range(i1, i2):
                    rects1_to_highlight.append(fitz.Rect(words1[i][:4]))
            if tag == 'replace' or tag == 'insert':
                for j in range(j1, j2):
                    rects2_to_highlight.append(fitz.Rect(words2[j][:4]))

        pix1 = page1.get_pixmap()
        img1 = Image.frombytes("RGB", [pix1.width, pix1.height], pix1.samples).convert("RGBA")
        if rects1_to_highlight:
            highlight1 = Image.new("RGBA", img1.size, (255, 255, 255, 0))
            draw_highlight1 = ImageDraw.Draw(highlight1)
            for rect in rects1_to_highlight:
                draw_highlight1.rectangle(rect, fill=(255, 100, 100, 100))
            img1 = Image.alpha_composite(img1, highlight1)

        pix2 = page2.get_pixmap()
        img2 = Image.frombytes("RGB", [pix2.width, pix2.height], pix2.samples).convert("RGBA")
        if rects2_to_highlight:
            highlight2 = Image.new("RGBA", img2.size, (255, 255, 255, 0))
            draw_highlight2 = ImageDraw.Draw(highlight2)
            for rect in rects2_to_highlight:
                draw_highlight2.rectangle(rect, fill=(100, 255, 255, 100))
            img2 = Image.alpha_composite(img2, highlight2)

        self.show_page(1, img=img1)
        self.show_page(2, img=img2)
        self.status_bar.config(text="Ready")

    def _update_ui_for_view_mode(self):
        if self.view_mode == 'continuous':
            self.btn_toggle_view.config(text="Switch to Page View")
            self.nav_frame.pack_forget()
            self.btn_compare_page.config(state=tk.DISABLED)
            self.btn_compare_book.config(state=tk.NORMAL)
            self.btn_prev_diff.config(state=tk.DISABLED)
            self.btn_next_diff.config(state=tk.DISABLED)
        else:
            self.btn_toggle_view.config(text="Switch to Continuous View")
            self.nav_frame.pack(side=tk.LEFT)
            self.btn_compare_page.config(state=tk.NORMAL)
            self.btn_compare_book.config(state=tk.NORMAL)
            self.btn_prev_diff.config(state=tk.NORMAL)
            self.btn_next_diff.config(state=tk.NORMAL)

    def toggle_view_mode(self):
        if self.view_mode == 'page':
            self.view_mode = 'continuous'
        else:
            self.view_mode = 'page'
        self.update_view()
        self._update_ui_for_view_mode()

    def compare_book(self):
        if not self.doc1 or not self.doc2:
            messagebox.showerror("Error", "Please open both PDF files.")
            return

        self.book_diffs.clear()
        self.current_diff_index = -1
        max_pages = min(len(self.doc1), len(self.doc2))

        for i in range(max_pages):
            self.status_bar.config(text=f"Comparing page {i + 1} of {max_pages}...")
            self.root.update_idletasks()
            page1 = self.doc1.load_page(i)
            page2 = self.doc2.load_page(i)
            words1 = page1.get_text("words")
            words2 = page2.get_text("words")
            word_list1 = [w[4] for w in words1]
            word_list2 = [w[4] for w in words2]
            matcher = difflib.SequenceMatcher(None, word_list1, word_list2, autojunk=False)
            for tag, i1, i2, j1, j2 in matcher.get_opcodes():
                if tag == 'replace' or tag == 'delete':
                    for k in range(i1, i2):
                        self.book_diffs.append({'page': i, 'type': 'delete', 'rect': fitz.Rect(words1[k][:4])})
                if tag == 'replace' or tag == 'insert':
                    for k in range(j1, j2):
                         self.book_diffs.append({'page': i, 'type': 'insert', 'rect': fitz.Rect(words2[k][:4])})

        self.status_bar.config(text="Ready")
        if not self.book_diffs:
            messagebox.showinfo("Compare Book", "No textual differences found.")
        else:
            messagebox.showinfo("Compare Book", f"Comparison complete. Found {len(self.book_diffs)} differences.")
            self.navigate_diff(0)

    def navigate_diff(self, delta):
        if not self.book_diffs:
            messagebox.showerror("Error", "No differences found. Please run 'Compare Book' first.")
            return
        if delta == 0:
            self.current_diff_index = 0
        else:
            self.current_diff_index += delta
        if self.current_diff_index < 0:
            self.current_diff_index = len(self.book_diffs) - 1
        elif self.current_diff_index >= len(self.book_diffs):
            self.current_diff_index = 0
        diff_info = self.book_diffs[self.current_diff_index]
        self.page_num = diff_info['page']
        rect = diff_info['rect']
        diff_type = diff_info['type']
        self.view_mode = 'page'
        self.show_page(1, highlight_rect=rect if diff_type == 'delete' else None)
        self.show_page(2, highlight_rect=rect if diff_type == 'insert' else None)
        self._update_ui_for_view_mode()
        self.update_view()

    def on_mouse_wheel(self, event):
        if event.state & 0x1:
            self.canvas1.xview_scroll(int(-1 * (event.delta / 120)), "units")
            self.canvas2.xview_scroll(int(-1 * (event.delta / 120)), "units")
        else:
            self.canvas1.yview_scroll(int(-1 * (event.delta / 120)), "units")
            self.canvas2.yview_scroll(int(-1 * (event.delta / 120)), "units")
        return "break"

    def on_scroll_y(self, *args):
        self.canvas1.yview(*args)
        self.canvas2.yview(*args)

    def on_scroll_x(self, *args):
        self.canvas1.xview(*args)
        self.canvas2.xview(*args)

if __name__ == "__main__":
    root = tk.Tk()
    app = PDFComparator(root)
    root.mainloop()
