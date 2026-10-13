
# batch_panel.py
# Python Includes
import json
import customtkinter as ctk
import tkinter as tk
from tkinter import ttk, font, filedialog, messagebox
import time
import datetime
from time import perf_counter

# 3rd Party Includes

# Project Includes
import apswSql as sql
from read_qfx import read_qfx
#from treeutils import sortby_column, autosizeTreeColumns
from finrules.treeutils2 import (
    clear_tree,
    configure_zebra_rows,
    enable_column_sorting,
    insert_transaction_rows,
    sizeTreeColumns,
)
from config import fin_config,  TWIDTH, TANCHOR, TSTRETCH
from finrules.account_info_panel import AccountInfoPanel
from finrules.rules.helpers import normalize_description
from finrules.rules_editor_panel import RuleDetailsPanel
from theme_manager import theme_manager  # automatically get theme updated
import progressbar
from status_bus import StatusBus
from logging_manager import get_logger, log_exception
log = get_logger(__name__)

NEWCOLOR = "#FFFFE0"
DUPLICATECOLOR = "#D8697C"
'''
def end_time(text, start_time):
    end_time = time.perf_counter()
    elapsed_seconds = end_time - start_time
    duration = datetime.timedelta(seconds=elapsed_seconds)
    print(f"{text} time: {duration}")
'''
def normalize_qfx_date(dt):
    return f"{dt[:4]}-{dt[4:6]}-{dt[6:8]}" if dt else ""

