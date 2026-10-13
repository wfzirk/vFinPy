
# Python Includes
import tkinter as tk
from tkinter import filedialog, messagebox
import logging

# 3rd Party Includes
import urllib.parse
import apsw

# Project Includes

def select_db_file(entry_widget):
    filepath = filedialog.askopenfilename(filetypes=[("SQLite databases", "*.db")])
    if filepath:
        entry_widget.delete(0, tk.END)
        entry_widget.insert(0, filepath)
        
def get_table_name(cursor, table_name):
    cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
            (table_name,)
        )
    result = cursor.fetchone()
    if result:
        table = result[0]
    else:
        table = None
    logging.info('get_table %s, %s',table_name, table)
    return table
        
def open_copy_db(dbname, passwd=None, cipher="aes256cbc", kdf_iter=8192):
    
    uri_filename = urllib.parse.quote(dbname)
    uri_parameters = urllib.parse.urlencode({
        "cipher": cipher,          #Wxsqlite aes256cbc
        "kdf_iter": kdf_iter,
        "key": passwd,
        }
    )
    logging.info(uri_filename)
    logging.info(uri_parameters)  
    conn = apsw.Connection(
        f"file:{uri_filename}?{uri_parameters}",
        flags=apsw.SQLITE_OPEN_URI
           | apsw.SQLITE_OPEN_CREATE
           | apsw.SQLITE_OPEN_READWRITE,
    )

    cur = conn.cursor()
    return cur, conn

