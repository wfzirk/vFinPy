

# https://pypi.org/project/apsw-sqlite3mc/
# https://github.com/utelle/apsw-sqlite3mc
# https://czb404.github.io/apsw/tips.html
# https://rogerbinns.github.io/apsw/example.html


# Python Includes
import os, sys
from tkinter import messagebox, simpledialog, filedialog
import csv
import hashlib
import traceback

# 3rd Party Includes
#import urllib.parse
import apsw
import apsw.ext
import customtkinter as ctk

# Project Includes
from config import fin_config
from password import OpenDBDialog
from logging_manager import get_logger
log = get_logger(__name__)

''' 
    # Supported ciphers include: 'aes128cbc', 'aes256cbc', 'chacha20', 'sqlcipher'
'''
'''
def xlog_exception(exc: Exception):
    etype, evalue, tb = sys.exc_info()
    tb_str = "".join(traceback.format_exception(etype, evalue, tb))
    log.error(f"EXCEPTION: {exc}\n{tb_str}")
'''

gTrackerList = ["INSERT", "UPDATE", "DELETE"]
gTables = []
gTriggerCount = 0
gConn = None
secParams = []

CANONICAL_SCHEMA = {
    "transactions": [
        "Id INTEGER PRIMARY KEY AUTOINCREMENT",
         "Date DATE",   
         "Alias STRING",
         "Number STRING",
         "Type STRING(15)",
         "Amount REAL(8)",
         "Category STRING(25)",
         "SubCategory STRING(25)",
         "Notes STRING",
         "Account STRING(20)",
         "Description STRING",
         "Fitid STRING",
         "import_file_key STRING"
        ],
    "accounts": [ 
        "Id INTEGER PRIMARY KEY AUTOINCREMENT",
         "AccountID STRING",   
         "Organization STRING",
         "OrganizationName STRING"
        ],  
    "import_files": [
        "import_file_key TEXT PRIMARY KEY",
        "filename TEXT",
        "imported_at TEXT"
    ],
    "patterns": [
        "Id INTEGER PRIMARY KEY AUTOINCREMENT",
        "Alias STRING",
        "Pattern STRING",
        "Category STRING",
        "SubCategory STRING",
        "Account STRING"
    ], 
    "rules": [
        "rule_id INTEGER PRIMARY KEY AUTOINCREMENT",
        "account TEXT NOT NULL",
        "pattern TEXT NOT NULL",
        "alias TEXT",
        "category TEXT",
        "subcategory TEXT",
        "import_file_key TEXT",
        "enabled INTEGER NOT NULL DEFAULT 1",
        "created_at DATETIME DEFAULT CURRENT_TIMESTAMP",
        "updated_at DATETIME DEFAULT CURRENT_TIMESTAMP"
    ] 
}

def update_hook(operation, dbname, tablename, rowid):
    global gTriggerCount
    op_type = {apsw.SQLITE_INSERT: "INSERT", apsw.SQLITE_UPDATE: "UPDATE", apsw.SQLITE_DELETE: "DELETE"}.get(operation, "UNKNOWN")
    log.info(f"Hook: Operation: {op_type} on table {tablename} for rowid {rowid}")
    if op_type in gTrackerList:
        gTriggerCount += 1

def close_db(conn):  
    global gConn
    if conn: conn.close()
    gConn = None

def create_new_database():
    # Prompt user where to save the new database file
    file_path = filedialog.asksaveasfilename(
        title="Create New Database",
        defaultextension=".db",
        filetypes=[("SQLite Database", "*.db"), ("All Files", "*.*")]
    )

    if file_path:
        passWd = simpledialog.askstring("Password", "Enter password:", show='*')           
        if passWd:
            return file_path, passWd
            
def change_password(filename, old_password, new_password):
    try:
        conn = apsw.Connection(filename)
        cur = conn.cursor()
        
        cur.execute(f"PRAGMA key = '{old_password}';")
        cur.execute(f"PRAGMA rekey = '{new_password}';")
        return ""
    except Exception as ex:
        #raise apsw.NotADBError(str(ex))
        log.error("DB open error %s", ex)
        messagebox.showerror("Error", str(ex))
        return ex    

