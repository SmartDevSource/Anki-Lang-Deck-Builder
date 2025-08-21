# src/about.py
import tkinter as tk
from tkinter import ttk

def show_about(master, get_text):
    win = tk.Toplevel(master)
    win.title(get_text("about_title"))
    win.configure(bg="#f9f1da")
    win.resizable(False, False)
    win.transient(master)
    win.grab_set()

    # Contenu
    container = tk.Frame(win, bg="#f9f1da")
    container.pack(padx=18, pady=18)

    msg = tk.Label(
        container,
        text=get_text("about_text"),
        bg="#f9f1da",
        justify="center",
        font=("Segoe UI", 11),
        wraplength=420,
    )
    msg.pack(anchor="center", pady=(0, 14))

    close_btn = ttk.Button(container, text=get_text("close"), command=win.destroy)
    close_btn.pack(anchor="center")

    # Centrage écran
    win.update_idletasks()
    w, h = win.winfo_width(), win.winfo_height()
    sw, sh = win.winfo_screenwidth(), win.winfo_screenheight()
    x, y = (sw // 2) - (w // 2), (sh // 2) - (h // 2)
    win.geometry(f"{w}x{h}+{x}+{y}")

    # Focus par défaut
    close_btn.focus_set()
