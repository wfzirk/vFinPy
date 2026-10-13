
# treeviewsearch.py


import tkinter as tk
from tkinter import ttk
import customtkinter as ctk


class TreeviewSearchAttach:
    def __init__(self, tree: ttk.Treeview, callback):
        self.tree = tree
        self.all_items = set()
        self._patch_insert()
        self.callback = callback

        # container for overlay labels
        self.overlays = []

        # bind redraw events
        #tree.bind("<Configure>", lambda e: self.redraw_highlights())

        # store last search parameters
        self._last_query = ""
        self._last_columns = None
        self._last_search_tags = False
        self._last_invert = False

    # ------------------------------------------------------------
    # Track inserted rows
    # ------------------------------------------------------------
    def _patch_insert(self):
        original_insert = self.tree.insert

        def patched_insert(parent, index, iid=None, **kw):
            new_iid = original_insert(parent, index, iid=iid, **kw)
            self.all_items.add(new_iid)
            return new_iid

        self.tree.insert = patched_insert

     # ------------------------------------------------------------
    # Clear search
    # ------------------------------------------------------------
    def clear(self):
        #self.clear_highlights()
        for iid in list(self.all_items):
            try:
                self.tree.reattach(iid, self.tree.parent(iid), "end")
            except tk.TclError:
                pass

    # ------------------------------------------------------------
    # Search + label overlay highlight
    # ------------------------------------------------------------
    def search(self, query: str, columns=None, search_tags=False, invert=False):
        query = query.lower().strip()

        # store last search
        self._last_query = query
        self._last_columns = columns
        self._last_search_tags = search_tags
        self._last_invert = invert

        #self.clear_highlights()

        if not query:
            self.clear()
            return
        
        matches = []

        for iid in list(self.all_items):
            item = self.tree.item(iid)
            text = item["text"].lower()
            values = [str(v).lower() for v in item["values"]]
            tags = [t.lower() for t in item["tags"]]

            found = False

            # text column (#0)
            if columns is None or 0 in columns:
                if query in text:
                    found = True
                    matches.append((iid, 0))

            # value columns
            if columns is None:
                for idx, v in enumerate(values):
                    if query in v:
                        found = True
                        matches.append((iid, idx + 1))
            else:
                for col in columns:
                    if col == 0:
                        continue
                    idx = col - 1
                    if idx < len(values) and query in values[idx]:
                        found = True
                        matches.append((iid, col))

            # tags
            if search_tags and any(query in t for t in tags):
                found = True
                matches.append((iid, 0))

            if invert:
                found = not found

            # attach/detach
            try:
                if found:
                    self.tree.reattach(iid, self.tree.parent(iid), "end")
                else:
                    self.tree.detach(iid)
            except tk.TclError:
                pass

        
        self.callback()
        
        # draw overlays
        #self.highlight_cells(matches)

