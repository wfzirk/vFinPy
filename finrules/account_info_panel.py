    
import customtkinter as ctk

class AccountInfoPanel:
    def __init__(self, app, parent):
        self.app = app
        self.parent = parent
        self.collapsed = False

        self.frame = ctk.CTkFrame(parent, corner_radius=10)

        self.frame.grid_columnconfigure(0, weight=1)

        # Header
        self.header = ctk.CTkFrame(self.frame, fg_color="transparent")
        self.header.grid(
            row=0,
            column=0,
            sticky="ew",
            padx=5,
            pady=(5, 0)
        )

        self.header.grid_columnconfigure(1, weight=1)

        self.toggle_btn = ctk.CTkButton(
            self.header,
            width=30,
            text="▼",
            command=self.toggle
        )
        self.toggle_btn.grid(row=0, column=0, padx=(0, 5))

        self.title_lbl = ctk.CTkLabel(
            self.header,
            text="Account Information",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        self.title_lbl.grid(row=0, column=1, sticky="w")

        # Content
        self.content = ctk.CTkFrame(
            self.frame,
            fg_color="transparent"
            #fg_color="yellow"
        )

        self.content.grid(
            row=1,
            column=0,
            sticky="ew",
            padx=10,
            pady=(5, 10)
        )

        self.content.grid_columnconfigure(1, weight=1)

        self.info_labels = {}

    def toggle(self):
        self.collapsed = not self.collapsed
        if self.collapsed:
            self.content.grid_remove()
            self.toggle_btn.configure(text="►")
        else:
            self.content.grid()
            self.toggle_btn.configure(text="▼")
        
    def update_account_info(self, info):

        for widget in self.content.winfo_children():
            widget.destroy()

        self.info_labels.clear()

        if not info:
            lbl = ctk.CTkLabel(
                self.content,
                text="No account information available"
            )
            lbl.grid(row=0, column=0, sticky="w")
            return
 
        row = 0

        for key, value in info.items():
            if not value:
                continue

            key_lbl = ctk.CTkLabel(
                self.content,
                text=f"{key}:",
                anchor="w",
                font=ctk.CTkFont(size=12, weight="bold"),
                height=18
            )

            val_lbl = ctk.CTkLabel(
                self.content,
                text=str(value),
                anchor="w",
                font=ctk.CTkFont(size=12),
                height=18
            )

            key_lbl.grid(
                row=row,
                column=0,
                sticky="w",
                padx=(0, 10),
                pady=(1, 1)
            )

            val_lbl.grid(
                row=row,
                column=1,
                sticky="ew",
                pady=(1, 1)
            )

            row += 1