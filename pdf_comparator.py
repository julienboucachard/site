import tkinter as tk
from tkinter import filedialog, messagebox
import fitz  # PyMuPDF
from PIL import Image, ImageChops
import os
import io
import base64

class PDFComparator:
    def __init__(self, root):
        self.root = root
        self.root.title("PDF Comparator")
        self.root.geometry("1200x800")

        self.file1 = None
        self.file2 = None

        # Create main frame
        self.main_frame = tk.Frame(root)
        self.main_frame.pack(fill=tk.BOTH, expand=1)

        # Create tool bar
        self.toolbar = tk.Frame(self.main_frame, bd=1, relief=tk.RAISED)
        self.toolbar.pack(side=tk.TOP, fill=tk.X)

        self.btn_open1 = tk.Button(self.toolbar, text="Open PDF 1", command=self.open_file1)
        self.btn_open1.pack(side=tk.LEFT, padx=2, pady=2)

        self.btn_open2 = tk.Button(self.toolbar, text="Open PDF 2", command=self.open_file2)
        self.btn_open2.pack(side=tk.LEFT, padx=2, pady=2)

        self.btn_compare = tk.Button(self.toolbar, text="Compare", command=self.compare_pdfs)
        self.btn_compare.pack(side=tk.LEFT, padx=2, pady=2)

        # Create canvas for PDF display
        self.canvas_frame = tk.Frame(self.main_frame)
        self.canvas_frame.pack(fill=tk.BOTH, expand=1)

        self.canvas1 = tk.Canvas(self.canvas_frame, bg="white")
        self.canvas1.pack(side=tk.LEFT, fill=tk.BOTH, expand=1)

        self.canvas2 = tk.Canvas(self.canvas_frame, bg="white")
        self.canvas2.pack(side=tk.RIGHT, fill=tk.BOTH, expand=1)

        self.vsb1 = tk.Scrollbar(self.canvas1, orient="vertical", command=self.canvas1.yview)
        self.vsb1.pack(side=tk.RIGHT, fill="y")
        self.canvas1.configure(yscrollcommand=self.vsb1.set)

        self.vsb2 = tk.Scrollbar(self.canvas2, orient="vertical", command=self.canvas2.yview)
        self.vsb2.pack(side=tk.RIGHT, fill="y")
        self.canvas2.configure(yscrollcommand=self.vsb2.set)

        self.canvas1.bind("<MouseWheel>", self.on_mouse_wheel)
        self.canvas2.bind("<MouseWheel>", self.on_mouse_wheel)

        self.images1 = []
        self.images2 = []

    def _pil_to_tk_image(self, pil_image):
        """Converts a Pillow image to a Tkinter PhotoImage object using an in-memory GIF workaround."""
        with io.BytesIO() as buffer:
            pil_image.save(buffer, format="GIF")
            b64_data = base64.b64encode(buffer.getvalue())
        return tk.PhotoImage(data=b64_data)

    def open_file1(self):
        self.file1 = filedialog.askopenfilename(filetypes=[("PDF files", "*.pdf")])
        if self.file1:
            self.display_pdf(self.file1, self.canvas1, self.images1)

    def open_file2(self):
        self.file2 = filedialog.askopenfilename(filetypes=[("PDF files", "*.pdf")])
        if self.file2:
            self.display_pdf(self.file2, self.canvas2, self.images2)

    def display_pdf(self, file_path, canvas, images_list):
        images_list.clear()
        canvas.delete("all")

        doc = fitz.open(file_path)
        y_offset = 0
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            pix = page.get_pixmap()
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            tk_img = self._pil_to_tk_image(img)
            images_list.append(tk_img)
            canvas.create_image(0, y_offset, anchor="nw", image=tk_img)
            y_offset += img.height

        canvas.config(scrollregion=canvas.bbox("all"))

    def compare_pdfs(self):
        if not self.file1 or not self.file2:
            messagebox.showerror("Error", "Please open both PDF files.")
            return

        doc1 = fitz.open(self.file1)
        doc2 = fitz.open(self.file2)

        num_pages1 = len(doc1)
        num_pages2 = len(doc2)

        self.images1.clear()
        self.images2.clear()
        self.canvas1.delete("all")
        self.canvas2.delete("all")

        y_offset1 = 0
        y_offset2 = 0

        max_pages = max(num_pages1, num_pages2)

        diff_dir = "diff_images"
        if not os.path.exists(diff_dir):
            os.makedirs(diff_dir)

        for i in range(max_pages):
            img1, img2, diff_img = None, None, None
            page_in_1 = i < num_pages1
            page_in_2 = i < num_pages2

            if page_in_1 and page_in_2:
                # Both pages exist, compare them
                page1 = doc1.load_page(i)
                page2 = doc2.load_page(i)

                pix1 = page1.get_pixmap()
                pix2 = page2.get_pixmap()

                img1 = Image.frombytes("RGB", [pix1.width, pix1.height], pix1.samples)
                img2 = Image.frombytes("RGB", [pix2.width, pix2.height], pix2.samples)

                if img1.size != img2.size:
                    # Resize images to the larger of the two sizes for comparison
                    new_width = max(img1.width, img2.width)
                    new_height = max(img1.height, img2.height)

                    img1_resized = Image.new("RGB", (new_width, new_height), (255, 255, 255))
                    img1_resized.paste(img1, (0, 0))
                    img1 = img1_resized

                    img2_resized = Image.new("RGB", (new_width, new_height), (255, 255, 255))
                    img2_resized.paste(img2, (0, 0))
                    img2 = img2_resized

                diff = ImageChops.difference(img1, img2)
                diff = diff.convert("L")
                diff = diff.point(lambda x: 255 if x > 20 else 0)

                # Create a color image for the difference
                diff_color = Image.new("RGBA", diff.size, (0, 0, 0, 0))
                pixels = diff_color.load()
                for x in range(diff.width):
                    for y in range(diff.height):
                        if diff.getpixel((x, y)) > 0:
                            pixels[x, y] = (255, 0, 0, 128) # Red highlight

                img1.paste(diff_color, (0, 0), diff_color)
                img2.paste(diff_color, (0, 0), diff_color)

            elif page_in_1:
                # Page only in PDF 1 (removed from PDF 2)
                page1 = doc1.load_page(i)
                pix1 = page1.get_pixmap()
                img1 = Image.frombytes("RGB", [pix1.width, pix1.height], pix1.samples)

                # Create a green overlay
                overlay = Image.new("RGBA", img1.size, (0, 255, 0, 128))
                img1.paste(overlay, (0, 0), overlay)
                img2 = Image.new("RGB", img1.size, (200, 200, 200)) # Gray placeholder

            elif page_in_2:
                # Page only in PDF 2 (added to PDF 2)
                page2 = doc2.load_page(i)
                pix2 = page2.get_pixmap()
                img2 = Image.frombytes("RGB", [pix2.width, pix2.height], pix2.samples)

                # Create a blue overlay
                overlay = Image.new("RGBA", img2.size, (0, 0, 255, 128))
                img2.paste(overlay, (0, 0), overlay)
                img1 = Image.new("RGB", img2.size, (200, 200, 200)) # Gray placeholder

            if img1:
                tk_img1 = self._pil_to_tk_image(img1)
                self.images1.append(tk_img1)
                self.canvas1.create_image(0, y_offset1, anchor="nw", image=tk_img1)
                y_offset1 += img1.height

            if img2:
                tk_img2 = self._pil_to_tk_image(img2)
                self.images2.append(tk_img2)
                self.canvas2.create_image(0, y_offset2, anchor="nw", image=tk_img2)
                y_offset2 += img2.height

        self.canvas1.config(scrollregion=self.canvas1.bbox("all"))
        self.canvas2.config(scrollregion=self.canvas2.bbox("all"))

    def on_mouse_wheel(self, event):
        self.canvas1.yview_scroll(int(-1*(event.delta/120)), "units")
        self.canvas2.yview_scroll(int(-1*(event.delta/120)), "units")
        return "break"

if __name__ == "__main__":
    root = tk.Tk()
    app = PDFComparator(root)
    root.mainloop()