class CTkSearchBarAttach(ctk.CTkFrame):
    """
    CustomTkinter SearchBar UI for attach/detach Treeview search.
    Works with TreeviewSearchAttach engine.
    """

    def __init__(self, parent, search_engine, tree):
        super().__init__(parent)

        self.search_engine = search_engine
        self.tree = tree

        self._debounce_after = None
        self._debounce_ms = 180

        self._build_ui()
        self._wire_events()

    # ------------------------------------------------------------
    # UI Construction
    # ------------------------------------------------------------
    def _build_ui(self):
        self.configure(fg_color="transparent")

        self.grid_columnconfigure(0, weight=1)

        gcol = 0

        self.entry = ctk.CTkEntry(
            self,
            placeholder_text="Search...",
            height=24
        )
        self.entry.grid(
            row=0,
            column=gcol,
            sticky="ew",
            padx=(2, 2),
            pady=0
        )
        gcol += 1

        col_labels = ["All Columns"] + [
            f"{i}: {col}"
            for i, col in enumerate(self.tree["columns"], start=1)
        ]

        self.col_select = ctk.CTkComboBox(
            self,
            values=col_labels,
            width=140,
            height=24,
            state="readonly"
        )
        self.col_select.set("All Columns")
        self.col_select.grid(
            row=0,
            column=gcol,
            padx=2,
            pady=0
        )
        gcol += 1

        self.tag_var = ctk.BooleanVar(value=False)

        self.inv_var = ctk.BooleanVar(value=False)
        self.inv_chk = ctk.CTkCheckBox(
            self,
            text="Invert",
            width=10,
            variable=self.inv_var
        )
        self.inv_chk.grid(
            row=0,
            column=gcol,
            padx=2,
            pady=0
        )
        gcol += 1

        self.clear_btn = ctk.CTkButton(
            self,
            text="Clear",
            width=60,
            height=24,
            command=self.clear_search
        )
        self.clear_btn.grid(
            row=0,
            column=gcol,
            padx=2,
            pady=0
        )
    
    def xxxxx_build_ui(self):
        self.grid_columnconfigure(0, weight=1)
        gcol = 0
        # Search entry
        self.entry = ctk.CTkEntry(self, placeholder_text="Search…")
        self.entry.grid(row=0, column=gcol, sticky="ew", padx=6, pady=6)
        gcol+=1
        # Column selector
        col_labels = ["All Columns"] + [
            f"{i}: {col}" for i, col in enumerate(self.tree["columns"], start=1)
        ]

        self.col_select = ctk.CTkComboBox(
            self,
            values=col_labels,
            width=160,
            state="readonly"
        )
        self.col_select.set("All Columns")
        self.col_select.grid(row=0, column=gcol, padx=2)
        gcol+=1

        # Tag search toggle
        self.tag_var = ctk.BooleanVar(value=False)
        #self.tag_chk = ctk.CTkCheckBox(self, text="Tags", width=10, variable=self.tag_var)
        #self.tag_chk.grid(row=0, column=2, padx=2)

        # Invert toggle
        self.inv_var = ctk.BooleanVar(value=False)
        self.inv_chk = ctk.CTkCheckBox(self, text="Invert", width=10, variable=self.inv_var)
        self.inv_chk.grid(row=0, column=gcol, padx=2)
        gcol+=1

        # Clear button
        self.clear_btn = ctk.CTkButton(self, text="Clear", width=70, command=self.clear_search)
        self.clear_btn.grid(row=0, column=gcol, padx=2)
        gcol+=1
    # ------------------------------------------------------------
    # Event Wiring
    # ------------------------------------------------------------
    def _wire_events(self):
        self.entry.bind("<KeyRelease>", self._on_key)
        self.col_select.bind("<<ComboboxSelected>>", lambda e: self.apply_search())
        #self.tag_chk.configure(command=self.apply_search)
        self.inv_chk.configure(command=self.apply_search)

    # ------------------------------------------------------------
    # Debounced Key Handler
    # ------------------------------------------------------------
    def _on_key(self, event):
        if self._debounce_after:
            self.after_cancel(self._debounce_after)

        self._debounce_after = self.after(self._debounce_ms, self.apply_search)

    # ------------------------------------------------------------
    # Apply Search
    # ------------------------------------------------------------
    def apply_search(self):
        query = self.entry.get().strip()
        tag_search = self.tag_var.get()
        invert = self.inv_var.get()
        #print('apply_search %s',query)
        # Determine columns
        col_sel = self.col_select.get()
        if col_sel == "All Columns":
            columns = None
        else:
            col_index = int(col_sel.split(":")[0])
            columns = [col_index]

        self.search_engine.search(
            query=query,
            columns=columns,
            search_tags=tag_search,
            invert=invert
        )

    # ------------------------------------------------------------
    # Clear Search
    # ------------------------------------------------------------
    def clear_search(self):
        self.entry.delete(0, "end")
        self.search_engine.clear()


if __name__ == "__main__":
    import sys
    root = ctk.CTk()
    def totalAmtCol():
       print('callback') 
    #from treeview_search_attach import TreeviewSearchAttach
    #from ctk_searchbar_attach import CTkSearchBarAttach

    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")

    root = ctk.CTk()

    frame = ctk.CTkFrame(root)
    frame.pack(fill="both", expand=True, padx=10, pady=10)

    tree = ttk.Treeview(frame, columns=("amount", "date"), show="tree headings")
    tree.pack(fill="both", expand=True)

    tree.heading("amount", text="Amount")
    tree.heading("date", text="Date")

    tree.insert("", "end", iid="a", text="Groceries", values=("42.50", "2025-01-02"), tags=("food",))
    tree.insert("", "end", iid="b", text="Gas", values=("19.99", "2025-01-03"), tags=("gas",))
    tree.insert("", "end", iid="c", text="Rent", values=("120.00", "2025-01-04"), tags=("rent",))

    search_engine = TreeviewSearchAttach(tree, totalAmtCol)

    searchbar = CTkSearchBarAttach(root, search_engine, tree)
    searchbar.pack(fill="x", padx=10, pady=10)
    
    def close_all():
        #print('close_all')
        root.destroy()
        sys.exit()
    
    # Bind the close event
    root.protocol("WM_DELETE_WINDOW", close_all)


    root.mainloop()
