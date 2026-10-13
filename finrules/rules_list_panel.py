# rules_list_panel.py

import customtkinter as ctk
from tkinter import ttk, messagebox
import apswSql as sql
from logging_manager import get_logger
from treeutils import sortby_column
from theme_manager import theme_manager

log = get_logger(__name__)


class RulesListPanel:
    def __init__(self, app, parent):
        self.app = app
        self.parent = parent

        left = ctk.CTkFrame(parent)
        left.pack(side="left", fill="both", expand=True, padx=(10, 5), pady=10)

        right = ctk.CTkFrame(parent)
        right.pack(side="right", fill="y", padx=(5, 10), pady=10)
        self.right_frame = right

        rules_frame = ctk.CTkFrame(left, corner_radius=12, fg_color="yellow")
        rules_frame.pack(fill="both", expand=True)

        rules_columns = ("rule_id", "account", "pattern", "alias", "category", "subcategory", "import_file_key")

        self.rules_tree = ttk.Treeview(
            rules_frame,
            columns=rules_columns,
            show="headings",
            height=25
        )

        for col, text, width in [
                ("rule_id", "rule_id", 50),
                ("account", "Account", 130),
                ("pattern", "Pattern", 260),
                ("alias", "Alias", 140),
                ("category", "Category", 140),
                ("subcategory", "Subcategory", 160),
            ]:
            self.rules_tree.heading(col, text=text, command=lambda c=col: sortby_column(self.rules_tree, c, 1))
            anchor = 'w'
            if text == 'rule_id':
                anchor = 'e'
            self.rules_tree.column(col, width=width, anchor=anchor)

        self.rules_tree.column("import_file_key", width=0, stretch=False)
        self.rules_tree.heading("import_file_key", text="")

        vsb = ttk.Scrollbar(rules_frame, orient="vertical", command=self.rules_tree.yview)
        hsb = ttk.Scrollbar(rules_frame, orient="horizontal", command=self.rules_tree.xview)

        self.rules_tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        self.rules_tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")

        rules_frame.grid_rowconfigure(0, weight=1)
        rules_frame.grid_columnconfigure(0, weight=1)

        self.rules_tree.bind("<ButtonRelease-1>", self._on_rules_list_click)

        theme_manager.enable_treeview_hover(self.rules_tree)
        self.rules_tree.configure(style="CTk.Treeview")

        self.editor_panel = None

    def attach_editor(self, editor_panel):
        self.editor_panel = editor_panel

    def refresh_rules_list(self):
        try:
            for row in self.rules_tree.get_children():
                self.rules_tree.delete(row)
            
            for idx, rule in enumerate(self.app.current_ruleset.rules):
                #accounts = ", ".join(rule.get("account", ["*"]))
                 
                tid = self.rules_tree.insert(
                    "",
                    "end",
                    iid=str(idx),
                    values=(
                        rule["rule_id"],
                        rule["account"],
                        rule["pattern"],
                        rule.get("alias", ""),
                        rule.get("category", ""),
                        rule.get("subcategory", ""),
                        rule.get("import_file_key", ""),
                    )
                )
                #print('rrl', tid, idx, rule)
        except Exception as e:
            #print("DEBUG rule type:", type(rule))
            #print("DEBUG rule value:", rule)
            log.error(f'error rule={rule}')
            log.error(e)
            messagebox.showerror("refresh_rules_list Error", f"{e}", parent=self)

    def _on_rules_list_click(self, event):
        try:
            item_id = self.rules_tree.identify_row(event.y)
            region = self.rules_tree.identify("region", event.x, event.y)
            if region == "heading" or not item_id:
                return

            keys = self.rules_tree["columns"]
            row = self.rules_tree.item(item_id, 'values')
            dict_row = dict(zip(keys, row))

            if self.editor_panel:
                self.editor_panel.load_from_dict(dict_row)

        except Exception as e:
            log.error(e)
            messagebox.showerror("_on_rules_list_click", f"{e}", parent=self)

    def edit_rule(self):
        try:
            selected = self.rules_tree.selection()
            if not selected:
                messagebox.showwarning("Edit Rule", "No rule selected.", parent=self.parent)
                return

            idx = int(selected[0])
            rule = self.app.current_ruleset.rules[idx]
            print('rule_list..', rule)
            p = self.editor_panel
            p.account_var.set(rule.get("account", ""))
            p.pattern_var.set(rule.get("pattern", ""))
            p.alias_var.set(rule.get("alias", ""))
            p.category_var.set(rule.get("category", ""))
            p.subcategory_var.set(rule.get("subcategory", ""))
            p.import_file_key_var.set(rule.get("import_file_key", ""))

            if hasattr(p, "accounts_dropdown"):
                p.accounts_dropdown.set(p.account_var.get())

            messagebox.showinfo("Edit Rule", "Rule loaded for editing.", parent=self.parent)

        except Exception as e:
            log.error(e)
            messagebox.showerror("Edit Rule Error", f"{e}", parent=self.parent)

    # NEW: unified add_rule_from_panel
    def add_rule_from_panel(self, panel):
        try:
            account_raw = panel.accounts_dropdown.get().strip()
            try:
                account = sql.get_account_name(account_raw) or account_raw
            except Exception:
                account = account_raw

            pattern = panel.pattern_var.get().strip()
            log.info(f'pattern {pattern}')
            if not pattern:
                raise ValueError("Pattern is required (RulesConsoleApp.add_rule)")

            alias = panel.alias_var.get().strip()
            category = panel.category_var.get().strip()
            subcategory = panel.subcategory_var.get().strip()
            import_key = panel.import_file_key_var.get().strip() or None

            log.info(f"ADD RULE: account={account} | {pattern} | {alias} | {category} | {subcategory}")

            self.app.current_ruleset.add_rule(
                account=account,
                pattern=pattern,
                alias=alias,
                category=category,
                subcategory=subcategory,
                import_file_key=import_key
            )

            self.refresh_rules_list()
            self.app.save_account()

            if hasattr(self.app, "batch_panel"):
                self.app.batch_panel.update_batch_row_after_rule_add()

            panel.account_var.set("*")
            panel.accounts_dropdown.set("*")
            panel.pattern_var.set("")
            panel.alias_var.set("")
            panel.category_var.set("")
            panel.subcategory_var.set("")
            panel.import_file_key_var.set("")

        except Exception as e:
            log.error(e)
            messagebox.showerror("Add Rule Error", f"{e}", parent=self.parent)

    def auto_save_from_panel(self):
        selected = self.rules_tree.selection()

        if not selected:
            return

        idx = int(selected[0])

        rule = self.app.current_ruleset.rules[idx]

        rule["account"] = self.editor_panel.accounts_dropdown.get().strip()
        rule["pattern"] = self.editor_panel.pattern_var.get().strip()
        rule["alias"] = self.editor_panel.alias_var.get().strip()
        rule["category"] = self.editor_panel.category_var.get().strip()
        rule["subcategory"] = self.editor_panel.subcategory_var.get().strip()

        self.refresh_rules_list()
        self.app.save_account()

    def delete_selected_rule(self):
        try:
            selected = self.rules_tree.selection()
            log.info(f"DELETE RULE selected={selected}")
            if not selected:
                raise ValueError("No rule selected.")

            log.info(self.rules_tree.item(selected))
            keys = self.rules_tree["columns"]
            row = self.rules_tree.item(selected)
            dict_row = dict(zip(keys, row['values']))

            self.app.current_ruleset.delete_rule(str(dict_row['rule_id']))
             
        except Exception as e:
            log.error(e)
            messagebox.showerror("Delete Rule Error", f"{e}", parent=self.parent)
    