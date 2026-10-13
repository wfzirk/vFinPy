
# Python Includes
import sys
import locale
from datetime import datetime, date
import tkinter as tk
from tkinter import ttk
from tkcalendar import DateEntry

# 3rd Party Includes
import customtkinter as ctk


# Project Includes
from config import fin_config
from theme_manager import theme_manager  # automatically get theme updated
#from theme_manager import refresh_tree_colors

from finreport import CTkReportTree, getDuplicates
from logging_manager import get_logger
log = get_logger(__name__)

class SidePanel(ctk.CTkFrame):
    def __init__(self, panel, treeFrame):  #, client_exit):
        super().__init__(panel)   #, width=160)
        log.info('SidePanel Loaded')
        # Internal grid: 3 rows
        self.grid_rowconfigure(0, weight=0)   # dateFrame
        self.grid_rowconfigure(1, weight=1)   # report tree expands
        self.grid_rowconfigure(2, weight=0)   # bottom buttons
        self.grid_columnconfigure(0, weight=1)
        
        #self.client_exit = client_exit
        self.treeFrame = treeFrame

        self.report_tree = CTkReportTree(self, self.treeFrame, fin_config.daterange)
        self.report_tree.grid(row=1, column=0, sticky="nsew", padx=0, pady=0)

        self.btm = ctk.CTkFrame(self)
        self.btm.grid(row=2, column=0, sticky="ew", padx=0, pady=(2, 0))

        self.dateFrame = ctk.CTkFrame(self)
        self.dateFrame.grid(row=0, column=0, sticky="ew", padx=0, pady=(0, 2))

        try:
            locale.setlocale(locale.LC_ALL, '')
        except:
            pass

        self.daterange = fin_config.daterange
        if self.daterange:
            year_start = datetime.strptime(self.daterange[0], '%Y-%m-%d').date()
            year_end = datetime.strptime(self.daterange[1], '%Y-%m-%d').date()
        else:
            y = date.today().year
            year_start = date(y, 1, 1)
            year_end = date(y, 12, 31)

        ctk.CTkLabel(self.dateFrame, text="From").grid(row=0, column=0, sticky="w")
        self.datestart = DateEntry(self.dateFrame, width=10, style='my.DateEntry')
        self.datestart.grid(row=1, column=0, sticky="w", padx=5)
        self.datestart.set_date(year_start)
        self.datestart.bind("<<DateEntrySelected>>", self.dateselected)

        ctk.CTkLabel(self.dateFrame, text="To").grid(row=0, column=1, sticky="w")
        self.dateend = DateEntry(self.dateFrame, width=10, style='my.DateEntry')
        self.dateend.grid(row=1, column=1, sticky="e", padx=5)
        self.dateend.set_date(year_end)
        self.dateend.bind("<<DateEntrySelected>>", self.dateselected)

        self.var_all_dates = tk.BooleanVar()
        #ctk.CTkLabel(self.dateFrame, text="All Dates").grid(row=2, column=0, sticky="w")
        ctk.CTkCheckBox(self.dateFrame, text="All Dates", variable=self.var_all_dates, command=self.on_datechk_change).grid(row=2, column=0, columnspan=2, sticky="e", padx=15)

        # -------------------------
        # BOTTOM BUTTONS
        # -------------------------
        #ctk.CTkButton(self.btm, text="Quit", width=10, command=self.client_exit).grid(row=0, column=0, padx=3)
        ctk.CTkButton(self.btm, text="Refresh", width=15, command=self.refresh).grid(row=0, column=1, padx=3)
        ctk.CTkButton(self.btm, text="Dup...", width=20, command=self.duplicates).grid(row=0, column=2, padx=3)

    # -------------------------
    # LOGIC METHODS
    # -------------------------

    def on_datechk_change(self):
        
        
        all_dates = self.var_all_dates.get()
        state = "disabled" if all_dates else "normal"
        self.datestart.configure(state=state)
        self.dateend.configure(state=state)

    def refresh(self, *args):
        self.report_tree.refresh()

    def duplicates(self, *args):
        self.report_tree.duplicates()

    def dateselected(self, *args):
        ds = self.datestart.get_date().strftime("%Y-%m-%d")
        de = self.dateend.get_date().strftime("%Y-%m-%d")
        self.daterange = [ds, de]
        fin_config.set_daterange(ds,de)
        self.refresh()

