
# Python Includes
import os, sys
import tkinter as tk
from time import perf_counter

# 3rd Party Includes
import apswSql as sql

# Project Includes
from treeutils import sortby_column
from theme_manager import theme_manager   # your global instance
from status_bus import StatusBus
from logging_manager import get_logger
log = get_logger(__name__)

printdatabymonth = False
printcolumntodict = True
printtotalbycolumn = False
printtree = False

def getAncestry(tree):
    #log.info('============= Get Ancestry ==========')
    if tree.selection():
        item_iid = tree.selection()[0]
        parent_iid = tree.parent(item_iid)
        gparent_iid = tree.parent(parent_iid)
        ggparent_iid = tree.parent(gparent_iid)
        
        ct = tree.item(item_iid)['text'] 
        if ct:
            ggt = tree.item(ggparent_iid)['text']
            gt = tree.item(gparent_iid)['text']
            pt = tree.item(parent_iid)['text']  
        else:
            ggt1 = tree.item(ggparent_iid)['values']
            gt1 = tree.item(gparent_iid)['values']
            pt1 = tree.item(parent_iid)['values'] 
            ct1 = tree.item(item_iid)['values']

            ct = ct1[0] if len(ct1)>0 else ct1 
            pt = pt1[0] if len(pt1)>0 else pt1 
            gt = gt1[0] if len(gt1)>0 else gt1 
            ggt = ggt1[0] if len(ggt1)>0 else ggt1 
            
        log.info(f'=== Ancestry {ggt}:{gt}:{pt}:{ct}')
        #log.info('==== Ancestry ggtext:%s gtext:%s ptext:%s ctext:%s',ggt,gt, pt, ct)
        return ggt, gt, pt, ct
    else:
        return "","","",""
        
def doQuery(table='transactions', alias=None, _type=None, category=None, subcat=None, account=None, tags=None, dateRange=None):
    stmtData = []
    dataSort = []
    cols = []
    log.info('doquery  %s %s %s',table, alias, _type)
    try:
        #conn, cursor = openDatabase()
        if table == 'transactions':
            stmt = "SELECT * FROM transactions"

            if  alias:    # != None:
                alias = alias.replace("'", "''");
                stmtData.append(" Alias LIKE '"+alias+"'")
                stmtData.append(' AND' )
            if  _type:    # != None:
                stmtData.append(" Type LIKE '%"+_type+"%'")
                stmtData.append(' AND' )
            if  category:   # != None:
                stmtData.append(" Category LIKE '%"+category+"%'")
                stmtData.append(' AND' )
            if  subcat:   # != None:
                stmtData.append(" SubCategory LIKE '%"+subcat+"%'")
                stmtData.append(' AND' )
            if  account:    # != None:
                stmtData.append(" Account LIKE '%"+account+"%'")
                stmtData.append(' AND' )
            if  tags:    # != None:
                stmtData.append(" Tags LIKE '%"+tags+"%'")
                stmtData.append(' AND' )
            if dateRange:
                stmtData.append(" date(date) BETWEEN date('"+dateRange[0]+"') AND date('"+dateRange[1]+"')")   
                stmtData.append(' AND' )

            apdata = ''
            if len(stmtData) > 0:
                apdata = ' WHERE '
            del stmtData[-1]
            for d in stmtData:
                apdata = apdata + d   

            stmt = stmt + apdata + ";"
            #log.info('doQuery %s',stmt)

            data, cols, err = sql.sqlQuery(stmt)
            #log.info("data len  %s", len(data))
            if data:
                #log.info("data %s", data[0])  
                if table == 'transactions':
                    dataSort = sorted(data, key=lambda x: x[1])   # sort by date
                else:
                    dataSort = sorted(data, key=lambda x: x[1])   # sort by col 1
            
        else:
            cols = []
            
    except Exception as ex:
        log.exception("Failed %s",ex)
        tk.messagebox.showierror("Error", ex)
    
    return data , cols  #data_sort   

def ShowTransactions(win, daterange=None, table="transactions", dataList=None, columns=[] ):
    from TreeDataView import TreeDataView
    log.info("ShowTransactions  %s",table)
    try:
        start = perf_counter()
        if not win:
            win = tk.Toplevel()
            win.title("All Table="+table)
            win.attributes("-toolwindow", True)  
            win.geometry("800x400")  #width, height
            win.deiconify()
            win.lift()
            win.focus_force()

        win.name = table

        amtCol = -1
        hover = False
        if "Amount" in columns:
            amtCol = columns.index("Amount")
            hover = True
                                         
        # Apply Treeview theme BEFORE creating the widget
        #theme_manager.apply_treeview_theme()                
              
        tree = TreeDataView(win, columns, searchbar=True, hover=hover, right_click=True, double_click=True, left_click=False, show='headings')
        
        # Bind hover AFTER creation
        #theme_manager.enable_treeview_hover(tree)
        #tree.configure(style="CTk.Treeview")        # Rebind style explicitly
        
        tree.sizeColumns()

        tree.tag_configure('oddrow', background="#eaffff")  #, foreground="#400000") 
        tree.tag_configure('evenrow', background="#ddeeff")  #, foreground="#004000") 
        tree.tag_configure('neg', foreground="darkred")
        
        tag = 'oddrow'
        
        
        for val in dataList:
            if 'evenrow' in tag:
                tag1 = 'oddrow'
            else:
                tag1 = 'evenrow'
            if amtCol > -1:
                if float(val[amtCol]) < 0.0:
                    tag1 = tag1+',neg'
                    val[amtCol] = format(val[amtCol], '.2f')
                
            tag = tuple(tag1.split (","))
            iid = tree.insert('', 'end', values=(val),tags=tag)
        tree.totalAmtCol()
        sortby_column(tree, 1, 0)
        
        elapsed = perf_counter() - start
        
        msg = (
            f"ShowTransactions {len(dataList):,} rows "
            f"for {table} in {elapsed:.3f}s"
        )

        StatusBus.update_perf('ShowTransactions '+table, elapsed) 
        return tree
        
    except Exception as ex:
        log.exception('error %s',ex)
        message =  type(ex).__name__, str(ex), 'In', os.path.basename(__file__), 'On Line', ex.__traceback__.tb_lineno
        tk.messagebox.showerror("ERROR", message)

    