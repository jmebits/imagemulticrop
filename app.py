import os
import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk


class ImageCropperApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Image Cropper & Extractor")
        self.root.geometry("1150x700")

        # State variables
        self.file_path = None
        self.orig_image = None  # Original PIL image
        self.display_image = None  # Resized PIL image for display
        self.tk_image = None  # Tkinter compatible image

        self.scale_x = 1.0
        self.scale_y = 1.0

        self.rect_start_x = None
        self.rect_start_y = None
        self.current_rect = None

        self.crops = []  # List to store crops

        # --- Graphical User Interface ---

        # 1. Top Panel (Global action and rotation buttons)
        top_frame = tk.Frame(root, pady=10, padx=10, bg="#f0f0f0")
        top_frame.pack(side=tk.TOP, fill=tk.X)

        btn_load = tk.Button(top_frame, text="📁 Load Image", command=self.load_image, font=("Arial", 10, "bold"),
                             bg="#4CAF50", fg="white", padx=8, pady=5)
        btn_load.pack(side=tk.LEFT, padx=5)

        # Rotation Buttons
        btn_rotate_left = tk.Button(top_frame, text="↺ Rotate -90°", command=lambda: self.rotate_image(90),
                                    font=("Arial", 9), bg="#FF9800", fg="white", padx=6, pady=5)
        btn_rotate_left.pack(side=tk.LEFT, padx=2)

        btn_rotate_right = tk.Button(top_frame, text="↻ Rotate 90°", command=lambda: self.rotate_image(-90),
                                     font=("Arial", 9), bg="#FF9800", fg="white", padx=6, pady=5)
        btn_rotate_right.pack(side=tk.LEFT, padx=2)

        btn_export = tk.Button(top_frame, text="💾 Export Crops", command=self.export_crops, font=("Arial", 10, "bold"),
                               bg="#2196F3", fg="white", padx=8, pady=5)
        btn_export.pack(side=tk.RIGHT, padx=5)

        # 2. Main Panel (Split into Left Canvas and Right Sidebar)
        main_frame = tk.Frame(root)
        main_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 2.1 Image Canvas (Left)
        self.canvas_frame = tk.Frame(main_frame, bg="gray", bd=2, relief=tk.SUNKEN)
        self.canvas_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.canvas = tk.Canvas(self.canvas_frame, cursor="cross", bg="#2b2b2b")
        self.canvas.pack(fill=tk.BOTH, expand=True)

        # Mouse events for rectangular selection
        self.canvas.bind("<ButtonPress-1>", self.on_button_press)
        self.canvas.bind("<B1-Motion>", self.on_move_press)
        self.canvas.bind("<ButtonRelease-1>", self.on_button_release)
        self.canvas.bind("<Configure>", lambda e: self.display_canvas_image())

        # 2.2 Thumbnails Sidebar (Right)
        sidebar_outer = tk.Frame(main_frame, width=320, bg="#e0e0e0", bd=2, relief=tk.GROOVE)
        sidebar_outer.pack(side=tk.RIGHT, fill=tk.Y, padx=(10, 0))
        sidebar_outer.pack_propagate(False)

        lbl_sidebar = tk.Label(sidebar_outer, text="Selected Crops", font=("Arial", 11, "bold"), bg="#e0e0e0", pady=5)
        lbl_sidebar.pack(side=tk.TOP, fill=tk.X)

        # Canvas with scrollbar for the thumbnail list
        self.sidebar_canvas = tk.Canvas(sidebar_outer, bg="#f9f9f9")
        self.scrollbar = tk.Scrollbar(sidebar_outer, orient="vertical", command=self.sidebar_canvas.yview)
        self.sidebar_inner = tk.Frame(self.sidebar_canvas, bg="#f9f9f9")

        self.sidebar_inner.bind(
            "<Configure>",
            lambda e: self.sidebar_canvas.configure(scrollregion=self.sidebar_canvas.bbox("all"))
        )

        self.sidebar_canvas.create_window((0, 0), window=self.sidebar_inner, anchor="nw")
        self.sidebar_canvas.configure(yscrollcommand=self.scrollbar.set)

        self.sidebar_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def load_image(self):
        file_path = filedialog.askopenfilename(
            title="Select image",
            filetypes=[("Image Files", "*.png *.jpg *.jpeg *.bmp *.webp *.tiff")]
        )
        if not file_path:
            return

        self.file_path = file_path
        self.orig_image = Image.open(file_path)

        # Clear previous selections when loading a new image
        self.crops.clear()
        self.refresh_sidebar()
        self.display_canvas_image()

    def rotate_image(self, angle):
        if not self.orig_image:
            messagebox.showwarning("Warning", "You must load an image first.")
            return

        # Rotate original PIL image (expand=True avoids clipping corners if not square)
        self.orig_image = self.orig_image.rotate(angle, expand=True)

        # Rotating clears previous selections since coordinates will change.
        if self.crops:
            if not messagebox.askyesno("Rotation Warning",
                                       "Rotating the image will clear current crops because their coordinates will change. Do you wish to continue?"):
                # Revert rotation if cancelled
                self.orig_image = self.orig_image.rotate(-angle, expand=True)
                return
            self.crops.clear()
            self.refresh_sidebar()

        self.display_canvas_image()

    def display_canvas_image(self):
        if not self.orig_image:
            return

        self.canvas.update_idletasks()
        c_width = self.canvas.winfo_width()
        c_height = self.canvas.winfo_height()

        if c_width < 10 or c_height < 10:
            c_width, c_height = 700, 600

        orig_w, orig_h = self.orig_image.size

        # Calculate scale maintaining aspect ratio
        ratio = min(c_width / orig_w, c_height / orig_h)
        new_w = int(orig_w * ratio)
        new_h = int(orig_h * ratio)

        self.scale_x = orig_w / new_w
        self.scale_y = orig_h / new_h

        # Resize for visualization
        resized_pil = self.orig_image.resize((new_w, new_h), Image.Resampling.LANCZOS)
        self.tk_image = ImageTk.PhotoImage(resized_pil)

        self.canvas.delete("all")
        self.img_on_canvas = self.canvas.create_image(c_width // 2, c_height // 2, anchor=tk.CENTER,
                                                      image=self.tk_image)

        bbox = self.canvas.bbox(self.img_on_canvas)
        if bbox:
            self.img_offset_x = bbox[0]
            self.img_offset_y = bbox[1]
        else:
            self.img_offset_x = 0
            self.img_offset_y = 0

    def on_button_press(self, event):
        if not self.orig_image:
            return
        self.rect_start_x = event.x
        self.rect_start_y = event.y
        self.current_rect = self.canvas.create_rectangle(
            self.rect_start_x, self.rect_start_y, 1, 1, outline="yellow", width=2, dash=(4, 2)
        )

    def on_move_press(self, event):
        if not self.current_rect:
            return
        cur_x, cur_y = event.x, event.y
        self.canvas.coords(self.current_rect, self.rect_start_x, self.rect_start_y, cur_x, cur_y)

    def on_button_release(self, event):
        if not self.current_rect or not self.orig_image:
            return

        coords = self.canvas.coords(self.current_rect)
        self.canvas.delete(self.current_rect)
        self.current_rect = None

        if not coords:
            return

        x1, y1, x2, y2 = coords
        xmin, xmax = min(x1, x2), max(x1, x2)
        ymin, ymax = min(y1, y2), max(y1, y2)

        if (xmax - xmin) < 5 or (ymax - ymin) < 5:
            return

        rel_x1 = xmin - self.img_offset_x
        rel_y1 = ymin - self.img_offset_y
        rel_x2 = xmax - self.img_offset_x
        rel_y2 = ymax - self.img_offset_y

        orig_w, orig_h = self.orig_image.size

        box_left = max(0, int(rel_x1 * self.scale_x))
        box_top = max(0, int(rel_y1 * self.scale_y))
        box_right = min(orig_w, int(rel_x2 * self.scale_x))
        box_bottom = min(orig_h, int(rel_y2 * self.scale_y))

        if box_right - box_left < 2 or box_bottom - box_top < 2:
            return

        crop_box = (box_left, box_top, box_right, box_bottom)
        cropped_img = self.orig_image.crop(crop_box)

        self.crops.append({
            "pil_img": cropped_img,
            "box": crop_box
        })

        self.refresh_sidebar()

    def refresh_sidebar(self):
        for widget in self.sidebar_inner.winfo_children():
            widget.destroy()

        for index, item in enumerate(self.crops):
            pil_img = item["pil_img"]
            box = item["box"]
            w, h = pil_img.size

            item_frame = tk.Frame(self.sidebar_inner, bg="white", bd=1, relief=tk.SOLID, padx=5, pady=5)
            item_frame.pack(fill=tk.X, padx=5, pady=5)

            thumb_img = pil_img.copy()
            thumb_img.thumbnail((80, 80))
            tk_thumb = ImageTk.PhotoImage(thumb_img)

            if not hasattr(self, "_thumb_refs"):
                self._thumb_refs = []
            self._thumb_refs.append(tk_thumb)

            lbl_img = tk.Label(item_frame, image=tk_thumb, bg="white")
            lbl_img.grid(row=0, column=0, rowspan=2, padx=5)

            info_text = f"#{index + 1}: {w}x{h} px\nPos: ({box[0]}, {box[1]})"
            lbl_info = tk.Label(item_frame, text=info_text, font=("Arial", 9), bg="white", justify=tk.LEFT)
            lbl_info.grid(row=0, column=1, sticky="w", padx=5)

            btn_delete = tk.Button(
                item_frame, text="❌ Delete", fg="red", font=("Arial", 8, "bold"),
                command=lambda idx=index: self.delete_crop(idx)
            )
            btn_delete.grid(row=1, column=1, sticky="w", padx=5, pady=2)

    def delete_crop(self, index):
        if 0 <= index < len(self.crops):
            del self.crops[index]
            self.refresh_sidebar()

    def export_crops(self):
        if not self.crops:
            messagebox.showwarning("No Crops", "There are no selected areas to export.")
            return

        dir_path = filedialog.askdirectory(title="Select destination folder")
        if not dir_path:
            return

        try:
            base_name = os.path.splitext(os.path.basename(self.file_path))[0] if self.file_path else "crop"
            for i, item in enumerate(self.crops):
                pil_img = item["pil_img"]
                out_path = os.path.join(dir_path, f"{base_name}_crop_{i + 1}.png")
                pil_img.save(out_path, "PNG")

            messagebox.showinfo("Export Complete", f"Successfully exported {len(self.crops)} crops to:\n{dir_path}")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred while saving the images:\n{str(e)}")


if __name__ == "__main__":
    root = tk.Tk()
    app = ImageCropperApp(root)
    root.mainloop()