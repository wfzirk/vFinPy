

import copy
import ctypes
'''
try:
ctypes.windll.user32.SetProcessDpiAwarenessContext(
        ctypes.c_void_p(-4)
    )
except Exception:
    pass
'''
import customtkinter as ctk
import tkinter as tk
import tkinter.ttk as ttk
import tkinter.colorchooser as cc

from tkinter import messagebox
from config import fin_config

# ---------------------------------------------------------
# Utilities
# ---------------------------------------------------------

def normalize_color(value):

    if not isinstance(value, str):
        return value

    value = value.strip()

    if value.startswith("(") and value.endswith(")"):

        try:
            r, g, b = [
                int(v.strip())
                for v in value[1:-1].split(",")
            ]

            return f"#{r:02x}{g:02x}{b:02x}"

        except Exception:
            pass

    return value


# ---------------------------------------------------------
# Config Editor
# ---------------------------------------------------------

class ConfigEditor(ctk.CTkToplevel):

    def __init__(self, master=None):

        super().__init__(master)

        self.withdraw()
        
        self.title("Config Editor")
        #self.geometry("850x700+100+25")
        self.resizable(False, False)
        self.minsize(800, 700)

        self.tree_colors = copy.deepcopy(
            fin_config.tree_colors.to_dict()
        )

        self.trans_widths = copy.deepcopy(
            fin_config.transWidths.to_dict()
        )

        self.color_controls = {}
        
        self._refresh_after = None

        self._build_layout()
        self._populate_color_editor()
        self._populate_width_tree()

        self._build_sample_tree()

        self._refresh_preview()

        self.update_idletasks()
        #self.after_idle(self.deiconify)
        self.after(50, self.deiconify)
    
    # ---------------------------------------------------------
    # Layout
    # ---------------------------------------------------------

    def _build_layout(self):

        #self.grid_rowconfigure(1, weight=1)
        #self.grid_columnconfigure(0, weight=1)

        toolbar = ctk.CTkFrame(self)
        toolbar.grid(
            row=0,
            column=0,
            sticky="ew",
            padx=10,
            pady=(10, 5)
        )

        # toolbar.grid_rowconfigure(0, weight=1)
        #toolbar.grid_columnconfigure(0, weight=0)
        toolbar.grid_columnconfigure(2, weight=1)
        
        saveBtn = ctk.CTkButton(
            toolbar,
            text="Save All",
            command=self.save_config
        )

        reloadBtn = ctk.CTkButton(
            toolbar,
            text="Reload",
            command=self.reload_config
        )
        saveBtn.grid(row=0, column=0, padx=5, pady=5)
        reloadBtn.grid(row=0, column=1, padx=5, pady=5)
    
        main = ctk.CTkFrame(self)
        main.grid(
            row=1,
            column=0,
            sticky="nsew",
            padx=10,
            pady=(5, 10)
        )

        main.grid_rowconfigure(0, weight=1)
        main.grid_columnconfigure(0, weight=0)  #, minsize=475)
        #main.grid_columnconfigure(1, weight=2)
        main.grid_columnconfigure(1, weight=1)

        #self.left_frame = ctk.CTkScrollableFrame(main)
        self.left_frame = ctk.CTkFrame(main)
        self.left_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        self.left_frame.grid_rowconfigure(0, weight=1)
        self.left_frame.grid_columnconfigure(0, weight=0)
        
        self.color_frame = ctk.CTkFrame(self.left_frame)
        self.color_frame.grid(row=0, column=0, sticky="nsew")
        self.color_frame.grid_rowconfigure(0, weight=1)
        self.color_frame.grid_columnconfigure(0, weight=1)

        self.width_frame = ctk.CTkFrame(self.left_frame)
        self.width_frame.grid(row=1, column=0, sticky="nsew", pady=(10,0))
        self.width_frame.grid_rowconfigure(1, weight=1)
        self.width_frame.grid_columnconfigure(0, weight=1)
        
        self.right_frame = ctk.CTkFrame(main)
        self.right_frame.grid(row=0, column=1, sticky="nsew")
        self.right_frame.grid_rowconfigure(1, weight=1)
        self.right_frame.grid_columnconfigure(0, weight=1)

        #self.right_frame.grid_propagate(False)
        self._build_preview()
 
    # ---------------------------------------------------------
    # Preview Panel
    # ---------------------------------------------------------

    def _build_preview(self):

        ctk.CTkLabel(
            self.right_frame,
            text="Tree Preview",
            font=("Segoe UI", 18, "bold")
        ).grid(
            row=0,
            column=0,
            sticky="w",
            padx=10,
            pady=10
        )

        preview_frame = ctk.CTkFrame(
            self.right_frame
        )

        preview_frame.grid(
            row=1,
            column=0,
            sticky="nsew",
            padx=10,
            pady=(0, 10)
        )

        preview_frame.grid_rowconfigure(0, weight=1)
        preview_frame.grid_columnconfigure(0, weight=1)
        #preview_frame.grid_propagate(False)
        
        self.preview_tree = ttk.Treeview(
            preview_frame,
            columns=("amount",),
            show="tree headings"
        )

        self.preview_tree.heading(
            "#0",
            text="Description"
        )

        self.preview_tree.heading(
            "amount",
            text="Amount"
        )

        self.preview_tree.column(
            "#0",
            width=300,
            anchor="w"
        )

        self.preview_tree.column(
            "amount",
            width=120,
            anchor="e"
        )

        self.preview_tree.grid(
            row=0,
            column=0,
            sticky="nsew"
        )
        
    # ---------------------------------------------------------
    # Sample Tree
    # ---------------------------------------------------------

    def _build_sample_tree(self):

        for item in self.preview_tree.get_children():
            self.preview_tree.delete(item)

        revenue = self.preview_tree.insert(
            "",
            "end",
            text="Revenue",
            values=("",),
            tags=("lvl0row",)
        )

        salary = self.preview_tree.insert(
            revenue,
            "end",
            text="Salary",
            values=("",),
            tags=("lvl1row",)
        )

        self.preview_tree.insert(
            salary,
            "end",
            text="Primary Job",
            values=("65000",),
            tags=("lvl2row",)
        )

        self.preview_tree.insert(
            salary,
            "end",
            text="Bonus",
            values=("5000",),
            tags=("lvl2row",)
        )

        self.preview_tree.insert(
            revenue,
            "end",
            text="Revenue Subtotal",
            values=("70000",),
            tags=("SubTotal",)
        )

        expenses = self.preview_tree.insert(
            "",
            "end",
            text="Expenses",
            values=("",),
            tags=("lvl0row",)
        )

        housing = self.preview_tree.insert(
            expenses,
            "end",
            text="Housing",
            values=("",),
            tags=("lvl1row",)
        )

        self.preview_tree.insert(
            housing,
            "end",
            text="Mortgage",
            values=("18000",),
            tags=("lvl2row",)
        )

        self.preview_tree.insert(
            housing,
            "end",
            text="Insurance",
            values=("1200",),
            tags=("lvl2row",)
        )

        self.preview_tree.insert(
            expenses,
            "end",
            text="Expense Subtotal",
            values=("19200",),
            tags=("SubTotal",)
        )

        self.preview_tree.insert(
            "",
            "end",
            text="NET TOTAL",
            values=("50800",),
            tags=("finaltotal",)
        )

        self.preview_tree.item(revenue, open=True)
        self.preview_tree.item(expenses, open=True)
        self.preview_tree.item(salary, open=True)
        self.preview_tree.item(housing, open=True)

    # ---------------------------------------------------------
    # Color Editor
    # ---------------------------------------------------------

    def _populate_color_editor(self):
        row = ctk.CTkFrame(
                self.color_frame, border_width=0
            )
        row.grid(row=0, column=0, sticky="ew", padx=(2, 2))
        
        ctk.CTkLabel(
            row,
            text="Tree Colors", width=120,
            font=("Segoe UI", 18, "bold")
        ).grid(row=0, column=0, sticky="w", padx=10, pady=10)

        ctk.CTkLabel(
            row,
            text="Foreground",
            width=128,
            font=("Segoe UI", 14, "bold")
        ).grid(row=0, column=2, columnspan=2, sticky="w", padx=10, pady=10)
        
        ctk.CTkLabel(
            row,
            text="Background",
            width=128,
            font=("Segoe UI", 14, "bold")
        ).grid(row=0, column=4, columnspan=2, sticky="w", padx=(30,10), pady=10)
        
        for rowno, (name, cfg) in enumerate(
            self.tree_colors.items(),
            start=1):
            
            row = ctk.CTkFrame(
                self.color_frame, border_width=0
            )
            row.grid(row=rowno, column=0, sticky="ew", padx=(2, 2))

            ctk.CTkLabel(
                row,
                text=name,
                width=120
            ).grid(
                row=0,
                column=1,
                sticky="ew",
                padx=(0, 5)
            )

            fg = normalize_color(
                cfg.get(
                    "Foreground",
                    "#000000"
                )
            )

            bg = normalize_color(
                cfg.get(
                    "Background",
                    "#ffffff"
                )
            )

            fg_btn = ctk.CTkButton(
                row,
                text="",
                width=28,
                height=22,
                fg_color=fg,
                command=lambda n=name:
                self.pick_color(
                    n,
                    "Foreground"
                )
            )
            fg_btn.grid(
                row=0,
                column=2,
                sticky="ew",
                padx=(0, 10)
            )
            #sFgBtn = ctk.CTkButton(
            sFgBtn = ctk.CTkLabel(
                row,
                text=fg.replace('#','').upper(),
                width=100,
                fg_color=bg,
                text_color=fg
            )
            sFgBtn.grid(
                row=0,
                column=3,
                sticky="e",
                padx=(10, 10)
            )
            
            bg_btn = ctk.CTkButton(
                row,
                text="",
                width=28,
                height=22,
                fg_color=bg,
                command=lambda n=name:
                self.pick_color(
                    n,
                    "Background"
                )
            )
            bg_btn.grid(
                row=0,
                column=4,
                sticky="e",
                padx=(30, 10)
            )

            #sBgBtn = ctk.CTkButton(
            sBgBtn = ctk.CTkLabel(
                row,
                text=bg.replace('#',''),
                width=100,
                fg_color=bg,
                text_color=fg
            )
            sBgBtn.grid(
                row=0,
                column=5,
                sticky="e",
                padx=(0, 10)
            )

            self.color_controls[name] = {
                "fg": fg_btn,
                "bg": bg_btn,
                "sfg": sFgBtn,
                "sbg": sBgBtn
            }
            #rowno+=1
            
    # ---------------------------------------------------------
    # Width Tree
    # ---------------------------------------------------------
    
    def _build_width_tabs(self):
    
        for table_name, columns in self.trans_widths.items():

            tab = ctk.CTkFrame(
                self.width_notebook
            )

            self.width_notebook.add(
                tab,
                text=table_name
            )

            tree = ttk.Treeview(
                tab,
                columns=(
                    "column",
                    "width",
                    "anchor",
                    "stretch"
                ),
                show="headings"
            )

            tree.heading(
                "column",
                text="Column"
            )

            tree.heading(
                "width",
                text="Width"
            )

            tree.heading(
                "anchor",
                text="Anchor"
            )

            tree.heading(
                "stretch",
                text="Stretch"
            )

            tree.column(
                "column",
                width=180
            )

            tree.column(
                "width",
                width=70,
                anchor="center"
            )

            tree.column(
                "anchor",
                width=70,
                anchor="center"
            )

            tree.column(
                "stretch",
                width=70,
                anchor="center"
            )

            tab.grid_rowconfigure(0, weight=1)
            tab.grid_columnconfigure(0, weight=1)

            tree.grid(
                row=0,
                column=0,
                sticky="nsew"
            )

            tree.tag_configure(
                "evenrow",
                background="#ffffff"
            )

            tree.tag_configure(
                "oddrow",
                background="#eef5ff"
            )

            rownum = 0

            for column_name, values in columns.items():

                tag = (
                    "evenrow"
                    if rownum % 2 == 0
                    else "oddrow"
                )

                tree.insert(
                    "",
                    "end",
                    values=(
                        column_name,
                        values[0],
                        values[1],
                        values[2]
                    ),
                    tags=(tag,)
                )

                rownum += 1

            tree.bind(
                "<Double-1>",
                lambda e,
                       table=table_name,
                       tr=tree:
                       self.edit_width_cell(
                           e,
                           table,
                           tr
                       )
            )

            self.width_trees[
                table_name
            ] = tree


    def edit_width_cell(
        self,
        event,
        table_name,
        tree):

        item = tree.identify_row(event.y)
        column = tree.identify_column(event.x)

        if not item:
            return

        values = list(
            tree.item(item, "values")
        )

        col_index = int(column[1:]) - 1

        #
        # column name not editable
        #
        if col_index == 0:
            return

        bbox = tree.bbox(item, column)

        if not bbox:
            return

        x, y, w, h = bbox

        #
        # remove existing editor
        #
        if hasattr(self, "_active_editor"):
            try:
                self._active_editor.destroy()
            except Exception:
                pass

        editor = tk.Entry(tree)
        self._active_editor = editor

        editor.place(
            x=x,
            y=y,
            width=w,
            height=h
        )

        editor.insert(
            0,
            str(values[col_index])
        )

        editor.select_range(0, "end")
        editor.focus_set()

        def save_edit(event=None):

            if not editor.winfo_exists():
                return

            editor.unbind("<Return>")
            editor.unbind("<KP_Enter>")
            editor.unbind("<FocusOut>")

            new_value = editor.get().strip()

            #
            # Validate width column
            #
            if col_index == 1:

                try:
                    new_value = int(new_value)

                    if new_value < 1:
                        new_value = 1

                except ValueError:

                    messagebox.showerror(
                        "Invalid Width",
                        "Width must be an integer.",
                        parent=self
                    )

                    editor.focus_set()
                    return

            #
            # Validate anchor column
            #
            elif col_index == 2:

                new_value = new_value.lower()

                anchor_map = {
                    "w": "w",
                    "left": "w",
                    "e": "e",
                    "right": "e",
                    "center": "center",
                    "c": "center"
                }

                if new_value not in anchor_map:

                    messagebox.showerror(
                        "Invalid Anchor",
                        "Anchor must be w, e, or center.",
                        parent=self
                    )

                    editor.focus_set()
                    return

            #
            # Validate stretch column
            #
            elif col_index == 3:

                txt = new_value.lower()

                if txt in (
                    "true",
                    "1",
                    "yes",
                    "y"
                ):
                    new_value = True

                elif txt in (
                    "false",
                    "0",
                    "no",
                    "n"
                ):
                    new_value = False

                else:

                    messagebox.showerror(
                        "Invalid Stretch",
                        "Stretch must be True or False.",
                        parent=self
                    )

                    editor.focus_set()
                    return

            values[col_index] = new_value

            #
            # update tree row
            #
            tree.item(
                item,
                values=values
            )

            column_name = values[0]

            self.trans_widths[table_name][column_name] = [
                int(values[1]),
                str(values[2]),
                bool(values[3])
            ]
            
            fin_config.update_finance_settings(
                trans_widths=self.trans_widths
            )

            fin_config._flush_save()
            
            editor.destroy()

            self.schedule_preview_refresh()

        def cancel_edit(event=None):

            try:
                editor.destroy()
            except Exception:
                pass

        editor.bind("<Return>", save_edit)
        editor.bind("<KP_Enter>", save_edit)
        editor.bind("<FocusOut>", save_edit)
        editor.bind("<Escape>", cancel_edit)
    
    def _populate_width_tree(self):

        ctk.CTkLabel(
            self.width_frame,
            text="Column Widths",
            font=("Segoe UI", 18, "bold")
        ).grid(
            row=0,
            column=0,
            sticky="w",
            padx=10,
            pady=10
        )

        self.width_notebook = ttk.Notebook(
            self.width_frame
        )

        self.width_notebook.grid(
            row=1,
            column=0,
            sticky="nsew"
        )

        self.width_trees = {}

        self._build_width_tabs()
        
    def edit_width_tree_row(self, event):
    
        item = self.width_tree.identify_row(event.y)

        column = self.width_tree.identify_column(event.x)

        if not item:
            return

        col_index = int(
            column.replace("#", "")
        ) - 1

        if col_index < 2:
            return

        values = list(
            self.width_tree.item(
                item,
                "values"
            )
        )

        x, y, w, h = self.width_tree.bbox(
            item,
            column
        )

        editor = tk.Entry(
            self.width_tree
        )

        editor.place(
            x=x,
            y=y,
            width=w,
            height=h
        )

        editor.insert(
            0,
            values[col_index]
        )

        editor.focus_set()
        
    # ---------------------------------------------------------
    # Color Picker
    # ---------------------------------------------------------

    def pick_color(
        self,
        row_name,
        field
        ):

        current = normalize_color(
            self.tree_colors[row_name][field]
        )

        rgb, new_color = cc.askcolor(
            initialcolor=current,
            parent=self
        )

        if not new_color:
            return

        self.tree_colors[row_name][field] = new_color
        fg = normalize_color(self.tree_colors[row_name]["Foreground"])
        bg = normalize_color(self.tree_colors[row_name]["Background"])
        sfg = normalize_color(self.tree_colors[row_name]["Foreground"])
        sbg = normalize_color(self.tree_colors[row_name]["Background"])
        ctl = self.color_controls[row_name]
        ctl["fg"].configure(fg_color=fg)
        ctl["bg"].configure(fg_color=bg)
        ctl["sfg"].configure(
            text=fg.replace("#", "").upper(),
            fg_color=bg,
            text_color=fg
        )

        ctl["sbg"].configure(
            text=bg.replace("#", "").upper(),
            fg_color=bg,
            text_color=fg
        )

        fin_config.update_finance_settings(
            tree_colors=self.tree_colors,
            trans_widths=self.trans_widths
        )

        fin_config._flush_save()

        self.schedule_preview_refresh()

    # ---------------------------------------------------------
    # Debounced Refresh
    # ---------------------------------------------------------

    def schedule_preview_refresh(self):
        #print('spr refresh',self._refresh_after)
        if self._refresh_after:

            self.after_cancel(
                self._refresh_after
            )

        self._refresh_after = self.after(
            100,
            self._refresh_preview
        )

    # ---------------------------------------------------------
    # Preview Refresh
    # ---------------------------------------------------------

    def _refresh_preview(self):
        #print('refresh_preview')
        for tag_name, cfg in self.tree_colors.items():

            fg = normalize_color(
                cfg.get(
                    "Foreground",
                    "#000000"
                )
            )

            bg = normalize_color(
                cfg.get(
                    "Background",
                    "#ffffff"
                )
            )

            font_cfg = cfg.get(
                "font",
                ("Calibri", 11)
            )

            try:

                self.preview_tree.tag_configure(
                    tag_name,
                    foreground=fg,
                    background=bg,
                    font=tuple(font_cfg)
                )

            except Exception:

                self.preview_tree.tag_configure(
                    tag_name,
                    foreground=fg,
                    background=bg
                )

        desc = (
            self.trans_widths
            .get("transactions", {})
            .get("Description")
        )

        if desc:

            try:
                width = int(desc[0])
            except Exception:
                width = 12

            self.preview_tree.column(
                "#0",
                width=max(
                    180,
                    width * 10
                )
            )

    # ---------------------------------------------------------
    # Save / Reload
    # ---------------------------------------------------------

    def save_config(self):

        fin_config.update_finance_settings(
            tree_colors=self.tree_colors,
            trans_widths=self.trans_widths
        )

        fin_config._flush_save()

        messagebox.showinfo(
            "Saved",
            "Configuration saved.",
            parent=self
        )

    def reload_config(self):

        self.destroy()

        ConfigEditor(
            self.master
        )

# ---------------------------------------------------------
# Main
# ---------------------------------------------------------

def main():

    import sys

    ctk.set_appearance_mode("System")
    ctk.set_default_color_theme("blue")
    
    ctk.set_widget_scaling(1.0)
    ctk.set_window_scaling(1.0)
    
    app = ConfigEditor()

    def close_all():

        app.destroy()

        sys.exit()

    app.protocol(
        "WM_DELETE_WINDOW",
        close_all
    )
    #app.geometry("850x700+100+25")
    app.mainloop()


if __name__ == "__main__":
    main()