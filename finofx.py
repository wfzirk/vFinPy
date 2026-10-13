# finofx.py
#from __init__ import __version__
from version import __version__


"""
    -- Required imports --
    apsw_sqlite3mc==3.53.4.0
    babel==2.18.0
    contourpy==1.3.3
    customtkinter==6.0.0
    cycler==0.12.1
    darkdetect==0.8.0
    fonttools==4.64.0
    kiwisolver==1.5.1
    matplotlib==3.11.1
    numpy==2.5.2
    packaging==26.3
    pillow==12.3.0
    pyparsing==3.3.2
    pyperclip==1.11.0
    python-dateutil==2.9.0.post0
    six==1.17.0
    tkcalendar==1.6.1
"""

# Python Includes
import sys
import os
if not os.path.exists("logs"):
    os.makedirs("logs")
if not os.path.exists("rules"):
    os.makedirs("rules")
if not os.path.exists("output"):
    os.makedirs("output")


#import signal
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
from tkinter.messagebox import askyesnocancel
import subprocess
import tkinter.colorchooser as tk_colorchooser
from time import perf_counter

# 3rd Party Includes
import customtkinter as ctk
from customtkinter import ThemeManager

# Project Includes
parentdir = os.path.dirname(__file__)
sys.path.append(os.path.join(parentdir, '..'))

from config import fin_config   #FinanceConfig
from theme_manager import theme_manager  # automatically get theme updated
from theme_editor import ThemeEditor
from config_editor import ConfigEditor
from finrules.rules_console_app import RulesConsoleApp
import apswSql as sql
from password import OpenDBDialog,  CreateEncryptedDBDialog, PasswordChangeDialog
from util import mkdirp
import sidepanel as sp
from qfx_viewer import QFXViewer
from rollingBackup import backup
from copytable import copyTable
import window_pos as win_pos
from tooltip import Tooltip
from status_bus import StatusBus,  show_timing_details
from logging_manager import get_logger   #, open_logs_folder

