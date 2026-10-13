
#import theme_manager  # must happen BEFORE any CTk/Tk widgets are created

# Python Includes
from tkinter import filedialog, messagebox
import tkinter as tk
from tkinter import ttk

# 3rd Party Includes
import customtkinter as ctk

# Project Includes
from read_qfx import read_qfx
from theme_manager import theme_manager  # automatically get theme updated

ctk.set_appearance_mode("light")
ctk.set_default_color_theme("ctk_themes/finofx.json")


class QFXViewer(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("QFX Viewer")
        #self.geometry("1100x650")

        # --- Root grid config ---
        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # --- Open Button ---
        self.open_btn = ctk.CTkButton(self, text="Open QFX File", command=self.load_file)
        self.open_btn.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 5))

        # --- Account Info Frame ---
        self.account_frame = ctk.CTkFrame(self)
        self.account_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=5)
        self.account_frame.grid_columnconfigure(0, weight=1)

        self.account_label = ctk.CTkLabel(
            self.account_frame,
            text="No account loaded",
            anchor="w",
            justify="left",
            font=("Consolas", 14)
        )
        self.account_label.grid(row=0, column=0, sticky="ew", padx=10, pady=10)

        # --- Table Frame ---
        table_frame = ctk.CTkFrame(self)
        table_frame.grid(row=2, column=0, sticky="nsew", padx=10, pady=10)
        table_frame.grid_rowconfigure(0, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)

        # --- Treeview (Tkinter inside CTk frame) ---
        columns = ["date", "amount", "description", "fitid", "type", "number"]
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings")

        for col in columns:
            self.tree.heading(col, text=col.capitalize())
            self.tree.column(col, width=180)

        self.tree.grid(row=0, column=0, sticky="nsew")
        
        table_frame.grid_columnconfigure(0, weight=1)
        table_frame.grid_rowconfigure(0, weight=1)

        # --- Scrollbars ---
        yscroll = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        xscroll = ttk.Scrollbar(table_frame, orient="horizontal", command=self.tree.xview)

        self.tree.configure(yscrollcommand=yscroll.set, xscrollcommand=xscroll.set)

        yscroll.grid(row=0, column=1, sticky="ns")
        xscroll.grid(row=1, column=0, sticky="ew")

    def load_file(self):
        path = filedialog.askopenfilename(
            title="Select QFX File",
            filetypes=[("QFX Files", "*.qfx")]
        )
        if not path:
            return

        try:
            statement, account_info = read_qfx(path)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to parse QFX:\n{e}")
            return

        # --- Update account info ---
        lines = [f"{k}: {v}" for k, v in account_info.items() if v]
        self.account_label.configure(text="\n".join(lines))

        # --- Clear old rows ---
        for row in self.tree.get_children():
            self.tree.delete(row)

        # --- Insert new rows ---
        for row in statement:
            self.tree.insert("", tk.END, values=[
                row["date"],
                row["amount"],
                row["description"],
                row["fitid"],
                row["type"],
                row["number"],
            ])


if __name__ == "__main__":
    QFXViewer().mainloop()
