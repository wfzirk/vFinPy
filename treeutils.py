
# Python Includes
import sys
import tkinter as tk
from tkinter import ttk, font
import traceback

# 3rd Party Includes

# Project Includes
import progressbar
from config import fin_config,  TWIDTH, TANCHOR, TSTRETCH
from logging_manager import get_logger
log = get_logger(__name__)

# ============================================================
# detect duplicates in a Treeview by extracting each row’s values,
# normalizing them, and grouping rows by a duplicate key 
# (date + amount + cleaned description, or whatever you choose).
# Then you return only keys that have more than one row.
# ============================================================
def find_treeview_duplicates(tree, columns, normalizer=None):
    """
    Return dict: {duplicate_key: [item_ids]} for all duplicates in the Treeview.

    columns: list of column names to include in the duplicate key.
             MUST be explicit — never use tree["columns"].
    """
    log.info('dup %s', columns)
    if normalizer is None:
        def normalizer(v):
            if v is None:
                return ""
            return str(v).strip().upper()

    col_index = {col: idx for idx, col in enumerate(tree["columns"])}

    buckets = {}
    children = tree.get_children("")
    #log.info(children)
    pb = progressbar.ProgressBarPR(title='Batch Classifier', steps=len(children))
    for item_id in children:
        row = tree.item(item_id, "values")
        key_parts = [normalizer(row[col_index[col]]) for col in columns]
        dup_key = tuple(key_parts)

        buckets.setdefault(dup_key, []).append(item_id)
 
        if pb.progress():   # <-- returns True when done or cancelled
            break
    pb.close()  # <-- ALWAYS closes cleanly      

    return {k: v for k, v in buckets.items() if len(v) > 1}

class TreeTooltip:
    def __init__(self, widget):
        log.info('tooltip')
        self.widget = widget
        self.tip = None
        widget.bind("<Motion>", self.on_motion)
        widget.bind("<Leave>", self.hide)

    def show(self, text, x, y):
        self.hide()
        tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x+20}+{y+20}")
        label = tk.Label(
            tw, text=text,
            background="#333333", foreground="white",
            relief="solid", borderwidth=1,
            padx=6, pady=3
        )
        label.pack()
        self.tip = tw

    def hide(self, event=None):
        if self.tip:
            self.tip.destroy()
            self.tip = None

    def on_motion(self, event):
        row_id = self.widget.identify_row(event.y)
        log.info('onmotion %s',row_id)
        if not row_id:
            self.hide()
            return

        reason = self.widget.set(row_id, "duplicate_reason")
        if reason:
            self.show(reason, event.x_root, event.y_root)
        else:
            self.hide()

# ---------------------------
# sort tree columns
# ---------------------------
def sort_type(num): 
    # allow numeric sort
    try: 
        ele = float(num[0]) 
        return (0, ele, '') 
    except ValueError: 
        return (1, num, '') 
            
def sortby_column(tree, col, descending):
    """sort tree contents when a column header is clicked on"""
    # grab values to sort
    data = [(tree.set(child, col), child) for child in tree.get_children()]
    data.sort(key = sort_type, reverse=descending) 

    for ix, item in enumerate(data):
        tree.move(item[1], '', ix)
    
    # switch the heading so that it will sort in the opposite direction
    tree.heading(col, command=lambda col=col: sortby_column(tree, col, int(not descending)))   

def convert_value(value):
    """Convert to int/float when possible; otherwise return lowercase string."""
    try:
        # Try integer
        return int(value.replace(",", ""))
    except:
        pass
    try:
        # Try float
        return float(value.replace(",", ""))
    except:
        pass
    # Fallback: string
    return value.lower()
    
def treeview_sort_column(tree, col, reverse):
    """Sort a Treeview column numerically when possible, otherwise alphabetically."""
    # Extract values
    data = []
    for child in tree.get_children(""):
        val = tree.set(child, col)
        data.append((convert_value(val), child))

    # Sort
    data.sort(key=lambda x: x[0], reverse=reverse)

    # Reorder rows
    for index, (_, child) in enumerate(data):
        tree.move(child, "", index)

    # Toggle next sort direction
    tree.heading(col, command=lambda: treeview_sort_column(tree, col, not reverse))

