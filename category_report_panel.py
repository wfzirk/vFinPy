
# category_report_panel.py

import csv
from datetime import datetime
from collections import defaultdict

import tkinter as tk
from tkinter import ttk, filedialog, messagebox

import customtkinter as ctk

from apswSql import open_db
from util import clear_all_inside_frame
from logging_manager import get_logger
from theme_manager import theme_manager

log = get_logger(__name__)

_sort_state = {}

def convert_value(value):
    if value is None:
        return (3, "")

    value = str(value).strip()

    if value == "":
        return (3, "")

    try:
        return (0, int(value.replace(",", "")))
    except Exception:
        pass

    try:
        return (1, float(value.replace(",", "")))
    except Exception:
        pass

    return (2, value.lower())
    
def hierarchical_sort_children(tree, parent, col):

    reverse = _sort_state.get(col, False)
    _sort_state[col] = not reverse

    data = []

    for child in tree.get_children(parent):

        if col == "#0":
            val = tree.item(child, "text")
        else:
            val = tree.set(child, col)

        data.append((convert_value(val), child))

    data.sort(key=lambda x: x[0], reverse=reverse)

    for pos, (_, iid) in enumerate(data):
        tree.move(iid, parent, pos)
        
class CategoryReportPanel:

    def __init__(self, parent, date_range=None):

        clear_all_inside_frame(parent)

        self.parent = parent
        self.date_range = date_range

        _, self.conn = open_db()

        self.view_mode = ctk.StringVar(value="year")
        self.filter_category = ctk.StringVar(value="All")
        self.filter_alias = ctk.StringVar(value="All")

        self.periods = []
        self.tree_data = {}

        self.build_ui()
        self.refresh()
        
    def build_ui(self):
        for row in range(20):
            self.parent.grid_rowconfigure(
                row,
                weight=0
            )

        for col in range(20):
            self.parent.grid_columnconfigure(
                col,
                weight=0
            )
        self.parent.grid_rowconfigure(1, weight=1)
        self.parent.grid_columnconfigure(0, weight=1)

        #
        # Toolbar
        #

        #
        # Toolbar
        #

        toolbar = ctk.CTkFrame(self.parent)

        toolbar.grid(
            row=0,
            column=0,
            sticky="ew",
            padx=5,
            pady=(5, 2)
        )

        #
        # Keep toolbar at natural height
        #

        toolbar.grid_rowconfigure(0, weight=0)

        #
        # Left controls
        #

        ctk.CTkRadioButton(
            toolbar,
            text="Year",
            variable=self.view_mode,
            value="year",
            command=self.refresh
        ).grid(
            row=0,
            column=0,
            padx=(5, 2),
            pady=4,
            sticky="w"
        )

        ctk.CTkRadioButton(
            toolbar,
            text="Month",
            variable=self.view_mode,
            value="month",
            command=self.refresh
        ).grid(
            row=0,
            column=1,
            padx=2,
            pady=4,
            sticky="w"
        )

        ctk.CTkLabel(
            toolbar,
            text="Category:"
        ).grid(
            row=0,
            column=2,
            padx=(15, 2),
            pady=4,
            sticky="w"
        )

        self.category_cb = ctk.CTkComboBox(
            toolbar,
            values=["All"],
            variable=self.filter_category,
            command=lambda _: self.refresh()
        )

        self.category_cb.grid(
            row=0,
            column=3,
            padx=2,
            pady=4,
            sticky="ew"
        )

        ctk.CTkLabel(
            toolbar,
            text="Alias:"
        ).grid(
            row=0,
            column=4,
            padx=(15, 2),
            pady=4,
            sticky="w"
        )

        self.alias_cb = ctk.CTkComboBox(
            toolbar,
            values=["All"],
            variable=self.filter_alias,
            command=lambda _: self.refresh()
        )

        self.alias_cb.grid(
            row=0,
            column=5,
            padx=2,
            pady=4,
            sticky="ew"
        )

        #
        # This column absorbs all extra width
        #

        toolbar.grid_columnconfigure(
            6,
            weight=1
        )

        #
        # Right buttons
        #
        '''
        ctk.CTkButton(
            toolbar,
            text="Import CSV",
            command=self.import_csv
        ).grid(
            row=0,
            column=7,
            padx=2,
            pady=4
        )

        ctk.CTkButton(
            toolbar,
            text="Export CSV",
            command=self.export_csv
        ).grid(
            row=0,
            column=8,
            padx=2,
            pady=4
        )
        '''
        ctk.CTkButton(
            toolbar,
            text="Expand",
            command=self.expand_all
        ).grid(
            row=0,
            column=9,
            padx=2,
            pady=4
        )

        ctk.CTkButton(
            toolbar,
            text="Collapse",
            command=self.collapse_all
        ).grid(
            row=0,
            column=10,
            padx=(2, 5),
            pady=4
        )

        #
        # Tree area
        #

        tree_frame = ctk.CTkFrame(self.parent)

        tree_frame.grid(
            row=1,
            column=0,
            sticky="nsew",
            padx=5,
            pady=(2, 5)
        )

        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)

        self.tree = ttk.Treeview(
            tree_frame,
            show="tree headings"
        )

        self.tree.grid(
            row=0,
            column=0,
            sticky="nsew"
        )

        vscroll = ttk.Scrollbar(
            tree_frame,
            orient="vertical",
            command=self.tree.yview
        )

        vscroll.grid(
            row=0,
            column=1,
            sticky="ns"
        )

        hscroll = ttk.Scrollbar(
            tree_frame,
            orient="horizontal",
            command=self.tree.xview
        )

        hscroll.grid(
            row=1,
            column=0,
            sticky="ew"
        )

        self.tree.configure(
            yscrollcommand=vscroll.set,
            xscrollcommand=hscroll.set
        )

        self.tree.bind(
            "<Double-1>",
            self.show_transactions
        )
        
    def show_transactions(self, event=None):
        iid = self.tree.focus()

        if not iid:
            return

        label = self.tree.item(
            iid,
            "text"
        )

        parent = self.tree.parent(iid)
        grandparent = self.tree.parent(parent)

        if not parent:

            where_sql = """
            WHERE Category = ?
            """

            params = (label,)

        elif parent and not grandparent:

            where_sql = """
            WHERE Category = ?
              AND SubCategory = ?
            """

            params = (
                self.tree.item(parent, "text"),
                label,
            )

        else:

            where_sql = """
            WHERE Alias = ?
            """

            params = (label,)

        TransactionDrilldownDialog(
            self.parent,
            self.conn,
            self.refresh,
            where_sql,
            params,
            f"Transactions - {label}"
        )
    
    
    def fetch_rows(self):

        sql = """
        SELECT
            Date,
            Alias,
            Category,
            SubCategory,
            Amount
        FROM transactions
        """

        if self.date_range:

            sql += """
            WHERE date(Date)
            BETWEEN date(?)
            AND date(?)
            """

            params = (
                self.date_range[0],
                self.date_range[1]
            )

        else:
            params = ()

        cur = self.conn.cursor()

        for row in cur.execute(sql, params):
            yield row
            
    def period_key(self, dt):

        dt = datetime.fromisoformat(dt)

        if self.view_mode.get() == "year":
            return f"{dt.year:04d}"

        return f"{dt.year:04d}-{dt.month:02d}"
        
    def aggregate(self):

        data = defaultdict(
            lambda: defaultdict(
                lambda: defaultdict(
                    lambda: defaultdict(float)
                )
            )
        )

        periods = set()

        for d, alias, cat, subcat, amount in self.fetch_rows():

            if (
                self.filter_category.get() != "All"
                and cat != self.filter_category.get()
            ):
                continue

            if (
                self.filter_alias.get() != "All"
                and alias != self.filter_alias.get()
            ):
                continue

            period = self.period_key(d)

            periods.add(period)

            data[cat][subcat][alias][period] += float(amount)

        self.periods = sorted(periods)
        self.tree_data = data
        
    def refresh(self):

        self.aggregate()
        self.build_columns()
        self.populate_tree()
        self.refresh_filters()
        
    def build_columns(self):

        cols = self.periods + ["Total", "Pct"]

        self.tree["columns"] = cols

        self.tree.heading(
            "#0",
            text="Category / SubCategory / Alias"
        )

        for col in cols:

            self.tree.heading(
                col,
                text=col,
                command=lambda c=col:
                hierarchical_sort_children(
                    self.tree,
                    "",
                    c
                )
            )
        
            self.tree.column(
                col,
                width=100,
                minwidth=40,
                stretch=False,
                anchor="e"
            )
            
        self.tree.column(
            "#0",
            width=300,
            minwidth=300,
            stretch=False
        )   

    def row_values(self, period_dict, pct=None):

        values = []

        total = 0.0

        for period in self.periods:

            amount = period_dict.get(
                period,
                0.0
            )

            total += amount

            values.append(
                ""
                if abs(amount) < 0.0001
                else f"{amount:,.2f}"
            )

        values.append(
            ""
            if abs(total) < 0.0001
            else f"{total:,.2f}"
        )

        values.append(
            ""
            if pct is None
            else f"{pct:.1f}%"
        )

        return values   
        
    def populate_tree(self):

        self.tree.delete(*self.tree.get_children())

        #
        # First pass - determine grand totals
        #

        grand_periods = defaultdict(float)

        for category, subcats in self.tree_data.items():

            for subcategory, aliases in subcats.items():

                for alias, period_dict in aliases.items():

                    for period, amount in period_dict.items():

                        grand_periods[period] += amount

        grand_total_amount = sum(
            grand_periods.values()
        )

        #
        # Second pass - build tree
        #

        for category, subcats in sorted(self.tree_data.items()):

            category_periods = defaultdict(float)

            subcat_nodes = []

            for subcategory, aliases in sorted(subcats.items()):

                subcat_periods = defaultdict(float)

                alias_nodes = []

                #
                # Alias rows
                #

                for alias, period_dict in sorted(aliases.items()):

                    alias_periods = defaultdict(
                        float,
                        period_dict
                    )

                    alias_id = self.tree.insert(
                        "",
                        "end",
                        text=alias,
                        values=self.row_values(
                            alias_periods,
                            None
                        ),
                        tags=("lvl2",)
                    )

                    alias_nodes.append(alias_id)

                    for period, amount in alias_periods.items():

                        subcat_periods[period] += amount

                #
                # SubCategory row
                #

                subcat_id = self.tree.insert(
                    "",
                    "end",
                    text=subcategory,
                    values=self.row_values(
                        subcat_periods,
                        None
                    ),
                    tags=("lvl1",)
                )

                for alias_id in alias_nodes:

                    self.tree.move(
                        alias_id,
                        subcat_id,
                        "end"
                    )

                subcat_nodes.append(subcat_id)

                #
                # Roll SubCategory into Category
                #

                for period, amount in subcat_periods.items():

                    category_periods[period] += amount

            #
            # Category row
            #

            category_total = sum(
                category_periods.values()
            )

            category_pct = (
                (category_total * 100.0) / grand_total_amount
                if grand_total_amount
                else 0.0
            )

            category_id = self.tree.insert(
                "",
                "end",
                text=category,
                values=self.row_values(
                    category_periods,
                    category_pct
                ),
                tags=("lvl0",)
            )

            for subcat_id in subcat_nodes:

                self.tree.move(
                    subcat_id,
                    category_id,
                    "end"
                )

        #
        # Grand Total row
        #

        self.tree.insert(
            "",
            "end",
            text="GRAND TOTAL",
            values=self.row_values(
                grand_periods,
                100.0
            ),
            tags=("grand-total",)
        )

        self.expand_all(level=1)
        self.collapse_all()
        
    def expand_all(self, level=None):
    
        def expand_node(node="", current_level=0):

            children = self.tree.get_children(node)

            if not children:
                return

            if level is None or current_level < level:
                self.tree.item(node, open=True)

                for child in children:
                    expand_node(
                        child,
                        current_level + 1
                    )

        for root in self.tree.get_children():
            expand_node(root, 0)
            
    def collapse_all(self):
        for item in self.tree.get_children():
            self._collapse_recursive(item)
            
    def _collapse_recursive(self, item):

        self.tree.item(
            item,
            open=False
        )

        for child in self.tree.get_children(item):
            self._collapse_recursive(child)

    def refresh_filters(self):
        cur = self.conn.cursor()

        categories = ["All"]
        aliases = ["All"]

        for (cat,) in cur.execute(
            """
            SELECT DISTINCT Category
            FROM transactions
            ORDER BY Category
            """
        ):
            categories.append(cat)

        for (alias,) in cur.execute(
            """
            SELECT DISTINCT Alias
            FROM transactions
            ORDER BY Alias
            """
        ):
            aliases.append(alias)

        self.category_cb.configure(
            values=categories
        )

        self.alias_cb.configure(
            values=aliases
        )

        if self.filter_category.get() not in categories:
            self.filter_category.set("All")

        if self.filter_alias.get() not in aliases:
            self.filter_alias.set("All")

    def export_csv(self):

        filename = filedialog.asksaveasfilename(
            defaultextension=".csv"
        )

        if not filename:
            return

        cur = self.conn.cursor()

        with open(
            filename,
            "w",
            newline="",
            encoding="utf-8"
        ) as f:

            writer = csv.writer(f)

            writer.writerow([
                "Date",
                "Alias",
                "Number",
                "Amount",
                "Category",
                "SubCategory",
            ])

            for row in cur.execute(
                """
                SELECT
                    Date,
                    Alias,
                    Number,
                    Amount,
                    Category,
                    SubCategory
                FROM transactions
                ORDER BY Date
                """
            ):
                writer.writerow(row)
        
