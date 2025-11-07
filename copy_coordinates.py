import fitz  # PyMuPDF
import tkinter as tk
from tkinter import filedialog, simpledialog, messagebox
from PIL import Image, ImageTk
import json
import os


class PDFRectangleSelector:
    def __init__(self, root):
        self.root = root
        self.root.title("PDF Rectangle Selector")
        self.root.geometry("900x1100")

        # Canvas
        self.canvas = tk.Canvas(root, bg="white", cursor="cross")
        self.canvas.pack(fill="both", expand=True)

        # Menu
        self.menu = tk.Menu(root)
        root.config(menu=self.menu)
        self.menu.add_command(label="Open PDF", command=self.open_pdf)
        self.menu.add_command(label="Prev Page", command=self.prev_page)
        self.menu.add_command(label="Next Page", command=self.next_page)
        self.menu.add_command(label="Clear Markings", command=self.clear_rectangles)
        self.menu.add_command(label="Save JSON", command=self.save_json)

        # Bind events
        self.canvas.bind("<ButtonPress-1>", self.on_click)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)
        self.canvas.bind("<ButtonPress-3>", self.select_rectangle)

        # State
        self.pdf_doc = None
        self.page_num = 0
        self.scale = 1.0
        self.image_id = None
        self.current_rect = None
        self.start_x = None
        self.start_y = None
        self.selected_rect = None
        self.pdf_name = None
        self.json_base = None
        self.page_rectangles = []  # stores coordinates for current page
        self.rect_draw_order = 1

        # Ensure ./regions folder exists
        os.makedirs("regions", exist_ok=True)

    def open_pdf(self):
        pdf_path = filedialog.askopenfilename(filetypes=[("PDF files", "*.pdf")])
        if not pdf_path:
            return
        self.pdf_doc = fitz.open(pdf_path)
        self.pdf_name = os.path.splitext(os.path.basename(pdf_path))[0]

        # Ask for session name
        self.json_base = simpledialog.askstring(
            "Save File",
            "Enter base name for output JSON (without extension):",
            initialvalue=self.pdf_name
        ) or self.pdf_name

        self.page_num = 0
        self.page_rectangles.clear()
        self.rect_draw_order = 1
        self.show_page(self.page_num)

    def show_page(self, page_num):
        page = self.pdf_doc.load_page(page_num)
        screen_w = self.root.winfo_screenwidth() - 100
        screen_h = self.root.winfo_screenheight() - 200
        zoom_x = screen_w / page.rect.width
        zoom_y = screen_h / page.rect.height
        zoom = min(zoom_x, zoom_y)
        mat = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat, alpha=False)
        self.scale = 1 / zoom

        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        self.img_tk = ImageTk.PhotoImage(img)

        self.canvas.delete("all")
        self.image_id = self.canvas.create_image(0, 0, anchor="nw", image=self.img_tk)
        self.root.title(f"{self.pdf_name} — Page {page_num + 1}/{len(self.pdf_doc)}")

        # Redraw previous rectangles for this page
        for rect in self.page_rectangles:
            self.canvas.create_rectangle(
                rect["screen_x0"], rect["screen_y0"],
                rect["screen_x1"], rect["screen_y1"],
                outline="red", width=2
            )

    def next_page(self):
        if self.pdf_doc and self.page_num < len(self.pdf_doc) - 1:
            self.save_json()
            self.page_num += 1
            self.page_rectangles.clear()
            self.rect_draw_order = 1
            self.show_page(self.page_num)

    def prev_page(self):
        if self.pdf_doc and self.page_num > 0:
            self.save_json()
            self.page_num -= 1
            self.page_rectangles.clear()
            self.rect_draw_order = 1
            self.show_page(self.page_num)

    def on_click(self, event):
        self.start_x = event.x
        self.start_y = event.y
        self.current_rect = self.canvas.create_rectangle(
            self.start_x, self.start_y, self.start_x, self.start_y, outline="red", width=2
        )

    def on_drag(self, event):
        if self.current_rect:
            self.canvas.coords(self.current_rect, self.start_x, self.start_y, event.x, event.y)

    def on_release(self, event):
        if not self.current_rect:
            return

        x0, y0, x1, y1 = self.canvas.coords(self.current_rect)

        # Skip zero-area rectangles
        if abs(x1 - x0) < 2 or abs(y1 - y0) < 2:
            print(f"[WARN] Ignored zero-area rectangle on page {self.page_num + 1}")
            self.canvas.delete(self.current_rect)
            self.current_rect = None
            return

        # Convert to PDF coordinates
        pdf_x0 = min(x0, x1) * self.scale
        pdf_y0 = min(y0, y1) * self.scale
        pdf_x1 = max(x0, x1) * self.scale
        pdf_y1 = max(y0, y1) * self.scale

        rect_data = {
            "order": self.rect_draw_order,
            "page": self.page_num + 1,
            "x0": round(pdf_x0, 2),
            "y0": round(pdf_y0, 2),
            "x1": round(pdf_x1, 2),
            "y1": round(pdf_y1, 2),
            "screen_x0": x0,
            "screen_y0": y0,
            "screen_x1": x1,
            "screen_y1": y1
        }

        self.page_rectangles.append(rect_data)
        self.rect_draw_order += 1
        print(f"Added rectangle #{rect_data['order']} on page {rect_data['page']}")
        self.current_rect = None

    def select_rectangle(self, event):
        # Right-click to select and move a rectangle
        items = self.canvas.find_overlapping(event.x, event.y, event.x, event.y)
        if items:
            self.selected_rect = items[0]
            self.start_move_x = event.x
            self.start_move_y = event.y
            self.canvas.bind("<B3-Motion>", self.move_rectangle)
            self.canvas.bind("<ButtonRelease-3>", self.release_rectangle)

    def move_rectangle(self, event):
        if not self.selected_rect:
            return
        dx = event.x - self.start_move_x
        dy = event.y - self.start_move_y
        self.canvas.move(self.selected_rect, dx, dy)
        self.start_move_x = event.x
        self.start_move_y = event.y

    def release_rectangle(self, event):
        self.selected_rect = None
        self.canvas.unbind("<B3-Motion>")

    def clear_rectangles(self):
        """Remove all drawn rectangles from the current page."""
        if not self.page_rectangles:
            return
        if messagebox.askyesno("Clear Markings", "Are you sure you want to remove all rectangles?"):
            self.page_rectangles.clear()
            self.show_page(self.page_num)
            print(f"Cleared all rectangles on page {self.page_num + 1}")

    def save_json(self):
        if not self.page_rectangles:
            print(f"No rectangles drawn on page {self.page_num + 1}.")
            return

        # Ensure the ./regions directory exists
        os.makedirs("regions", exist_ok=True)

        # Convert rectangles to PDF coordinate form
        json_data = [
            {
                "order": r["order"],
                "page": r["page"],
                "x0": r["x0"],
                "y0": r["y0"],
                "x1": r["x1"],
                "y1": r["y1"]
            }
            for r in self.page_rectangles
        ]

        json_filename = os.path.join("regions", f"{self.json_base}_page{self.page_num + 1}.json")
        with open(json_filename, "w", encoding="utf-8") as f:
            json.dump(json_data, f, indent=2, ensure_ascii=False)

        print(f"Saved {len(json_data)} rectangles to {json_filename}")


# Run
if __name__ == "__main__":
    root = tk.Tk()
    app = PDFRectangleSelector(root)
    root.mainloop()
