# status_bus.py

# Python Includes
from tkinter import ttk

# 3rd Party Includes
import customtkinter as ctk

# Project Includes
from logging_manager import get_logger
log = get_logger(__name__)

def show_timing_details():

    timings = StatusBus.get_perf()

    win = ctk.CTkToplevel()
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

    btn_clear_status = ctk.CTkButton(frame, text="Clear", width=70, command=clear_statusbar)

    btn_clear_status.pack(side="left", padx=2, pady=2)
    
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
 
def clear_statusbar():
    StatusBus.clear_perf() 
    
def set_status(msg):
    log.info(f'set_status {msg}')
    self.status_var.set(msg)
    self.root.update_idletasks() 

 
def timed_call(name, func, *args, **kwargs):
    start = perf_counter()

    try:
        #StatusBus.set_status(f"{name} running...")
        return func(*args, **kwargs)

    finally:
        #elapsed = perf_counter() - start
        #self.set_status(f"{name}: {elapsed:.3f}s")
        #log.info("%s completed in %.3f sec", name, elapsed)  
        StatusBus.update_perf("Side Panel", perf_counter()-start)
      

class StatusBus:
    _callback = None
    _perf = {}

    @classmethod
    def register(cls, callback):
        cls._callback = callback

    @classmethod
    def clear_perf(cls):
        cls._perf.clear()

        if cls._callback:
            cls._callback("Ready")

    @classmethod
    def update_perf(cls, name, elapsed):
        log.info(f'update_perf {name}:{elapsed:.4f}')
        cls._perf[name] = elapsed

        msg = " | ".join(
            f"{k}:{v:.3f}s"
            for k, v in cls._perf.items()
        )

        if cls._callback:
            log.info(f'update callback {msg}')
            cls._callback(msg)

    @classmethod
    def get_perf(cls):
        return dict(cls._perf)

#StatusBus.register(self.set_status)