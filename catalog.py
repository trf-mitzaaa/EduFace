import tkinter as tk
from PIL import Image, ImageTk
import subprocess
import sys
import os

# === Helper pentru căi absolute ===
def script_path(filename):
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), filename)

# === Lansează scripturile cu Python ===
def launch(script):
    subprocess.Popen([sys.executable, script_path(script)])

# === Meniu principal ===
def show_main_menu():
    splash.destroy()

    root = tk.Tk()
    root.title("Meniu Sistem Școlar")
    root.geometry("350x650")
    root.configure(bg="#f0f6fa")

    tk.Label(root, text="Meniu Aplicații Școlare", font=("Segoe UI", 16, "bold"),
             bg="#31415e", fg="white", pady=16).pack(fill=tk.X, pady=16)

    btn_style = {
        "font": ("Segoe UI", 12, "bold"), "bg": "#2a6786", "fg": "white",
        "width": 22, "height": 2, "bd": 0, "cursor": "hand2"
    }

    tk.Button(root, text="Aplicație Admin", command=lambda: launch("admin.py"), **btn_style).pack(pady=10)
    tk.Button(root, text="Aplicație Profesori", command=lambda: launch("catalog_profesori.py"), **btn_style).pack(pady=10)
    tk.Button(root, text="Aplicație Diriginți", command=lambda: launch("catalog_diriginti.py"), **btn_style).pack(pady=10)
    tk.Button(root, text="Aplicație Elevi", command=lambda: launch("elevi.py"), **btn_style).pack(pady=10)
    tk.Button(root, text="Recunoaștere Facială", command=lambda: launch("face.py"), **btn_style).pack(pady=10)

    tk.Button(root, text="Ieșire", command=root.destroy, bg="#b0413e", fg="white",
              font=("Segoe UI", 12, "bold"), width=22, height=2, bd=0).pack(pady=16)

    root.mainloop()

# === SPLASH SCREEN ===
splash = tk.Tk()
splash.title("EduFace Launcher")

# Centrare + dimensiuni ecran
screen_w = splash.winfo_screenwidth()
screen_h = splash.winfo_screenheight()
win_w, win_h = 520, 450
x = (screen_w - win_w) // 2
y = (screen_h - win_h) // 2
splash.geometry(f"{win_w}x{win_h}+{x}+{y}")
splash.configure(bg="#f0f6fa")

# Încarcă și redimensionează imaginea
try:
    img_path = script_path("splash.png")
    img_original = Image.open(img_path)

    # Compatibilitate Pillow 10+
    try:
        resample_mode = Image.Resampling.LANCZOS
    except AttributeError:
        resample_mode = Image.LANCZOS

    max_w = int(win_w * 0.8)
    max_h = int(win_h * 0.6)
    img_resized = img_original.copy()
    img_resized.thumbnail((max_w, max_h), resample_mode)

    tk_img = ImageTk.PhotoImage(img_resized)
    panel = tk.Label(splash, image=tk_img, bg="#f0f6fa")
    panel.pack(pady=(40, 20))
except Exception as e:
    tk.Label(splash, text="Imagine indisponibilă.", bg="#f0f6fa", fg="red", font=("Segoe UI", 12)).pack(pady=20)
    print("Eroare încărcare imagine:", e)

# Buton continuă
tk.Button(splash, text="Continuă", command=show_main_menu,
          font=("Segoe UI", 12, "bold"), bg="#344675", fg="white", width=18, height=2).pack(pady=20)

splash.mainloop()
