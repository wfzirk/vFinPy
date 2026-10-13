""" copilot
with python, apsw and tcl treeview show hierarchaial tree with each column being a month with category as first level, subcategory as 2nd level and alias as third level and present in hierarchical treeview. alias contains an array of floats. 
Each Category row and column is to be totaled. with final totals and totals for each category.
Each SubCategory row and column is to be totaled. with final totals and totals for each SubCategory, 
Each Alias row and column is to be totaled. with final totals and totals for each alias.
Add grand total row at end of tree.
add scrollbars and expand collapse buttons

read data from sqlite database

Use class instead of functions
"""
"""
Design Highlights
- Class-based encapsulation for modularity
- Lazy data hydration to scale with large data sets
- Recursive hierarchy aggregation
- Scrollbar + expand/collapse support
- Grand total row rendered at bottom
"""
"""
CREATE TABLE finance (
    category TEXT,
    subcategory TEXT,
    alias TEXT,
    month INTEGER, -- 0-based index (e.g., 0=January)
    value REAL
);
"""
# Python imports

import tkinter as tk
from tkinter import ttk
from collections import defaultdict
from datetime import datetime
import logging

#Project imports
from transdata import getAncestry, ShowTransactions, doQuery
from util import clear_all_inside_frame, saveView2csv
from TreeEvents import view_row

gDateRange = []

def treeSettings(tree):
    tree.tag_configure('lvl0', background='#ecfaff', foreground='#004000', font=('Calibri', 11,  'bold')) 
    tree.tag_configure('lvl1', background='#ecfaff', foreground='#004b00', font=('Calibri', 11,  'normal')) 
    tree.tag_configure('lvl2', background='#ecfaff', foreground='#316249', font=('Calibri', 10,  'normal')) 
    
    tree.tag_configure('grand-total', background='#ecfaff', foreground = '#000000', font=('Calibri', 12,  'bold'))
    
#def editAlias(alias):
#    #print('editAlias %s', alias)

def noMonths(d1, d2):
    ##print('nomonths',d1,d2)
    st_date = datetime.strptime(d1, "%Y-%m-%d")
    end_date = datetime.strptime(d2, "%Y-%m-%d")

    ##print('calc',st_date.year, end_date.year, st_date.month, end_date.month)

    months = (end_date.year - st_date.year) * 12 + (end_date.month - st_date.month)
    months += 1
    return months

def catHeader(dateRange):
    stYear = datetime.strptime(dateRange[0], "%Y-%m-%d").year
    stMonth = datetime.strptime(dateRange[0], "%Y-%m-%d").month
    months = []
    #logging.info('stMonth: %s stYear: %s noMonths: %s',stMonth, stYear, noMonths)
    for i in range(noMonths(dateRange[0], dateRange[1])):
        if stMonth > 12:
            stMonth = 1
            stYear += 1
        ##print(i, stMonth, stYear)
        months.append(str(stYear)+'-'+str(stMonth)) 
        stMonth += 1 

    return months #+ ["Row Total"]
    #logging.info(self.months)

class CatEventHandler: 
    def __init__(self, parent, tree):
    
        self.tree = tree
        self.parent = parent
        self.table = parent.name
        
        # Right Click Pop-up Menu
        self.right_click_menu = tk.Menu(self.tree, tearoff=0)
        self.right_click_menu.add_command(label='Copy', command=self.copy_to_clipboard)
        self.right_click_menu.add_command(label='View row', command=lambda: view_row(self.tree, self.table))
        self.right_click_menu.add_command(label='Edit Alias', command=lambda: editAlias(self.tree, self.table))
        self.right_click_menu.add_command(label='Save View', command=lambda: saveView2csv(self.tree))
         
    def copy_to_clipboard(self):
        global my_event
        column = self.tree.identify_column(my_event.x)
        selitem = self.tree.selection()
        if selitem:
            text = self.tree.item(selitem[0], 'values')
            cell = int(column[1]) - 1
            my_event = None
            pyperclip.copy(text[cell])
        else:
            messagebox.showwarning('Warning', 'Please make a selection and try again!')
            
    def double_click(self, event):
        #def doQuery(table= 'transactions', alias=None, _type=None, category=None, subcat=None, account=None, tags=None, dateRange=None):
        logging.info('------ double_click')
        ggtext, gtext, ptext, ctext = getAncestry(self.tree)
        data = []
        if ggtext:
            pass
        
        elif gtext == '???':
            data, cols = doQuery(alias=ctext, dateRange=gDateRange)
        elif ptext == '???':
            data, cols = doQuery(alias=ctext, dateRange=gDateRange)
        elif gtext:
            data, cols = doQuery(category=gtext, subcat=ptext, alias=ctext, dateRange=gDateRange)
        elif ptext:
            data, cols = doQuery(category=ptext, subcat=ctext, dateRange=gDateRange)
        elif ctext:
            data, cols = doQuery(category=ctext, dateRange=gDateRange)
        else:
            messagebox.showwarning('Warning', 'Please make a selection and try again!')
        if data:
            winc = tk.Toplevel()
            winc.attributes("-toolwindow", True)  
            winc.geometry("1000x400")
            ShowTransactions(winc, gDateRange, table="transactions", dataList=data, columns=cols)

    def right_click_func(self):
        global my_event
        logging.info('right_click_function')
        column = self.tree.identify_column(my_event.x)
        selitem = self.tree.selection()
        logging.info(self.parent.name)
        if selitem:
            text = self.tree.item(selitem[0], 'values')
            cell = int(column[1]) - 1
            my_event = None
            #print(text)
            #print(cell)
        else:
            messagebox.showwarning('Warning', 'Please make a selection and try again!')

    def popup_menu(self, event):
        global my_event
        my_event = event
        row_id = self.tree.identify_row(event.y)
        self.tree.selection_set(row_id)
        self.right_click_menu.post(event.x_root, event.y_root)