def open_db():
    #if not fin_config.secParams.fileName:

    if not fin_config.secParams.key:
        dialog = OpenDBDialog(None)     
        dialog.wait_window()
        if not dialog.result:
            raise apsw.NotADBError("Canceled")
        if not dialog.result["file"]:
            raise apsw.NotADBError("No database file selected")
        if not dialog.result["password"]:
            raise apsw.NotADBError("No password entered")        
            
        fin_config.secParams.fileName = dialog.result["file"]
        fin_config.secParams.key = dialog.result["password"]
        fin_config.secParams.cipher = dialog.result["cipher"]
        fin_config.secParams.kdf_iter = dialog.result["kdf_iter"]
        
    secParams = fin_config.secParams
    filename = secParams.fileName
    password = secParams.key
    cipher = secParams.cipher or "chacha20"
    kdf_iter = secParams.kdf_iter or 64007

    conn = apsw.Connection(filename)
    cur = conn.cursor()

    # If password provided, try to unlock
    if password:
        cur.execute(f"PRAGMA key = '{password}';")

    # Validate by reading schema
    try:
        #list(cur.execute("SELECT name FROM sqlite_master LIMIT 1;"))
        tbls = cur.execute(
            "SELECT name FROM sqlite_schema WHERE type='table' AND name NOT LIKE 'sqlite_%';"
        )

    except Exception as ex:
        #raise apsw.NotADBError(str(ex))
        log.error("DB open error %s", ex)
        messagebox.showerror("Error", str(ex))
        return "error", "error"
    
    return cur, conn

def init_db(root):
    try:
        cur, conn = open_db()
        log.info("init_db ")
        if cur == "error":
            return cur
            
        tbls = [row[0] for row in cur.execute(
            "SELECT name FROM sqlite_schema WHERE type='table' AND name NOT LIKE 'sqlite_%';"
        )]

        log.info("init_db tables %s", tbls)

        if "transactions" not in tbls:
            createTable(cur, "transactions")
        if "accounts" not in tbls:
            createTable(cur, "accounts")
        if "import_files" not in tbls:
            createTable(cur, tableName='import_files') 
        if "patterns" not in tbls:
            createTable(cur, tableName='patterns')  
        if "rules" not in tbls:
            createTable(cur, tableName='rules')   
   
            stmt = """CREATE INDEX idx_rules_account
                ON rules(account);
            """    
            cur.execute(stmt)
            stmt = """CREATE INDEX idx_rules_pattern
                ON rules(pattern);
            """    
            cur.execute(stmt)
            stmt = """CREATE INDEX idx_rules_category
                ON rules(category);
            """  
            cur.execute(stmt)
        
        close_db(conn)

    except apsw.NotADBError as ex:
        log.error("DB open error %s", ex)
        messagebox.showerror("Error", str(ex))
        return ex

def createTable(cur, tableName='transactions'):
    rc = 1
    try:     
        cols = CANONICAL_SCHEMA[tableName]
        stmt = "CREATE TABLE IF NOT EXISTS " + tableName + " (%s)" % ",".join(cols)           
        log.info('createTable %s',tableName)
        cur.execute(stmt)
        rc = 0
    except apsw.Error as e:
        log.error(f"An error occurred: {e}")
        messagebox.showerror("ERROR", e)
 
def add_column(table, column, coltype="TEXT", default=None):
    """
    Add a column to an existing table if it does not already exist.
    """
    # Check if column already exists
    cols = getColumnNames(table)
    if column in cols:
        return ""  # already exists, no error

    # Build SQL
    if default is None:
        sql = f"ALTER TABLE {table} ADD COLUMN {column} {coltype};"
        params = []
    else:
        sql = f"ALTER TABLE {table} ADD COLUMN {column} {coltype} DEFAULT ?;"
        params = [default]

    _, _, err = sqlQuery(sql, params)
    return err

def migrate_schema():
    """
    Ensures all tables contain all columns defined in CANONICAL_SCHEMA.
    Adds missing columns automatically.
    """
    for table, columns in CANONICAL_SCHEMA.items():
        try:
            existing = getColumnNames(table)
        except Exception:
            continue  # table does not exist yet

        for col, coltype in columns.items():
            if col not in existing:
                log.info(f"[MIGRATE] Adding column {col} to {table}")
                add_column(table, col, coltype)


# https://czb404.github.io/apsw/tips.html    
def row_factory(cursor, row):
    return {k[0]: row[i] for i, k in enumerate(cursor.getdescription())}


