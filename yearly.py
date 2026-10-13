""" copilot

from a database table containing year, category, subcategory, alias, amount

with python, apsw and tcl treeview show hierarchaial tree with each column being a year with category as first level, subcategory as 2nd level and alias as third level and present in hierarchical treeview. alias contains an array of floats. 

Each Category row and column is to be totaled. with final totals and totals for each category.
Each SubCategory row and column is to be totaled. with final totals and totals for each SubCategory, 
Each Alias row and column is to be totaled. with final totals and totals for each alias.
Add grand total row at end of tree.
add scrollbars and expand collapse buttons

read data from sqlite database

Use class instead of functions
"""

# Python Includes
import tkinter as tk
from tkinter import ttk
from decimal import Decimal, ROUND_HALF_UP
import logging

#Project Includes
import apswSql as sql
from util import clear_all_inside_frame, saveView2csv
from bymonth import treeSettings, CatEventHandler

from finchart import Charts   #, linechart, barchart, piechart

class DataModel:
    """
    Loads data from a single fact table: (year, category, subcategory, alias, amount).
    Builds hierarchy Category -> SubCategory -> Alias.
    Computes per-level row totals and per-year column totals, plus grand total.
    """
    #def __init__(self, db_path, table_name="facts"):
    def __init__(self, table_name="transactions", dateRange=[]):
        self.cursor, self.conn = sql.open_db()
        self.dateRange = dateRange
        self.table_name = table_name
        self.years = []
        # data[cat][sub][alias] = {'values': {year: float}, '__row_totals__': {per_year, total}}
        self.data = {}
        self.grand_totals = {'per_year': {}, 'total': 0.0}

    def load(self):
        self._load_years()
        self._load_facts()
        self._compute_totals()

    def _execute(self, sql, args=()):
        #cur = self.conn.cursor()
        ##print('curr-----', cur)
        #rows = cur.execute(sql, args)

        #with self.conn.cursor() as cur:
        logging.info(sql)
        for row in self.cursor.execute(sql, args):
            #logging.info(row)
            yield row

    def _load_years(self):
        query = f"SELECT DISTINCT strftime('%Y', Date) AS year FROM transactions WHERE date(date) BETWEEN date('{self.dateRange[0]}') AND date('{self.dateRange[1]}') ORDER BY Date;"
        logging.info('load_years %s',query)
        self.cursor.execute(query)
        distinct_years = self.cursor.fetchall()
        logging.info("Distinct Years: %s", distinct_years)
        
        self.years = []
        for year_tuple in distinct_years:
            self.years.append(year_tuple[0])

        if not self.years:
            # Fallback years if table empty
            self.years = [str(y) for y in range(2020, 2026)]
         
    def _load_facts(self):
        # Preload all facts sorted to keep deterministic insertion order
        sql = f"""
            SELECT Date, category, subcategory, alias, amount
            FROM {self.table_name} WHERE date(date) BETWEEN date('{self.dateRange[0]}') AND date('{self.dateRange[1]}') ORDER BY category, subcategory, alias, Date
        """
        #self.catcnt = {}
        for date, cat, sub, al, amt in self._execute(sql):
            year=date[:4]
            #logging.info('year %s %s %s',date, year, al)
            self.data.setdefault(cat, {}).setdefault(sub, {}).setdefault(
                al, {'values': {y: 0.0 for y in self.years}}
            )
            # Assign amount (sum if duplicates exist)
            self.data[cat][sub][al]['values'][year] = (
                self.data[cat][sub][al]['values'].get(year, 0.0) + (float(amt) if amt is not None else 0.0)
            )
        ##print('catcnt', self.catcnt)
        # Ensure any aliases missing some years have zeros
        for cat, submap in self.data.items():
            for sub, aliasmap in submap.items():
                for al, payload in aliasmap.items():
                    for y in self.years:
                        payload['values'].setdefault(y, 0.0)

    def _sum_dict_values(self, d):
        return sum(float(x) for x in d.values())

    def _sum_across_children_years(self, child_objs):
        per_year = {y: 0.0 for y in self.years}
        for child in child_objs:
            # child is either alias payload with 'values' or nested map with '__row_totals__'
            if 'values' in child:
                for y in self.years:
                    per_year[y] += child['values'].get(y, 0.0)
            else:
                for y in self.years:
                    per_year[y] += child['__row_totals__']['per_year'].get(y, 0.0)
        total = self._sum_dict_values(per_year)
        return per_year, total

    def _compute_totals(self):
        # Alias totals (row totals mirror values)
        catno = {}
        for cat, submap in self.data.items():
            for sub, aliasmap in submap.items():
                for al, payload in aliasmap.items():
                    per_year = payload['values']
                    alias_total = self._sum_dict_values(per_year)
                    payload['__row_totals__'] = {
                        'per_year': dict(per_year),
                        'total': alias_total
                    }
            if cat in catno:
                catno[cat] += 1
            else:
                catno[cat] = 0
        logging.info(catno)        

        # SubCategory totals
        for cat, submap in self.data.items():
            for sub, aliasmap in submap.items():
                child_objs = [aliasmap[k] for k in aliasmap.keys()]
                per_year, total = self._sum_across_children_years(child_objs)
                aliasmap['__row_totals__'] = {
                    'per_year': per_year,
                    'total': total
                }

        # Category totals
        for cat, submap in self.data.items():
            child_objs = [submap[k] for k in submap.keys() if k != '__row_totals__']
            per_year, total = self._sum_across_children_years(child_objs)
            submap['__row_totals__'] = {
                'per_year': per_year,
                'total': total
            }

        # Grand totals
        grand_per_year = {y: 0.0 for y in self.years}
        for cat, submap in self.data.items():
            for y in self.years:
                grand_per_year[y] += submap['__row_totals__']['per_year'][y]
        self.grand_totals['per_year'] = grand_per_year
        self.grand_totals['total'] = self._sum_dict_values(grand_per_year)


