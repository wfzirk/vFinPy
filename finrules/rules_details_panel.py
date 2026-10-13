# rules_details_panel.py

import customtkinter as ctk
from tkinter import messagebox
import apswSql as sql
from logging_manager import get_logger

log = get_logger(__name__)

class RuleDetailsPanel(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master)

        self.parent_app = None

        self.account_var = ctk.StringVar()
        self.pattern_var = ctk.StringVar()
        self.alias_var = ctk.StringVar()
        self.category_var = ctk.StringVar()
        self.subcategory_var = ctk.StringVar()
        self.import_file_key_var = ctk.StringVar()
        self.batch_dates_var = ctk.StringVar()

        ctk.CTkLabel(self, text="Account (comma-separated, * = all)").pack(anchor="w", pady=(0, 2))
        self.accounts_dropdown = ctk.CTkComboBox(
            self,
            variable=self.account_var,
            width=250,
            values=["*"],
            state="readonly"
        )
        self.accounts_dropdown.pack(anchor="w", pady=(0, 8))

        ctk.CTkLabel(self, text="Pattern").pack(anchor="w", pady=(0, 2))
        self.pattern_entry = ctk.CTkEntry(self, textvariable=self.pattern_var, width=250)
        self.pattern_entry.pack(anchor="w", pady=(0, 8))

        ctk.CTkLabel(self, text="Alias").pack(anchor="w", pady=(0, 2))
        self.alias_entry = ctk.CTkEntry(self, textvariable=self.alias_var, width=250)
        self.alias_entry.pack(anchor="w", pady=(0, 8))

        ctk.CTkLabel(self, text="Category").pack(anchor="w", pady=(0, 2))
        self.category_entry = ctk.CTkEntry(self, textvariable=self.category_var, width=250)
        self.category_entry.pack(anchor="w", pady=(0, 8))

        ctk.CTkLabel(self, text="Subcategory").pack(anchor="w", pady=(0, 2))
        self.subcategory_entry = ctk.CTkEntry(self, textvariable=self.subcategory_var, width=250)
        self.subcategory_entry.pack(anchor="w", pady=(0, 8))

        ctk.CTkLabel(self, text="Import File Key (optional)").pack(anchor="w", pady=(0, 2))
        self.import_file_key_entry = ctk.CTkEntry(self, textvariable=self.import_file_key_var, width=250)
        self.import_file_key_entry.pack(anchor="w", pady=(0, 8))

        btn_frame = ctk.CTkFrame(self)
        btn_frame.pack(anchor="w", pady=(10, 0))

        self.btn_add_rule = ctk.CTkButton(
            btn_frame,
            text="Add Rule",
            width=120,
            command=self._on_add_rule
        )
        self.btn_add_rule.pack(side="left", padx=(0, 10))

        self.btn_delete_rule = ctk.CTkButton(
            btn_frame,
            text="Delete Rule",
            width=120,
            command=self._on_delete_rule
        )
        self.btn_delete_rule.pack(side="left")

    def bind_dialogs(self, parent_app):
        self.parent_app = parent_app
        self.category_entry.bind("<Button-1>", self.update_cat)
        self.subcategory_entry.bind("<Button-1>", self.update_scat)

    def update_cat(self, event):
        try:
            app = self.parent_app
            app.categories = {}

            try:
                app._suppress_batch_click = True
            except Exception:
                pass

            categories, _, _ = sql.getColumnDistinct('Category')
            for cat in categories:
                if cat:
                    scat_list, _, _ = sql.getSubCatDistinct(cat)
                    app.categories[cat] = scat_list

            dlg = CategoryEditorDialog(
                app,
                app.categories,
                self._on_categories_updated
            )
            dlg.protocol("WM_DELETE_WINDOW", app._on_cat_dialog_close)
            app.cat_dialog_window = dlg

        except Exception as e:
            log.error(e)

    def update_scat(self, event):
        try:
            app = self.parent_app
            app.categories = {}

            try:
                app._suppress_batch_click = True
            except Exception:
                pass

            categories, _, _ = sql.getColumnDistinct('Category')
            for cat in categories:
                scat_list, _, _ = sql.getSubCatDistinct(cat)
                app.categories[cat] = scat_list

            dlg = CategoryEditorDialog(
                app,
                app.categories,
                self._on_categories_updated
            )
            dlg.protocol("WM_DELETE_WINDOW", app._on_scat_dialog_close)
            app.scat_dialog_window = dlg

        except Exception as e:
            log.error(e)

    def _on_categories_updated(self, new_data, cat, subcat):
        app = self.parent_app
        app.categories = new_data

        self.category_var.set(cat)
        self.subcategory_var.set(subcat)

        if self.pattern_var.get().strip():
            app._auto_save_rule_from_active_panel()

        app._suppress_batch_click = True
        app.cat_dialog_window = None
        app.scat_dialog_window = None

        app.after(300, lambda: setattr(app, "_suppress_batch_click", False))
    '''
    def load_from_dict(self, d):
        self.account_var.set(d.get("account", ""))
        self.accounts_dropdown.set(d.get("account", ""))
        self.pattern_var.set(d.get("pattern", ""))
        self.alias_var.set(d.get("alias", ""))
        self.category_var.set(d.get("category", ""))
        self.subcategory_var.set(d.get("subcategory", ""))
        self.import_file_key_var.set(d.get("import_file_key", ""))
    '''
    def _on_add_rule(self):
        if self.parent_app:
            self.parent_app.add_rule()

    def _on_delete_rule(self):
        log.info('on_delete_rule')
        selected = self.rules_tree.selection()
        log.info(f"DELETE RULE selected={selected}")
        
        if self.parent_app:
            self.parent_app.delete_selected_rule()
