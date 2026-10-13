import customtkinter as ctk
import tkinter.ttk as ttk
import tkinter.colorchooser as cc
from tkinter import filedialog, messagebox
from pathlib import Path
import json

from theme_manager import theme_manager   # your global instance


class ThemeEditor(ctk.CTkToplevel):
    """
    Visual JSON theme editor with live CTk + Treeview preview.
    """

    def __init__(self, master=None, theme_path=None):
        super().__init__(master)

        self.title("Theme Editor")
        self.geometry("1100x700+120+80")
        self.after(100, self.lift)

        self.theme_path = None
        self.theme_data = {}

        self._build_layout()

        if theme_path:
            self.load_theme(theme_path)

    # ---------------------------------------------------------
    # Layout
    # ---------------------------------------------------------
    def _build_layout(self):
        # Top buttons
        top = ctk.CTkFrame(self)
        top.pack(fill="x", padx=10, pady=(10, 0))

        ctk.CTkButton(top, text="Open Theme JSON", command=self.open_theme).pack(side="left")
        ctk.CTkButton(top, text="Save", command=self.save_theme).pack(side="left", padx=10)
        ctk.CTkLabel(top, text="Theme", anchor="w").pack(side="left", padx=10)
        self.label_file = ctk.CTkLabel(top, text="Theme Name", anchor="w")
        self.label_file.pack(side="left", padx=10)

        # Main split
        main = ctk.CTkFrame(self)
        main.pack(fill="both", expand=True, padx=10, pady=10)

        # LEFT: JSON editor
        self.left_frame = ctk.CTkScrollableFrame(main, corner_radius=12, width=500)
        self.left_frame.pack(side="left", fill="both", expand=True, padx=(0, 10))

        # RIGHT: Preview panel
        self.right_frame = ctk.CTkFrame(main, corner_radius=12, width=500)
        self.right_frame.pack(side="right", fill="both", expand=True)

        self._build_preview_panels()

    # ---------------------------------------------------------
    # Load JSON
    # ---------------------------------------------------------
    def open_theme(self):
        path = filedialog.askopenfilename(
            parent=self,
            title="Select Theme JSON",
            filetypes=[("JSON Files", "*.json")]
        )
        if not path:
            return
        print('***********loadpath',path)
        self.label_file.configure(text=path)
        self.load_theme(path)

    def load_theme(self, path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                self.theme_data = json.load(f)
            self.theme_path = Path(path)

            # Sync global theme manager
            theme_manager.theme_data = self.theme_data
            theme_manager.theme_path = self.theme_path
            theme_manager.apply_treeview_theme()

            self._populate_editor()
            self._refresh_preview()
        except Exception as e:
            messagebox.showerror("Theme Load Error", str(e), parent=self)

    # ---------------------------------------------------------
    # Save JSON
    # ---------------------------------------------------------
    def save_theme(self):
        if not self.theme_path:
            messagebox.showwarning("Save", "No theme loaded.", parent=self)
            return

        try:
            with open(self.theme_path, "w", encoding="utf-8") as f:
                json.dump(self.theme_data, f, indent=4)
            messagebox.showinfo("Saved", f"Theme saved:\n{self.theme_path}", parent=self)
        except Exception as e:
            messagebox.showerror("Save Error", str(e), parent=self)

    # ---------------------------------------------------------
    # Populate JSON editor
    # ---------------------------------------------------------
    def _populate_editor(self):
        for w in self.left_frame.winfo_children():
            w.destroy()

        for section, values in self.theme_data.items():
            if not isinstance(values, dict):
                continue

            sec_label = ctk.CTkLabel(self.left_frame, text=f"[ {section} ]", font=("Segoe UI", 16, "bold"))
            sec_label.pack(anchor="w", pady=(10, 4))

            for key, val in values.items():
                self._add_color_entry(section, key, val)

    # ---------------------------------------------------------
    # Add a single color entry row
    # ---------------------------------------------------------
    def _add_color_entry(self, section, key, val):
        row = ctk.CTkFrame(self.left_frame)
        row.pack(fill="x", pady=4)

        ctk.CTkLabel(row, text=key, width=180, anchor="w").pack(side="left")

        colors = None
        if isinstance(val, list) and all(isinstance(v, str) and v.startswith("#") for v in val):
            colors = val
        elif isinstance(val, str) and val.startswith("#"):
            colors = [val]

        if not colors:
            ctk.CTkLabel(row, text=str(val), anchor="w").pack(side="left")
            return

        # Swatches
        for idx, color in enumerate(colors):
            hex_entry = ctk.CTkEntry(
                row,
                width=90,
                justify="left"
            )
            hex_entry.insert(0, color)
            hex_entry.pack(side="left", padx=10)

            # Manual entry handler
            hex_entry.bind(
                "<FocusOut>",
                lambda e, s=section, k=key, i=idx, entry=hex_entry: self._manual_color_edit(s, k, i, entry)
            )

            # Create swatch FIRST
            swatch = ctk.CTkButton(
                row,
                width=40,
                height=25,
                fg_color=color,
                text=""
            )
            swatch.pack(side="left", padx=5)

            # Now that swatch exists, bind the command
            swatch.configure(
                command=lambda s=section, k=key, i=idx, entry=hex_entry, sw=swatch:
                    self._edit_color(s, k, i, entry, sw)
            )

            # Store reference for manual edit
            hex_entry._swatch = swatch

        ctk.CTkLabel(row, text=str(colors), anchor="w").pack(side="left", padx=10)

    # ---------------------------------------------------------
    # Edit color
    # ---------------------------------------------------------
    def _edit_color(self, section, key, index, hex_entry, swatch):
        old_color = self.theme_data[section][key][index]

        rgb, new_color = cc.askcolor(
            title=f"Pick Color for {section}.{key}[{index}]",
            initialcolor=old_color,
            parent=self
        )

        if not new_color:
            return

        # Update JSON
        self.theme_data[section][key][index] = new_color

        # Update entry text
        hex_entry.delete(0, "end")
        hex_entry.insert(0, new_color)

        # Update swatch color
        swatch.configure(fg_color=new_color)

        # Refresh UI
        self._refresh_preview()

    def _manual_color_edit(self, section, key, index, entry):
        new_color = entry.get().strip()

        # Basic hex validation
        if not new_color.startswith("#") or len(new_color) not in (4, 7):
            entry.configure(border_color="#FF3333")   # red border for invalid
            return

        # Reset border to original color (safe)
        entry.configure(border_color=entry._border_color)

        # Update JSON
        self.theme_data[section][key][index] = new_color

        # Update swatch color
        if hasattr(entry, "_swatch"):
            entry._swatch.configure(fg_color=new_color)

        # Refresh UI
        self._refresh_preview()

    # ---------------------------------------------------------
    # Build preview panels
    # ---------------------------------------------------------
    def _build_preview_panels(self):
        ctk.CTkLabel(self.right_frame, text="Live Preview", font=("Segoe UI", 18, "bold")).pack(anchor="w", pady=(10, 10))

        # CTk preview
        self.ctk_preview = ctk.CTkFrame(self.right_frame, corner_radius=12)
        self.ctk_preview.pack(fill="x", padx=10, pady=10)

        ctk.CTkLabel(self.ctk_preview, text="CTk Widgets", font=("Segoe UI", 14, "bold")).pack(anchor="w", pady=(0, 10))

        self.preview_label = ctk.CTkLabel(self.ctk_preview, text="Sample Label")
        self.preview_label.pack(anchor="w", pady=4)

        self.preview_button = ctk.CTkButton(self.ctk_preview, text="Sample Button")
        self.preview_button.pack(anchor="w", pady=4)

        self.preview_entry = ctk.CTkEntry(self.ctk_preview)
        self.preview_entry.pack(anchor="w", pady=4)

        self.preview_checkbox = ctk.CTkCheckBox(self.ctk_preview, text="Sample Checkbox")
        self.preview_checkbox.pack(anchor="w", pady=4)

        self.preview_switch = ctk.CTkSwitch(self.ctk_preview, text="Sample Switch")
        self.preview_switch.pack(anchor="w", pady=4)

        # Hover preview (CTk)
        self.hover_preview_frame = ctk.CTkFrame(self.right_frame, corner_radius=12)
        self.hover_preview_frame.pack(fill="x", padx=10, pady=(10, 10))

        ctk.CTkLabel(self.hover_preview_frame, text="Hover Preview", font=("Segoe UI", 14, "bold")).pack(anchor="w", pady=(5, 5))
        self.hover_preview_label = ctk.CTkLabel(self.hover_preview_frame, text="Treeview hover color sample")
        self.hover_preview_label.pack(fill="x", padx=5, pady=5)

        # Treeview preview
        ctk.CTkLabel(self.right_frame, text="Treeview Preview", font=("Segoe UI", 14, "bold")).pack(anchor="w", pady=(20, 10))

        tree_container = ctk.CTkFrame(self.right_frame, corner_radius=12)
        tree_container.pack(fill="both", expand=True, padx=10, pady=10)

        # Apply Treeview theme BEFORE creating the widget
        theme_manager.apply_treeview_theme()

        self.preview_tree = ttk.Treeview(
            tree_container,
            columns=("col1", "col2"),
            show="headings",
            height=10
        )

        self.preview_tree.heading("col1", text="Column A")
        self.preview_tree.heading("col2", text="Column B")

        for i in range(20):
            self.preview_tree.insert("", "end", values=(f"Row {i+1}", f"Value {i+1}"))

        self.preview_tree.grid(row=0, column=0, sticky="nsew")

        tree_container.grid_rowconfigure(0, weight=1)
        tree_container.grid_columnconfigure(0, weight=1)

        # Initial style + stripes + hover
        theme_manager.style_treeview_widget(self.preview_tree)

    # ---------------------------------------------------------
    # Refresh preview
    # ---------------------------------------------------------
    def _refresh_preview(self):
        # Sync global theme manager
        theme_manager.theme_data = self.theme_data
        if self.theme_path:
            theme_manager.theme_path = self.theme_path

        # Reapply CTk theme
        theme_manager.apply_ctk_theme()

        # Reapply Treeview theme
        theme_manager.apply_treeview_theme()
        self.preview_tree.configure(style="CTk.Treeview")
        theme_manager.apply_treeview_stripes(self.preview_tree)
        theme_manager.enable_treeview_hover(self.preview_tree)

        # Helper to read values
        def get(section, key, default):
            sec = self.theme_data.get(section, {})
            val = sec.get(key, default)
            return val[0] if isinstance(val, list) else val

        frame_bg = get("CTkFrame", "fg_color", "#1A1A1A")
        label_fg = get("CTkLabel", "text_color", "#FFFFFF")
        button_bg = get("CTkButton", "fg_color", "#2D6D7D")
        hover_bg = get("Treeview", "hover_bg", "#333333")

        # Refresh CTk preview widgets
        self.ctk_preview.configure(fg_color=frame_bg)
        self.preview_label.configure(text_color=label_fg)
        self.preview_button.configure(fg_color=button_bg)
        self.preview_entry.configure(fg_color=frame_bg, text_color=label_fg)
        self.preview_checkbox.configure(text_color=label_fg)
        self.preview_switch.configure(text_color=label_fg)

        # Live hover preview
        self.hover_preview_frame.configure(fg_color=hover_bg)
        print('hover', label_fg)
        self.hover_preview_label.configure(text_color=label_fg)

    def mainloop(self, *args, **kwargs):
        super().mainloop(*args, **kwargs)


def main():
    import sys

    ctk.set_appearance_mode("System")
    ctk.set_default_color_theme("blue")

    app = ThemeEditor(theme_path="ctk_themes/finofx.json")

    def close_all():
        app.destroy()
        sys.exit()

    app.protocol("WM_DELETE_WINDOW", close_all)
    app.mainloop()


if __name__ == "__main__":
    main()