log = get_logger(__name__)
print(__name__)
class CustomMenuBarApp(ctk.CTkFrame):

    def __init__(self, parent):
        super().__init__(
            parent,
            fg_color="transparent",   # no background padding
            corner_radius=0,
            border_width=0,
            height=50
        )
        
        self.grid_propagate(False)

        # Appearance settings
        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("dark-blue")

        self._build_widgets()

    # ---------------------------------------------------------
    # Event Handlers
    # ---------------------------------------------------------
    def button_callback(self):
        log.info("Button click %s", self.combobox_1.get())

    def change_appearance_mode_event(self, new_mode: str):
        ctk.set_appearance_mode(new_mode)

    def change_scaling_event(self, new_scaling: str):
        scale = int(new_scaling.replace("%", "")) / 100
        ctk.set_widget_scaling(scale)

    # ---------------------------------------------------------
    # UI Construction
    # ---------------------------------------------------------

    def _build_widgets(self):

        # --- FILE MENU ---
        self.file_menu = ctk.CTkOptionMenu(
            self,
            values=[
                "Open DB",
                "New DB",
                #"View Qfx File",
                "QFX Classifier",
                #"Import CSV",
                #"Qfx/Ofx to CSV",
                #"Export Table to CSV",
                "Exit"
            ],
            command=self._file_menu_action
        )
        self.file_menu.set("File")
        self.file_menu.grid(row=0, column=0, padx=5, pady=0)

        # --- TOOLS MENU ---
        self.tools_menu = ctk.CTkOptionMenu(
            self,
            values=[
                "Add/Change Password",
                "Open Logs Folder",
                "Import CSV to Table",
                "Export Table to CSV",
                "Settings",
                "Timings"
            ],
            command=self._tools_menu_action
        )
        self.tools_menu.set("Tools")
        self.tools_menu.grid(row=0, column=1, padx=5, pady=0)

        # --- THEME MENU ---
        theme_values = [
            "Theme Editor",
            "Dark Mode",
            "Light Mode",
            "System Mode",
            "Blue",
            "Dark Blue",
            "Green"
        ]

        # Add theme files from ctk_themes folder
        directory_path = "ctk_themes"
        try:
            files = [
                f for f in os.listdir(directory_path)
                if os.path.isfile(os.path.join(directory_path, f))
            ]
            theme_values.extend(files)
        except Exception:
            pass

        self.theme_menu = ctk.CTkOptionMenu(
            self,
            values=theme_values,
            command=self._theme_menu_action
        )
        self.theme_menu.set("Theme")
        self.theme_menu.grid(row=0, column=2, padx=5, pady=0)

        # --- HELP MENU ---
        self.help_menu = ctk.CTkOptionMenu(
            self,
            values=[
                "Help Index",
                "About"
            ],
            command=self._help_menu_action
        )
        self.help_menu.set("Help")
        self.help_menu.grid(row=0, column=5, padx=5, pady=0)
        
                
        Tooltip(self.file_menu, "Open or create encrypted finance databases")
        Tooltip(self.tools_menu, "CSV import/export, password tools, logs")
        Tooltip(self.theme_menu, "Switch appearance mode or load custom themes")
        Tooltip(self.help_menu, "Help Index and About dialog")

    def _file_menu_action(self, choice):
        app = self.master.app  # reference to App instance

        match choice:
            case "Open DB": app.openDB()
            case "New DB": app.newDB()
            #case "View QFX File": app.qfx_view()
            case "QFX Classifier": app.qfx_classify()
            case "Import CSV": app.importCSV()
            #case "Qfx/Ofx to CSV": app.ofx2CSV()
            case "Exit": app.app_exit()

    def _tools_menu_action(self, choice):
        app = self.master.app
        match choice:
            case "Settings": ConfigEditor()
            case "Add/Change Password": app.change_password()
            case "Open Logs Folder": open_logs_folder()
            case "Import CSV to Table": self.show_csv_menu("import")
            case "Export Table to CSV": self.show_csv_menu("export")
            case "Timings": show_timing_details()
   
    def show_csv_menu(self, import_export):
        win = ctk.CTkToplevel(self)
        win.title("Select Table for CSV Import")
        win.geometry("300x150")
        win.resizable(False, False)
        win.grab_set()
        
        def import_csv(tbl):
            log.info('import csv %s', tbl)
            sql.import_csv_to_table(tbl)
            win.destroy()
         
        def export_csv(tbl):
            log.info('export to csv %s', tbl)
            sql.export_table_to_csv(tbl)
            win.destroy()
        
        # Tables you support
        #table_list = ["transactions", "accounts", "patterns"]
        table_list = sql.getTables()
        
        if import_export == "export":
            label = ctk.CTkLabel(win, text="Export which table?")
        else:    
            label = ctk.CTkLabel(win, text="Import CSV into which table?")
        label.pack(pady=10)
        
        if import_export == "export":
            menu = ctk.CTkOptionMenu(
                win,
                values=table_list,
                #command=lambda tbl: sql.import_csv_to_table(tbl)  #, win)
                command=lambda tbl: export_csv(tbl)
            )
        else:    
            menu = ctk.CTkOptionMenu(
                win,
                values=table_list,
                #command=lambda tbl: sql.import_csv_to_table(tbl)  #, win)
                command=lambda tbl: import_csv(tbl)
            )
        menu.set("Select Table")
        menu.pack(pady=10)


    def _theme_menu_action(self, choice):
        app = self.master.app
        match choice:
            case "Theme Editor": ThemeEditor()
            case "Dark Mode": app.change_mode("dark")
            case "Light Mode": app.change_mode("light")
            case "System Mode": app.change_mode("system")
            case "Blue": app.switch_theme("blue")
            case "Dark Blue": app.switch_theme("dark-blue")
            case "Green": app.switch_theme("green")
            case _:  # theme file
                app.switch_theme(os.path.join("ctk_themes", choice))

    def _help_menu_action(self, choice):
        app = self.master.app
        match choice:
            case "Help Index": app.open_help_index()
            case "About": app.open_about_dialog()