class TransactionDrilldownDialog(ctk.CTkToplevel):

    def __init__(
        self,
        parent,
        conn,
        refresh_callback,
        where_sql,
        params,
        title
    ):
        super().__init__(parent)

        self.conn = conn
        self.refresh_callback = refresh_callback
        self.where_sql = where_sql
        self.params = params

        self.title(title)
        self.geometry("1100x500")

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        cols = (
            "Id",
            "Date",
            "Alias",
            "Number",
            "Amount",
            "Category",
            "SubCategory",
        )

        self.tree = ttk.Treeview(
            self,
            columns=cols,
            show="headings"
        )

        for col in cols:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=120)
        self.tree.column("Pct", width=80, anchor="e")
        
        self.tree.grid(
            row=0,
            column=0,
            sticky="nsew",
            padx=5,
            pady=5
        )

        btn_frame = ctk.CTkFrame(self)
        btn_frame.grid(
            row=1,
            column=0,
            sticky="ew",
            padx=5,
            pady=5
        )

        ctk.CTkButton(
            btn_frame,
            text="Add",
            command=self.add_transaction
        ).pack(side="left", padx=5)

        ctk.CTkButton(
            btn_frame,
            text="Edit",
            command=self.edit_transaction
        ).pack(side="left", padx=5)

        ctk.CTkButton(
            btn_frame,
            text="Delete",
            command=self.delete_transaction
        ).pack(side="left", padx=5)

        self.load_data()
        
    def load_data(self):

        self.tree.delete(
            *self.tree.get_children()
        )

        sql = f"""
        SELECT
            Id,
            Date,
            Alias,
            Number,
            Amount,
            Category,
            SubCategory
        FROM transactions
        {self.where_sql}
        ORDER BY Date
        """

        cur = self.conn.cursor()

        for row in cur.execute(
            sql,
            self.params
        ):
            self.tree.insert(
                "",
                "end",
                values=row
            )
            
    def add_transaction(self):

        TransactionEditorDialog(
            self,
            self.conn,
            None,
            self.after_edit
        )
        
    def edit_transaction(self):

        iid = self.tree.focus()

        if not iid:
            return

        values = self.tree.item(
            iid,
            "values"
        )

        TransactionEditorDialog(
            self,
            self.conn,
            values,
            self.after_edit
        )
        
    def delete_transaction(self):

        iid = self.tree.focus()

        if not iid:
            return

        values = self.tree.item(
            iid,
            "values"
        )

        tid = values[0]

        if not messagebox.askyesno(
            "Delete",
            f"Delete transaction {tid}?"
        ):
            return

        cur = self.conn.cursor()

        cur.execute(
            "DELETE FROM transactions WHERE Id=?",
            (tid,)
        )

        self.load_data()
        self.refresh_callback()
        
    def after_edit(self):

        self.load_data()
        self.refresh_callback()
        
