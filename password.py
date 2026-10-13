
# Python Includes
from tkinter import filedialog, messagebox

# 3rd Party Includes
import customtkinter as ctk
import apsw

# Project Includes

class CreateEncryptedDBDialog(ctk.CTkToplevel):
    def __init__(self, master):
        super().__init__(master)
        self.title("Create New Encrypted Database")
        self.geometry("420x420")
        self.resizable(False, False)
        self.grab_set()

        self.result = None

        # --- GRID CONFIG ---
        self.columnconfigure(0, weight=1, uniform="col")
        self.columnconfigure(1, weight=1, uniform="col")

        pad = {"padx": 12, "pady": 8}

        # --- FILE PICKER ---
        self.file_entry = ctk.CTkEntry(self, placeholder_text="Save database as...")
        self.file_entry.grid(row=0, column=0, columnspan=2, sticky="ew", **pad)
        self.file_entry.bind("<Button-1>", self.pick_file)
        #self.browse_btn = ctk.CTkButton(self, text="Browse", command=#self.pick_file)
        #self.browse_btn.grid(row=0, column=1, sticky="ew", **pad)

        # --- PASSWORD ---
        self.pass_entry = ctk.CTkEntry(self, show="*", placeholder_text="Password")
        self.pass_entry.grid(row=1, column=0, columnspan=2, sticky="ew", **pad)

        # --- CONFIRM PASSWORD ---
        self.pass_confirm_entry = ctk.CTkEntry(self, show="*", placeholder_text="Confirm Password")
        self.pass_confirm_entry.grid(row=2, column=0, columnspan=2, sticky="ew", **pad)

        # --- CIPHER ---
        self.cipher_opt = ctk.CTkOptionMenu(
            self,
            values=["aes128cbc", "aes256cbc", "chacha20", "sqlcipher"],
        )
        self.cipher_opt.set("aes256cbc")
        self.cipher_opt.grid(row=3, column=0, columnspan=2, sticky="ew", **pad)

        # --- KDF ITERATIONS ---
        self.kdf_entry = ctk.CTkEntry(self, placeholder_text="KDF Iterations (default 64000)")
        self.kdf_entry.insert(0, "64000")
        self.kdf_entry.grid(row=4, column=0, columnspan=2, sticky="ew", **pad)

        # --- ENCODING ---
        self.encoding_opt = ctk.CTkOptionMenu(
            self,
            values=["utf-8", "utf-16", "latin-1"],
        )
        self.encoding_opt.set("utf-8")
        self.encoding_opt.grid(row=5, column=0, columnspan=2, sticky="ew", **pad)

        # --- BUTTONS ---
        self.ok_btn = ctk.CTkButton(self, text="Create", command=self.on_ok)
        self.ok_btn.grid(row=6, column=0, sticky="ew", **pad)

        self.cancel_btn = ctk.CTkButton(self, text="Cancel", command=self.on_cancel)
        self.cancel_btn.grid(row=6, column=1, sticky="ew", **pad)

    def pick_file(self, *args):
        path = filedialog.asksaveasfilename(
            title="Create New Database",
            defaultextension=".db",
            filetypes=[("SQLite DB", "*.db"), ("All Files", "*.*")]
        )
        if path:
            self.file_entry.delete(0, "end")
            self.file_entry.insert(0, path)

    def on_ok(self):
        file = self.file_entry.get().strip()
        password = self.pass_entry.get().strip()
        confirm = self.pass_confirm_entry.get().strip()
        cipher = self.cipher_opt.get()
        encoding = self.encoding_opt.get()

        try:
            kdf_iter = int(self.kdf_entry.get().strip())
        except:
            kdf_iter = 64000

        if not file:
            #ctk.CTkMessagebox(title="Error", message="No file selected")
            tk.messagebox.showerror("Error", "No database file selected")
            return

        if not password:
            #CTkMessagebox(title="Error", message="Password cannot be empty")
            tk.messagebox.showerror("Error", "Password cannot be empty")
            return

        if password != confirm:
            #ctk.CTkMessagebox(title="Error", message="Passwords do not match")
            tk.messagebox.showerror("Error", "Passwords do not match")
            return

        self.result = {
            "file": file,
            "password": password,
            "cipher": cipher,
            "kdf_iter": kdf_iter,
            "encoding": encoding,
        }
        self.destroy()

    def on_cancel(self):
        self.result = None
        self.destroy()

