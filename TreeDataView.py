# https://github.com/vsantiago113/TreeDataView
# https://tkdocs.com/shipman/ttk-Treeview.html
# https://tkdocs.com/tutorial/tree.html

# Python Includes
import tkinter as tk
from tkinter import ttk, font

# 3rd Party Includes
import customtkinter as ctk

#project imports
from theme_manager import theme_manager
from util import clear_all_inside_frame
from treeutils import sortby_column, find_treeview_duplicates
from treeviewsearch import TreeviewSearchAttach, CTkSearchBarAttach
from TreeEvents import TreeEventHandler
from config import fin_config,  TWIDTH, TANCHOR, TSTRETCH
from logging_manager import get_logger
log = get_logger(__name__)

transWidths = fin_config.transWidths

class TreeDataView(tk.Frame):
 
    def __init__(self, parent, headers, height=False, searchbar=False, scrollbar_x=True, scrollbar_y=True, selectmode='extended', left_click=None, right_click=None, double_click=None, sortColumns=True, return_key=None, **options):
        
        self.parent = parent
        tk.Frame.__init__(self, self.parent)
        clear_all_inside_frame(self.parent)
        
        self._to_search = tk.StringVar()
        self._amtTotal = tk.StringVar()      
        self._noRows = tk.IntVar()   
        self._srch_invert = tk.IntVar()         # Search/Filter
        self._detached = set()                  # Search/Filter
        self.show_only_dupes = ctk.BooleanVar(value=False)

        self.headers = headers
        self.sortColumns = sortColumns  
        log.info('Headers %s %s',self.parent.name, headers)
        
        self.table = self.parent.name
        if self.table not in ['transactions', 'accounts', 'patterns', "rules"]: 
            self.table = 'other'
        self.font=font.Font(family='Calibri', size=11)    
               
        self.style = ttk.Style()

        self.style.configure("TreeDataView.Treeview", highlightthickness=0, bd=0, font=self.font) # Modify the font of the body
        self.style.configure("TreeDataView.Treeview.Heading", font=('None', self.font["size"], 'bold')) # Modify the font of the headings

        if selectmode is None:
            pass
        else:
            pass
        #########################################
        # Apply Treeview theme BEFORE creating the widget
        theme_manager.apply_treeview_theme()
        self.tree = ttk.Treeview(self.parent, columns=self.headers, show='headings', selectmode='extended', style="TreeDataView.Treeview") 
        self.tree['columns'] = self.headers
        
        # Bind hover AFTER creation
        #theme_manager.enable_treeview_hover(self.tree)
        # Rebind style explicitly
        #self.tree.configure(style="CTk.Treeview")
        #######################################       
        
        vsb = ttk.Scrollbar(self.parent, orient='vertical', command=self.tree.yview)
        hsb = ttk.Scrollbar(self.parent, orient='horizontal', command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        #self.tree.grid(
        #    row=1,
        #    column=0,
        #    sticky="nsew"
        #)

        if bool(height) is True:
            self.tree.configure(height=height)
        
        #---------------------------------------------
        # Layout
        #
        # Row 0 = Search Bar
        # Row 1 = Treeview
        # Row 2 = Horizontal Scrollbar
        #
        # Col 0 = Content
        # Col 1 = Vertical Scrollbar
        #---------------------------------------------
        self.parent.grid_columnconfigure(0, weight=1)

        self.parent.grid_rowconfigure(
            0,
            weight=0,
            minsize=28
        )

        self.parent.grid_rowconfigure(
            1,
            weight=1
        )

        self.parent.grid_rowconfigure(
            2,
            weight=0
        )

        if searchbar:
            self.searchBar()

        self.tree.grid(
            row=1,
            column=0,
            sticky="nsew"
        )

        if scrollbar_y:
            vsb.grid(
                row=1,
                column=1,
                sticky="ns"
            )

        if scrollbar_x:
            hsb.grid(
                row=2,
                column=0,
                sticky="ew"
            )

        self.sizeColumns()
        self.autosizeColumns()
        
        self.tev = TreeEventHandler(self.parent, self.tree)

        if right_click:
            #log.info('right_click')
            self.tree.bind('<Button-3>', self.tev.popup_menu)
            
        if double_click:
            #log.info('double_click')
            self.tree.bind('<Double-Button-1>', self.tev.double_click)

        self.tree.bind('<Control-plus>', self.scaleUp)
        self.tree.bind('<Control-equal>', self.scaleUp)
        self.tree.bind('<Control-minus>', self.scaleDown)    

        '''
        if return_key:
            self.tree.bind('<Return>', return_key)
        '''           
    # ===== magnify, minimize font ====
    # https://stackoverflow.com/questions/26957845/ttk-treeview-cant-change-row-height
    def scaleUp(self, event):
        self.font['size']+=1
        #log.info('scaleUp %s', self.font['size'])
        self.autosizeColumns()

    def scaleDown(self, event):
        self.font['size']-=1
        #log.info('scaleDown %s', self.font['size'])
        self.autosizeColumns()
      
    def autosizeColumns(self):
        # https://blog.finxter.com/5-best-ways-to-change-ttk-treeview-column-width-and-weight-in-python-3-3/
        self.style.configure("TreeDataView.Treeview", rowheight=self.font.metrics()['linespace'])
        self.style.configure("TreeDataView.Treeview.Heading", font=('None', self.font['size'],'bold')) # Modify the font of the headings
        #log.info(f'{self.table}: {transWidths[self.table]}')
        for col in self.tree['columns']:
            if col in transWidths[self.table]:
                w = transWidths[self.table][col][TWIDTH] * self.font['size']
                self.tree.column(col, width=w)
            #if col == 'Date': log.info('width %s', w)

    def sizeColumns(self):
        #log.info(f'{self.table}: {transWidths[self.table]}')
        for column in self.headers:
            if column in transWidths[self.table].keys():
                w = transWidths[self.table][column][TWIDTH] * self.font['size']
                a = transWidths[self.table][column][TANCHOR]
                s = transWidths[self.table][column][TSTRETCH]
                #log.info('size %s \t%s',column, w)
            else:
                w = 12 * self.font['size']     # width
                a = 'w'     # anchor
                s = True    # stretch
 
            
            if self.sortColumns:
                self.tree.heading(column, text=column, command=lambda c=column: sortby_column(self.tree, c, 1))
            else:
                self.tree.heading(column, text=column)
                
            self.tree.column(column, anchor=a,width=w, stretch=s)

    #=========================================    
    def searchBar(self):
        self.search_engine = TreeviewSearchAttach(
            self.tree,
            self.totalAmtCol
        )

        srchctrl = ctk.CTkFrame(
            self.parent,
            fg_color="transparent",
            corner_radius=0
        )

        srchctrl.grid(
            row=0,
            column=0,
            sticky="ew",
            padx=0,
            pady=0
        )

        srchctrl.grid_columnconfigure(0, weight=1)

        searchbar = CTkSearchBarAttach(
            srchctrl,
            self.search_engine,
            self.tree
        )

        searchbar.pack(
            side="left",
            fill="x",
            expand=True,
            padx=0,
            pady=0
        )

        self.lblTotal = tk.Label(
            srchctrl,
            textvariable=self._amtTotal,
            bg="lightblue",
            fg="black"
        )

        self.lblTotal.pack(
            side=tk.RIGHT,
            padx=2,
            pady=0
        )

        tk.Label(
            srchctrl,
            text="Balance:",
            width=8,
            bg="lightblue"
        ).pack(
            side=tk.RIGHT,
            padx=2,
            pady=0
        )
     
    def colorUpdate(self, *args):
        at = self._amtTotal.get()
        colr = 'Blue'
        if at:
            if float(at) < 0.0:
                    colr = 'red'   
        self.lblTotal.config(fg=colr) 

    def get_all_descendants(self, tree, item=""):
        """Recursively get all children (descendants) for a given item."""
        children = tree.get_children(item)
        for child in children:
            children += self.get_all_descendants(tree, child) # Append grandchildren and further descendants
        return children
        
    def totalAmtCol(self):
        self._noRows.set(len(self.get_all_descendants(self.tree)))
        if "Amount" in self.tree["columns"]:
            amt_col = self.tree["columns"].index("Amount")
            #log.info(amt_col)
            if amt_col:
                amt_sum = 0.0
                for child in self.tree.get_children():
                    if self.tree.item(child, "values")[amt_col]:
                        amt_sum += float(self.tree.item(child, "values")[amt_col])
                self._amtTotal.set(str(round(amt_sum,2))) 
            else:
                self._amtTotal.set("---.--")  

    def expandAll(self, *args):
        for item in self.tree.get_children():
            self.tree.item(item, open=True)

    def collapseAll(self, *args):
        for item in self.tree.get_children():
            self.tree.item(item, open=False)
            
    def showHide(self):
        ##print(len(self.tree["displaycolumns"]),len(self.columns["columns"]))
        if len(self.tree["displaycolumns"]) == len(self.columns["columns"]):
            self.tree["displaycolumns"] = fin_config.table_form["DisplayColumns"]
        else:
            self.tree["displaycolumns"]=self.columns["columns"]
            
    def toggle_duplicates(self):
        # use _brut_searcher to find tag
        #self.show_only_dupes
        children = list(self._detached) + list(self.tree.get_children())
        self._detached = set()
        query = 'duplicate'
        self.search_engine.search(query, columns=None, search_tags=self.show_only_dupes.get(), invert=False)
        #self._brut_searcher(children, query.lower(), tags=self.show_only_dupes.get())
    
    def duplicates_with_file_key(self):    
        dupes = find_treeview_duplicates(self.tree, columns=["Date", "Amount", "Description", "import_file_key"])

        for key, item_ids in dupes.items():
            for iid in item_ids:
                self.tree.item(iid, tags=("duplicate",))
        self.tree.tag_configure("duplicate", background="#FFCCCC")
        
    def duplicates_without_file_key(self):
        dupes = find_treeview_duplicates(self.tree, columns=["Date", "Amount", "Description"])
        #print('dupes', dupes)
        for key, item_ids in dupes.items():
            for iid in item_ids:
                self.tree.item(iid, tags=("duplicate",))
        self.tree.tag_configure("duplicate", background="#FFCCCC")
    
    
    
    #===========================================
    # Built in functions for ttk.TreeView
    def bbox(self, *arg, **kw):
        return self.tree.bbox(*arg, **kw)

    def get_children(self, **kw):
        return self.tree.get_children(**kw)

    def set_children(self, *args):
        self.tree.set_children(*args)

    def column(self, *args, **kwargs):
        #log.info('column %s %s',*args, **kwargs)
        return self.tree.column(*args, **kwargs)
        
    def configure(self, *args, **kwargs):
        return self.tree.configure(*args, **kwargs)

    def delete(self, *arg):
        self.tree.delete(*arg)

    def detach(self, *arg):
        self.tree.detach(*arg)

    def exists(self, *arg):
        return self.tree.exists(*arg)

    def focus(self, **kw):
        return self.tree.focus(**kw)

    def heading(self, *args, **kwargs):
        return self.tree.heading(*args, **kwargs)

    def identify(self, *args):
        return self.tree.identify(*args)

    def identify_row(self, *arg):
        return self.tree.identify_row(*arg)

    def identify_column(self, *arg):
        return self.tree.identify_column(*arg)

    def identify_region(self, *args):
        return self.tree.identify_region(*args)

    def identify_element(self, *args):
        return self.tree.identify_element(*args)

    def index(self, *arg):
        return self.tree.index(*arg)

    def insert(self, *args, **kwargs):
        return self.tree.insert(*args, **kwargs)

    def item(self, *args, **kwargs):
        return self.tree.item(*args, **kwargs)

    def move(self, *args, **kwargs):
        self.tree.move(*args, **kwargs)

    def next(self, *arg):
        return self.tree.next(*arg)

    def parent(self, *arg):
        return self.tree.parent(*arg)

    def prev(self, *arg):
        return self.tree.prev(*arg)

    def reattach(self, *args):
        self.tree.reattach(*args)

    def see(self, *arg):
        self.tree.see(*arg)

    def selection(self):
        return self.tree.selection()

    def selection_set(self, *args):
        self.tree.selection_set(*args)

    def selection_add(self, *args):
        self.tree.selection_add(*args)

    def selection_remove(self, *args):
        self.tree.selection_remove(*args)

    def selection_toggle(self, *args):
        self.tree.selection_toggle(*args)

    def set(self, *args, **kwargs):
        return self.tree.set(*args, **kwargs)

    def tag_configure(self, *args, **kwargs):
        return self.tree.tag_configure(*args, **kwargs)

    def tag_has(self, *arg, **kw):
        return self.tree.tag_has(*arg, **kw)

    def xview(self, *args):
        return self.tree.xview(*args)

    def yview(self, *args):
        return self.tree.yview(*args)

    # Custom Functions
    def insert_data(self, data):
        self.tree.insert('', 'end', values=data)

    def clear(self): 
        for item in self.tree.get_children():
            self.tree.delete(item)

    def get_all_items(self):
        items = []
        for item in self.tree.get_children():
            items.append(self.tree.item(item, 'values'))
        return items
        
   