class ByMonthTreeApp:
    def __init__(self, parent, data, noMonths, right_click=True, double_click=True):
        
        clear_all_inside_frame(parent)

        self.parent = parent
        
        self.months = catHeader(gDateRange)
        self.columns = self.months + ["Row Total"]
        
        
        
        #self.searchBar()
        self.tree = self.create_tree()
        self.cev = CatEventHandler(parent, self.tree)
        if right_click:
            self.tree.bind('<Button-3>', self.cev.popup_menu)
        if double_click:
            self.tree.bind('<Double-Button-1>', self.cev.double_click)
        
        treeSettings(self.tree)

        self.data = data
        
        self.populate_tree()

    def create_tree(self):
        frame = ttk.Frame(self.parent)
        frame.pack(fill="both", expand=True)
 
        self.style = ttk.Style()
        self.style.configure("ftree.Treeview",  indent=25 , bd=0)
        
        tree = ttk.Treeview(
            frame,
            columns=self.columns,
            show="tree headings",
            yscrollcommand=lambda f, l: vsb.set(f, l),
            xscrollcommand=lambda f, l: hsb.set(f, l)
        )

        vsb = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
        hsb = ttk.Scrollbar(frame, orient="horizontal", command=tree.xview)

        tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        
        frame.grid_rowconfigure(0, weight=1)
        frame.grid_columnconfigure(0, weight=1)

        for col in self.columns:
            ##print('----------',col, self.columns[0])
            anchor = "e"
            tree.heading(col, text=col, anchor="center")
            tree.column(col, anchor=anchor, width=100)
        tree.heading("#0", text="By Cat", anchor="center")
        
        return tree
    
    def searchBar(self):
        self._to_search = tk.StringVar()
        self._srch_invert = tk.IntVar()         # Search/Filter
        self._detached = set()                  # Search/Filter
        
        srchFrame = tk.Frame(self.parent, bg='lightblue', height=20)
        #srchFrame.grid(row=0, column=0, sticky="ew")
        srchFrame.pack(fill="x")
        #srchFrame.grid_rowconfigure(0, weight=1)
        #srchFrame.grid_columnconfigure(0, weight=1)
        
        tk.Label(srchFrame, text="Search:").pack(side=tk.LEFT, padx=(10, 5))

        self.srchEnt = ttk.Entry(srchFrame, textvariable=self._to_search)
        self.srchEnt.pack(side="left", fill="x", expand=True, padx=(0, 5))

        
        self.srchEnt.bind('<Return>', self._columns_searcher)
        self.srchEnt.bind('<KeyRelease>', self._columns_searcher)
        self.srchEnt.bind('<Escape>', self.clearSrchEntry)
        
        self.srchCB = tk.Checkbutton(srchFrame, text='Invert',variable=self._srch_invert, onvalue=1, offvalue=0, command=self.toggle_srch) 
        self.srchCB.pack(side="left", padx=(0, 5)) 
        self.rstBtn = tk.Button(srchFrame, text='Clear', command=self.clearSrchEntry)
        self.rstBtn.pack(side="left", fill="x", expand=False, padx=(0, 5))
        
        #========== expand collapse buttons =============
 
        expand_btn = ttk.Button(srchFrame, text="Expand All", command=self.expand_all)
        expand_btn.pack(side="left", padx=(10, 5))

        collapse_btn = ttk.Button(srchFrame, text="Collapse All", command=self.collapse_all)
        collapse_btn.pack(side="left")

    def populate_tree(self):
        grand_totals = [0.0] * len(self.months)
        logging.info('populate_tree')
  
        for cat, subcats in self.data.items():
            tag = 'lvl0'
            cat_totals = [0.0] * len(self.months)
            
            cat_id = self.tree.insert("", "end", text=cat, values=[""] * (len(self.months)+1), open=False, tags=(tag,))

            for subcat, aliases in subcats.items():
                tag = 'lvl1'
                sub_totals = [0.0] * len(self.months)
                subcat_id = self.tree.insert(cat_id, "end", text=subcat, values=[""] * (len(self.months)+1), open=False, tags=(tag,))
                
                for alias, values in aliases.items():
                    tag = 'lvl2'
                    row_total = sum(values)
                    tag1 = "highlight" if row_total > 200 else ""  # Change threshold as needed

                    self.tree.insert(subcat_id, "end", text=alias,
                        values=[f"{v:.2f}" for v in values] + [f"{row_total:.2f}"], tags=(tag,tag1))
                    sub_totals = [x + y for x, y in zip(sub_totals, values)]
                fsub_totals = ['%.2f' % elem for elem in sub_totals] 
                sub_row_total = sum(sub_totals)

                for x, col in enumerate(self.columns):
                    if col == "Row Total": break
                    #logging.info('%s %s',x, col)
                    self.tree.set(subcat_id, col, fsub_totals[x])
  
                self.tree.set(subcat_id, 'Row Total', sub_row_total)

                cat_totals = [x + y for x, y in zip(cat_totals, sub_totals)]
            fcat_totals = ['%.2f' % elem for elem in cat_totals]    # display 2 decimal places 
            cat_row_total = round(sum(cat_totals), 2)
            
            for x, col in enumerate(self.columns):
                if col == "Row Total": break
                self.tree.set(cat_id, col, fcat_totals[x])
 
            self.tree.set(cat_id, 'Row Total', cat_row_total)

            grand_totals = [x + y for x, y in zip(grand_totals, cat_totals)]
            
        grand_row_total = sum(grand_totals)
        self.tree.insert("", "end", text="_Grand Total",
            values=[f"{v:.2f}" for v in grand_totals] + [f"{grand_row_total:.2f}"],
            tags=("grand-total",))

    #==== search filter bar =========
    def toggle_srch(self, *args):
        query = self.srchEnt.get()
        children = list(self._detached) + list(self.tree.get_children())
        self._detached = set()
        self._brut_searcher(children, query.lower())
        
    def _columns_searcher(self, event):
        #              originally a set            returns a tuple
        children = list(self._detached) + list(self.tree.get_children())
        self._detached = set()
        query = self._to_search.get()
        self._brut_searcher(children, query.lower())
    
    def _brut_searcher(self, children, query):
        #logging.info('_brut_searcher %s', children)
        i_r = -1
        for item_id in children:
            textStr = self.tree.item(item_id)['text']
            if not textStr:
                textStr = self.tree.item(item_id)['values'] # already contains the string-concatenation (over columns) of the row's values
            txt = [str(i) for i in textStr]    
            #logging.info(textStr)
            txt = ' '.join(txt)
            text = txt.lower()
            qArry = query.split(' ')
            found = False
            for q in qArry:
                if q in text:
                    found = True
                if q not in text:
                    found = False   
                    break
                    
            if self._srch_invert.get():        
                if not found:
                    i_r += 1
                    self.tree.reattach(item_id, '', i_r)
                else:
                    self._detached.add(item_id)
                    self.tree.detach(item_id)
            else:
                if found:
                    i_r += 1
                    self.tree.reattach(item_id, '', i_r)
                else:
                    self._detached.add(item_id)
                    self.tree.detach(item_id)
                    
    def clearSrchEntry(self, *args):
        self.srchEnt.delete(0, 'end')
        self._columns_searcher('')
        #self.heading(searched=True)
        
    #========== expand collapse funtions =============
    def expand_all(self):
        def _expand(node):
            self.tree.item(node, open=True)
            for child in self.tree.get_children(node):
                _expand(child)
        for item in self.tree.get_children():
            _expand(item)

    def collapse_all(self):
        def _collapse(node):
            self.tree.item(node, open=False)
            for child in self.tree.get_children(node):
                _collapse(child)
        for item in self.tree.get_children():
            _collapse(item)
            
