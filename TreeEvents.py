# https://github.com/vsantiago113/TreeDataView
# https://tkdocs.com/shipman/ttk-Treeview.html
# https://tkdocs.com/tutorial/tree.html

# Python Includes
import tkinter as tk
from tkinter import ttk
from tkinter.messagebox import askyesno
from datetime import datetime
from time import perf_counter

# 3rd party includes
import pyperclip

# Project Includes
import apswSql as sql
from finLists import acCatList, acSubCatList, update_cat, update_scat
import transdata
import progressbar
from util import saveReport2CSV, saveAccounts2MMX, saveAccounts2KMY, saveView2csv
from status_bus import StatusBus
from logging_manager import get_logger
log = get_logger(__name__)

popEvent = None

#==========================================
def table_info(table):
    log.info('table_info %s',table)

    data,  err = sql.sqlPragma('PRAGMA table_info('+table+')') 
    
    row = []
    cols = []
    for i in range(len(data)):
        r = [data[i][1], ""]
        if data[i][4] == None:
            r[1] = ""
        else:
            r[1] = data[i][4]
        if r[0] == 'Date':
            r[1] = datetime.today().strftime('%Y-%m-%d')
        if r[0] in ('Alias', 'Pattern', 'AccountID', 'Sender'):
            r[1] = '--added--'+datetime.now().isoformat(timespec='milliseconds')
        if r[0] == 'Id':
            #continue
            r[1] = ''
        if r[0] == 'Amount':
            r[1] = 00.00
  
        if r[1]:
            if data[i][2] == 'INTEGER':
                r[1] == int(r[1])
            if data[i][2] == 'REAL':
                r[1] == float(r[1])
        ##print('------',i, data[i])        
        cols.append(r[0])
        row.append(r[1])
    return cols, row
    
def add_row(tree, table):
    log.info('add_row %s', table)
    cols, row = table_info(table)

    tags = 'Added'
    new_id = tree.insert('', 'end', values=row, tags=tags)
    #tree.focus(new_id)
    tree.selection_set(new_id)
    save_new_2_db(table, row, cols)

def save_new_2_db(table, row, columns):
    # https://stackoverflow.com/questions/13177324/cant-get-last-row-id
    log.info('save_new_2_db %s',table)
    #log.info('columns %s', columns)
    stmt = "INSERT INTO "+table+" ("
    params = []
    values = " VALUES("
    for i in range(len(columns)):
        if columns[i] == 'Id': 
            #log.info('=Id')
            continue
        stmt = stmt + str(columns[i])+", "
        values = values + '?, '
        params.append(row[i])
        #log.info('%s %s %s', i, columns[i], row[i])
    stmt = stmt[:-2]+")"
    values = values[:-2]+")"
    stmt = stmt+values
    log.info(stmt)
    log.info(params)
    max_id = sql.sqlExecute(stmt, params)
    log.info('max_id %s', max_id)
    tk.messagebox.showinfo("INFO", "Row added Id = "+str(max_id))
    return max_id

def view_row(tree, name):
    import TreeDataView
    #log.info(name)
    winc = tk.Toplevel()
    winc.attributes("-toolwindow", True) 
    winc.wm_attributes("-topmost", True)
    #winc.geometry("300x350")  #width, height
    winc.name = name
    iids = tree.selection()
    iid = iids[0]
    
    winc.title("Row View "+iid)
    
    row = tree.item(iid, 'values')
    tags = tree.item(iid, 'tags')

    if len(iids) > 1:
        tk.messagebox.showinfo(title='Display Row '+str(iids[0]), message='Only the first selection will be shown', icon='info')

    columns = ['Name', 'Value']
    tdv = TreeDataView.TreeDataView(winc,  columns, height=len(row)+3)

    tdv.insert("", "end", values=["iid", iid])

    for x, v in enumerate(row):
        if tree["columns"][x] == "import_file_key": 
            import_key = sql.get_import_file_name(v)
            tdv.insert("", "end", values=[v, import_key])
        else:    
            tdv.insert("", "end", values=[tree["columns"][x], v])
        
    item_iid = tdv.insert("", "end", values=["Tags", tags])
    
    # Get the bounding box for the item
    #bbox = tdv.bbox(item_iid, column=1)
    #log.info(item_iid)
    #if bbox:
    #    # The height is the fourth element (index 3) of the returned tuple
    #    row_height = bbox[3]
    #    log.info(f"The height of the row (iid: {item_iid}) is: {row_height} pixels")
    #else:
    #    log.info("Item is not visible or does not exist.")
    
     
