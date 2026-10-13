# finrules/qfx_treeutils.py

# Python Includes
import tkinter as tk
from tkinter import ttk

# 3rd Party Includes

#project imports
from config import fin_config,  TWIDTH, TANCHOR, TSTRETCH

def clear_tree(tree):
    """
    Remove all rows from a Treeview.
    """

    children = tree.get_children()

    for item_id in children:
        tree.delete(item_id)


def configure_zebra_rows(
    tree,
    even_bg="#ddeeff",
    odd_bg="#eaffff",
):
    """
    Configure alternating row colors.
    """

    tree.tag_configure(
        "evenrow",
        background=even_bg
    )

    tree.tag_configure(
        "oddrow",
        background=odd_bg
    )


def sortby_column(tree, column, descending=False):
    """
    Sort a Treeview column.
    """

    rows = []

    children = tree.get_children()

    for item_id in children:
        value = tree.set(item_id, column)
        rows.append((value, item_id))

    try:
        rows.sort(
            key=lambda row: float(row[0]),
            reverse=descending
        )
    except Exception:
        rows.sort(
            key=lambda row: str(row[0]).lower(),
            reverse=descending
        )

    index = 0

    for value, item_id in rows:
        tree.move(
            item_id,
            "",
            index
        )
        index += 1

    tree.heading(
        column,
        command=lambda: sortby_column(
            tree,
            column,
            not descending
        )
    )


def enable_column_sorting(tree):
    """
    Enable sorting on all columns.
    """

    columns = tree["columns"]

    for column in columns:

        tree.heading(
            column,
            command=lambda c=column: sortby_column(
                tree,
                c,
                False
            )
        )

def sizeTreeColumns(tree, col_attr, font, sortColumns=True):
    #===============================
    # Size columns from Settings.
    #===============================
    headers = tree['columns']

    for column in headers:
        if column in col_attr.keys():
            w = col_attr[column][TWIDTH] * font['size']
            a = col_attr[column][TANCHOR]
            s = col_attr[column][TSTRETCH]
            
        else:
            w = 12 * font['size']     # width
            a = 'w'     # anchor
            s = True    # stretch
        #print(column, type(s),s)
        if sortColumns:
            tree.heading(column, text=column, command=lambda c=column: sortby_column(tree, c, 1))
        else:
            tree.heading(column, text=column)
            
        tree.column(column, anchor=a,width=w, stretch=s)
        
def sizeTreeColumnsFromContent(tree, font, min_width=80, max_width=600):
    #===============================
    # Auto size columns from content.
    #===============================

    columns = tree["columns"]

    for column in columns:
        width = font.measure(column)
        children = tree.get_children()
        for item_id in children:
            value = tree.set(
                item_id,
                column
            )
            text_width = font.measure(
                str(value)
            )
            if text_width > width:
                width = text_width
        width += 30

        if width < min_width:
            width = min_width

        if width > max_width:
            width = max_width

        tree.column(column, width=width)

def insert_transaction_rows(
    tree,
    transactions
):
    #=================================================
    # Insert transactions using alternating row colors.
    #=================================================
    clear_tree(tree)

    row_num = 0

    for tx in transactions:

        if row_num % 2 == 0:
            tag = "evenrow"
        else:
            tag = "oddrow"

        tree.insert(
            "",
            "end",
            tags=(tag,),
            values=(
                tx.get("date", ""),
                tx.get("amount", ""),
                tx.get("description", ""),
                tx.get("fitid", ""),
                tx.get("type", ""),
                tx.get("number", "")
            )
        )

        row_num += 1