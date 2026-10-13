# finrules/qfx_view_panel.py
# finrules/qfx_view_panel.py

# Python Includes
import csv
import traceback
from tkinter import ttk
from tkinter import filedialog
from tkinter import font
from tkinter import messagebox

# 3rd Party Includes
import customtkinter as ctk

#project imports
import apswSql as sql
from finrules.account_info_panel import AccountInfoPanel
from finrules.csv_exporter import export_transactions_csv
from read_qfx import read_qfx

from finrules.treeutils2 import (
    configure_zebra_rows,
    enable_column_sorting,
    insert_transaction_rows,
    sizeTreeColumns,
)
from config import fin_config   #,  TWIDTH, TANCHOR, TSTRETCH

class QFXViewPanel:

    def __init__(self, app, parent):

        self.app = app
        self.parent = parent

        self.transactions = []
        self.account_info = {}
        self.qfx_path = ""

        parent.grid_columnconfigure(0, weight=1)
        parent.grid_rowconfigure(2, weight=1)

        # --------------------------------------------------
        # Toolbar
        # --------------------------------------------------

        self.toolbar = ctk.CTkFrame(parent)

        self.toolbar.grid(
            row=0,
            column=0,
            sticky="ew",
            padx=10,
            pady=(10, 5)
        )

        self.toolbar.grid_columnconfigure(99, weight=1)

        self.open_button = ctk.CTkButton(
            self.toolbar,
            text="Open QFX",
            command=self.load_qfx
        )

        self.open_button.grid(
            row=0,
            column=0,
            padx=5,
            pady=5
        )

        self.export_button = ctk.CTkButton(
            self.toolbar,
            text="Export CSV",
            command=self.export_csv
        )

        self.export_button.grid(
            row=0,
            column=1,
            padx=5,
            pady=5
        )

        self.count_label = ctk.CTkLabel(
            self.toolbar,
            text="Transactions: 0"
        )

        self.count_label.grid(
            row=0,
            column=2,
            padx=(15, 0),
            sticky="w"
        )

        # --------------------------------------------------
        # Account Information
        # --------------------------------------------------

        self.account_info_panel = AccountInfoPanel(
            app,
            parent
        )

        self.account_info_panel.frame.grid(
            row=1,
            column=0,
            sticky="ew",
            padx=10,
            pady=(0, 5)
        )

        # --------------------------------------------------
        # Table Frame
        # --------------------------------------------------

        self.table_frame = ctk.CTkFrame(parent)

        self.table_frame.grid(
            row=2,
            column=0,
            sticky="nsew",
            padx=10,
            pady=(0, 10)
        )

        self.table_frame.grid_rowconfigure(0, weight=1)
        self.table_frame.grid_columnconfigure(0, weight=1)

        columns = (
            "date",
            "amount",
            "description",
            "fitid",
            "type",
            "number"
        )

        self.tree = ttk.Treeview(
            self.table_frame,
            columns=columns,
            show="headings"
        )

        headings = {
            "date": "Date",
            "amount": "Amount",
            "description": "Description",
            "fitid": "FITID",
            "type": "Type",
            "number": "Number",
        }

        for column in columns:

            self.tree.heading(
                column,
                text=headings[column]
            )

            self.tree.column(
                column,
                width=120,
                stretch=True
            )

        self.tree.grid(
            row=0,
            column=0,
            sticky="nsew"
        )

        self.v_scroll = ttk.Scrollbar(
            self.table_frame,
            orient="vertical",
            command=self.tree.yview
        )

        self.v_scroll.grid(
            row=0,
            column=1,
            sticky="ns"
        )

        self.h_scroll = ttk.Scrollbar(
            self.table_frame,
            orient="horizontal",
            command=self.tree.xview
        )

        self.h_scroll.grid(
            row=1,
            column=0,
            sticky="ew"
        )

        self.tree.configure(
            yscrollcommand=self.v_scroll.set,
            xscrollcommand=self.h_scroll.set
        )

        configure_zebra_rows(self.tree)
        enable_column_sorting(self.tree)

    def load_qfx(self, path=None):

        if not path:

            path = filedialog.askopenfilename(
                title="Open QFX File",
                filetypes=[
                    ("QFX Files", "*.qfx"),
                    ("OFX Files", "*.ofx"),
                    ("All Files", "*.*")
                ]
            )

        if not path:
            return

        try:
            transactions, account_info = read_qfx(path)
            
        except FileNotFoundError:

            messagebox.showerror(
                "QFX Error",
                "File not found."
            )
            return

        except PermissionError:

            messagebox.showerror(
                "QFX Error",
                "File is locked or inaccessible."
            )
            return

        except Exception as ex:

            traceback.print_exc()

            messagebox.showerror(
                "QFX Parse Error",
                str(ex)
            )
            return

        self.transactions = transactions
        self.account_info = account_info
        account_id = account_info.get('Account ID')
        self.app.current_account_id.set(account_id)
        account_name = sql.get_account_name(account_id)
        self.app.current_account_name.set(account_name)
        
        self.qfx_path = path

        self.account_info_panel.update_account_info(
            account_info
        )

        insert_transaction_rows(
            self.tree,
            transactions
        )

        col_attr = fin_config.transWidths['qfx']
        sizeTreeColumns(
            self.tree,
            col_attr,
            font=font.Font(family='Calibri', size=11)
        )

        self.count_label.configure(
            text=f"Transactions: {len(transactions):,}"
        )

    def export_csv(self):

        if not self.transactions:

            messagebox.showwarning(
                "Export CSV",
                "No transactions loaded."
            )
            return

        filename = filedialog.asksaveasfilename(
            title="Export CSV",
            defaultextension=".csv",
            filetypes=[
                ("CSV Files", "*.csv")
            ]
        )

        if not filename:
            return

        try:

            export_transactions_csv(
                filename=filename,
                transactions=self.transactions,
                account_info=self.account_info
            )

            messagebox.showinfo(
                "Export Complete",
                f"Exported {len(self.transactions):,} transactions."
            )

        except Exception as ex:

            messagebox.showerror(
                "Export Failed",
                str(ex)
            )