def add_pattern(tree, name):
    log.info('add_pattern %s',name)
    iid = tree.selection()[0]
    trValues = list(tree.item(iid, 'values'))
    treeCols = list(tree["columns"])
    patCols = sql.getColumnNames('Patterns')
    #log.info(trValues)
    #log.info(treeCols)
    #log.info(patCols)
    patRow = []
    for x in range(len(patCols)):
        if patCols[x] == 'Id': 
            patRow.append('')
        if patCols[x] == 'Alias': 
            patRow.append(trValues[treeCols.index('Description')])
        if patCols[x] == 'Pattern': 
            patRow.append(trValues[treeCols.index('Description')])
        if patCols[x] == 'Category': 
            patRow.append('-----')
        if patCols[x] == 'SubCategory': 
            patRow.append('-----')
        if patCols[x] == 'Account': 
            patRow.append(trValues[treeCols.index('Account')])
 
    winc = tk.Toplevel()
    winc.attributes("-toolwindow", True) 
    winc.wm_attributes("-topmost", True)
    #winc.geometry("300x600")  #width, height
    winc.name = 'patterns'
    
    pTree = ttk.Treeview(winc, columns=patCols, show='tree')
    newIid = pTree.insert('', 'end', values=patRow)
    pTree.focus(newIid)
    pTree.selection_set(newIid)
    update_sel_rows(pTree, 'patterns', newRow=True)
    