def sqlQueryDict(query, params=[]):
    
    #log.info('*********** sqlQueryDict ***************')
    ##log.debug('sqlQueryDict %s', query)
    #log.debug(params)
    try:
        c, conn = open_db()
        conn.setrowtrace(row_factory)
        c.execute(query, params)

        transactions = c.fetchall()
        qd = apsw.ext.query_info(conn, query)
        items = dict(qd.description)
        columnNames = list(items.keys())

        close_db(conn)
        return  transactions,  columnNames, ""
    except Exception as ex:
        log.error('sqlQueryDict error %s', ex)
        messagebox.showerror("ERROR", "sqlQuery error "+ str(ex))
        return "", columnNames, str(e)

def sqlPragma(query, params=[]):
    
    log.debug('**** %s', query)
    log.info('**** %s', params)
    allData = []
    try:

        c, conn = open_db()
        conn.setrowtrace(row_factory)
        c.execute(query, params)
        fetch = c.fetchall()
        for data in fetch:
            ad = list(data.values())
            allData.append(ad)

        close_db(conn)
        return  allData, ""

    except Exception as ex:
        log.error('sqlQuery error %s', ex)
        messagebox.showerror("ERROR", "sqlQuery error "+ str(ex))
        return "", "", str(ex)

def sqlQuery(query, params=[]):
    
    #log.info('sqlQuery %s', query)
    #log.info('****     %s', params)
    allData = []
    try:
        c, conn = open_db()
        conn.setrowtrace(row_factory)
        c.execute(query, params)

        transactions = c.fetchall()
        qd = apsw.ext.query_info(conn, query)
        #print('description',qd.description)
        items = dict(qd.description)
        #print('---- trans', transactions)
        columnNames = list(items.keys())
        if not transactions:
            transactions = []
        if not columnNames:
            columnNames = []
        for data in transactions:
            ad = list(data.values()) 
            row = ["" if v is None else v for v in ad]
            allData.append(row)
        #log.debug(allData[0])
        close_db(conn)
        return  allData,  columnNames, ""

    except Exception as ex:
        log.error('sqlQuery error %s', ex)
        messagebox.showerror("ERROR", "sqlQuery error "+ str(ex))
        return "", "", str(ex)
 
def sqlExecute(query, params):
    
    log.debug('****sqlExecute %s',query)
    log.debug('****params %s',params)
    try:
        cur, conn = open_db()
        with conn:
            cur.execute(query, (params))
        close_db(conn)
        return "" 
    except Exception as ex:
        log.error('sqlExecute error %s', ex)
        log.info(f'{query}  {params}')
        messagebox.showerror("ERROR", "sqlExecute error "+ str(ex))
        return str(ex)

def sql_executemany():
    
    data = request.get_json()
    query = data["sql"]
    params = data["params"]
    tracker = data["tracker"]
    log.debug('****sql_executemany %s',query)

    #print('*********** sql_executemany', tracker, '***************')
    #print(sql)
    #print(params)

    try:
        c, conn = open_db()
        with conn:
            c.executemany(query, params)
   
        close_db(conn)
        return ""
    except Exception as ex:
        log.error('sqlQuery error %s', ex)
        messagebox.showerror("ERROR", "sql_executemany "+ str(ex))
        return "", str(ex)
   
def add_account(accountid, organization, organizationname):
    query = "INSERT INTO accounts (AccountID, Organization, OrganizationName) VALUES (?, ?, ?)"
    err = sqlExecute(query, [accountid, organization, organizationname])
    return err

def accounts(accountId=""):
    #log.debug('AccountID %s ',accountId)
    #c, conn = open_db()
    query = "SELECT * FROM accounts"
    if accountId:
        query+=" WHERE AccountID = '"+accountId+"'"
    query += ";"
    return sqlQueryDict(query, params=[])
    
def get_account_name(accnt_id):   #, routing_number):
    cur, conn = open_db()
    query = "SELECT OrganizationName FROM accounts WHERE accountId = ?;"  
    cur.execute(query, [accnt_id])
    fetch = cur.fetchone()
    #print('-----fetch-',fetch)
    if fetch:
        data = list(fetch)[0]
        #print('------data-',data[0])
    else:
        data = None
    close_db(conn)
    return data

def get_import_file_name(file_key):   #, routing_number):
    cur, conn = open_db()
    query = "SELECT filename FROM import_files WHERE import_file_key = ?;"  
    log.info(f'{query} {file_key}')
    cur.execute(query, [file_key])
    fetch = cur.fetchall()
    log.info(fetch)
    close_db(conn)
    return fetch   
    
