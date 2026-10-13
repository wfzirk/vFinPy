import locale
from datetime import datetime, date

import customtkinter as ctk
import tkinter as tk
from tkinter import ttk
from tkcalendar import DateEntry

from logging_manager import get_logger
log = get_logger(__name__)

import settings
import finReport as rpt


class SidePanel(ctk.CTkFrame):
    def __init__(self, panel, treeFrame, client_exit):
        super().__init__(panel, fg_color="transparent")

        self.panel = panel
        self.treeFrame = treeFrame
        self.client_exit = client_exit

        self.bg, self.fg = settings.getColors("leftside")
        log.info("sidepanel")

        # ---------------- Date Frame (CTk) ----------------
        self.dateFrame = ctk.CTkFrame(self, fg_color=self.bg)
        self.dateFrame.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)

        # ---------------- Tk Frame INSIDE CTkFrame (critical) ----------------
        # MUST use pack() so CTk canvas does NOT clip it
        self.dateFrame_tk = tk.Frame(self.dateFrame, bg=self.bg)
        self.dateFrame_tk.pack(fill="both", expand=True)

        # ---------------- Left Side ----------------
        self.leftSide = ctk.CTkFrame(self, fg_color=self.bg)
        self.leftSide.grid(row=1, column=0, sticky="nsew", padx=5, pady=(0, 5))

        # ---------------- Bottom Buttons ----------------
        self.btm = ctk.CTkFrame(self, fg_color=self.bg)
        self.btm.grid(row=2, column=0, sticky="ew", padx=5, pady=5)

        # ---------------- Locale ----------------
        try:
            locale.setlocale(locale.LC_ALL, "")
        except locale.Error as ex:
            log.exception("Locale error: %s", ex)

        # ---------------- Date Range Init ----------------
        self.daterange = settings.stg.daterange

        if self.daterange:
            year_start = datetime.strptime(self.daterange[0], "%Y-%m-%d").date()
            year_end = datetime.strptime(self.daterange[1], "%Y-%m-%d").date()
        else:
            epoch = date.today().year
            year_start = date(epoch, 1, 1)
            year_end = date(epoch, 12, 31)
            self.daterange = [year_start, year_end]

        # ---------------- DateEntry Styling ----------------
        style = ttk.Style()
        style.theme_use("clam")
        style.configure(
            "my.DateEntry",
            fieldbackground="white",
            background="white",
            foreground="black",
            arrowcolor="black",
        )

        # ---------------- Date Widgets ----------------
        self.var_all_dates = tk.BooleanVar()

        tk.Label(self.dateFrame_tk, text="From Date", bg=self.bg, fg=self.fg).grid(
            row=0, column=0, sticky="w"
        )
        self.datestart = DateEntry(
            self.dateFrame_tk, width=12, style="my.DateEntry"
        )
        self.datestart.grid(row=1, column=0, sticky="w", pady=2)
        self.datestart.set_date(year_start)
        self.datestart.bind("<<DateEntrySelected>>", self.dateselected)

        tk.Label(self.dateFrame_tk, text="To Date", bg=self.bg, fg=self.fg).grid(
            row=0, column=1, sticky="w"
        )
        self.dateend = DateEntry(
            self.dateFrame_tk, width=12, style="my.DateEntry"
        )
        self.dateend.grid(row=1, column=1, sticky="w", pady=2)
        self.dateend.set_date(year_end)
        self.dateend.bind("<<DateEntrySelected>>", self.dateselected)

        tk.Label(self.dateFrame_tk, text="All Dates", bg=self.bg, fg=self.fg).grid(
            row=2, column=0, sticky="w"
        )
        ttk.Checkbutton(
            self.dateFrame_tk,
            variable=self.var_all_dates,
            command=self.on_datechk_change,
            takefocus=False
        ).grid(row=2, column=1, sticky="w")

        # ---------------- Bottom Buttons ----------------
        ctk.CTkButton(self.btm, text="Quit", width=70, command=self.client_exit).grid(
            row=0, column=0, padx=5
        )
        ctk.CTkButton(self.btm, text="Refresh", width=90, command=self.refresh).grid(
            row=0, column=1, padx=5
        )
        ctk.CTkButton(self.btm, text="Duplicates", width=110, command=self.duplicates).grid(
            row=0, column=2, padx=5
        )

        # ---------------- Report Tree ----------------
        self.rfsh = rpt.reportTree(self.leftSide, self.treeFrame, settings.stg["daterange"])

    # ------------------------------------------------------------------
    # EVENT HANDLERS
    # ------------------------------------------------------------------
    def on_datechk_change(self):
        all_dates = self.var_all_dates.get()

        if all_dates:
            self.datestart.configure(state="disabled")
            self.dateend.configure(state="disabled")
        else:
            self.datestart.configure(state="normal")
            self.dateend.configure(state="normal")

    def refresh(self):
        log.info("refresh")
        self.rfsh.refresh()

        for w in self.treeFrame.winfo_children():
            w.destroy()
        for w in self.leftSide.winfo_children():
            w.destroy()

        self.rfsh = rpt.reportTree(self.leftSide, self.treeFrame, settings.stg["daterange"])

    def duplicates(self):
        self.rfsh.duplicates()

    def dateselected(self, *args):
        ds = self.datestart.get_date().strftime("%Y-%m-%d")
        de = self.dateend.get_date().strftime("%Y-%m-%d")

        self.daterange = [ds, de]
        settings.stg["daterange"] = self.daterange

        log.info("daterange %s", self.daterange)
        self.refresh()
        return self.daterange
