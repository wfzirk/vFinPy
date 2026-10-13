
# Python Includes
import sys
import tkinter as tk
from tkinter import ttk, messagebox
from collections import defaultdict
import re
from time import perf_counter

# 3rd Party Includes
import customtkinter as ctk


# Project Includes
from theme_manager import theme_manager
import apswSql as sql
from config import fin_config
from finrules.rules_console_app import RulesConsoleApp
from transdata import getAncestry, ShowTransactions, doQuery
from bymonth import byMonth
from yearly import ByYear, DataModel
from monthly import MonthlyHierarchyApp
from category_report_panel import CategoryReportPanel
from status_bus import StatusBus
from logging_manager import get_logger
log = get_logger(__name__)

#==========================
#  find duplicates in data
#==========================
def find_dupes(_data):
    def normalize_desc(desc):
        """
        Extract store number + city, aggressively normalized.
        """
        d = desc.upper()

        m = re.search(r"#(\d+)\*?\s*(.*)", d)
        if not m:
            return d.strip()

        store = m.group(1)

        # Normalize city: letters only, first 4 chars
        city = re.sub(r"[^A-Z]", "", m.group(2))[:4]

        return f"{store}-{city}"


    duplicates = defaultdict(list)

    for id, date, amount, desc in _data[1:]:
        norm = normalize_desc(desc)

        # Normalize amount to float
        amt = float(amount)

        # Key now includes DATE + AMOUNT + NORMALIZED DESCRIPTION
        key = (date, amt, norm)

        duplicates[key].append([id, date, amount, desc])

    # Keep only groups with >1
    dupes = {k: v for k, v in duplicates.items() if len(v) > 1}

    return dupes




# ------------------------------------------------------------
# Duplicates Window (converted to CTkToplevel)
# ------------------------------------------------------------

def getDuplicates(dateRange=None):
    import TreeDataView
    
    log.info("getDuplicates")

    stmt = """
        SELECT Id, Date, Amount, Description FROM transactions
        GROUP BY Date, Amount, Description;
    """

    _data, hdr, err = sql.sqlQuery(stmt)
    
    dupes = find_dupes(_data)

    if dupes:
        winc = ctk.CTkToplevel()
        winc.title("Duplicates")
        winc.geometry("900x400")
        winc.name = "transactions"
        frame = ctk.CTkFrame(winc)
        frame.pack(fill="both", expand=True)

        hdr1 = hdr+["Id2","Description2"]
        #tree = ttk.Treeview(frame, columns=hdr1, show="headings")
        tree = TreeDataView.TreeDataView(winc, hdr1, searchbar=True, right_click=True, double_click=True, left_click=False, show='headings')

        #tree.pack(fill="both", expand=True)
        ##print(hdr1)

        for col in hdr1:
            tree.heading(col, text=col)
            tree.column(col, width=120, anchor="w")
        
        tag1 = 'oddrow'
   
        for row in dupes:
            if 'evenrow' in tag1:
                tag1 = 'oddrow'
            else:
                tag1 = 'evenrow'
                
            r = dupes[row][0] + [dupes[row][1][0],dupes[row][1][3]]
            tree.insert("", "end", values=r, tags=tag1)