def get_last_date(table, account_name):
    try:
        cur, conn = open_db()
        query = f"SELECT MAX(date) FROM {table} WHERE account='{account_name}'"
        log.info(query)
        cur.execute(query)
        latest_date = cur.fetchone()[0]
        log.info(latest_date)
        return latest_date
    except Exception as ex:
        log.error(f'latest date error {query}')
        log.exception('error %s',ex)
        messagebox.showerror("ERROR", "Failed to get data "+ str(ex))
        return None
    return latest_date   
    
def getSubCatDistinct(category, dateRange=None, table="transactions"):
    #log.info("getSubCatDistinct %s", category)
    try:
        cur, conn = open_db()
        query = "SELECT DISTINCT SubCategory FROM "+table+" WHERE Category='"+category+"'"
        if dateRange:
            query = query + " AND date(date) BETWEEN date('"+dateRange[0]+"') AND date('"+dateRange[1]+"')"
        query = query + " ORDER BY SubCategory;"
        #data, cols, err = sqlQuery(query)
        cur.execute(query, [])
        fetch = cur.fetchall()
        all_data = []
        for data in fetch:
            ad = list(data)[0]
            all_data.append(ad)
        #log.info(all_data)
        #log.info(data)
        return all_data, "", ""
    except Exception as ex:
        log.exception('error %s',ex)
        messagebox.showerror("ERROR", "Failed to get data "+ str(ex))
        return "", "", ex
            
def catItems(cl, dateRange=None):
    #log.info('catItems')
    catList, cols, err = getColumnDistinct('Category', dateRange=dateRange)
    return catList

def sqlDeleteRow(table, iid): 
    try:
        #log.info('sqlDeleteRow %s', iid)
        c, conn = open_db()
        query = "DELETE FROM '"+table+"' WHERE id = ?"
        c.execute(query, (iid,))
        c.fetchall()
       
        close_db(conn)
    except Exception as ex:
        log.exception('error %s',ex)
        messagebox.showerror("ERROR", 'Failed to delete row '+str(ex))
        return "", ex
 
def getTables():
    global gTables
    
    c, conn = open_db()
    query = "SELECT name FROM sqlite_master WHERE type='table';"
    #log.debug('getTables %s', query)
    try:
        c.execute(query)

        fetchall = c.fetchall() 
        if not fetchall:
            raise ValueError(f"No tables exist")
            
        tables = [
            v[0] for v in fetchall
            if v[0] != "sqlite_sequence"
        ]
        log.info(f'gettables {tables}')
        close_db(conn)
        gTables = tables
        return tables
    except Exception as ex:
        log.error(f"An error occurred: {ex}")
        #messagebox.showerror('Error', 'Failed to get tables '+str(ex))
        return ex
        
def getColumnNames(tblName): 
    log.debug('getColumnNames %s',tblName)
    query = "select * from pragma_table_info('"+tblName+"');"
    c, conn = open_db()
    c.execute('PRAGMA table_info('+tblName+')')
    column_names = []
    for row in c.fetchall():
        #print(row[1])
        column_names.append(row[1])
        close_db(conn)
    #log.debug('column names %s',column_names)
    return column_names


def getColumnDistinct(column, dateRange=None, table='transactions'):
    try:
        #log.info(column)
        query = "SELECT DISTINCT "+column+" FROM "+table
        if dateRange:
            query = query + " WHERE date(date) BETWEEN date('"+dateRange[0]+"') AND date('"+dateRange[1]+"')"
        query = query + " ORDER BY "+column+";"
        transactions, column_names, err = sqlQuery(query, [])
        all_data = []
        for data in transactions:
            ad = list(data)[0]
            all_data.append(ad)
            
        return all_data, column_names, err
    except Exception as ex:
        log.exception('error %s',ex)
        messagebox.showerror('Error', 'Failed to get data '+str(ex))
        return "", "", ex

def compute_import_file_key(path):
    
    h = hashlib.sha1()
    with open(path, "rb") as f:
        while chunk := f.read(8192):
            h.update(chunk)
            
    import_file_key = h.hexdigest()[:12]
    
    sqlExecute("INSERT OR IGNORE INTO import_files (import_file_key, filename, imported_at) VALUES (?, ?, datetime('now'))",  (import_file_key, os.path.basename(path)))   
    
    return import_file_key   # short, stable, unique


