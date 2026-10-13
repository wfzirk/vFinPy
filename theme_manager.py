import json
import customtkinter as ctk
import tkinter.ttk as ttk
from pathlib import Path

from logging_manager import get_logger
log = get_logger(__name__)

# ---------------------------------------------------------
# Safe JSON getter
# ---------------------------------------------------------
def _safe_get(section, key, default):
    try:
        val = section.get(key, default)
        if isinstance(val, list):
            return val[0]  # light mode for preview
        return val
    except Exception:
        return default


# ---------------------------------------------------------
# Global Theme Manager
# ---------------------------------------------------------
class GlobalThemeManager:
    def __init__(self):
        self.theme_data = {}
        self.theme_path = None
        log.info('GlobalThemeManager loaded')
    # -----------------------------------------------------
    # Load JSON theme
    # -----------------------------------------------------
    def load_theme(self, path):
        self.theme_path = Path(path)
        with open(path, "r", encoding="utf-8") as f:
            self.theme_data = json.load(f)

    # -----------------------------------------------------
    # Apply CTk theme (CustomTkinter built‑in)
    # -----------------------------------------------------
    def apply_ctk_theme(self):
        if not self.theme_path:
            return
        ctk.set_default_color_theme(str(self.theme_path))

    def apply_named_theme(self, root, name):
        if name in ("blue", "green", "dark-blue"):
            ctk.set_default_color_theme(name)
        else:
            #theme_file = Path("themes") / f"{name}.json"
            theme_file = Path(name)
            self.load_theme(theme_file)
            self.apply_all(root)

    # -----------------------------------------------------
    # Apply Treeview theme (JSON‑driven)
    # -----------------------------------------------------
    def apply_treeview_theme(self):
        """
        Applies JSON-driven Treeview theme to ALL ttk.Treeview widgets.
        """
        if "Treeview" not in self.theme_data:
            return

        tv = self.theme_data["Treeview"]
        print('apply_treeview_theme')
        bg = _safe_get(tv, "bg_color", "#1A1A1A")
        alt_bg = _safe_get(tv, "alt_bg_color", "#222222")
        
        table_even_bg = _safe_get(tv, "bg_color", "#1A1A1A")
        table_odd_bg = _safe_get(tv, "alt_bg_color", "#222222")
        
        fg = _safe_get(tv, "text_color", "#FFFFFF")
        sel_bg = _safe_get(tv, "selection_bg", "#3A7EBF")
        header_bg = _safe_get(tv, "header_bg", "#111111")
        header_fg = _safe_get(tv, "header_fg", "#42A5F5")
        hover_bg = _safe_get(tv, "hover_bg", "#333333")

        style = ttk.Style()
        style.theme_use("clam")

        # Body
        style.configure(
            "CTk.Treeview",
            background=bg,
            fieldbackground=bg,
            foreground=fg,
            borderwidth=0,
            rowheight=24,
            font=("Segoe UI", 11)
        )

        # Selection
        style.map(
            "CTk.Treeview",
            background=[("selected", sel_bg)],
            foreground=[("selected", fg)]
        )

        # Headers
        style.configure(
            "CTk.Treeview.Heading",
            background=header_bg,
            foreground=header_fg,
            relief="flat",
            padding=6,
            font=("Segoe UI", 11, "bold")
        )

        # Tag-based colors (even/odd/hover)
        style.configure("CTk.Treeview.Even", background=bg)
        style.configure("CTk.Treeview.Odd", background=alt_bg)
        style.configure("CTk.Treeview.Hover", background=hover_bg)

    # -----------------------------------------------------
    # Apply alternating stripes to a Treeview
    # -----------------------------------------------------
    def apply_treeview_stripes(self, tree):
        """
        Apply alternating row colors to a Treeview.
        """
        if "Treeview" not in self.theme_data:
            return

        tv = self.theme_data["Treeview"]
        bg = _safe_get(tv, "bg_color", "#1A1A1A")
        alt_bg = _safe_get(tv, "alt_bg_color", "#222222")

        tree.tag_configure("even", background=bg)
        tree.tag_configure("odd", background=alt_bg)

        for index, iid in enumerate(tree.get_children()):
            tag = "even" if index % 2 == 0 else "odd"
            tree.item(iid, tags=(tag,))

    # -----------------------------------------------------
    # Apply hover highlight to a Treeview
    # -----------------------------------------------------
    def enable_treeview_hover(self, tree):
        if "Treeview" not in self.theme_data:
            return

        tv = self.theme_data["Treeview"]
        default_bg = _safe_get(tv, "bg_color", "#1A1A1A")
        hover_bg = _safe_get(tv, "hover_bg", "#333333")

        tree.tag_configure("hover", background=hover_bg)

        # Store original tags per row
        if not hasattr(tree, "_orig_row_tags"):
            tree._orig_row_tags = {}

        # Track last hovered row
        if not hasattr(tree, "_last_hover"):
            tree._last_hover = None

        def restore_row(iid):
            orig_tags = tree._orig_row_tags.get(iid)
            if orig_tags:
                tree.item(iid, tags=orig_tags)
            else:
                tree.item(iid, tags=())

        def on_motion(event):
            row_id = tree.identify_row(event.y)

            # Pointer NOT over any row → clear hover
            if not row_id:
                if tree._last_hover:
                    restore_row(tree._last_hover)
                    tree._last_hover = None
                return

            # Leaving previous row
            if tree._last_hover and tree._last_hover != row_id:
                restore_row(tree._last_hover)

            # Entering new row
            if row_id != tree._last_hover:
                # Save original tags (even/odd/selection)
                tree._orig_row_tags[row_id] = tree.item(row_id, "tags")

                # Apply hover tag only so it wins
                tree.item(row_id, tags=("hover",))

                tree._last_hover = row_id

        def on_leave(event):
            if tree._last_hover:
                try:
                    restore_row(tree._last_hover)
                except Exception:
                    pass
            tree._last_hover = None

        tree.bind("<Leave>", on_leave)
        tree.bind("<Motion>", on_motion)
    # -----------------------------------------------------
    # Apply theme to a specific Treeview widget
    # -----------------------------------------------------
    def style_treeview_widget(self, tree):
        """
        Apply CTk.Treeview style to a specific Treeview instance.
        """
        self.apply_treeview_theme()
        tree.configure(style="CTk.Treeview")
        self.apply_treeview_stripes(tree)
        self.enable_treeview_hover(tree)

    # -----------------------------------------------------
    # Apply theme to entire app
    # -----------------------------------------------------
    def apply_theme(self, root):
        self.apply_all(root)
        
    def apply_all(self, root):
        """
        Apply CTk theme + Treeview theme to entire app.
        """
        self.apply_ctk_theme()
        self.apply_treeview_theme()

        # Style all Treeviews in the app
        for widget in root.winfo_children():
            self._style_recursive(widget)

    def _style_recursive(self, widget):
        if isinstance(widget, ttk.Treeview):
            widget.configure(style="CTk.Treeview")
            self.apply_treeview_stripes(widget)
            self.enable_treeview_hover(widget)

        for child in widget.winfo_children():
            self._style_recursive(child)


# ---------------------------------------------------------
# Global instance
# ---------------------------------------------------------

theme_manager = GlobalThemeManager()