class TransactionEditorDialog(ctk.CTkToplevel):

    def __init__(
        self,
        parent,
        conn,
        record,
        callback,
    ):
        super().__init__(parent)

        self.conn = conn
        self.record = record
        self.callback = callback

        self.title("Transaction")
        self.geometry("550x350")

        labels = [
            "Date",
            "Alias",
            "Number",
            "Amount",
            "Category",
            "SubCategory",
        ]

        defaults = [
            datetime.today().strftime("%Y-%m-%d"),
            "",
            "",
            "0.00",
            "",
            "",
        ]

        if record:
            defaults = list(record[1:])

        self.entries = []

        for row, text in enumerate(labels):

            ctk.CTkLabel(
                self,
                text=text,
            ).grid(
                row=row,
                column=0,
                sticky="e",
                padx=5,
                pady=5,
            )

            entry = ctk.CTkEntry(
                self,
                width=300
            )

            entry.grid(
                row=row,
                column=1,
                sticky="ew",
                padx=5,
                pady=5,
            )

            entry.insert(
                0,
                str(defaults[row])
            )

            self.entries.append(entry)

        self.grid_columnconfigure(
            1,
            weight=1
        )

        ctk.CTkButton(
            self,
            text="Save",
            command=self.save
        ).grid(
            row=len(labels),
            column=0,
            columnspan=2,
            pady=10
        )
        
    def save(self):

        values = [
            e.get().strip()
            for e in self.entries
        ]

        (
            date_value,
            alias,
            number,
            amount,
            category,
            subcategory,
        ) = values

        try:
            datetime.fromisoformat(
                date_value
            )
        except Exception:
            messagebox.showerror(
                "Error",
                "Invalid Date"
            )
            return

        try:
            amount = float(amount)
        except Exception:
            messagebox.showerror(
                "Error",
                "Invalid Amount"
            )
            return

        cur = self.conn.cursor()

        if self.record:

            cur.execute(
                """
                UPDATE transactions
                SET
                    Date=?,
                    Alias=?,
                    Number=?,
                    Amount=?,
                    Category=?,
                    SubCategory=?
                WHERE Id=?
                """,
                (
                    date_value,
                    alias,
                    number,
                    amount,
                    category,
                    subcategory,
                    self.record[0],
                )
            )
        else:

            cur.execute(
                """
                INSERT INTO transactions(
                    Date,
                    Alias,
                    Number,
                    Amount,
                    Category,
                    SubCategory
                )
                VALUES(?,?,?,?,?,?)
                """,
                (
                    date_value,
                    alias,
                    number,
                    amount,
                    category,
                    subcategory,
                )
            )

        self.callback()
        self.destroy()
        
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

class ChartDialog(ctk.CTkToplevel):

    def __init__(
        self,
        parent,
        title,
        data
    ):
        super().__init__(parent)

        self.title(title)
        self.geometry("1000x600")

        figure = Figure(
            figsize=(8, 5),
            dpi=100
        )

        axis = figure.add_subplot(111)

        labels = list(data.keys())
        values = list(data.values())

        axis.bar(
            labels,
            values
        )

        axis.set_title(title)

        canvas = FigureCanvasTkAgg(
            figure,
            self
        )

        canvas.draw()

        canvas.get_tk_widget().pack(
            fill="both",
            expand=True
        )
        
import sys
if __name__ == "__main__":
    #lgh = log_setup(__file__[:-3]+'.log') 
    root = tk.Tk()
    root.geometry("1000x600")
    def close_all():
            print('close_all')
            root.destroy()
            sys.exit()
    
    root.protocol("WM_DELETE_WINDOW", close_all) 

    date_range = ["2025-07-01","2026-12-31"]
    app = CategoryReportPanel(root, date_range=date_range)
    root.mainloop()