def import_csv_to_table(table_name):
    """
    Generic CSV importer for any table in the database.
    - Prompts user for CSV file
    - Reads header row
    - Maps CSV columns to table columns
    - Inserts rows using executemany
    """
    try:
        # Pick CSV file
        csv_path = filedialog.askopenfilename(
            title=f"Import CSV into {table_name}",
            filetypes=[("CSV Files", "*.csv"), ("All Files", "*.*")]
        )
        if not csv_path:
            return "No file selected"

        # Get table columns
        table_cols = getColumnNames(table_name) 
        
        if not table_cols:
            messagebox.showerror("ERROR", f"Table '{table_name}' does not exist or has no columns")
            return "error"

        #table_cols.remove("Id")     # Id is usually unique delete if present
        log.info(f'sql cols {table_cols}')
        
        # Read CSV
        with open(csv_path, newline="", encoding="utf-8-sig") as f:
            if table_name == 'transactions':
                reader = csv.DictReader(f, delimiter='|')
            else:    
                reader = csv.DictReader(f, delimiter=',')
            
            csv_cols = reader.fieldnames
            if not csv_cols:
                messagebox.showerror("ERROR", "CSV file has no header row")
                return "error"
            #csv_cols.remove("Id")     # Id is usually unique delete if present
            
            if table_name == 'transactions':
                csv_cols.append('import_file_key')
            
            log.info(f'csv cols {csv_cols}')
            # Determine which CSV columns map to table columns
            mapped_cols = [c for c in csv_cols if c in table_cols]
            log.info(f'mapped cols {mapped_cols}')
            if not mapped_cols:
                #for x in csv_cols:
                #    print('mapped', x, v, table_cols[x])
                
                
                messagebox.showerror(
                    "ERROR",
                    f"No matching columns found.\nCSV columns: {csv_cols}\nTable columns: {table_cols}"
                )
                return "error"

            # Prepare INSERT statement
            placeholders = ",".join(["?"] * len(mapped_cols))
            col_list = ",".join(mapped_cols)
            log.info(col_list)
            log.info(placeholders)
            sql = f"INSERT INTO {table_name} ({col_list}) VALUES ({placeholders})"

            key = None
            if table_name == 'transactions':
                key = compute_import_file_key(csv_path)

            # Build row list
            rows = []
            for row in reader:
                if key:
                    row["import_file_key"] = key
                rows.append([row.get(col, None) for col in mapped_cols])
                log.info(row)
               
 
        # Insert into DB
        cur, conn = open_db()
        with conn:
            log.info(sql)
            cur.executemany(sql, rows)
        close_db(conn)

        messagebox.showinfo("Success", f"Imported {len(rows)} rows into '{table_name}'")
        return

    except Exception as ex:
        log.exception("CSV import error %s", ex)
        messagebox.showerror("ERROR", f"Failed to import CSV: {ex}")
        return str(ex)

def export_table_to_csv(table_name):
    """
    Export any table to a CSV file.
    - Auto-detects columns
    - Exports all rows
    - Writes UTF-8 with BOM for Excel compatibility
    """
    try:
        # Pick save location
        save_path = filedialog.asksaveasfilename(
            title=f"Export '{table_name}' to CSV",
            defaultextension=".csv",
            filetypes=[("CSV Files", "*.csv"), ("All Files", "*.*")]
        )
        if not save_path:
            return "No file selected"

        # Get table columns
        cols = getColumnNames(table_name)
        if not cols:
            messagebox.showerror("ERROR", f"Table '{table_name}' does not exist or has no columns")
            return "error"

        # Query all rows
        query = f"SELECT {','.join(cols)} FROM {table_name};"
        rows, _, err = sqlQuery(query, [])
        if err:
            return err

        # Write CSV
        with open(save_path, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f, delimiter='|', quoting=csv.QUOTE_NONNUMERIC)
            writer.writerow(cols)  # header
            for row in rows:
                writer.writerow(row)

        messagebox.showinfo("Success", f"Exported {len(rows)} rows from '{table_name}'")

        return 

    except Exception as ex:
        log.exception("CSV export error %s", ex)
        messagebox.showerror("ERROR", f"Failed to export CSV: {ex}")
        return str(ex)

"""
def import_transactions_csv():
    return import_csv_to_table("transactions")

def import_accounts_csv():
    return import_csv_to_table("accounts")

def import_patterns_csv():
    return import_csv_to_table("patterns")

def export_transactions_csv():
    return export_table_to_csv("transactions")

def export_accounts_csv():
    return export_table_to_csv("accounts")

def export_patterns_csv():
    return export_table_to_csv("patterns")
"""

#migrate_schema()

if __name__ == "__main__":  
    
   import_transactions_csv()
   
