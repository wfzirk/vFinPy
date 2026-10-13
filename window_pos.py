import tkinter as tk
import customtkinter as ctk
import os

GEOM_FILE = "window_geom.txt"

# -----------------------------
# Configuration
# -----------------------------
DEFAULT_GEOMETRY = "900x600+120+80"   # fallback if no saved geometry
MIN_WIDTH = 600
MIN_HEIGHT = 400


# -----------------------------
# Load saved geometry
# -----------------------------
def load_geometry():
    if os.path.exists(GEOM_FILE):
        try:
            with open(GEOM_FILE, "r") as f:
                return f.read().strip()
        except:
            return None
    return None


# -----------------------------
# Save geometry on exit
# -----------------------------
def save_geometry(root):
    geom = root.winfo_geometry()
    #with open(GEOM_FILE, "w") as f:
    #    f.write(geom)


# -----------------------------
# Apply geometry safely
# -----------------------------
def apply_geometry(root):
    #root.withdraw()  # prevent flashing

    saved = load_geometry()
    if saved:
        root.geometry(saved)
    else:
        root.geometry(DEFAULT_GEOMETRY)

    # Apply minimum size
    root.minsize(MIN_WIDTH, MIN_HEIGHT)

    root.deiconify()  # show window already sized correctly


# ------------------------------
# Main CustomTkinter App
# ------------------------------
if __name__ == "__main__":

    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")

    app = ctk.CTk()
    app.title("CustomTkinter Window Restore")

    apply_geometry(app)

    app.protocol("WM_DELETE_WINDOW", lambda: (save_geometry(app), app.destroy()))

    app.mainloop()