class App:
    
    def __init__(self, root):  
        self.root = root
        self.root.app = self  # lets the menubar call back into the App instance
        self.fin_config = fin_config
        
        self.status_var = tk.StringVar(value="Ready")
        self.perf_stats = {}
        
        self.root.title(f'Finance Utility FinOfx {__version__} {self.fin_config.secParams.fileName}')

        result = sql.init_db(self.root)      # verify all tables are present
        log.info(result)

        if result:
            log.exception('error %s', result)
            messagebox.showerror("ERROR", result)
            self.root.destroy()
            sys.exit()
            
        #self.timed_call("Database Init", sql.init_db, self.root)

        self.menu_bar = CustomMenuBarApp(self.root)
        self.menu_bar.grid(row=0, column=0, columnspan=2, sticky="ew")

        ctk.set_appearance_mode(fin_config.theme.appearance_mode)
        #ctk.set_default_color_theme(fin_config.theme.theme_name)
        theme_manager.apply_named_theme(
            self.root,
            self.fin_config.theme.theme_name
        )

        # ---------------------------------------------------------
        # MAIN LAYOUT
        # ---------------------------------------------------------
        #if not self.init_error:

        self.left = ctk.CTkFrame(self.root, corner_radius=0, border_width=2, border_color="green", width=160)
        self.left.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        self.left.grid_rowconfigure(0, weight=1)
        self.left.grid_columnconfigure(0, weight=1)

        self.right = ctk.CTkFrame(self.root, corner_radius=0, border_width=2, border_color="green", width=980)

        self.right.grid(row=1, column=1, rowspan=2, sticky="nsew", padx=1, pady=1)

        self.right.grid_rowconfigure(1, weight=1)
        self.right.grid_columnconfigure(0, weight=1)
        self.right.grid_propagate(False)

        Tooltip(self.left, "Navigation panel: accounts, tables, tools")
        Tooltip(self.right, "Workspace area: views, tables, dialogs")

        # Status Bar
        
        self.status_frame = ctk.CTkFrame(
            self.root,
            corner_radius=0,
            height=28
        )

        self.status_frame.grid(
            row=2,
            column=0,
            columnspan=2,
            sticky="ew"
        )
        '''
        self.btn_clear_status = ctk.CTkButton(
            self.status_frame,
            text="Clear",
            width=70,
            command=self.clear_statusbar
        )

        self.btn_clear_status.pack(
            side="left",
            padx=2,
            pady=2
        )

        self.statusbar = ctk.CTkLabel(
            self.status_frame,
            textvariable=self.status_var,
            anchor="w"
        )
        
        self.statusbar.pack(
            side="left",
            fill="x",
            expand=True,
            padx=5
        )
        
        self.statusbar.bind(
            "<Button-1>",
            self.show_timing_details
        )
        '''
        self.root.grid_rowconfigure(0, weight=0)
        self.root.grid_rowconfigure(1, weight=1)
        self.root.grid_rowconfigure(2, weight=0)
       
        #StatusBus.register(self.set_status)
        # ---------------------------------------------------------
        # SIDEPANEL
        # ---------------------------------------------------------
        #if self.fin_config.secParams.fileName:
        #if not self.init_error:
        try:
            #self.spc = sp.SidePanel(self.left, self.right)   #, self.app_exit(self.root))
            start = perf_counter()

            self.spc = sp.SidePanel(
                self.left,
                self.right
            )   

            #self.set_status(
            #    f"SidePanel created in {perf_counter()-start:.3f}s"
            #)
            StatusBus.update_perf("Side Panel", perf_counter()-start)
            
            self.spc.grid(row=0, column=0, sticky="nsew")
   
        except Exception as ex:
            log.exception('error %s', ex)
            messagebox.showerror("ERROR", ex)
            self.root.destroy()
    ''' 
    def clear_statusbar(self):
        StatusBus.clear_perf() 
     
    def set_status(self, msg):
        log.info(f'set_status {msg}')
        self.status_var.set(msg)
        self.root.update_idletasks()

    from tkinter import ttk

    def show_timing_details(self, event=None):

        timings = StatusBus.get_perf()

        win = ctk.CTkToplevel(self.root)
        win.title("Performance Timings")
        win.geometry("300x350")
        win.after(100, win.lift)

        frame = ctk.CTkFrame(win)
        frame.pack(fill="both", expand=True, padx=10, pady=10)

        tree = ttk.Treeview(
            frame,
            columns=("operation", "seconds"),
            show="headings"
        )

        tree.tag_configure(
            "even",
            background="#fafafa"
        )
            
        tree.tag_configure(
            "odd",
            background="#e8eef7"
        )

        tree.tag_configure(
            "total",
            background="#cfe2f3",
            font=("Segoe UI", 10, "bold")
        )

        tree.heading("operation", text="Operation")
        tree.heading("seconds", text="Seconds")

        #tree.column("operation", width=500, anchor="w")
        #tree.column("seconds", width=120, anchor="e")
        tree.column("operation", width=180, anchor="w")
        tree.column("seconds", width=100, anchor="e", stretch=True)

        scroll = ttk.Scrollbar(
            frame,
            orient="vertical",
            command=tree.yview
        )

        tree.configure(yscrollcommand=scroll.set)

        tree.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")

        total = 0.0

        #for name, elapsed in timings.items():
        for row_num, (name, elapsed) in enumerate(timings.items()):
            total += elapsed
            tag = "even" if row_num % 2 == 0 else "odd"
            tree.insert(
                "",
                "end",
                values=(name, f"{elapsed:.3f}"),
                tags=(tag,)
            )

        tree.insert(
            "",
            "end",
            values=("─────────────────", "─────")
        )

        tree.insert(
            "",
            "end",
            values=("TOTAL", f"{total:.3f}"),
            tags=("total",)
        )
        
    def timed_call(self, name, func, *args, **kwargs):
        start = perf_counter()

        try:
            #StatusBus.set_status(f"{name} running...")
            return func(*args, **kwargs)

        finally:
            #elapsed = perf_counter() - start
            #self.set_status(f"{name}: {elapsed:.3f}s")
            #log.info("%s completed in %.3f sec", name, elapsed)  
            StatusBus.update_perf("Side Panel", perf_counter()-start)
    '''        

    def open_help_index(self):
        win = ctk.CTkToplevel(self.root)
        win.title("FinOfx Help Index")
        win.geometry("700x600")
        win.resizable(True, True)
        win.grab_set()

        text = ctk.CTkTextbox(win, wrap="word")
        text.pack(fill="both", expand=True, padx=10, pady=10)

        help_text = """
        FinOfx Help Index

        1. Databases
           - Open encrypted DB
           - Create new DB
           - Change password

        2. QFX/OFX Tools
           - View/Import OFX
           - QFX Classifier
           - Convert OFX/QFX to CSV

        3. CSV Tools
           - Import CSV into tables
           - Export tables to CSV

        4. Themes & Appearance
           - Light/Dark/System modes
           - Built-in color themes
           - Custom theme files

        5. Logs & Diagnostics
           - Open logs folder
           - Error reporting

        6. Window Behavior
           - Geometry persistence
           - Restart behavior after DB changes
        """

        text.insert("1.0", help_text)
        text.configure(state="disabled")

    def open_about_dialog(self):
        win = ctk.CTkToplevel(self.root)
        win.title("About FinOfx")
        win.geometry("400x300")
        win.resizable(False, False)
        win.grab_set()

        frame = ctk.CTkFrame(win)
        frame.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(frame, text=f"FinOfx {__version__}", font=("Segoe UI", 18, "bold")).pack(pady=10)
        ctk.CTkLabel(frame, text="A modular finance utility for encrypted DBs,\nQFX/OFX processing, and rule-based classification.", justify="center").pack(pady=10)

        #ctk.CTkLabel(frame, text=f"Python: {sys.version.split()[0]}\nTCL: {self.fin_config.TCLlevel}", justify="center").pack(pady=10)

        ctk.CTkButton(frame, text="OK", command=win.destroy).pack(pady=15)


    # -------------------------------------------------------------
    # THEME SWITCHING
    # -------------------------------------------------------------
    def switch_theme(self, name):
        self.fin_config.theme.theme_name = name
        theme_manager.apply_named_theme(
            self.root,
            name
        )
        for child in self.root.winfo_children():
            child.destroy()
            
        self.__init__(self.root)
        
    def change_mode(self, mode_name):
        self.fin_config.theme.appearance_mode = mode_name
        ctk.set_appearance_mode(mode_name)
        self.root.update_idletasks()

    #def open_theme_inspector(self):
    #    ThemeInspector(self.root)

    def color_chooser(self):
        color_tuple, color = tk_colorchooser.askcolor(title="Choose Accent Color")
        self.fin_config.theme.accent_color = color

    # -------------------------------------------------------------
    # MENU ACTIONS
    # -------------------------------------------------------------
    def donothing(self):
        pass

    def copyTable(self):
        copyTable()

    def viewOfx(self):
        #start = perf_counter()

        file = filedialog.askopenfilename(
            filetypes=(("Q/Ofx files", "*.?fx"), ("all files", "*.*"))
        )

        if file:
            QFXViewer().mainloop()

        #elapsed = perf_counter() - start
        #self.set_status(f"OFX Viewer: {elapsed:.3f}s")
    
    def qfx_view(self, qfx_path=None):
        app = RulesConsoleApp()

        if qfx_path:
            app.after(
                100,
                lambda: (
                    app.qfx_view_panel.load_qfx(qfx_path),
                    app.tabview.set("QFX Viewer")
                )
            )

        return app    
    
    def qfx_classify(self, qfx_path=None):
        app = RulesConsoleApp()

        if qfx_path:
            app.after(
                100,
                lambda: (
                    app.batch_panel.load_batch_file(qfx_path),
                    app.tabview.set("Batch Classifier")
                )
            )

        return app    
    
    def importCSV(self):
        pass
        #    sql.import_transactions_csv()
        log.info('option csv')
        

    def importOFX(self):
        subprocess.run('python readOfxGUI.py')
        self.fin_config._flush_save()
        os.execv(sys.executable, ['python'] + sys.argv)

    def change_password(self):
        dlg = PasswordChangeDialog(None)
        dlg.wait_window()

        if not dlg.result:
            return "error"

        self.fin_config.secParams.key = dlg.result["new_password"]
        filename = self.fin_config.secParams.fileName
        sql.change_password(filename, dlg.result["old_password"], dlg.result["new_password"])
        
        ext = sys.argv[0].split('.')[-1]
        self.fin_config._flush_save()
        if ext == 'exe':
            os.execv(sys.executable, [sys.argv[0]])
        else:
            os.execv(sys.executable, ['python'] + [sys.argv[0]])


    
    # -------------------------------------------------------------
    # DB OPEN / NEW
    # -------------------------------------------------------------
    def openDB(self):
        
        dlg = OpenDBDialog(None)     
        dlg.wait_window()
        if not dlg.result:
            return "error"

        self.fin_config.secParams.fileName = dlg.result["file"]
        self.fin_config.secParams.key = dlg.result["password"]
        self.fin_config.secParams.cipher = dlg.result["cipher"]
        self.fin_config.secParams.kdf_iter = dlg.result["kdf_iter"]
        
        ext = sys.argv[0].split('.')[-1]
        self.fin_config._flush_save()
        log.info(sys.argv)
        print(sys.argv)
        log.info(sys.argv[0])
        log.info(__file__)
        print(__file__)
        if ext == 'exe':
            os.execv(sys.executable, [sys.argv[0]])
        else:
            os.execv(sys.executable, ['python'] + [sys.argv[0]])

    def newDB(self):
        dlg = CreateEncryptedDBDialog(None)
        dlg.wait_window()

        if not dlg.result:
            return "error"
        self.fin_config.secParams.fileName = dlg.result["file"]
        self.fin_config.secParams.key = dlg.result["password"]
        self.fin_config.secParams.cipher = dlg.result["cipher"]
        self.fin_config.secParams.kdf_iter = dlg.result["kdf_iter"]
        
        ext = sys.argv[0].split('.')[-1]
        self.fin_config._flush_save()
        if ext == 'exe':
            os.execv(sys.executable, [sys.argv[0]])
        else:
            os.execv(sys.executable, ['python'] + [sys.argv[0]])

    # -------------------------------------------------------------
    # Loop Timing
    # -------------------------------------------------------------
    # reusable loop timing
    def loop_progress(self, title, current, total, start_time):

        if current % 100 == 0 or current == total:

            elapsed = perf_counter() - start_time

            self.set_status(
                f"{title}: {current:,}/{total:,} "
                f"({elapsed:.1f}s)"
            )
    ''' example:
        start = perf_counter()
        for idx, txn in enumerate(transactions, start=1):
            process_transaction(txn)
            app.loop_progress(
                "Classifying",
                idx,
                len(transactions),
                start
            )
    '''
    # -------------------------------------------------------------
    # Rolling execution history
    # -------------------------------------------------------------
    def update_perf(self, name, elapsed):

        self.perf_stats[name] = elapsed

        parts = []

        for k, v in self.perf_stats.items():
            parts.append(f"{k}:{v:.2f}s")

        self.status_var.set(" | ".join(parts))
    
    """  example
        elapsed = perf_counter() - start
        self.update_perf("DB", elapsed)
    """
    # -------------------------------------------------------------
    # EXIT HANDLING
    # -------------------------------------------------------------

    def app_exit(self, *args):
        print("exit", args)
        #win_pos.save_geometry(self.root)
        fin_config.window.geometry = self.root.winfo_geometry()
        fin_config._flush_save()   # force immediate write
        self.root.destroy()
    '''
    def protocol_exit(self, *args):
        self.app_exit(self.root, *args)

    def ctrlq_exit(self, *args):
        self.app_exit(*args)

    def menu_exit(self, *args):
        self.app_exit(*args)

    def signal_exit(self, *args):
        self.app_exit(*args)

    def client_exit(self, *args):
        pass
    '''