# ---------------------------
# Hierarchical tree  sorter
#If your Treeview has nested rows, you likely want to sort only the children
#of the clicked parent, not the entire tree.
# ---------------------------
def sort_children(tree, parent, col, reverse):
    children = list(tree.get_children(parent))
    data = [(convert_value(tree.set(c, col)), c) for c in children]
    data.sort(key=lambda x: x[0], reverse=reverse)

    for index, (_, child) in enumerate(data):
        tree.move(child, parent, index)

    # Recursively sort deeper levels if desired
    # for _, child in data:
    #     sort_children(tree, child, col, reverse)
    
   
#import tkinter.font as tkfont
'''
def autosize_treeview(tree, padding=20, max_width=600):
    """
    Resize Treeview columns to fit content.

    tree       : ttk.Treeview
    padding    : extra pixels added to measured text width
    max_width  : prevents extremely wide columns
    """

    font = tk.font.nametofont("TkDefaultFont")

    for col in tree["columns"]:

        width = font.measure(col)

        for item in tree.get_children():
            value = tree.set(item, col)

            if value is None:
                value = ""

            width = max(
                width,
                font.measure(str(value))
            )

        tree.column(
            col,
            width=min(width + padding, max_width)
        )   
'''
def autosizeTreeColumns(tree, style=ttk.Style(), fnt=font.nametofont("TkDefaultFont"), table="transactions"):
    transWidths = fin_config.transWidths
   
    for col in tree['columns']:
        if col in transWidths[table]:
            w = transWidths[table][col][TWIDTH] * fnt['size']
            tree.column(col, width=w)

def sizeTreeColumns(tree, sortColumns=False, table='transactions', font=font.nametofont('TkDefaultFont')):
        #log.info(font.Font().measure('W'))
        colWidth = fin_config.transWidths[table]
        #log.info(colWidth)
        columns = tree['columns']
        for col in columns:
            if col in colWidth.keys():
                w = colWidth[col][TWIDTH] * font['size']
                a = colWidth[col][TANCHOR]
                s = colWidth[col][TSTRETCH]
                #log.info('size %s \t%s',column, w)
            else:
                w = 12 * font['size']     # width
                a = 'w'     # anchor
                s = True    # stretch

            if sortColumns:
                tree.heading(col, text=col, command=lambda c=col: sortby_column(tree, c, 1))
            else:
                tree.heading(col, text=col)
            #log.info('colsize %s',colWidth[col])
            tree.column(col, anchor=a, width=w, stretch=s)
'''
def autosize_treeview_nolimit(tree):
    font = tk.font.nametofont("TkDefaultFont")

    for col in tree["columns"]:
        width = font.measure(col)

        for item in tree.get_children():
            width = max(
                width,
                font.measure(str(tree.set(item, col)))
            )

        if col == "description":
            width = min(width + 30, 1000)
        else:
            width = min(width + 20, 200)

        tree.column(col, width=width)
'''        
# -----------------------------
# Entry point
# -----------------------------

def main():

    # ------------------------------
    # Demo UI
    # ------------------------------
    root = tk.Tk()
    tree = ttk.Treeview(root, columns=("col1", "col2"), show="headings")
    tree.pack(fill="both", expand=True)

    tree.heading("col1", text="Name")
    tree.heading("col2", text="City")

    # Sample data
    rows = [
        ("Alice", "Chicago"),
        ("Bob", "Boston"),
        ("Charlie", "Denver"),
        ("Diana", "Dallas"),
        ("Evan", "Detroit"),
    ]

    for r in rows:
        tree.insert("", "end", values=r)

    searcher = TreeviewSearch(tree)

    entry = tk.Entry(root)
    entry.pack(fill="x")

    def on_search(*_):
        searcher.search(entry.get())
        
    entry.bind("<KeyRelease>", on_search)



if __name__ == "__main__":
    root = tk.Tk()
    main()
    root.mainloop()