#------- debug -------
def byMonthDb(treeFrame, db_path):
    def load_data():
        conn = apsw.Connection("finance.db")
        cursor = conn.cursor()
        query = """SELECT category, subcategory, alias, month, value FROM finance"""
        results = defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: [0.0]*12)))

        for category, subcat, alias, month, value in cursor.execute(query):
            results[category][subcat][alias][int(month)] += value
            ##print(results)
            break
        return results

    FinanceTreeApp(treeFrame, load_data(), 12)
#-------------------- 
'''
def xnoMonths(d1, d2):
    ##print('nomonths',d1,d2)
    st_date = datetime.strptime(d1, "%Y-%m-%d")
    end_date = datetime.strptime(d2, "%Y-%m-%d")

    ##print('calc',st_date.year, end_date.year, st_date.month, end_date.month)

    months = (end_date.year - st_date.year) * 12 + (end_date.month - st_date.month)
    months += 1
    return months
'''
def byMonth(treeFrame, data, dateRange):
    global gDateRange
    gDateRange = dateRange
    
    stDate = dateRange[0]
    months = noMonths(stDate, dateRange[1])

    results = defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: [0.0]*months)))
    #print('----------results', results)
    for category, subcat, alias, date, amount, account in data:
        if category == None: category = "???"
        if subcat == None: subcat = "???"
        mnth = noMonths(stDate, date)
        results[category][subcat][alias][mnth-1] += amount

    treeFrame.name = 'transactions'
    fta = ByMonthTreeApp(treeFrame, results, months)
    fta.collapse_all()   
        