class ByYear:
    """
    Tkinter UI with ttk.Treeview showing hierarchical yearly totals.
    """
    def __init__(self, parent, model: DataModel):
        
        clear_all_inside_frame(parent)
        self.parent = parent
        self.parent.name = "ByYear"
        self.model = model
        self.chrts = None
        #============================================
        # Create a horizontal PanedWindow
        # orient=tk.VERTICAL would stack them top/bottom
        #pwindow = ttk.PanedWindow(root, orient=tk.HORIZONTAL)
        pwindow = ttk.PanedWindow(parent, orient=tk.VERTICAL)
        pwindow.pack(fill=tk.BOTH, expand=True)

        # Create the two panes (frames)
        self.top_frame = ttk.Frame(pwindow)  #, width=150, height=150, relief=tk.SUNKEN)
        self.bottom_frame = ttk.Frame(pwindow)   #, width=250, height=250, relief=tk.SUNKEN)
        self.top_frame.name = self.parent.name
        # Add frames to the PanedWindow
        # The weight option determines how extra space is distributed when resizing
        pwindow.add(self.top_frame, weight=1)
        pwindow.add(self.bottom_frame, weight=1) # Right pane gets twice the space

        #==================================================
        #self.root.title("Hierarchical Yearly Totals")
        self.build_widgets()
        self.populate_tree()

    def build_widgets(self):
        # Controls
        ctrl = ttk.Frame(self.top_frame)
        ctrl.pack(fill='x', padx=8, pady=4)

        ttk.Button(ctrl, text="Expand all", command=self.expand_all).pack(side='left', padx=(0, 6))
        ttk.Button(ctrl, text="Collapse all", command=self.collapse_all).pack(side='left', padx=(0, 6))
        ttk.Button(ctrl, text="Line Chart", command=lambda: self.year_charts("line")).pack(side='left', padx=(0, 6))
        ttk.Button(ctrl, text="Bar Chart", command=lambda: self.year_charts("bar")).pack(side='left', padx=(0, 6))
        ttk.Button(ctrl, text="Pie Chart", command=lambda: self.year_charts("pie")).pack(side='left')

        # Tree + scrollbars
        frame = ttk.Frame(self.top_frame)
        frame.pack(fill='both', expand=True, padx=8, pady=8)

        self.tree = ttk.Treeview(frame, columns=self._columns(), show='tree headings')
        self.tree.heading('#0', text='Category/SubCategory/Alias')
        self.tree.column('#0', width=180, anchor='w')

        for col in self._columns():
            self.tree.heading(col, text=col)
            self.tree.column(col, width=80, anchor='e')

        vsb = ttk.Scrollbar(frame, orient='vertical', command=self.tree.yview)
        hsb = ttk.Scrollbar(frame, orient='horizontal', command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        self.tree.grid(row=0, column=0, sticky='nsew')
        vsb.grid(row=0, column=1, sticky='ns')
        hsb.grid(row=1, column=0, sticky='ew')

        frame.rowconfigure(0, weight=1)
        frame.columnconfigure(0, weight=1)

        self.cev = CatEventHandler(self.top_frame, self.tree)
        self.tree.bind('<Button-3>', self.cev.popup_menu)
        self.tree.bind('<Double-Button-1>', self.cev.double_click)
        #self.tev = TreeEventHandler(self.parent, self.tree)

        #if right_click:
        #    logging.info('right_click')
        #    self.tree.bind('<Button-3>', self.tev.popup_menu)
        treeSettings(self.tree)

    def _columns(self):
        return self.model.years + ["Total"]

    def _fmt(self, value):
        d = Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        return f"{d:.2f}"

    def populate_tree(self):
        # Category level
        self.catcnt = {}
        for cat, submap in sorted(self.model.data.items()):
            tag = 'lvl0'
            cat_vals = [self._fmt(submap['__row_totals__']['per_year'][y]) for y in self.model.years]
            cat_total = self._fmt(submap['__row_totals__']['total'])
            cat_item = self.tree.insert('', 'end', text=f"{cat}", values=cat_vals + [cat_total], open=False, tags=(tag,))

            # SubCategory level
            for sub, aliasmap in sorted(submap.items()):
                if sub == '__row_totals__':
                    continue
                tag = 'lvl1'    
                sub_vals = [self._fmt(aliasmap['__row_totals__']['per_year'][y]) for y in self.model.years]
                sub_total = self._fmt(aliasmap['__row_totals__']['total'])
                sub_item = self.tree.insert(cat_item, 'end', text=f"{sub}",values=sub_vals + [sub_total], open=False, tags=(tag,))

                # Alias level
                Stag = 'lvl2'
                for al, payload in sorted(aliasmap.items()):
                    if cat in self.catcnt:
                        self.catcnt[cat] += 1 
                        ##print('catcnt',cat, catcnt[cat])
                    else:
                        ##print(cat, catcnt)
                        self.catcnt[cat]= 1
                    if al == '__row_totals__':
                        continue
                    alias_vals = [self._fmt(payload['values'][y]) for y in self.model.years]
                    alias_total = self._fmt(payload['__row_totals__']['total'])
                    self.tree.insert(sub_item, 'end', text=f"{al}",                  values=alias_vals + [alias_total], open=False, tags=(tag,))
                    
        # Grand total row
        self.grand_vals = [self._fmt(self.model.grand_totals['per_year'][y]) for y in self.model.years]
        grand_total = self._fmt(self.model.grand_totals['total'])
        self.tree.insert('', 'end', text="Grand total", values=self.grand_vals + [grand_total], open=True, tags=('grand-total',))
        #self.chrts = None
    
    def cls(self):
        #print('yearly close')
        self.chrts = None
    
    
    def year_charts(self, chart_type): 
        logging.info(f'==== year_charts  {chart_type}')
        #print('self.chts', self.chrts)
        gv=[]
        for v in self.grand_vals:
            gv.append(float(v))
        
        if not self.chrts:

            self.chrts = Charts(self.parent, self.cls)
                        
        if "line" in chart_type:     
            self.chrts.line_chart(self.tree["columns"][:-1], gv, x_label="Year", y_label="Amount", title="By Year")
        if "pie" in chart_type:     
            self.chrts.pie_chart(self.catcnt.values(), labels=self.catcnt.keys(), title="Categories")
        if "bar" in chart_type: 
            self.chrts.bar_chart(self.tree["columns"][:-1], gv, x_label="Year", y_label="Amount", title="By Year")
    '''
    def expand_all(self):
        for item in self.tree.get_children(''):
            self.tree.item(item, open=True)
            for child in self.tree.get_children(item):
                self.tree.item(child, open=True)
                for grandchild in self.tree.get_children(child):
                    self.tree.item(grandchild, open=True)

    def collapse_all(self):
        for item in self.tree.get_children(''):
            self.tree.item(item, open=False)
            for child in self.tree.get_children(item):
                self.tree.item(child, open=False)
                for grandchild in self.tree.get_children(child):
                    self.tree.item(grandchild, open=False)
    '''                
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


def main(db_path="example.db", table_name="facts"):
    model = DataModel(db_path=db_path, table_name=table_name)
    model.load()

    root = tk.Tk()
    ByYear(root, model)
    root.mainloop()

if __name__ == "__main__":
    main(db_path="D:/Documents/PyScripts314/vPyFin314/__finofx/database/test2025.db", table_name="transactions")