def create_new_encrypted_db():
    dialog = CreateEncryptedDBDialog(None)
    dialog.wait_window()

    params = dialog.result
    if not params:
        return "error"

    # You now have:
    # params["file"]
    # params["password"]
    # params["cipher"]
    # params["kdf_iter"]
    # params["encoding"]

    # Create the DB
    try:
        conn = apsw.Connection(params["file"])
        cur = conn.cursor()

        cur.execute(f"PRAGMA key = '{params['password']}';")
        cur.execute(f"PRAGMA cipher = '{params['cipher']}';")
        cur.execute(f"PRAGMA kdf_iter = {params['kdf_iter']};")

        # Initialize schema
        cur.execute("SELECT 1;")

        return params

    except Exception as ex:
        messagebox.showerror("Error", str(ex))
        return "error"





class PasswordChangeDialog(ctk.CTkToplevel):
    def __init__(self, master):
        super().__init__(master)
        self.title("Change Database Password")
        self.geometry("420x320")
        self.resizable(False, False)
        self.grab_set()

        self.result = None

        # --- GRID CONFIG ---
        self.columnconfigure(0, weight=1, uniform="col")
        self.columnconfigure(1, weight=1, uniform="col")

        pad = {"padx": 12, "pady": 8}

        # --- OLD PASSWORD ---
        self.old_pw = ctk.CTkEntry(self, show="*", placeholder_text="Old Password")
        self.old_pw.grid(row=0, column=0, columnspan=2, sticky="ew", **pad)

        self.old_toggle = ctk.CTkCheckBox(self, text="Show", width=60,
                                        command=lambda: self.toggle_pw(self.old_pw, self.old_toggle))
        self.old_toggle.grid(row=0, column=2, sticky="ew", **pad)

        # --- NEW PASSWORD ---
        self.new_pw = ctk.CTkEntry(self, show="*", placeholder_text="New Password")
        self.new_pw.grid(row=1, column=0, columnspan=2, sticky="ew", **pad)

        self.new_toggle = ctk.CTkCheckBox(self, text="Show", width=60,
                                        command=lambda: self.toggle_pw(self.new_pw, self.new_toggle))
        self.new_toggle.grid(row=1, column=2, sticky="ew", **pad)

        # --- CONFIRM NEW PASSWORD ---
        self.confirm_pw = ctk.CTkEntry(self, show="*", placeholder_text="Confirm New Password")
        self.confirm_pw.grid(row=2, column=0, columnspan=2, sticky="ew", **pad)

        self.confirm_toggle = ctk.CTkCheckBox(self, text="Show", width=60, command=lambda: self.toggle_pw(self.confirm_pw, self.confirm_toggle))
        self.confirm_toggle.grid(row=2, column=2, columnspan=2, sticky="ew", **pad)

        # --- BUTTONS --- 
        self.ok_btn = ctk.CTkButton(self, text="Change Password", command=self.on_ok)
        self.ok_btn.grid(row=3, column=0, sticky="ew", **pad)

        self.cancel_btn = ctk.CTkButton(self, text="Cancel", command=self.on_cancel)
        self.cancel_btn.grid(row=3, column=1, sticky="ew", **pad)

    # --- PASSWORD VISIBILITY TOGGLE ---
    def toggle_pw(self, entry, btn):
        if entry.cget("show") == "*":
            entry.configure(show="")
            btn.configure(text="Hide")
        else:
            entry.configure(show="*")
            btn.configure(text="Show")

    # --- OK HANDLER ---
    def on_ok(self):
        old_pw = self.old_pw.get().strip()
        new_pw = self.new_pw.get().strip()
        confirm = self.confirm_pw.get().strip()

        if not old_pw:
            #ctk.CTkMessagebox(title="Error", message="Old password cannot be empty")
            messagebox.showerror("Error", "Old password cannot be empty")
            return

        if not new_pw:
            #ctk.CTkMessagebox(title="Error", message="New password cannot be empty")
            messagebox.showerror("Error", "New password cannot be empty")
            return

        if new_pw != confirm:
            #ctk.CTkMessagebox(title="Error", message="New passwords do not match")
            messagebox.showerror("Error", "New passwords do not match")
            return

        self.result = {
            "old_password": old_pw,
            "new_password": new_pw,
        }
        self.destroy()

    # --- CANCEL HANDLER ---
    def on_cancel(self):
        self.result = None
        self.destroy()

