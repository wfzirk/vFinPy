
# pattern_matches_panel.py

import customtkinter as ctk
from tkinter import ttk
import fnmatch
#from rules.helpers import log.error


class PatternMatchesPanel:
    def __init__(self, app, parent):
        self.app = app
        self.parent = parent

        frame = ctk.CTkFrame(parent)
        frame.pack(fill="both", expand=True, padx=10, pady=10)

        top = ctk.CTkFrame(frame)
        top.pack(fill="x", pady=(0, 10))

        ctk.CTkLabel(top, text="Pattern:").pack(side="left", padx=(0, 5))
        self.match_pattern_var = ctk.StringVar()
        self.match_pattern_entry = ctk.CTkEntry(top, textvariable=self.match_pattern_var, width=400)
        self.match_pattern_entry.pack(side="left", padx=(0, 10))

        ctk.CTkButton(
            top,
            text="Show Matches",
            command=self._run_pattern_match_search
        ).pack(side="left")

        table_frame = ctk.CTkFrame(
            frame,
            corner_radius=12,
            fg_color="#111111"
        )
        table_frame.pack(fill="both", expand=True, pady=(10, 0))

        self.matches_tree = ttk.Treeview(
            table_frame,
            columns=("date", "account", "amount", "description"),
            show="headings",
            height=25
        )

        self.matches_tree.heading("date", text="Date")
        self.matches_tree.heading("account", text="Account")
        self.matches_tree.heading("amount", text="Amount")
        self.matches_tree.heading("description", text="Description")

        self.matches_tree.column("date", width=100)
        self.matches_tree.column("account", width=120)
        self.matches_tree.column("amount", width=80, anchor="e")
        self.matches_tree.column("description", width=600)

        self.matches_tree.pack(fill="both", expand=True)

    def _run_pattern_match_search(self):
        try:
            pattern = self.match_pattern_var.get().strip()

            for row in self.matches_tree.get_children():
                self.matches_tree.delete(row)

            if not pattern:
                return

            tx_list = self.app.batch_transactions or []

            for tx in tx_list:
                desc = tx.get("description", "")
                matched = fnmatch.fnmatch(desc.upper(), pattern.upper())

                if matched:
                    row_tag = "EvenRow" if len(self.matches_tree.get_children()) % 2 == 0 else "OddRow"
                    self.matches_tree.insert(
                        "",
                        "end",
                        values=(tx.get("date", ""), tx.get("account", ""), tx.get("amount", ""), desc),
                        tags=(row_tag,)
                    )
        except Exception as e:
            log.error(e)
            messagebox.showerror("_run_pattern_match_search Error", f"{e}", parent=self)
