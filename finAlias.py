
# Python Imports
import tkinter as tk
from tkinter import messagebox
import fnmatch
import logging

# Project Imports
from config import fin_config
import apswSql as sql
from finLists import autoCmplt

def insertifNotExistIntoPatterns(record, tableName='Patterns'):
    # using paramaterized entries because of apostrophes in data
    rc = 1
    try:
        conn, cursor = openDatabase()
        alias = record[0]
        pattern = record[1]
        record[2]
        record[3]
        account = record[4]
        #stmt = "SELECT Alias, Pattern FROM "+tableName+" WHERE Pattern='"+pattern+"'  AND Account='"+account+"'"
        stmt = "SELECT Alias, Pattern FROM "+tableName+" WHERE Pattern=? AND Account=?"

        #data_tuple = (pattern)
        logging.info(' %s', stmt)
        cursor.execute(stmt, (pattern, account,))  #, data_tuple)
        result = cursor.fetchone()
        #print('result ',result,'|')
        logging.info('insert if not %s',result)
        if result is None:   # or duplicate==True:
            # rec = [date, cat[0], r[_NUMBER], r[_TRANSTYPE], amount, cat[1]+':'+cat[2], account, payee]
            stmt = "INSERT INTO "+tableName+" (Alias, Pattern, Category, SubCategory, Account) VALUES (?,?,?,?,?);"
            logging.info('insertifNotExist %s %s',stmt, record)
            cursor.execute(stmt, record)
            commitDatabase()
            logging.info("Data inserted into Combined table")
            rc = 0
        else:
            logging.info('Record already exists %s %s %s', alias, pattern, account)
            messagebox.showerror("Error", message='Pattern '+pattern+' for '+account+' already exists')
            rc = 0   
        
    except sqlite3.Error as error:
        logging.exception("Failed to insert data into table %s", error)
        #m3essageWindow("ERROR", error)
        messagebox.showerror("Error", message=error)
        rc = 1
    finally:
        if (conn):
            logging.info('close connection')
            saveDatabase()
    return rc