# ------------------------------------------------------------
# CTkReportTree — Standalone CustomTkinter Frame
# ------------------------------------------------------------
class CTkReportTree(ctk.CTkFrame):
    
    def __init__(self, master, treeFrame, date_range):
        super().__init__(master)

        self.treeFrame = treeFrame
        #self.date_range = fin_config.daterange
        self.cfgDate = date_range
        self.grid_propagate(False)
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
                
        self.date_range = date_range
                                            
        # Layout
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        # Left navigation frame
        self.nav_frame = ctk.CTkFrame(self)
        self.nav_frame.grid(row=0, column=0, sticky="nsw")
        
        # Apply Treeview theme BEFORE creating the widget
        theme_manager.apply_treeview_theme()

        self.tree = ttk.Treeview(self.nav_frame, show="tree")
        self.tree.pack(fill="both", expand=True)
        
        # Bindings
        self.tree.bind("<<TreeviewSelect>>", self.onLeftClick)
        self.tree.bind("<Double-1>", self.onDoubleClick)

        # Bind hover AFTER creation
        theme_manager.enable_treeview_hover(self.tree)
        # Rebind style explicitly
        self.tree.configure(style="CTk.Treeview")

        self.build_tree()
        
        # Apply Treeview colors based on current CTk theme
        #theme_manager.refresh_tree_colors(self)

    # --------------------------------------------------------
    # Build Navigation Tree
    # --------------------------------------------------------
    def build_tree(self):
        
        tbls = sql.getTables()
        if tbls is None:
            return

        self.aliasList = {}
        self.catList = {}
        sql.catItems(self.catList, dateRange=fin_config.daterange)

        hpId = self.tree.insert("", "0", open=True, text="Home")
        self.tree.insert(hpId, "0", text="All Transactions")

        # Tables
        tblId = self.tree.insert(hpId, "end", text="Tables")
        for c in tbls:
            self.tree.insert(tblId, "end", text=c)

        # Accounts
        acId = self.tree.insert(hpId, "end", text="Accounts")
        data, cols, err = sql.getColumnDistinct("Account", dateRange=fin_config.daterange)
        if not err:
            for col in data:
                self.tree.insert(acId, "end", text=col)

        # Alias
        aliasId = self.tree.insert(hpId, "end", text="Alias")
        data, cols, err = sql.getColumnDistinct("Alias", dateRange=fin_config.daterange)
        for col in data:
            self.tree.insert(aliasId, "end", text=col)

        # Type
        typeId = self.tree.insert(hpId, "end", text="Type")
        data, cols, err = sql.getColumnDistinct("Type", dateRange=fin_config.daterange)
        for col in data:
            txt = col if col else "???"
            self.tree.insert(typeId, "end", text=txt)

        '''# Categories
        catId = self.tree.insert(hpId, "end", text="Categories")
        for cat in self.catList:
            sCatId = self.tree.insert(catId, "end", text=cat)
            for scat in self.catList[cat]:
                self.tree.insert(sCatId, "end", text=scat)
        '''
        # Reports
        rptId = self.tree.insert("", "end", open=True, text="Report")
        for label in [
            "By Category",
            "By Alias",
            "By Account",
            "By Type",
            "By Year",
            "By Month",
            "Categories",
            ]:
            self.tree.insert(rptId, "end", text=label)
        
        # Classification
        rptId = self.tree.insert("", "end", open=True, text="QFX Processing")
        for label in [
            "QFX Viewer",
            "Batch Classifier",
            "Rules Editor",
            ]:
            self.tree.insert(rptId, "end", text=label)

    # --------------------------------------------------------
    # Event Routing
    # --------------------------------------------------------
    def onLeftClick(self, *_):
        ggtext, gtext, ptext, ctext = getAncestry(self.tree)

        if not ggtext and not gtext and not ptext:
            self.level0(ctext)
        elif not ggtext and not gtext and ptext:
            self.level1(ptext, ctext)
        elif not ggtext and gtext:
            self.level2(gtext, ptext, ctext)
        else:
            self.level3(ggtext, gtext, ptext, ctext)

    def onDoubleClick(self, event):
        #self.date_range = self.date_range
        self.onLeftClick()

    # --------------------------------------------------------
    # Level Handlers (unchanged logic)
    # --------------------------------------------------------
    def level0(self, ctext):
        #log.info(f"level0 {ctext}")
        pass

    def level1(self, ptext, ctext):
        log.info(f"level1 {ptext}:{ctext}")
        start = perf_counter()
        
        # Clear content frame
        #for w in self.treeFrame.winfo_children():
        #    w.destroy()

        if ptext == "Report":
            self.handle_report(ctext)
        elif ptext == "Home":
            self.handle_home(ctext)
        elif ptext == "QFX Processing":
            self.qfx_classify(ptext, ctext)
          
    def level2(self, gtext, ptext, ctext):
        log.info(f"level2 {gtext}:{ptext}:{ctext}")
        start = perf_counter()
        #for w in self.treeFrame.winfo_children():
        #    w.destroy()

        if gtext == "Home":
            self.handle_home_level2(ptext, ctext)
        elif gtext == "Report":
            self.handle_report_config(ptext, ctext)
            
        StatusBus.update_perf(f"View level 2 {ctext}", perf_counter() - start)
        
    def level3(self, ggtext, gtext, ptext, ctext):
        log.info(f"level3 {ggtext}:{gtext}:{ptext}:{ctext}")
        start = perf_counter()
        #for w in self.treeFrame.winfo_children():
        #    w.destroy()

        if ggtext == "Home" and gtext == "Categories":
            ary, cols = doQuery(category=ptext, subcat=ctext, dateRange=fin_config.daterange)
            ShowTransactions(self.treeFrame, fin_config.daterange, dataList=ary, columns=cols)
        StatusBus.update_perf(f"View level 3 {gtext}", perf_counter() - start)
    # --------------------------------------------------------
    # Report Handlers
    # --------------------------------------------------------
    def handle_report(self, ctext):
        if ctext == "By Category":
            query = f"""
                SELECT Category, SubCategory, Alias, Date, Amount, Account
                FROM transactions
                WHERE date(date) BETWEEN date('{fin_config.daterange[0]}')
                AND date('{fin_config.daterange[1]}')
                ORDER BY Category, SubCategory, Alias;
            """
            data, cols, err = sql.sqlQuery(query)
            byMonth(self.treeFrame, data, fin_config.daterange)

        elif ctext == "By Alias":
            query = f"""
                SELECT Alias, Category, SubCategory, Date, Amount, Account
                FROM transactions
                WHERE date(date) BETWEEN date('{fin_config.daterange[0]}')
                AND date('{fin_config.daterange[1]}')
                ORDER BY Alias, Category, SubCategory;
            """
            data, cols, err = sql.sqlQuery(query)
            byMonth(self.treeFrame, data, fin_config.daterange)

        elif ctext == "By Account":
            query = f"""
                SELECT Account, Category, Alias, Date, Amount, SubCategory
                FROM transactions
                WHERE date(date) BETWEEN date('{fin_config.daterange[0]}')
                AND date('{fin_config.daterange[1]}')
                ORDER BY Account, Category, Alias;
            """
            data, cols, err = sql.sqlQuery(query)
            byMonth(self.treeFrame, data, fin_config.daterange)

        elif ctext == "By Type":
            query = f"""
                SELECT Type, Category, Alias, Date, Amount, Account
                FROM transactions
                WHERE date(date) BETWEEN date('{fin_config.daterange[0]}')
                AND date('{fin_config.daterange[1]}')
                ORDER BY Alias, Category, SubCategory;
            """
            data, cols, err = sql.sqlQuery(query)
            byMonth(self.treeFrame, data, fin_config.daterange)

        elif ctext == "By Year":
            model = DataModel(table_name="transactions", dateRange=fin_config.daterange)
            model.load()
            ByYear(self.treeFrame, model)

        elif ctext == "By Month":
            MonthlyHierarchyApp(self.treeFrame, table_name="transactions", date_range=fin_config.daterange)

        elif ctext == "Categories":
            CategoryReportPanel(self.treeFrame, date_range=fin_config.daterange)
        
    # --------------------------------------------------------
    # Home Handlers
    # --------------------------------------------------------
    def handle_home(self, ctext):
        
        if ctext != "All Transactions":
            #log.info(f"Invalid selection Home:{ctext}")
            return

        stmt = f"""
            SELECT * FROM transactions
            WHERE date(date) BETWEEN date('{fin_config.daterange[0]}')
            AND date('{fin_config.daterange[1]}');
        """

        ary, cols, err = sql.sqlQuery(stmt)
        st=ShowTransactions(self.treeFrame, None, table="transactions", dataList=ary, columns=cols)
        #st.grid(row=0, column=0, sticky="nsew")                                        

    def handle_home_level2(self, ptext, ctext):
        
        table = "transactions"
        start = perf_counter()
        
        if ptext == "Tables":
            table = ctext
            if table != "transactions":
                stmt = f"SELECT * FROM {table};"
            else:
                stmt = f"""
                    SELECT * FROM transactions
                    WHERE date(date) BETWEEN date('{fin_config.daterange[0]}')
                    AND date('{fin_config.daterange[1]}');
                """
            ary, cols, err = sql.sqlQuery(stmt)

        elif ptext == "Categories":
            ary, cols = doQuery(category=ctext, dateRange=fin_config.daterange)

        elif ptext == "Accounts":
            ary, cols = doQuery(account=ctext, dateRange=fin_config.daterange)

        elif ptext == "Alias":
            ary, cols = doQuery(alias=ctext, dateRange=fin_config.daterange)

        elif ptext == "Type":
            ary, cols = doQuery(_type=ctext, dateRange=fin_config.daterange)

        else:
            messagebox.showerror("ERROR", f"Invalid selection {ptext}:{ctext}")
            return
        
        ShowTransactions("", fin_config.daterange, table=table, dataList=ary, columns=cols)

    def qfx_classify(self, ptext, ctext):
        app = RulesConsoleApp()
        """if ctext == "QFX Browser":
            tab_name = "QFX Browser"
        elif ctext == "QFX Import":
            tab_name = "Batch Classifier"
        elif ctext == "QFX Import":
            tab_name = "Rules Editor" 
        else: 
            messagebox.showerror("ERROR", f"Invalid selection {ptext}:{ctext}")
        """    
        app.after(
            100,
            lambda: (
                app.tabview.set(ctext) 
            )
        )

        #return app  
        
    # --------------------------------------------------------
    # Public API
    # --------------------------------------------------------
    def refresh(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        for w in self.treeFrame.winfo_children():
            w.destroy()

        self.build_tree()

    def duplicates(self):
        return getDuplicates(dateRange=fin_config.daterange)
