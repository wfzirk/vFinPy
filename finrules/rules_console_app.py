# rules_console_app.py

# Python Includes
import sys, os
import json
#import fnmatch
from pathlib import Path
from tkinter import ttk, messagebox, filedialog
from time import perf_counter

# 3rd party includes
import customtkinter as ctk

# Project Includes
parentdir = os.path.dirname(__file__)
sys.path.append(os.path.join(parentdir, '..'))

import apswSql as sql
from logging_manager import get_logger
from status_bus import StatusBus
from finrules.rules.rule_manager import RuleManager
from finrules.rules_editor_panel import RuleDetailsPanel
from finrules.rules_list_panel import RulesListPanel
from finrules.pattern_matches_panel import PatternMatchesPanel
from finrules.batch_panel import BatchPanel
from finrules.qfx_view_panel import QFXViewPanel
#from finrules.account_info_panel import AccountInfoPanel
#from finrules.dialogs import AccountPrompt
from finrules.rules.helpers import colorscale, normalize_description
from theme_manager import theme_manager

log = get_logger(__name__)
print('rules_console', __name__)

class RulesConsoleApp(ctk.CTkToplevel):
    def __init__(self, rules_dir="rules"):
        super().__init__()
        self.title("Rules Console")
        self.geometry("1200x750+100+30")
        self.after(100, self.lift)

        # RULE ENGINE 
        self.rule_manager = RuleManager()
        self.current_account_id = ctk.StringVar(value="default_account")
        self.current_account_name = ctk.StringVar(value="Account")
        self.current_ruleset = self.rule_manager.load()
        self.after(10, self.refresh_rules_list)

        # STATE
        self._suppress_batch_click = False
        self.batch_transactions = []
        #self.batch_row_map = {}
        self.qfx_account_info = {}
        self.import_file_key = None

        self.cat_dialog_window = None
        self.scat_dialog_window = None
        self.categories = {}

        # UI
        self._build_layout()
        self._populate_account_dropdowns()
        StatusBus.clear_perf()

    def _build_layout(self):

        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        top_frame = ctk.CTkFrame(self)
        top_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=10)

        top_frame.grid_columnconfigure(4, weight=1)

        ctk.CTkLabel(
            top_frame,
            text="Account ID:",
            width=80
        ).grid(
            row=0,
            column=0,
            padx=(0, 5),
            pady=5,
            sticky="w"
        )

        self.account_entry = ctk.CTkEntry(
            top_frame,
            textvariable=self.current_account_id,
            width=200
        )

        self.account_entry.grid(
            row=0,
            column=1,
            padx=5,
            pady=5,
            sticky="w"
        )

        self.account_name_entry = ctk.CTkEntry(
            top_frame,
            textvariable=self.current_account_name,
            width=200
        )

        self.account_name_entry.grid(
            row=0,
            column=2,
            padx=5,
            pady=5,
            sticky="w"
        )

        ctk.CTkButton(
            top_frame,
            text="Load Rules",
            command=self.load_account
        ).grid(
            row=0,
            column=3,
            padx=5,
            pady=5,
            sticky="w"
        )

        # TABS
        self.tabview = ctk.CTkTabview(self)

        self.tabview.grid(
            row=1,
            column=0,
            sticky="nsew",
            padx=10,
            pady=(0, 10)
        )

        self.tab_rules = self.tabview.add("Rules Editor")
        self.tab_matches = self.tabview.add("Pattern Matches")
        self.tab_batch = self.tabview.add("Batch Classifier")
        self.tab_qfx = self.tabview.add("QFX Viewer")
        
        # RULES TAB
        self.rules_list_panel = RulesListPanel(self, self.tab_rules)

        self.rules_editor_panel = RuleDetailsPanel(self.rules_list_panel.right_frame)
        self.rules_editor_panel.pack(fill="y", anchor="n")
        self.rules_editor_panel.parent_app = self
        self.rules_editor_panel.bind_dialogs(self)

        self.rules_list_panel.attach_editor(self.rules_editor_panel)

        # PATTERN MATCHES TAB
        self.pattern_panel = PatternMatchesPanel(self, self.tab_matches)
       
        # BATCH TAB
        self.tab_batch.grid_rowconfigure(0, weight=0)  # account panel
        self.tab_batch.grid_rowconfigure(1, weight=1)  # batch panel
        self.tab_batch.grid_columnconfigure(0, weight=1)

        #self.account_info_panel = AccountInfoPanel(
        #    self,
        #    self.tab_batch
        #)
       
        self.batch_panel = BatchPanel(
            self,
            self.tab_batch,
            #self.account_info_panel
        )

        self.batch_panel.frame.grid(
            row=1,
            column=0,
            sticky="nsew",
            padx=10,
            pady=(5, 10)
        )
         
        # QFX VIEW TAB
        self.qfx_view_panel = QFXViewPanel(self, self.tab_qfx)

    def _populate_account_dropdowns(self):
        try:
            names = []
            data, _, _ = sql.accounts()
            for row in data:
                nm = row.get("OrganizationName")
                if nm:
                    names.append(nm)

            names = sorted(set(names))

            self.rules_editor_panel.accounts_dropdown.configure(values=["*"] + names)

            if hasattr(self.batch_panel, "batch_right_panel"):
                self.batch_panel.batch_right_panel.accounts_dropdown.configure(values=["*"] + names)

        except Exception as e:
            log.error(e)

    def load_account(self):
        try:
            account_id = self.current_account_id.get().strip()
            log.info(f'load context account {account_id}')
            if not account_id:
                messagebox.showwarning("Account", "Account ID cannot be empty.", parent=self)
                return

            self.current_ruleset = self.rule_manager.load()
            self.refresh_rules_list()

        except Exception as e:
            log.error(e)
            messagebox.showerror("Account Load Error", f"{e}", parent=self)

    def save_account(self):
        try:
            account_id = self.current_account_id.get().strip()
            log.info(f'save rules (context account {account_id})')
            if not account_id:
                messagebox.showwarning("Account", "Account ID cannot be empty.", parent=self)
                return

            self.rule_manager.save(self.current_ruleset)
            messagebox.showinfo("Saved", f"Rules saved (context account '{account_id}').", parent=self)

        except Exception as e:
            log.error(e)
            messagebox.showerror("Account Save Error", f"{e}", parent=self)

    def refresh_rules_list(self):
        log.info("refresh_rules_list")
        self.rules_list_panel.refresh_rules_list()

    def get_active_editor_panel(self):
        tab = self.tabview.get()
        log.info(f'get_active_editor_panel {tab}')

        if tab == "Rules Editor":
            return self.rules_editor_panel

        if tab == "Batch Classifier":
            return self.batch_panel.batch_right_panel

        return self.rules_editor_panel

    def _auto_save_rule_from_active_panel(self):
        print('*******autosave dir',dir(self.rules_list_panel))
        self.rules_list_panel.auto_save_from_panel()

    # FIXED: unified add_rule
    def add_rule(self):
        log.info("add_rule")
        panel = self.get_active_editor_panel()
        self.rules_list_panel.add_rule_from_panel(panel)

    def delete_selected_rule(self):
        log.info("delete_selected_rule")
        self.rules_list_panel.delete_selected_rule()
        #self.current_ruleset = self.rule_manager.load()
        #self.refresh_rules_list()
        self.load_account()
        

def auto_load_qfx_from_cli():
    import sys
    for arg in sys.argv[1:]:
        if arg.lower().endswith(".qfx"):
            return arg
    return None

def auto_load_qfx_default():
    path = CONFIG.get("last_qfx")
    if path and os.path.exists(path):
        return path
    return None

def auto_load_qfx():
    path = auto_load_qfx_from_cli()
    if path:
        return path
    return None

def main():
    qfx_path = auto_load_qfx()
    app = RulesConsoleApp()

    def close_all():
        app.destroy()
        sys.exit()

    app.protocol("WM_DELETE_WINDOW", close_all)

    if qfx_path:
        #app.qfx_view_panel.load_qfx(qfx_path)
        #app.tabview.set("QFX Viewer")
        
        app.batch_panel.load_batch_file(qfx_path)
        app.tabview.set("Batch Classifier")
        

    app.mainloop()
    return

if __name__ == "__main__":
    main()