class newPattern(object):
   
    def __init__(self, treeRow):
 
        self.treeRow = treeRow
        logging.info('newpattern treerow %s', self.treeRow)
               
        self.win = tk.Toplevel(bg='lightblue')
        self.win.title("Edit Entry")
        self.win.attributes("-toolwindow", True)
        self.win.grid_rowconfigure(0, weight=0)
        self.win.grid_rowconfigure(1, weight=1)
        self.win.grid_columnconfigure(0, weight=1)
        self.win.lift()                  #ensure it appears above all others, probably will do this anyway

        upperFrame = tk.Frame(self.win, bg='lightblue')   #, height=45)
        upperFrame.grid(row=0, column=0, sticky="new", ipadx=5, ipady=1)
        upperFrame.grid_rowconfigure(0, weight=0)
        upperFrame.grid_columnconfigure(0, weight=1)
        
        # build create Alias Frame
        row = 0
        l1 = tk.Label(upperFrame, text="Description",bg='lightblue').grid(row=row, column=0, padx = 5, pady=1)
        tk.Label(upperFrame, text="Alias",bg='lightblue').grid(row=row, column=1, padx = 5, pady=1)
        tk.Label(upperFrame, text="Category",bg='lightblue').grid(row=row, column=2, padx = 5, pady=1)
        tk.Label(upperFrame, text="SubCategory",bg='lightblue').grid(row=row, column=3, padx = 5, pady=1)
        tk.Label(upperFrame, text="Account",bg='lightblue').grid(row=row, column=4, padx = 5, pady=1)
        tk.Label(upperFrame, text="Pattern",bg='lightblue').grid(row=row, column=5, padx = 5, pady=1)
        row+=1
        self.desc = tk.Entry(upperFrame, width=50)
        self.desc.grid(row=row, column=0, padx = 5, pady=1)
        logging.info('*** treerow %s',self.treeRow)
        self.desc.insert(0, self.treeRow['Description'])
        
        self.alias = tk.Entry(upperFrame, width=30)
        self.alias.grid(row=row, column=1, padx = 5, pady=1)
        self.alias.insert(0, self.treeRow['Alias'])

        self.cat = tk.Entry(upperFrame, width=25)
        self.cat.grid(row=row, column=2, padx = 5, pady=1)
        self.cat.insert(0, self.treeRow['Category'])
        self.cat.bind("<Button-1>", lambda event, cat=None: self.update_cat_pat(cat))   
        
        self.subcat = tk.Entry(upperFrame, width=25)
        self.subcat.grid(row=row, column=3, padx = 5, pady=1)
        self.subcat.insert(0, self.treeRow['SubCategory'])
        self.subcat.bind("<Button-1>", lambda event, scat=None: self.update_scat_pat(scat))   
        
        self.account = tk.Entry(upperFrame, width=25)
        self.account.grid(row=row, column=4, padx = 5, pady=1)
        self.account.insert(0, self.treeRow['Account'])
        
        self.pattern = tk.Entry(upperFrame, width=40)
        self.pattern.grid(row=row, column=5, padx = 5, pady=1)
        self.pattern.insert(0, self.treeRow['Pattern'])
        
        row+=1
        descFrame = tk.Frame(upperFrame, bg='lightblue')  #, height=40)
        descFrame.grid(row=row, column=0, columnspan=5)  #, ipady=5, ipadx=5)

        canButt = tk.Button(descFrame, text = "Cancel")
        canButt.pack(side=tk.RIGHT, pady=5, padx=5)
        canButt.bind("<Button-1>", lambda c: self.win.destroy())
        
        okButt = tk.Button(descFrame, text = "Show Result")
        okButt.pack(side=tk.RIGHT, pady=5, padx=5)
        okButt.bind("<Button-1>", self.showResult)

        hdr = ["DescId", "Date", "Description", "Alias", "Category", "SubCategory", "Account"]
        widths = [8,12,60,50,40,40,30]
        anchor = ["e","w","w","w","w","w","w"]
        dupl = {}
        dupl["columns"] = hdr
        dupl["widths"] = widths
        dupl["anchor"] = anchor
        self.patTree = finTree.fTree(self.win, dupl, searchbar=False, height=25, right_click=False, double_click=False)

        row+=1
        lowerFrame = tk.Frame(self.win, bg='lightblue')  #, height=40)
        lowerFrame.grid(row=row, column=0, columnspan=5)  #, ipady=5, ipadx=5)
        
                
        canButt = tk.Button(lowerFrame, text = "Cancel")
        canButt.pack(side=tk.RIGHT, pady=5, padx=5)
        canButt.bind("<Button-1>", lambda c: self.win.destroy())
        #canButt.grid(row=0, column = 3, sticky="e")
        
        #okButt = tk.Button(lowerFrame, text = "Add Pattern")
        #okButt.pack(side=tk.RIGHT, pady=5, padx=5)
        #okButt.bind("<Button-1>", self.add_pattern)
        
        udButt = tk.Button(lowerFrame, text = "Update Pattern")
        udButt.pack(side=tk.RIGHT, pady=5, padx=5)
        udButt.bind("<Button-1>", self.updatePattern)
        #okButt.grid(row=0, column = 1, sticky="e")
        
        okButt = tk.Button(lowerFrame, text = "Update Selected")
        okButt.pack(side=tk.RIGHT, pady=5, padx=5)
        okButt.bind("<Button-1>", self.updateSelected)
        #okButt.grid(row=0, column = 2, sticky="e")

    def update_cat_pat(self, *args):
        catList = {}
        catItems(catList, dateRange=fin_config.daterange)
        cat = autoCmplt.cl(self, catList)
        self.cat.delete(0, 'end')
        self.cat.insert('end', cat)
        if cat:
            self.update_scat_pat(catList[cat])
        
    def update_scat_pat(self, catList):
        if catList:
            scat = autoCmplt.sl(self, catList)
        else:
            catList = {}
            catItems(catList, dateRange=fin_config.daterange)
            cat = self.entC.get()
            scat = autoCmplt.cl(self, catList[cat])
            
        self.subcat.delete(0, 'end')
        self.subcat.insert('end', scat)

    def refresh(self, *args):
        logging.info('refresh %s', self.patTree.get_children())
        try:
            for i in self.patTree.get_children():
                logging.info('delete %s',i)
                self.patTree.delete(i)
        except Exception as e:   # AttributeError:
            logging.warning('Warning %s',e)
            messagebox.showerror("Error", message=e)
        return  
  
    def updatePattern(self, *args):
        rowId = self.treeRow['Id']
        pattern = self.pattern.get()
        alias = self.alias.get()
        category = self.cat.get()
        subcat = self.subcat.get()
        account = self.account.get()

        conn, cursor = openDatabase()
        #stmt = "SELECT Pattern FROM Patterns WHERE Pattern='"+pattern+"'  AND Account='"+account+"';"
        stmt = "SELECT Pattern, Account FROM Patterns WHERE Pattern=? AND Account=?"
        cursor.execute(stmt, (pattern, account,))
        logging.info(' %s', stmt)
        result = cursor.fetchall()
        logging.info(result)
        if result:
            logging.info('updatePattern %s %s %s %s %s',pattern, alias, category, subcat, account)
            stmt = "UPDATE Patterns SET Alias=?, Category=?, SubCategory=?, Account=?, Pattern=? WHERE ID = '"+str(rowId)+"';"
            logging.info('%s %s',stmt, (alias, category, subcat, account, pattern))
            rc = cursor.execute(stmt, (alias, category, subcat, account, pattern,))
            commitDatabase()
            if rc == 0:
                messagebox.showinfo("INFO", "Done")
        else:
            self.add_pattern()

    def add_pattern(self, *args):
        pattern = self.pattern.get()
        alias = self.alias.get()
        category = self.cat.get()
        subcat = self.subcat.get()
        account = self.account.get()
        logging.info('add_pattern %s %s %s %s %s',pattern, alias, category, subcat, account)
        rc = insertifNotExistIntoPatterns((alias, pattern, category, subcat, account))
        if rc == 0:
            messagebox.showinfo("INFO", "Done")
    
    def xupdateSelected(self, *args):
        #self.add_pattern()
        #pattern = self.pattern.get()
        alias = self.alias.get()
        category = self.cat.get()
        subcat = self.subcat.get()
        self.account.get()
        
        conn, cursor = openDatabase()
        
        selected = self.patTree.selection()
        logging.info('selected %s', selected)  
        
        #for parent in self.patTree.get_children():
        for iid in selected:
            row = self.patTree.item(iid)["values"]
            logging.info(row)
            stmt = "SELECT * from Combined WHERE ID = "+str(row[0])+";"    
            sqlrowx = selectStmt(stmt)[0]
            logging.info(sqlrowx)
            stmt = stmt = "UPDATE Combined SET Alias=?"
            record=[]
            record.append(alias)
            #if row[3] == '*':
            stmt = stmt + ", Category=?, SubCategory=?"
            record.append(category)
            record.append(subcat)
            stmt = stmt + " WHERE ID = '"+str(row[0])+"';"
 
 
            #stmt = "UPDATE Combined SET Alias=?, Category=?, SubCategory=? WHERE ID = '"+str(row[0])+"';"
            logging.info('%s %s',stmt, record)
            cursor.execute(stmt, record)
            commitDatabase()
        messageBox("INFO", "Done")
    
    def showResult(self, *args):
        self.refresh()
        logging.info('showResult')
        stmt = "SELECT * FROM Combined;"
        arry = selectStmt(stmt)
        
        #logging.info(arry)
        
        pattern = self.pattern.get().lower().strip()
        alias = self.alias.get()
        category = self.cat.get()
        subcat = self.subcat.get()

        for d in arry:
            descId = d[0]
            date = d[1]
            alias = d[2]
            category = d[6]
            subcat = d[7]
            
            account = d[10].strip()
            desc = d[11].strip()
            #descArry.append([descId, date, desc, alias, category, subcat, account])
            match = fnmatch.fnmatch(desc,pattern)
            if match:
                logging.info('p %s a %s m %s',    pattern,alias, match)
                self.patTree.insert("",'end',text=alias,values=(descId, date, desc, alias, category, subcat, account))

def getAliasOfx(_dict, account):
    description = _dict["Payee"]
                
    data, col, err = sql.sqlQueryDict("select * from Patterns");
    for d in data:
        pattern = d['Pattern']
        match = fnmatch.fnmatch(description,pattern)

        if match and account==d['Account']:
            logging.info('Match %s %s %s %s %s %s', d['Id'],['Pattern'], d['Alias'], d['Category'], d['SubCategory'], d['Account'])
            return [d['Alias'], d['Category'], d['SubCategory']]
            
    #logging.info('No Match')
    return [description, "???", "???"]            