class BatchPanel:
    def __init__(self, app, parent):  #  , account_info_panel):
        self.app = app
        self.parent = parent
        #self.account_info_panel = account_info_panel

        self.frame = ctk.CTkFrame(parent)
        frame = self.frame
        
        top = ctk.CTkFrame(frame)
        top.grid(row=0, column=0, sticky="ew", pady=(0, 10))

        for col in range(6):
            top.grid_columnconfigure(col, weight=0)

        ctk.CTkButton(
            top,
            text="Load QFX/JSON",
            command=self.load_batch_file
        ).grid(row=0, column=0, padx=(0, 5), pady=5)

        ctk.CTkButton(
            top,
            text="Export CSV",
            command=self.export_batch_csv
        ).grid(row=0, column=1, padx=5, pady=5)

        ctk.CTkButton(
            top,
            text="Import New Rows",
            fg_color=NEWCOLOR,
            hover_color="yellow",
            text_color="black",
            command=self.save_to_db
        ).grid(row=0, column=2, padx=5, pady=5)

        ctk.CTkButton(
            top,
            text="Find Duplicates",
            fg_color=DUPLICATECOLOR,
            text_color="black",
            hover_color=DUPLICATECOLOR,
            command=self.find_batch_duplicates
        ).grid(row=0, column=3, padx=5, pady=5)

        ctk.CTkButton(
            top,
            text="Import Row to DB",
            command=self.import_selected_batch_row_to_db
        ).grid(row=0, column=4, padx=5, pady=5)

        ctk.CTkButton(
            top,
            text="Save To GFX",
            command=self.save_selected_gfx_row
        ).grid(row=0, column=5, padx=(5, 0), pady=5)
        
        table_frame = ctk.CTkFrame(
            frame,
            corner_radius=12,
            fg_color="#111111"
        )

        frame.grid_rowconfigure(0, weight=0)  # toolbar
        frame.grid_rowconfigure(1, weight=0)  # account panel
        frame.grid_rowconfigure(2, weight=1)  # table

        frame.grid_columnconfigure(0, weight=1)

        self.account_info_panel = AccountInfoPanel(
            self.app,
            frame
        )

        self.account_info_panel.frame.grid(
            row=1,
            column=0,
            sticky="ew",
            pady=(0, 5)
        )
        table_frame.grid(row=2, column=0, sticky="nsew", pady=(10, 0))
        table_frame.grid_rowconfigure(0, weight=1)
        table_frame.grid_rowconfigure(1, weight=0) # hscroll
        table_frame.grid_columnconfigure(0, weight=1)  # treeview
        table_frame.grid_columnconfigure(1, weight=0)  # vscroll
        table_frame.grid_columnconfigure(2, weight=0)  # RuleDetailsPanel
                
        self.batch_right_panel = RuleDetailsPanel(table_frame)
        self.batch_right_panel.grid(row=0, column=2, rowspan=2, sticky="nsew")
        self.batch_right_panel.parent_app = app
        self.batch_right_panel.bind_dialogs(app)
        self.app.rule_details_panel = self.batch_right_panel
        
        self.batch_columns = ("new", "date", "amount", "description", "alias", "category", "subcategory", "fitid", "number", "type")   #, "duplicate_reason")
        
        # Apply Treeview theme BEFORE creating the widget
        theme_manager.apply_treeview_theme()
        
        self.batch_table = ttk.Treeview(
            table_frame,
            columns=self.batch_columns,
            show="headings",
            height=25
        )

        # Bind hover AFTER creation
        theme_manager.enable_treeview_hover(self.batch_table)
        # Rebind style explicitly
        self.batch_table.configure(style="CTk.Treeview")
        self.batch_table.tag_configure("new_row", background=NEWCOLOR)
        configure_zebra_rows(
            self.batch_table
            #even_bg="#242424",
            #odd_bg="#2E2E2E"
        )
        
        #for column in self.batch_columns:
        #    self.batch_table.heading(
        #        column,
        #        text=column
        #    )
         
        col_attr = fin_config.transWidths['qfx']
        sizeTreeColumns(
            self.batch_table,
            col_attr,
            font=font.Font(family='Calibri', size=11)
        )    
        #enable_column_sorting(self.batch_table)

        vsb = ttk.Scrollbar(table_frame, orient="vertical", command=self.batch_table.yview)
        hsb = ttk.Scrollbar(table_frame, orient="horizontal", command=self.batch_table.xview)

        self.batch_table.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        self.batch_table.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, columnspan=2, sticky="ew")

        table_frame.grid_rowconfigure(0, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)

        self.batch_table.bind("<ButtonRelease-1>", self._on_batch_row_click)
        self.batch_table.bind("<Button-3>", self._on_batch_right_click)
        
        try:
            self.batch_table.bind("<FocusIn>", self._on_batch_row_click)
        except Exception:
            pass

        self.app.batch_table = self.batch_table

    def load_qfx_and_route_account(self, path):
        try:
            log.info(f"Parsing QFX: {path}")
            txs, self.app.qfx_account_info = read_qfx(path)
            account_id = self.app.qfx_account_info["Account ID"]
            account_name = sql.get_account_name(account_id)

            if not account_name:
                dialog = ctk.CTkInputDialog(text="Enter Account Name\nFor Account" + account_id + ":", title="Add Account")
                account_name = dialog.get_input()

                if not account_name:
                    raise Exception("Add Account canceled")

                org = self.app.qfx_account_info.get("Org", "")
                err = sql.add_account(account_id, org, account_name)
                if err:
                    log.error(f'SQL error {err}')
                    raise Exception(f'Add Account Error {err}')

                messagebox.showinfo("Account Added", f"Account {account_name} added", parent=self.app)

            self.app.current_account_name.set(account_name)
            self.app.rule_details_panel.accounts_dropdown.set(account_name)
            self.app.current_account_id.set(account_id)
            self.app.current_ruleset = self.app.rule_manager.load()
            self.app.refresh_rules_list()

            return txs
        except Exception as e:
            log.error(e)
            raise

    def load_batch_file(self, path=None):
        log.info('load_batch_file |%s|', path)
        try:
            if not path:
                path = filedialog.askopenfilename(
                    parent=self.app,
                    title="Select QFX or JSON file",
                    filetypes=[
                        ("QFX Files", "*.qfx"),
                        ("OFX Files", "*.ofx"),
                        ("JSON Files", "*.json"),
                        ("All Files", "*.*")
                    ]
                )

            if not path:
                return

            if path.lower().endswith((".qfx", ".ofx")):
                self.app.batch_transactions = self.load_qfx_and_route_account(path)
            else:
                with open(path, "r", encoding="utf-8") as f:
                    self.app.batch_transactions = json.load(f)

            if not isinstance(self.app.batch_transactions, list):
                raise ValueError("Expected a list of transactions.")

            self.account_info_panel.update_account_info(self.app.qfx_account_info)

            self.app.import_file_key = sql.compute_import_file_key(path)

            self._run_batch_classification()
        except Exception as e:
            log_exception(e)
            messagebox.showerror("Batch Load Error", f"{e}", parent=self.app)
    
    def _run_batch_classification(self):
        if not hasattr(self.app, "current_ruleset") or self.app.current_ruleset is None:
            log.warning("No current ruleset set; skipping batch classification.")
            return
 
        account_name = self.app.current_account_name.get()
        qfx_start_date = normalize_qfx_date(self.app.qfx_account_info["Start Date"][:8])
        '''
        query = (
            "SELECT Date, Amount, Description, Alias, "
            "Category, SubCategory, Number, Fitid, import_file_key "
            "FROM transactions WHERE account=? AND date >= ?"
        )
        '''
        query = (
            "SELECT * "
            "FROM transactions WHERE account=? AND date >= ?"
        )
        
        self.existing_rows, cols, err = sql.sqlQueryDict(
            query, (account_name, qfx_start_date)
        )

        self.existing_lookup = {
            (
                str(r["Date"]),
                f"{r['Amount']:.2f}",
                str(r["Description"])
            ): r                  # add value to triple key
            for r in self.existing_rows
        }

        start = perf_counter()
        txs = getattr(self.app, "batch_transactions", None)
        #log.info(txs)
        if not txs:
            log.info("No batch transactions loaded; nothing to classify.")
            return

        log.info(f"Running classification on {len(txs)} transactions")
        
        sql_last_date = sql.get_last_date('transactions', account_name)

        self.app.batch_row_map = {}

        try:
            clear_tree(self.batch_table)
        except Exception:
            pass

        pb = progressbar.ProgressBarPR(title='Batch Classifier', steps=len(txs))
        
        class_cache = {}
        # txs is from qfx/csv/json file
        for idx, tx in enumerate(txs):
            progress = pb.progress()

            date_val = tx.get("date") or tx.get("Date") or ""
            #if date_val < sql_last_date:
            #    continue
            #print('date_val',date_val, sql_last_date)
            desc = tx.get("description") or tx.get("Desc") or ""
            date_val = tx.get("date") or tx.get("Date") or ""
            amount_val = tx.get("amount") or tx.get("Amount") or ""
            alias_val = tx.get("alias") or tx.get("Alias") or ""
            cat_val = tx.get("category") or tx.get("Category") or ""
            sub_val = tx.get("subcategory") or tx.get("Subcategory") or ""
            fitid_val = tx.get("fitid") or tx.get("FITID") or ""
            num_val = tx.get("number") or tx.get("NUMBER") or ""
            type_val = tx.get("type") or tx.get("TYPE") or ""
            
            #log.info(f'dates {date_val >= sql_last_date} {date_val} {sql_last_date}')
            if date_val >= sql_last_date:
                existing = False
                if date_val == sql_last_date:
                    existing = self.check_existing(tx)
            else:
                existing = self.check_existing(tx)
            
            if existing:
                tx["new"] = False
                tx.update(existing)

            else:
                tx["new"] = True
                cache_key = desc.upper()
                if cache_key not in class_cache:
                    class_cache[cache_key] = (
                        self.app.current_ruleset.classify(
                            desc,
                            account_name
                        )
                    )

                alias_val, cat_val, sub_val = class_cache[cache_key]

            tx["desc"] = tx.get("description") or tx.get("Desc") or ""
            tx["date"] = tx.get("date") or tx.get("Date") or ""
            amount_val = tx.get("amount") or tx.get("Amount") or ""

            if not existing:
                tx["alias"] = alias_val
                tx["category"] = cat_val
                tx["subcategory"] = sub_val

            row_id = str(idx)
            self.app.batch_row_map[row_id] = tx

            if progress:
                break

        pb.close()
        self.refresh_batch_table()
        elapsed = perf_counter() - start
        
        msg = (
            f"Batch_Classifier {len(txs):,} rows "
            f"for {account_name} in {elapsed:.3f}s"
        )

        StatusBus.update_perf(account_name, elapsed)  
       
    def refresh_batch_table(self):
        log.info("refresh_batch_table")
        if not hasattr(self, "batch_table"):
            return

        try:
            clear_tree(self.batch_table)
        except Exception:
            pass

        if not hasattr(self.app, "batch_row_map") or not self.app.batch_row_map:
            return

        for row_id, tx in self.app.batch_row_map.items():
            #log.info(tx)
            date_val = tx.get("date") or tx.get("Date") or ""
            amount_val = tx.get("amount") or tx.get("Amount") or ""
            desc = tx.get("description") or tx.get("Desc") or ""
            alias_val = tx.get("alias") or tx.get("Alias") or ""
            cat_val = tx.get("category") or tx.get("Category") or ""
            sub_val = tx.get("subcategory") or tx.get("Subcategory") or ""
            fitid_val = tx.get("fitid") or tx.get("FITID") or ""
            num_val = tx.get("number") or tx.get("NUMBER") or ""
            type_val = tx.get("type") or tx.get("TYPE") or ""
            new_flag = tx.get("new", True)

            values = (
                "✔" if new_flag else "",
                date_val,
                amount_val,
                desc,
                alias_val,
                cat_val,
                sub_val,
                fitid_val,
                num_val,
                type_val,
            )

            tags = []

            if int(row_id) % 2:
                tags.append("oddrow")
            else:
                tags.append("evenrow")

            if new_flag:
                tags.append("new_row")

            self.batch_table.insert(
                "",
                "end",
                iid=row_id,
                values=values,
                tags=tuple(tags)
            )
            #self.batch_table.see(item)
            #self.batch_table.update_idletasks()
        


    def _load_batch_row(self, tx):
        panel = getattr(self.app, "rule_details_panel", None)
        if panel is None:
            return

        desc = tx.get("description") or tx.get("Desc") or ""
        alias_val = tx.get("alias") or tx.get("Alias") or ""
        cat_val = tx.get("category") or tx.get("Category") or ""
        sub_val = tx.get("subcategory") or tx.get("Subcategory") or ""

        try:
            panel.pattern_var.set(desc)
        except Exception:
            pass

        try:
            panel.alias_var.set(alias_val)
        except Exception:
            pass

        try:
            panel.category_var.set(cat_val)
        except Exception:
            pass

        try:
            panel.subcategory_var.set(sub_val)
        except Exception:
            pass

    def _on_batch_row_click(self, event):
        try:
            if getattr(self.app, "_suppress_batch_click", False):
                return

            selection = self.batch_table.selection()
            if not selection:
                return

            row_id = selection[0]
            tx = self.app.batch_row_map.get(row_id)
            log.info(f'on_batch_row_click {row_id}')
            if not tx:
                return

            self._load_batch_row(tx)
        except Exception as e:
            log.error(e)
            messagebox.showerror("_on_batch_row_click Error", f"{e}", parent=self)

    def _on_batch_right_click(self, event):
        # placeholder for context menu
        pass

    def update_batch_row_after_rule_add(self):
        self._run_batch_classification()

    def find_batch_duplicates(self):
        try:
            rows = []
            for iid in self.batch_table.get_children():
                vals = self.batch_table.item(iid, "values")
                rows.append((iid, vals))

            col_index = {col: idx for idx, col in enumerate(self.batch_columns)}

            def norm(v):
                if v is None:
                    return ""
                return str(v).strip().upper()

            buckets = {}
            for iid, vals in rows:
                date = norm(vals[col_index["date"]])
                amt = norm(vals[col_index["amount"]])
                desc = norm(vals[col_index["description"]])
                fitid = norm(vals[col_index["fitid"]])

                key = (date, amt, desc, fitid)
                buckets.setdefault(key, []).append(iid)

            for iid in self.batch_table.get_children():
                self.batch_table.item(iid, tags=())

            for key, group in buckets.items():
                if len(group) <= 1:
                    continue

                date, amt, desc, fitid = key
                reason = f"Same date={date}, amount={amt}, desc={desc}, fitid={fitid}"

                for iid in group:
                    vals = list(self.batch_table.item(iid, "values"))
                    vals[col_index["duplicate_reason"]] = reason
                    self.batch_table.item(iid, values=vals)
                    self.batch_table.item(iid, tags=("duplicate",))

            self.batch_table.tag_configure("duplicate", background="#FFCCCC", foreground="black")

            messagebox.showinfo("Duplicates", "Duplicate scan complete.", parent=self.app)

        except Exception as e:
            log.error(e)
            messagebox.showerror("Duplicate Error", f"{e}", parent=self.app)
    
    def check_existing(self, tx):
        key = (
            str(tx.get("date", "")),
            f'{float(tx.get("amount", 0)):.2f}',
            str(tx.get("description", ""))
        )

        return self.existing_lookup.get(key)    
    
    '''
    def _tx_exists_in_sql(self, tx):
        try:
            date = tx.get("date") or ""
            amount = tx.get("amount") or ""
            desc = tx.get("description") or ""

            query = """
                SELECT COUNT(*) AS cnt
                FROM transactions
                WHERE date = ? AND amount = ? AND description = ?
            """
            rows, _, _ = sql.sqlQueryDict(query, (date, amount, desc))

            return rows and rows[0]["cnt"] > 0
        except Exception as e:
            log.error(e)
            messagebox.showerror("_tx_exists_in_sql Error", f"{e}", parent=self.parent_app)
            return False
    '''
    def save_to_db(self):
        try:
            if not self.app.batch_row_map:
                messagebox.showwarning("No Data", "No transactions to import.", parent=self)
                return

            account_id = self.app.current_account_id.get().strip()
            if not account_id:
                messagebox.showwarning("Account Missing", "Account ID is required.", parent=self)
                return
            #account_name = sql.get_account_name(account_id)
            account_name = self.app.current_account_name.get()
            inserted = 0
            skipped = 0
            pb = progressbar.ProgressBarPR(title='Batch Classifier', steps=len(self.app.batch_transactions))
            for row_id, tx in self.app.batch_row_map.items():
                date_val = tx.get("date", "")
                amount_val = tx.get("amount", "")
                desc_val = tx.get("description", "")
                alias_val = tx.get("alias", "")
                cat_val = tx.get("category", "")
                sub_val = tx.get("subcategory", "")
                fitid_val = tx.get("fitid", "")
                num_val = tx.get("number", "")
                type_val = tx.get("type", "")

                if not date_val or not amount_val or not desc_val:
                    skipped += 1
                    continue
                
                existing = tx.get("new", True)
                #existing = self.check_existing(date_val, amount_val, desc_val)
                if not existing:
                    skipped += 1
                    continue

                params = (
                    date_val,
                    amount_val,
                    desc_val,
                    alias_val,
                    cat_val,
                    sub_val,
                    account_name,
                    fitid_val,
                    num_val,
                    type_val,
                    self.app.import_file_key
                )

                query = "INSERT INTO transactions (Date, Amount, Description, Alias, Category, SubCategory, Account, Fitid, Number, import_file_key) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
                err = sql.sqlExecute(query, params)
                if err:
                    log.error(f"DB Insert Error: {err}")
                    skipped += 1
                else:
                    inserted += 1

                if pb.progress():
                    break

            pb.close()
            messagebox.showinfo(
                "Import Complete",
                f"Inserted: {inserted}\nSkipped: {skipped}",
                parent=self.parent
            )
            
        except Exception as e:
            log.error(e)
            messagebox.showerror("DB Import Error", f"{e}", parent=self.parent)    
            
    def _get_detail_panel_values(self):
        panel = self.app.rule_details_panel
        
        return {
            "alias": panel.alias_var.get().strip(),
            "category": panel.category_var.get().strip(),
            "subcategory": panel.subcategory_var.get().strip(),
        }


    def import_selected_batch_row_to_db(self):
        selection = self.batch_table.selection()
        if not selection:
            messagebox.showwarning(
                "No Selection",
                "Select a batch row first.",
                parent=self.app
            )
            return

        row_id = selection[0]
        tx = self.app.batch_row_map.get(row_id)

        if not tx:
            return

        panel = self.app.rule_details_panel

        # Apply current detail panel edits
        tx["alias"] = panel.alias_var.get().strip()
        tx["category"] = panel.category_var.get().strip()
        tx["subcategory"] = panel.subcategory_var.get().strip()

        account_name = self.app.current_account_name.get()

        params = (
            tx.get("date", ""),
            tx.get("amount", ""),
            tx.get("description", ""),
            tx.get("alias", ""),
            tx.get("category", ""),
            tx.get("subcategory", ""),
            account_name,
            tx.get("fitid", ""),
            self.app.import_file_key
        )

        query = """
            INSERT INTO transactions
            (
                Date,
                Amount,
                Description,
                Alias,
                Category,
                SubCategory,
                Account,
                Fitid,
                import_file_key
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """

        err = sql.sqlExecute(query, params)

        if err:
            log_exception(err)
            messagebox.showerror(
                "Import Error",
                str(err),
                parent=self.app
            )
            return

        tx["new"] = False

        self.refresh_batch_table()

        messagebox.showinfo(
            "Imported",
            "Selected transaction imported.",
            parent=self.app
        )

    def save_selected_gfx_row(self):
        values = self._get_detail_panel_values()

        tree = self.app.transactions_table    # adjust to actual GFX tree name

        selection = tree.selection()
        if not selection:
            return

        item = selection[0]

        current = list(tree.item(item, "values"))

        # date amount desc alias category subcategory ...
        current[3] = values["alias"]
        current[4] = values["category"]
        current[5] = values["subcategory"]

        tree.item(item, values=current)

        # Also update backing transaction object if you have one
        if hasattr(self.app, "row_map"):
            tx = self.app.row_map.get(item)
            if tx:
                tx["alias"] = values["alias"]
                tx["category"] = values["category"]
                tx["subcategory"] = values["subcategory"]


    def export_batch_csv(self):
        messagebox.showinfo(
            "export_batch_csv",
            f"export_batch_csv is not implemented yet",
            parent=self.parent
        )