class copyTable:
    def __init__(self):
        #self.root = root
        #def copyTable(root):
        self.winc = tk.Toplevel()
        self.winc.attributes("-toolwindow", False) 
        self.winc.wm_attributes("-topmost", True)
        #winc.geometry("300x600")  #width, height
        self.winc.resizable(False, False)  #width, heig
        
        self.list_var = tk.StringVar()
        self.list_var.trace("w", self.on_source_change)

        # Source DB
        row = 0
        tk.Label(self.winc, text="Source Database:").grid(row=row, column=0, padx=5, pady=5)
        self.source_db_entry = tk.Entry(self.winc, width=50, textvariable=self.list_var)
        self.source_db_entry.grid(row=row, column=1, padx=5, pady=5)
        tk.Button(self.winc, text="Browse", command=lambda: select_db_file(self.source_db_entry)).grid(row=row, column=2, padx=5, pady=5)

        # Source DB password
        row+=1
        tk.Label(self.winc, text="Source Password:").grid(row=row, column=0, padx=5, pady=5)
        self.source_pw_entry = tk.Entry(self.winc, width=50)
        self.source_pw_entry.grid(row=row, column=1, padx=5, pady=5)

        # Destination DB
        row+=1
        tk.Label(self.winc, text="Destination Database:").grid(row=row, column=0, padx=5, pady=5)
        self.dest_db_entry = tk.Entry(self.winc, width=50)
        self.dest_db_entry.grid(row=row, column=1, padx=5, pady=5)
        tk.Button(self.winc, text="Browse", command=lambda: select_db_file(self.dest_db_entry)).grid(row=row, column=2, padx=5, pady=5)

        # Target DB password
        row+=1
        tk.Label(self.winc, text="Target Password:").grid(row=row, column=0, padx=5, pady=5)
        self.dest_pw_entry = tk.Entry(self.winc, width=50)
        self.dest_pw_entry.grid(row=row, column=1, padx=5, pady=5)

        # Table Name
        row+=1
        tk.Label(self.winc, text="Table Name to Copy:").grid(row=row, column=0, padx=5, pady=5)

        self.table_name_listbox = tk.Listbox(self.winc, selectmode=tk.SINGLE, width=30, height=3) 
        self.table_name_listbox.grid(row=row, column=1, padx=5, pady=5)
        
        # Add a scrollbar to handle items beyond the visible height
        scrollbar = tk.Scrollbar(self.winc, orient="vertical", command=self.table_name_listbox.yview)
        scrollbar.grid(row=row, column=2, padx=5, pady=5)
        self.table_name_listbox.config(yscrollcommand=scrollbar.set)
        
        # Copy Button
        row+=1
        tk.Button(self.winc, text="Copy Table", command=self.copy_table_to_another_db).grid(row=row, column=1, pady=10)

        tk.Button(self.winc, text="Cancel", command=self.cancel_copy).grid(row=row, column=2, pady=10)
  
    def copy_table_to_another_db(self):
        logging.info('copy to db')
        source_db_path = self.source_db_entry.get()
        source_db_pw = self.source_pw_entry.get()
        dest_db_path = self.dest_db_entry.get()
        dest_db_pw = self.dest_pw_entry.get()
        
        if not all([source_db_path, dest_db_path]):
            messagebox.showerror("Error", "Please fill in all fields.")
            return

        try:
            # Connect to source database
            source_cursor, source_conn = open_copy_db(source_db_path, passwd=source_db_pw, cipher="aes256cbc", kdf_iter=8192)
            query = "SELECT name FROM sqlite_master WHERE type='table';"
            source_cursor.execute(query)

            selected_indices = self.table_name_listbox.curselection()
            if selected_indices:  # Check if anything is selected
                selected_table_index = selected_indices[0]
                table_name = self.table_name_listbox.get(selected_table_index)
                log.info(f"Selected item: {table_name}")
            else:
                log.info("No item selected.")
                messagebox.showwarning("Warning", f"No table selected.")
                return

            # Get CREATE TABLE statement from source
            source_cursor.execute(f"SELECT sql FROM sqlite_master WHERE type='table' AND name='{table_name}'")
            create_table_sql = source_cursor.fetchone()[0]
            logging.info(create_table_sql)
            
            dest_cursor, dest_conn = open_copy_db(dest_db_path, passwd=dest_db_pw, cipher="aes256cbc", kdf_iter=8192)

            result = get_table_name(dest_cursor, table_name)
            if result is not None:
                msg = f"Table {result} already exists."
                logging.warn(msg)
                messagebox.showwarning("Warning", msg)
                return

            # Create table in destination (if it doesn't exist)
            dest_cursor.execute(create_table_sql)

            # Copy data
            source_cursor.execute(f"SELECT * FROM {table_name}")
            rows = source_cursor.fetchall()

            # Construct INSERT statement
            num_columns = len(rows[0]) if rows else 0
            placeholders = ', '.join(['?' for _ in range(num_columns)])
            insert_sql = f"INSERT INTO {table_name} VALUES ({placeholders})"

            dest_cursor.executemany(insert_sql, rows)
            dest_conn.close()
            source_conn.close()
            messagebox.showinfo("Success", f"Table '{table_name}' copied successfully.")

        except Exception as e:
            logging.exception(e)
            messagebox.showerror("Error", f"An unexpected error occurred: {e}")

        finally:
            if 'source_conn' in locals() and source_conn:
                source_conn.close()
            if 'dest_conn' in locals() and dest_conn:
                dest_conn.close()
                
    def on_source_change(self, *args):
        logging.info('onsourcechange')
        new_value = self.list_var.get()
        source_db_path = self.source_db_entry.get()
        source_db_pw = self.source_pw_entry.get()
        
        try:
            source_cursor, source_conn = open_copy_db(source_db_path, passwd=source_db_pw, cipher="aes256cbc", kdf_iter=8192)
            query = "SELECT name FROM sqlite_master WHERE type='table';"
            source_cursor.execute(query)
         
            table_names = [row[0] for row in source_cursor.fetchall()]
            logging.info(table_names)
            # Add some items to the Listbox
            for i in table_names:
                self.table_name_listbox.insert(tk.END, i)
        except Exception as e:
            logging.exception(e)
            messagebox.showerror("Error", f"An unexpected error occurred: {e}")

        finally:
            if 'source_conn' in locals() and source_conn:
                source_conn.close()
                
    def cancel_copy(self):
        self.winc.destroy()
        #self.root.deiconify()
        
if __name__ == "__main__":
    # GUI Setup
    root = tk.Tk()
    root.title("SQLite Table Copier")
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(lineno)s:%(message)s')
    logging.info('starting')

    #root.withdraw()  
    copyTable()

    root.mainloop()