# -------------------------------------------------------------
# MAIN
# -------------------------------------------------------------
if __name__ == "__main__":

    try:
        root = ctk.CTk()
        #tcl = tk.Tcl()
        
        def close_all():
            print('close_all')
            win_pos.save_geometry(root)
            root.destroy()
            sys.exit()

    
        def resource_path(rel):
            # Nuitka onefile extracts into a temp folder stored in sys._MEIPASS
            base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
            return os.path.join(base, rel)

        root.geometry("1200x600+120+80")
        root.protocol("WM_DELETE_WINDOW", close_all)   
        #root.configure(fg_color='red')
        ICO = resource_path("assets/finofx.ico")
        try:
            root.iconbitmap(ICO)
        except Exception as e:
            print("Taskbar icon failed:", e)

        app = App(root)

        # Auto-open classifier if a QFX file was passed
        for arg in sys.argv[1:]:
            if arg.lower().endswith(".qfx") and os.path.exists(arg):
                app.qfx_view(arg)
                break

        fin_config.pythonlevel = sys.version
        #fin_config.TCLlevel = tcl.call("info", "patchlevel")
        #fin_config.TCLlevel = "tcl level"
        fin_config.SQlitelevel = ""
        log.info(f"FinOfx version {__version__} starting up")
        log.info(f"Python Level {sys.version}")
        #log.info(f"TCLlevel {fin_config.TCLlevel}")
        root.deiconify()
        root.lift()
        root.focus_force()
        root.mainloop()

    except Exception as error:
        log.exception("Failed %s", error)
        messagebox.showerror("Error", str(error))
        sys.exit(1)
