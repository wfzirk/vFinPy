""" copilot

from a database table containing date, category, subcategory, alias, amount

with python, apsw and tcl treeview show hierarchaial tree with each column being a month with category as first level, subcategory as 2nd level and alias as third level and present in hierarchical treeview. alias contains an array of floats. 

Each Category row and column is to be totaled. with final totals and totals for each category.
Each SubCategory row and column is to be totaled. with final totals and totals for each SubCategory, 
Each Alias row and column is to be totaled. with final totals and totals for each alias.
Add grand total row at end of tree.
add scrollbars and expand collapse buttons

read data from sqlite database

Use class instead of functions
"""

# Python Includes
import json
import tkinter as tk
from tkinter import ttk
from datetime import datetime
from collections import defaultdict
import logging

#Project Includes
import apswSql as sql
from util import clear_all_inside_frame
from bymonth import treeSettings, CatEventHandler
from finchart import Charts   #, linechart, barchart, piechart

class MonthlyHierarchyApp:
    #def __init__(self, parent, db_path, table_name="transactions", date_range=[]):
    def __init__(self, parent, table_name="transactions", date_range=[]):
        
        clear_all_inside_frame(parent)
        self.parent = parent
        self.parent.name = "Monthly"
        self.chrts = None
        self.table_name = table_name
        self.cursor, self.conn = sql.open_db()

        self.months = []      # e.g., ["2025-06", "2025-07", ...]
        self.data_tree = {}   # nested dict: category -> subcategory -> alias -> {month: total}
        self.col_totals = defaultdict(float)  # per-month totals across all rows
        self.grand_total = 0.0

        self.build_ui()
        self.load_and_aggregate(date_range)
        self.populate_tree()

    # UI setup: frame, tree, scrollbars, buttons
    def build_ui(self):
        #self.root.title("Monthly Hierarchical Treeview")

        # Top control bar
        controls = ttk.Frame(self.parent)
        controls.pack(fill="x", padx=6, pady=6)

        expand_btn = ttk.Button(controls, text="Expand all", command=self.expand_all)
        collapse_btn = ttk.Button(controls, text="Collapse all", command=self.collapse_all)
        expand_btn.pack(side="left", padx=(0, 6))
        collapse_btn.pack(side="left")
        ttk.Button(controls, text="Line Chart", command=lambda: self.month_charts("line")).pack(side='left', padx=(0, 6))
        ttk.Button(controls, text="Bar Chart", command=lambda: self.month_charts("bar")).pack(side='left', padx=(0, 6))
        ttk.Button(controls, text="Pie Chart", command=lambda: self.month_charts("pie")).pack(side='left')

        # Tree and scrollbars
        self.container = ttk.Frame(self.parent)
        self.container.pack(fill="both", expand=True)

        self.tree = ttk.Treeview(self.container, show="tree headings")
        self.tree.pack(side="left", fill="both", expand=True)
        '''
        vsb = ttk.Scrollbar(self.container, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(self.parent, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        vsb.pack(side="right", fill="y")
        hsb.pack(fill="x")
        '''
        treeSettings(self.tree)
        self.cev = CatEventHandler(self.parent, self.tree)
        self.tree.bind('<Button-3>', self.cev.popup_menu)
        self.tree.bind('<Double-Button-1>', self.cev.double_click)
        
        # Style for readability
        style = ttk.Style(self.parent)
        style.configure("Treeview", rowheight=24)

    # Load rows from SQLite via APSW and aggregate into nested dict
    def load_and_aggregate(self, date_range):
        # Fetch all relevant rows
        # Expecting: date TEXT 'YYYY-MM-DD', category TEXT, subcategory TEXT, alias TEXT, amount TEXT/REAL
        sql = f"""
            SELECT date, category, subcategory, alias, amount
            FROM {self.table_name}
            WHERE date IS NOT NULL AND category IS NOT NULL AND subcategory IS NOT NULL AND alias IS NOT NULL  AND date(date) BETWEEN date('{date_range[0]}') AND date('{date_range[1]}')
        """
        
        query = "SELECT DISTINCT SubCategory FROM transactions WHERE Category='category'"
        query = query + " AND date(date) BETWEEN date('"+date_range[0]+"') AND date('"+date_range[1]+"')"

        rows = list(self.cursor.execute(sql))

        # Extract month keys present in data
        month_set = set()
        for (date_str, category, subcategory, alias, amount_raw) in rows:
            month_key = self._to_month_key(date_str)
            if month_key:
                month_set.add(month_key)
        self.months = sorted(month_set)

        # Initialize data structure
        # category -> subcategory -> alias -> {month: total}
        self.data_tree = defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: defaultdict(float))))

        # Parse amounts, sum per alias per month
        for (date_str, category, subcategory, alias, amount_raw) in rows:
            month_key = self._to_month_key(date_str)
            if not month_key:
                continue

            # Parse amount: either a single float or a JSON array of floats
            amt = self._parse_amount(amount_raw)

            # Sum into structure
            # If amt is a list, sum it; if float, use directly
            value = sum(amt) if isinstance(amt, list) else float(amt)
            self.data_tree[category][subcategory][alias][month_key] += value

        # Compute column totals and grand total
        self.col_totals = defaultdict(float)
        self.grand_total = 0.0

        # Walk structure to accumulate totals
        for category, subcats in self.data_tree.items():
            for subcat, aliases in subcats.items():
                for alias, month_map in aliases.items():
                    for m in self.months:
                        v = month_map.get(m, 0.0)
                        self.col_totals[m] += v
                        self.grand_total += v

    def _parse_amount(self, amount_raw):
        # Handle None gracefully
        if amount_raw is None:
            return 0.0
        # Try JSON array
        if isinstance(amount_raw, (bytes, bytearray)):
            s = amount_raw.decode("utf-8", errors="ignore")
        else:
            s = str(amount_raw)
        s = s.strip()

        # If it looks like JSON array, parse
        if s.startswith("[") and s.endswith("]"):
            try:
                arr = json.loads(s)
                # Validate floats
                return [float(x) for x in arr]
            except Exception:
                # Fallback: try to split by commas
                try:
                    return [float(x) for x in s.strip("[]").split(",") if x.strip()]
                except Exception:
                    return 0.0
        else:
            # Single float
            try:
                return float(s)
            except Exception:
                return 0.0

    def _to_month_key(self, date_str):
        try:
            dt = datetime.strptime(date_str, "%Y-%m-%d")
            return f"{dt.year}-{dt.month:02d}"
        except Exception:
            return None

    # Create columns and populate tree with hierarchical rows and per-month totals
    def populate_tree(self):
        # Define columns: months + Total
        logging.info('populate_tree')
        columns = self.months + ["Total"]
        self.tree["columns"] = columns

        # Headings
        self.tree.heading("#0", text="Category / SubCategory / Alias")
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, anchor="e", width=100, stretch=True)
        self.tree.column("#0", anchor="w", width=280, stretch=True)

        # Insert category level
        self.catcnt = {}
        for category, subcats in sorted(self.data_tree.items()):
            tag = 'lvl0'
            cat_values = self._compute_node_totals(subcats)
            cat_item = self.tree.insert("", "end", text=category, values=self._row_values(cat_values), open=False, tags=(tag,))
            
            # SubCategory level
            for subcat, aliases in sorted(subcats.items()):
                tag = 'lvl1'
                sub_values = self._compute_node_totals(aliases)
                sub_item = self.tree.insert(cat_item, "end", text=subcat, values=self._row_values(sub_values), open=False, tags=(tag,))

                # Alias level
                tag = 'lvl2'
                for alias, month_map in sorted(aliases.items()):
                    if category in self.catcnt:
                        self.catcnt[category] += 1 
                        ##print('catcnt',category, catcnt[category])
                    else:
                        ##print(category, catcnt)
                        self.catcnt[category]= 1
                        
                    alias_values = self._compute_leaf_totals(month_map)
                    self.tree.insert(sub_item, "end", text=alias, values=self._row_values(alias_values), open=False, tags=(tag,))

        # Grand total row at end
        self.grand_values = [self.col_totals.get(m, 0.0) for m in self.months]
        grand_row = self.grand_values + [sum(self.grand_values)]
        self.tree.insert("", "end", text="Grand total", values=self._format_values(grand_row), tags=('grand-total',))
        #self.chrts = None
        
    def cls(self):
        #print('monthly close')
        self.chrts = None
        
    def month_charts(self, chart_type):     
        logging.info(f'==== month_charts  {chart_type}')
        
        gv=[]
        for v in self.grand_values:
            gv.append(float(v))
            
        if not self.chrts:
            #print('not')
            self.chrts = Charts(self.parent, self.cls)
                            
        if "line" in chart_type:     
            self.chrts.line_chart(self.tree["columns"][:-1], gv, x_label="Month", y_label="Amount ($)", title="By Month")
        if "pie" in chart_type:     
            self.chrts.pie_chart(self.catcnt.values(), labels=self.catcnt.keys(), title="Categories")
        if "bar" in chart_type: 
            self.chrts.bar_chart(self.tree["columns"][:-1], gv, x_label="Month", y_label="Amount ($)", title="By Month")
   
   # Compute totals for a leaf alias: month_map is {month: value}
    def _compute_leaf_totals(self, month_map):
        row = [month_map.get(m, 0.0) for m in self.months]
        return row + [sum(row)]

    # Compute totals for an internal node given children dict
    # children: dict of name -> (for alias: {month: value}) or nested dict
    def _compute_node_totals(self, children):
        # Accumulate per-month
        totals = [0.0 for _ in self.months]
        for _, child in children.items():
            if isinstance(child, dict) and all(isinstance(v, dict) for v in child.values()):
                # Nested level (e.g., subcategory has aliases)
                child_row = self._compute_node_totals(child)
                for i in range(len(self.months)):
                    totals[i] += child_row[i]
            else:
                # Leaf alias: child is month_map
                leaf_row = self._compute_leaf_totals(child)
                for i in range(len(self.months)):
                    totals[i] += leaf_row[i]
        return totals + [sum(totals)]

    def _row_values(self, numeric_row):
        # numeric_row: list per-month + total
        return self._format_values(numeric_row)

    def _format_values(self, values):
        # Right-align numbers, 2 decimals
        return [f"{v:,.2f}" for v in values]

    # Expand/collapse helpers
    def expand_all(self):
        for item in self.tree.get_children(""):
            self.set_open_recursive(item, True)

    def collapse_all(self):
        for item in self.tree.get_children(""):
            self.set_open_recursive(item, False)

    def set_open_recursive(self, item, open_flag):
        self.tree.item(item, open=open_flag)
        for child in self.tree.get_children(item):
            self.set_open_recursive(child, open_flag)
            


if __name__ == "__main__":
    root = tk.Tk()

    app = MonthlyHierarchyApp(root, table_name="transactions", date_range=["2025-01-01","2025-12-24"])
    root.mainloop()