def update_sel_rows(tree, table, newRow=False):
    log.info('update_sel_rows  %s %s',table, tree.selection())
    # ====== create edit dialog  ====================  
    row = 0
    entx = []
    winc = tk.Toplevel()
    winc.attributes("-toolwindow", True)  
    winc.wm_attributes("-topmost", True)
    #winc.geometry("300x600")  #width, height
    winc.name = table

    selected = tree.selection()  # Returns a tuple of selected item IDs

    if selected:
        winc.title("Edit Rows "+selected[0])
        columns, _ = table_info(table)
        values = tree.item(selected[0], 'values')
        tags = tree.item(selected[0], 'tags')
    else:
        winc.title("Edit Rows")
        columns, values = table_info(table)
        tags = 'added'

    #log.info('Building 2 col tree columns %s %s %s', selected, values, tags)
    centry = None  # Category Entry
    sentry = None   # SubCategory Entry
    
    for idx, _ in enumerate(values):
        #log.info('columns %-2s %-14s %-8s',idx,columns[idx], values[idx])
        chkVar = tk.BooleanVar()
        chkVar.set(newRow)      # set checked or unchecked

        tk.Label(winc, text = columns[idx]).grid(row=row, column=1, sticky='w')
        entx.append(ttk.Entry(winc, width = 30))   #.grid(row = row, column = 2))
        entx[idx].grid(row = row, column = 2, padx=(10, 5), pady=(10, 0))  
        if columns[idx] == "Category":
            centry = entx[idx]
        if columns[idx] == "SubCategory": 
            sentry = entx[idx]
        
        #left,right  top,bottom
        entx[idx].insert(0, values[idx])
        if columns[idx] != "Id":
            ttk.Checkbutton(winc, variable=chkVar, command=lambda e=entx[idx], c=chkVar: on_checkbox_change(e, c) ).grid(row=row, column=0, padx=5)

        if newRow: 
            state="enabled" 
        else: 
            state="disabled"
        entx[idx]['state'] = state
        row+=1
        
    for idx in columns:  
        if idx == "Category":
            centry.bind("<Button-1>", lambda event, entry=centry, scentry=sentry: update_cat(entry, scentry))

        if idx == "SubCategory": 
            sentry.bind("<Button-1>", lambda event, scentry=sentry, scat=None: update_scat(scentry, scat))

    separator = ttk.Separator(winc, orient=tk.HORIZONTAL)
    separator.grid(row=row, column=0, columnspan=3, pady=(10, 0),sticky='ew')
    row+=1
    # for tags row
    chkVar = tk.BooleanVar()
    chkVar.set(newRow)      # set checked or unchecked  
    tk.Label(winc, text = 'Tags').grid(row=row, column=1, sticky='w')
    entx.append(ttk.Entry(winc, width = 30))   #.grid(row = row, column = 2))
    tgx = len(entx)-1

    entx[tgx].grid(row = row, column = 2, padx=(10, 5), pady=(10, 0))  #left,right  top,botom
    entx[tgx].insert(0, tags)
    ttk.Checkbutton(winc,variable=chkVar, command=lambda e=entx[tgx], c=chkVar: on_checkbox_change(e, c) ).grid(row=row, column=0, padx=5)
    entx[tgx]['state'] = "disabled"
    row+=1

    okBtn = tk.Button(winc, text = "Update Row(s)", command=lambda t=tree, c=columns, e=entx, a=newRow: save_sel_rows(t,c,  e, a))
    okBtn.grid(row = row, column = 1)

    canBtn = tk.Button(winc, text = "Cancel")
    canBtn.bind("<Button-1>", lambda c: winc.destroy())
    canBtn.grid(row = row, column = 2, padx=1, pady=10)

    def on_checkbox_change(entry, cbs):
        log.info('oncheckboxchange %s',cbs.get())
        if cbs.get():
            entry['state'] = "enabled"
        else: 
            entry['state'] = "disabled"
    '''
    def update_cat(entC, entS):
        log.info('update_cat %s', entS)
        catList, _, _ = sql.getColumnDistinct('Category')
        cat = acCatList(catList)
        
        entC.delete(0, 'end')
        entC.insert('end', cat)
        if cat:
            update_scat(entS, cat)
   
    def update_scat(entS, cat):
        log.info('updatesubcat %s', cat)
        scatList, _, _ = sql.getSubCatDistinct(cat)
        scat = acSubCatList(scatList)
        entS.delete(0, 'end')
        entS.insert('end', scat)
    '''
    def save_2_db(table_name, _id, row):
        log.info('save_2_db %s %s %s',newRow, table_name, _id)
        log.info(row)
        stmt = "Update "+table_name+" SET "
        params = []
        for i in range(len(row)):
            stmt = stmt + row[i][0]+" = ?, "
            params.append(row[i][1])
        
        stmt = stmt[:-2]
        params.append(_id)
        stmt = stmt + " WHERE Id = ?;"
        log.info(stmt)
        log.info(params)
        sql.sqlExecute(stmt, tuple(params))
 
    def save_sel_rows(tree, columns, entry, newRow=False):
        try:
            log.info('save_sel_rows %s',tree.selection())
            selected = tree.selection()
           
            if 'Id' in columns:
                colIdx = columns.index('Id')
            else:
                colIdx = None
  
            ask_msg = False
            ask_msg = tk.messagebox.askyesnocancel (title="Update Row(s) ", message='Are you sure you want to\nupdate the selected item(s)?', icon='question')
            #log.info(ask_msg)
            if ask_msg is True:
                pb = progressbar.ProgressBarPR(title='Batch Classifier', steps=len(selected))
                for _, iid in enumerate(selected):
                    #log.info('%s %s', iid, ask_msg)
                    values = tree.item(iid, 'values')
                    newVal = list(values)
                    row = []
                    #log.info(values)
                    
                    for x, _ in enumerate(values):
                        #log.info('%s %s %s',x, entry[x]['state'],entry[x].get())
                        if str(entry[x]['state']) == "enabled":
                            row.append([columns[x], entry[x].get()])
                            newVal[x] = entry[x].get()

                    tree.item(iid, values=newVal)
                    if newRow:
                        save_new_2_db(winc.name, row) # table, Id, values
                    else:
                        save_2_db(winc.name, values[colIdx], row) # table, Id, values
                        
                    if pb.progress():   # <-- returns True when done or cancelled
                        break
                pb.close()  # <-- ALWAYS closes cleanly  
                
            winc.destroy()
        except Exception as ex:
            log.exception("Failed %s",ex)
            tk.messagebox.showerror("Error", str(ex))

