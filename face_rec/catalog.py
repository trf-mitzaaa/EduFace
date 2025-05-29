import tkinter as tk
import subprocess
import sys
import os

# Helper pentru a obține calea absolută a scriptului dacă rulează din alte directoare
def script_path(filename):
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), filename)

def launch(script):
    # Pornește fiecare aplicație într-un nou proces Python
    subprocess.Popen([sys.executable, script_path(script)])

root = tk.Tk()
root.title("Meniu Sistem Școlar")
root.geometry("350x650")
root.configure(bg="#f0f6fa")

tk.Label(root, text="Meniu Aplicații Școlare", font=("Segoe UI", 16, "bold"), bg="#31415e", fg="white", pady=16).pack(fill=tk.X, pady=16)

btn_style = {"font": ("Segoe UI", 12, "bold"), "bg": "#2a6786", "fg": "white", "width": 22, "height": 2, "bd": 0, "cursor": "hand2"}

tk.Button(root, text="Aplicație Admin", command=lambda: launch("admin.py"), **btn_style).pack(pady=10)
tk.Button(root, text="Aplicație Profesori", command=lambda: launch("catalog_profesori.py"), **btn_style).pack(pady=10)
tk.Button(root, text="Aplicație Diriginți", command=lambda: launch("catalog_diriginti.py"), **btn_style).pack(pady=10)
tk.Button(root, text="Aplicație Elevi", command=lambda: launch("elevi.py"), **btn_style).pack(pady=10)
tk.Button(root, text="Recunoaștere Facială", command=lambda: launch("face.py"), **btn_style).pack(pady=10)

tk.Button(root, text="Ieșire", command=root.destroy, bg="#b0413e", fg="white", font=("Segoe UI", 12, "bold"), width=22, height=2, bd=0).pack(pady=16)

root.mainloop()
