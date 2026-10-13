
# catlist.py — FULL CustomTkinter rewrite
import customtkinter as ctk
from tkinter import END
import traceback
from logging_manager import get_logger

log = get_logger(__name__)

# DPI safety
ctk.set_widget_scaling(1.0)
ctk.set_window_scaling(1.0)
ctk.deactivate_automatic_dpi_awareness()

class CategoryEditorDialog(ctk.CTkToplevel):
    """
    Fully CustomTkinter category/subcategory editor.
    Categories on the left, subcategories on the right.
    Right side has stacked management buttons.
    Save & Close + Cancel at bottom.
    """

    def __init__(self, parent, categories_dict, on_submit_callback):
        super().__init__(parent)

        self.parent = parent
        self.categories_dict = categories_dict or {}
        self.on_submit_callback = on_submit_callback

        self.title("Category / Subcategory Editor")
        self.geometry("760x480")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()
        self.focus_force()

        # --- MAIN LAYOUT ---
        main = ctk.CTkFrame(self)
        main.pack(fill="both", expand=True, padx=10, pady=10)

        # Grid layout: 3 columns
        # 0 = categories
        # 1 = subcategories
        # 2 = stacked buttons
        main.grid_columnconfigure(0, weight=1)
        main.grid_columnconfigure(1, weight=1)
        main.grid_columnconfigure(2, weight=0)
        main.grid_rowconfigure(1, weight=1)

        # -----------------------------
        # CATEGORY COLUMN (LEFT)
        # -----------------------------
        ctk.CTkLabel(main, text="Categories").grid(row=0, column=0, sticky="w")

        self.cat_listbox = ctk.CTkTextbox(main, height=300)
        self.cat_listbox.grid(row=1, column=0, sticky="nsew", padx=(0, 10))
        self.cat_listbox.configure(state="normal")

        for cat in sorted(self.categories_dict.keys()):
            self.cat_listbox.insert(END, cat + "\n")

        self.cat_listbox.configure(state="disabled")

        # Selected category entry
        ctk.CTkLabel(main, text="Selected Category").grid(row=2, column=0, sticky="w", pady=(10, 2))
        self.selected_cat_var = ctk.StringVar()
        self.selected_cat_entry = ctk.CTkEntry(main, textvariable=self.selected_cat_var)
        self.selected_cat_entry.grid(row=3, column=0, sticky="ew", pady=(0, 10))

        # -----------------------------
        # SUBCATEGORY COLUMN (CENTER)
        # -----------------------------
        ctk.CTkLabel(main, text="Subcategories").grid(row=0, column=1, sticky="w")

        self.subcat_listbox = ctk.CTkTextbox(main, height=300)
        self.subcat_listbox.grid(row=1, column=1, sticky="nsew", padx=(10, 10))
        self.subcat_listbox.configure(state="disabled")

        # Selected subcategory entry
        ctk.CTkLabel(main, text="Selected Subcategory").grid(row=2, column=1, sticky="w", pady=(10, 2))
        self.selected_subcat_var = ctk.StringVar()
        self.selected_subcat_entry = ctk.CTkEntry(main, textvariable=self.selected_subcat_var)
        self.selected_subcat_entry.grid(row=3, column=1, sticky="ew", pady=(0, 10))

        # -----------------------------
        # BUTTON STACK (RIGHT)
        # -----------------------------
        btn_stack = ctk.CTkFrame(main)
        btn_stack.grid(row=1, column=2, sticky="ns", padx=(10, 0))

        # Stack buttons vertically
        ctk.CTkButton(btn_stack, text="Add Category", width=140, command=self._add_category).pack(pady=5)
        ctk.CTkButton(btn_stack, text="Add Subcategory", width=140, command=self._add_subcategory).pack(pady=5)
        ctk.CTkButton(btn_stack, text="Rename Selected", width=140, command=self._rename_selected).pack(pady=5)
        ctk.CTkButton(btn_stack, text="Delete Selected", width=140, command=self._delete_selected).pack(pady=5)

        # -----------------------------
        # BOTTOM BUTTONS
        # -----------------------------
        bottom = ctk.CTkFrame(main)
        bottom.grid(row=4, column=0, columnspan=3, pady=(15, 0))

        ctk.CTkButton(bottom, text="Save & Close", command=self._save_and_close).pack(side="left", padx=10)
        ctk.CTkButton(bottom, text="Cancel", command=self._cancel).pack(side="left", padx=10)

        # -----------------------------
        # EVENT BINDINGS
        # -----------------------------
        self.cat_listbox.bind("<ButtonRelease-1>", self._on_cat_click)
        self.subcat_listbox.bind("<ButtonRelease-1>", self._on_subcat_click)

    # -----------------------------
    # CATEGORY HANDLERS
    # -----------------------------

    def _add_category(self):
        new_cat = self.selected_cat_var.get().strip()
        if not new_cat:
            return
        if new_cat not in self.categories_dict:
            self.categories_dict[new_cat] = []
            self._refresh_categories()

    def _rename_selected(self):
        # Rename category if category is selected
        cat = self.selected_cat_var.get().strip()
        if cat in self.categories_dict:
            new = self.selected_cat_var.get().strip()
            if new and new != cat:
                self.categories_dict[new] = self.categories_dict.pop(cat)
                self._refresh_categories()
                return

        # Rename subcategory if subcategory is selected
        cat = self.selected_cat_var.get().strip()
        sub = self.selected_subcat_var.get().strip()
        if cat in self.categories_dict and sub in self.categories_dict[cat]:
            new = self.selected_subcat_var.get().strip()
            if new and new != sub:
                lst = self.categories_dict[cat]
                lst[lst.index(sub)] = new
                self._refresh_subcategories(lst)

    def _delete_selected(self):
        # Delete category
        cat = self.selected_cat_var.get().strip()
        if cat in self.categories_dict:
            del self.categories_dict[cat]
            self.selected_cat_var.set("")
            self.selected_subcat_var.set("")
            self._refresh_categories()
            self._refresh_subcategories([])
            return

        # Delete subcategory
        sub = self.selected_subcat_var.get().strip()
        if cat in self.categories_dict and sub in self.categories_dict[cat]:
            self.categories_dict[cat].remove(sub)
            self.selected_subcat_var.set("")
            self._refresh_subcategories(self.categories_dict[cat])

    def _add_subcategory(self):
        cat = self.selected_cat_var.get().strip()
        if not cat or cat not in self.categories_dict:
            return
        new_sub = self.selected_subcat_var.get().strip()
        if new_sub and new_sub not in self.categories_dict[cat]:
            self.categories_dict[cat].append(new_sub)
            self._refresh_subcategories(self.categories_dict[cat])

    # -----------------------------
    # UI REFRESH HELPERS
    # -----------------------------

    def _refresh_categories(self):
        self.cat_listbox.configure(state="normal")
        self.cat_listbox.delete("1.0", END)
        for cat in sorted(self.categories_dict.keys()):
            self.cat_listbox.insert(END, cat + "\n")
        self.cat_listbox.configure(state="disabled")

    def _refresh_subcategories(self, subcats):
        self.subcat_listbox.configure(state="normal")
        self.subcat_listbox.delete("1.0", END)
        for s in sorted(subcats):
            self.subcat_listbox.insert(END, s + "\n")
        self.subcat_listbox.configure(state="disabled")

    # -----------------------------
    # EVENT HANDLERS
    # -----------------------------

    def _on_cat_click(self, event):
        index = self.cat_listbox.index(f"@{event.x},{event.y}")
        line = self.cat_listbox.get(f"{index} linestart", f"{index} lineend").strip()
        if line:
            self.selected_cat_var.set(line)
            self._refresh_subcategories(self.categories_dict.get(line, []))

    def _on_subcat_click(self, event):
        index = self.subcat_listbox.index(f"@{event.x},{event.y}")
        line = self.subcat_listbox.get(f"{index} linestart", f"{index} lineend").strip()
        if line:
            self.selected_subcat_var.set(line)

    # -----------------------------
    # CLOSE / SAVE
    # -----------------------------

    def _save_and_close(self):
        cat = self.selected_cat_var.get().strip()
        subcat = self.selected_subcat_var.get().strip()

        if self.on_submit_callback:
            self.on_submit_callback(self.categories_dict, cat, subcat)

        self.destroy()

    def _cancel(self):
        self.destroy()