class TreeEventHandler:
    def __init__(self, parent, tree):
    
        self.tree = tree
        self.parent = parent
        self.table = parent.name
        
        # Right Click Pop-up Menu
        self.right_click_menu = tk.Menu(self.tree, tearoff=0)
        self.right_click_menu.add_command(label='Copy', command=self.copy_to_clipboard)
        self.right_click_menu.add_command(label='Delete Row(s)', command=self.delete_rows)
        self.right_click_menu.add_command(label='View row', command=lambda: view_row(self.tree, self.table))
        self.right_click_menu.add_command(label='Update Selected', command=lambda: update_sel_rows(self.tree, self.table))
        
        self.right_click_menu.add_command(label='Add Row', command=lambda: add_row(self.tree, self.table))
        self.right_click_menu.add_command(label='Add Row to Patterns', command=lambda: add_pattern(self.tree, self.table))
        self.right_click_menu.add_command(label='Save View', command=self.save_view)
        self.right_click_menu.add_command(label='Export to Money Manager EX', command=self.save2mmx) 
        self.right_click_menu.add_command(label='Export to KMyMoney', command=self.save2kmy)
        self.right_click_menu.add_command(label='Save for reports', command=self.save_report)
        #saveView2csv(tree, colNames, outfile, summary=False, level=3)
        #saveReport2CSV(tree, rptCol, colNames
        #saveAccounts2KMY(tree, rptCol, colNames)
    
    def save_report(self):
        try:
            rptCol= self.tree["columns"].index('Account')
        except ValueError:
            rptCol = -1
        saveReport2CSV(self.tree, rptCol, self.tree["columns"])    
    
    def save_view(self, *args):
        curItem = self.tree.focus()
        #for item in self.tree.get_children():
        #    #print(self.tree.item(item))
        saveView2csv(self.tree) 
        
    def save2mmx(self):
        try:
            rptCol= self.tree["columns"].index('Account')
        except ValueError:
            rptCol = -1
        saveAccounts2MMX(self.tree, rptCol, self.tree["columns"])
        
    def save2kmy(self):
        try:
            rptCol= self.tree["columns"].index('Account')
            log.info(self.tree["columns"])
            log.info(rptCol)
        except ValueError:
            rptCol = -1
            
        saveAccounts2KMY(self.tree, rptCol, self.tree["columns"])

    def copy_to_clipboard(self):
        global popEvent
        column = self.tree.identify_column(popEvent.x)
        log.info('copy_to_clipboard %s', column)
        selitem = self.tree.selection()
        if selitem:
            text = self.tree.item(selitem[0], 'values')
            cell = int(column[1]) - 1
            popEvent = None
            pyperclip.copy(text[cell])
        else:
            tk.messagebox.showwarning('Warning', 'Please make a selection and try again!')
            
    def double_click(self, event):
        log.info('double_click')
        self.tree.identify_row(event.y)
        column = self.tree.identify_column(event.x).replace("#","")
        selitems = self.tree.selection()
        if selitems:
            if (self.tree["displaycolumns"] == self.tree["columns"]):
                treecol = self.tree["displaycolumns"]
                cell = int(column)-1
            else:
                treecol = self.tree["columns"]
                cell = int(column)
                
            #treecol = self.tree["columns"]
            #cell = int(column[1])-1
            selitem = selitems[0]
            text = list(self.tree.item(selitem, 'values'))[cell]

            column_name = treecol[cell]
            #log.info(f'id:{rowid}, cell:{cell}, column:{column}, column name:{column_name}:{text}') 
            if "'" in text:
                text = text.replace("'","''")
   
            query = f"SELECT * from {self.table} WHERE {column_name} LIKE '{text}'"

            data, cols, err = sql.sqlQuery(query)
            transdata.ShowTransactions(None, daterange=None, table=self.table,  dataList=data, columns=cols )
 
    def popup_menu(self, event):
        global popEvent
        popEvent = event    
        log.info('popup_menu')
 
        sel_ids = self.tree.selection()
        if not sel_ids:     # if not selected, select row under mouse
            sel_ids = self.tree.identify_row(event.y)
            if not sel_ids:
                pass  
        #log.info('selected %s', sel_ids)
        self.tree.selection_set(sel_ids)
        self.right_click_menu.post(event.x_root, event.y_root)

    #def get_row_data(self):
    #    rowPopup(self.tree)

    def delete_rows(self):
        iids = self.tree.selection()
        log.info('delete_rows %s ...', iids[:5])

        answer = askyesno(message='Delete ' + str(len(iids)) + ' items?')

        if answer is True:

            start = perf_counter()

            pb = progressbar.ProgressBarPR(
                title='Delete Rows',
                steps=len(iids)
            )

            deleted = 0

            try:
                for iid in iids:

                    value = self.tree.item(iid, 'values')

                    self.tree.delete(iid)
                    sql.sqlDeleteRow(self.table, value[0])

                    deleted += 1

                    if pb.progress():
                        break

            finally:
                pb.close()

                #msg = (
                #    f"Deleted {deleted:,} rows "
                #    f"from {self.table} in {elapsed:.3f}s"
                #)

                #log.info(msg)
                #StatusBus.info(f"Deleted {deleted:,} rows "
                #    f"from {self.table} in {elapsed:.3f}s")
                StatusBus.update_perf(f"Deleted {deleted:,} rows ", perf_counter() - start)  