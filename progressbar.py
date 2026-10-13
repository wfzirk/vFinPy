# progressbar.py
# progressbar.py

import customtkinter as ctk

class ProgressBarPR:
    def __init__(self, title="", steps=0):
        self.totalSteps = steps
        self.currentStep = 0

        self.cancelled = False
        self.paused = False

        self.winc = ctk.CTkToplevel()
        self.winc.title(title)
        self.winc.attributes("-topmost", True)
        self.winc.resizable(False, False)
        self.winc.grab_set()

        # Progress bar
        self.pb = ctk.CTkProgressBar(self.winc, width=280, height=25)
        self.pb.grid(column=0, row=0, columnspan=3, padx=10, pady=20)
        self.pb.set(0)

        # Percentage text inside bar
        self.percent_label = ctk.CTkLabel(self.winc, text="0%")
        self.percent_label.place(in_=self.pb, relx=0.5, rely=0.5, anchor="center")

        # Pause button
        self.pause_button = ctk.CTkButton(
            self.winc, text="Pause",
            fg_color="#666666", hover_color="#444444",
            command=self.pauseClick
        )
        self.pause_button.grid(column=0, row=1, padx=10, pady=10)

        # Resume button
        self.resume_button = ctk.CTkButton(
            self.winc, text="Resume",
            fg_color="#2E8B57", hover_color="#1E6B47",
            command=self.resumeClick,
            state="disabled"
        )
        self.resume_button.grid(column=1, row=1, padx=10, pady=10)

        # Cancel button
        self.cancel_button = ctk.CTkButton(
            self.winc, text="Cancel",
            fg_color="#AA3333", hover_color="#882222",
            command=self.cancelClick
        )
        self.cancel_button.grid(column=2, row=1, padx=10, pady=10)
        
        self.winc.protocol("WM_DELETE_WINDOW", self.close_all)
    
    def close_all(self):
        self.winc.destroy()
        #sys.exit()

    def update_percent(self):
        pct = round((self.currentStep / self.totalSteps) * 100, 1) if self.totalSteps else 0
        self.percent_label.configure(text=f"{pct}%")

    def progress(self):
        """Returns True when finished or cancelled."""
        if self.cancelled:
            return True

        if self.paused:
            self.winc.update()
            return False

        if self.currentStep < self.totalSteps:
            self.currentStep += 1
            self.pb.set(self.currentStep / self.totalSteps)
            self.update_percent()
        else:
            return True

        self.winc.update()
        return False

    def pauseClick(self):
        self.paused = True
        self.pause_button.configure(state="disabled")
        self.resume_button.configure(state="normal")

    def resumeClick(self):
        self.paused = False
        self.resume_button.configure(state="disabled")
        self.pause_button.configure(state="normal")

    def cancelClick(self):
        self.cancelled = True
        self.cancel_button.configure(text="Cancelling…", state="disabled")

    def close(self):
        try:
            self.winc.destroy()
        except:
            pass


if __name__ == '__main__':
    import time
    import sys
    root = ctk.CTk()
    root.geometry('300x120')
    root.title('Progressbar Demo')

    pb = ProgressBarPR('', 20 )
    for x in range(20):
        pb.progress()
        time.sleep(0.2)
    pb.stop()    
    sys.exit()
    root.mainloop()