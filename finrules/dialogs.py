
# dialogs.py

import customtkinter as ctk


class AccountPrompt(ctk.CTkToplevel):
    def __init__(self, parent, on_submit):
        super().__init__(parent)

        self.on_submit = on_submit
        self.title("Enter Account Name")
        self.geometry("360x150")
        self.resizable(False, False)

        self.transient(parent)
        self.grab_set()
        self.focus_force()

        frame = ctk.CTkFrame(self)
        frame.pack(fill="both", expand=True, padx=10, pady=10)

        self.entry = ctk.CTkEntry(frame, placeholder_text="", show="*")
        self.entry.pack(fill="x", pady=(0, 10))

        btn = ctk.CTkButton(frame, text="OK", command=self.submit)
        btn.pack()

    def submit(self):
        pw = self.entry.get()
        self.destroy()
        if self.on_submit:
            self.on_submit(pw)

    def export_batch_file(self):
        try:
            if not self.app.batch_row_map:
                messagebox.showwarning("No Data", "No transactions to export.", parent=self.app)
                return

            path = filedialog.asksaveasfilename(
                parent=self.app,
                title="Export Classified JSON",
                defaultextension=".json",
                filetypes=[("JSON Files", "*.json"), ("All Files", "*.*")]
            )
            if not path:
                return

            account_id = self.app.current_account_id.get().strip()

            export_list = []
            for row_id in self.batch_table.get_children():
                tx = self.app.batch_row_map.get(row_id)
                if not tx:
                    continue

                export_list.append({
                    "account": account_id,
                    "date": tx.get("date", ""),
                    "amount": tx.get("amount", ""),
                    "description": tx.get("description", ""),
                    "alias": tx.get("alias", ""),
                    "category": tx.get("category", ""),
                    "subcategory": tx.get("subcategory", "")
                })

            with open(path, "w", encoding="utf-8") as f:
                json.dump(export_list, f, indent=4)

            messagebox.showinfo("Export Complete", f"JSON exported to:\n{path}", parent=self.app)

        except Exception as e:
            log.error(e)
            messagebox.showerror("JSON Export Error", f"{e}", parent=self.app)
    
    def export_batch_csv(self):
        try:
            if not self.app.batch_row_map:
                messagebox.showwarning("No Data", "No transactions to export.", parent=self.app)
                return

            path = filedialog.asksaveasfilename(
                parent=self.app,
                title="Export CSV",
                defaultextension=".csv",
                filetypes=[("CSV Files", "*.csv"), ("All Files", "*.*")]
            )
            if not path:
                return

            import csv
            with open(path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["date", "amount", "description", "alias", "category", "subcategory", "fitid"])

                for row_id in self.batch_table.get_children():
                    tx = self.app.batch_row_map.get(row_id)
                    if not tx:
                        continue

                    writer.writerow([
                        tx.get("date", ""),
                        tx.get("amount", ""),
                        tx.get("description", ""),
                        tx.get("alias", ""),
                        tx.get("category", ""),
                        tx.get("subcategory", ""),
                        tx.get("fitid", "")
                    ])

            messagebox.showinfo("Export Complete", f"CSV exported to:\n{path}", parent=self.app)

        except Exception as e:
            log.error(e)
            messagebox.showerror("CSV Export Error", f"{e}", parent=self.app)

    def save_to_db(self):
        try:
            imported = 0
            skipped = 0

            for row_id, tx in self.app.batch_row_map.items():
                date_val = tx.get("date")
                amount_val = tx.get("amount")
                desc_val = tx.get("description")
                alias_val = tx.get("alias")
                cat_val = tx.get("category")
                sub_val = tx.get("subcategory")
                fitid_val = tx.get("fitid")
                import_key = self.app.import_file_key

                exists = self._tx_exists_in_sql(tx)
                if exists:
                    skipped += 1
                    continue

                err = sql.insert_transaction(
                    date_val,
                    amount_val,
                    desc_val,
                    alias_val,
                    cat_val,
                    sub_val,
                    fitid_val,
                    import_key,
                    self.app.current_account_id.get()
                )

                if err:
                    log.error(f"SQL Insert Error: {err}")
                    continue

                imported += 1

            messagebox.showinfo(
                "Import Complete",
                f"Imported: {imported}\nSkipped (existing): {skipped}",
                parent=self.app
            )

            self._run_batch_classification()

        except Exception as e:
            log.error(e)
            messagebox.showerror("Import Error", f"{e}", parent=self.app)