def prompt_password_change(master=None):
    dlg = PasswordChangeDialog(master)
    dlg.wait_window()
    return dlg.result

#=======================================================

#class InvalidPasswordError(Exception):
#    #print('invalid password', Exception)
#    pass

def verify_password(db_path, password):
    try:
        con = apsw.Connection(db_path)

        # Apply key
        con.pragma("key", password)

        # Force database access to validate key
        con.cursor().execute(
            "SELECT count(*) FROM sqlite_master"
        ).fetchall()

        print("Password verified")

        return True, None

    except apsw.CorruptError as e:
        print("CorruptError:", e)
        return False, "invalid_password"

    except apsw.SQLError as e:
        msg = str(e).lower()

        print("SQLError:", msg)

        if (
            "file is not a database" in msg
            or "not a database" in msg
        ):
            return False, "invalid_password"

        return False, f"sql_error: {e}"

    except Exception as e:
        print("Exception:", repr(e))
        msg = str(e).lower()

        print("Exception:", msg)
        if (
            "file is not a database" in msg
            or "not a database" in msg
        ):
            return False, "invalid_password"

        return False, f"sql_error: {e}"
        
        
class OpenDBDialog(ctk.CTkToplevel):
    def __init__(self, master):
        super().__init__(master)
        self.title("Open Encrypted Database")
        self.geometry("420x360")
        self.resizable(False, False)
        self.grab_set()

        self.result = None
        
        # --- GRID CONFIG ---
        self.columnconfigure(0, weight=1, uniform="col")
        self.columnconfigure(1, weight=1, uniform="col")

        pad = {"padx": 12, "pady": 8}

        # --- FILE PICKER ---
        self.file_entry = ctk.CTkEntry(self, placeholder_text="Select database file...")
        self.file_entry.grid(row=0, column=0, columnspan=2, sticky="ew", **pad)
        self.file_entry.bind("<Button-1>", self.pick_file)

        # --- PASSWORD ---
        pw_frame = ctk.CTkFrame(self, fg_color="transparent")
        pw_frame.grid(
            row=1,
            column=0,
            columnspan=2,
            sticky="ew",
            padx=(12, 0),   # no right padding
            pady=8
        )

        pw_frame.columnconfigure(0, weight=1)
        pw_frame.columnconfigure(1, weight=0)

        self.pass_entry = ctk.CTkEntry(
            pw_frame,
            show="*",
            placeholder_text="Password"
        )
        self.pass_entry.grid(
            row=0,
            column=0,
            sticky="ew",
            padx=(0, 8)
        )

        self.show_password_var = ctk.BooleanVar(value=False)

        self.show_password_chk = ctk.CTkCheckBox(
            pw_frame,
            text="Show",
            width=45,
            variable=self.show_password_var,
            command=self.toggle_password
        )
        self.show_password_chk.grid(
            row=0,
            column=1,
            sticky="e",
            padx=(0,12)
        )

        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)

        # --- CIPHER ---
        self.cipher_opt = ctk.CTkOptionMenu(
            self,
            values=["aes128cbc", "aes256cbc", "chacha20", "sqlcipher"],
        )
        self.cipher_opt.set("chacha20")
        self.cipher_opt.grid(row=2, column=0, columnspan=2, sticky="ew", **pad)

        # --- KDF ITERATIONS ---
        self.kdf_entry = ctk.CTkEntry(self, placeholder_text="KDF Iterations (default 64000)")
        self.kdf_entry.insert(0, "64007")
        self.kdf_entry.grid(row=3, column=0, columnspan=2, sticky="ew", **pad)
        
        # --- ENCODING ---
        self.encoding_opt = ctk.CTkOptionMenu(
            self,
            values=["utf-8", "utf-16", "latin-1"],
        )
        self.encoding_opt.set("utf-8")
        self.encoding_opt.grid(row=4, column=0, columnspan=2, sticky="ew", **pad)

        # --- BUTTONS ---
        self.ok_btn = ctk.CTkButton(self, text="Open", command=self.on_ok)
        self.ok_btn.grid(row=5, column=0, sticky="ew", **pad)
        #ctrl_frame.bind('<Return>', self.popup)
        self.cancel_btn = ctk.CTkButton(self, text="Cancel", command=self.on_cancel)
        self.cancel_btn.grid(row=5, column=1, sticky="ew", **pad)

    def toggle_password(self):
        if self.show_password_var.get():
            self.pass_entry.configure(show="")
        else:
            self.pass_entry.configure(show="*")

    def pick_file(self, *args):
        print('pick_file')
        path = filedialog.askopenfilename(
            title="Select Encrypted Database",
            filetypes=[("SQLite DB", "*.db *.sqlite"), ("All Files", "*.*")]
        )
        print('path', path)
        if path:
            self.file_entry.delete(0, "end")
            self.file_entry.insert(0, path)

    def on_ok(self, *args):
        file = self.file_entry.get().strip()
        password = self.pass_entry.get().strip()
        cipher = self.cipher_opt.get()
        encoding = self.encoding_opt.get()

        print(file)
        print(password)

        try:
            kdf_iter = int(self.kdf_entry.get().strip())
        except Exception:
            kdf_iter = 64000

        if not file:
            messagebox.showerror(
                "Error",
                "No database file selected"
            )
            return

        ok, error = verify_password(file, password)
        print('ok',ok)
        print('---error',error)
        if not ok:
            if error == "invalid_password":
                messagebox.showerror(
                    "Password Error",
                    "The database password is incorrect."
                )
            else:
                messagebox.showerror(
                    "Database Error",
                    error
                )

            self.pass_entry.focus()
            self.pass_entry.select_range(0, "end")
            return
            
        self.result = {
            "file": file,
            "password": password,
            "cipher": cipher,
            "kdf_iter": kdf_iter,
            "encoding": encoding,
        }

        self.destroy()
    def on_cancel(self):
        self.result = None
        self.destroy()

def prompt_open_db(master=None):
    dlg = OpenDBDialog(master)
    dlg.wait_window()
    return dlg.result      
    
if __name__ == "__main__":
    import sys
    
    root = ctk.CTk()
    
    def close_all():
        root.destroy()
        sys.exit()
            
    root.protocol("WM_DELETE_WINDOW", close_all)         
    
    #dlg = OpenDBDialog(None) 
    #dlg = PasswordChangeDialog(None)
    dlg = CreateEncryptedDBDialog(None)
    dlg.wait_window()
    if not dlg.result:
        sys.exit()

    print(dlg.result["file"])
    print(dlg.result["password"])
    print(dlg.result["cipher"])
    print(dlg.result["kdf_iter"])
        
    root.mainloop()    