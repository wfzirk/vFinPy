
import tkinter as tk
from tkinter import messagebox
from tkinter import filedialog 
import csv
import logging

# 3rd Party Includes

#Project Includes
import apswSql as sql
    
class table2csv:
    def __init__(self):
        logging.info('table2csv')

        self.winc = tk.Toplevel()
        self.winc.attributes("-toolwindow", False)  
        self.winc.geometry("350x100")  #width, height
        self.winc.wm_attributes("-topmost", True)
        self.winc.resizable(False, False)  #width, height

        # Table Name
        row = 0
        tk.Label(self.winc, text="Table Name to export").grid(row=row, column=0, padx=5, pady=5)

        self.table_name_listbox = tk.Listbox(self.winc, selectmode=tk.SINGLE, width=20, height=3) 
        self.table_name_listbox.grid(row=row, column=1, padx=5, pady=5)
        
        # Add a scrollbar to handle items beyond the visible height
        scrollbar = tk.Scrollbar(self.winc, orient="vertical", command=self.table_name_listbox.yview)
        scrollbar.grid(row=row, column=2, padx=5, pady=5)
        self.table_name_listbox.config(yscrollcommand=scrollbar.set)
        
        row+=1
        tk.Button(self.winc, text="Cancel", command=self.cancel_export).grid(row=row, column=1, pady=10)
        tables = sql.getTables()

        for i in tables:
            self.table_name_listbox.insert(tk.END, i)
        self.table_name_listbox.bind('<<ListboxSelect>>', self.on_select)

    def on_select(self, event):
        """
        Callback function to handle the Listbox selection event.
        """
        # Get the widget that generated the event
        widget = event.widget
        # Get the tuple of selected indices (even single-select returns a tuple)
        selection_indices = widget.curselection()

        if selection_indices:
            # Get the first selected index
            index = selection_indices[0]
            # Get the value (text) of the selected item
            selected_item = widget.get(index)
            logging.info(f"Selected item index: {index}, value: {selected_item}")
            self.export_table(selected_item)
        else:
            # Handle the case where no item is selected (e.g., clearing selection)
            logging.info("No item selected")    
        

    def export_table(self, table):
        logging.info('==== exportDB %s ======', table)
        file_opt = options = {}
        options['filetypes'] = [('CSV file', '.csv'), ('all files', '.*')]
        options['initialfile'] = table+'.csv'
        csv_file = filedialog.asksaveasfilename(**file_opt)
        #print('----',csv_file)
        if csv_file:
            logging.info('exportTrans %s',csv_file)
            
            query = "SELECT * from "+table+";"    
            #query = "SELECT Date, Amount, Description from "+table+";" 
            data,  columns, err = sql.sqlQuery(query)
            #print(columns)
            #print(data)
            
            with open(csv_file, "w", newline='') as csvf:
                csv_writer = csv.writer(csvf, delimiter=',')
                csv_writer.writerow(columns)
                csv_writer.writerows(data)
        else:
            messagebox.showinfo("INFO", "No file selected")

    def cancel_export(self):
        self.winc.destroy()
        #self.root.deiconify()

if __name__ == "__main__":
    # GUI Setup
    root = tk.Tk()
    root.title("Export CSV")
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(lineno)s:%(message)s')
    logging.info('starting')
    logging.warning('starting')
    table2csv()
    ''''
    export_table("transactions")
    export_table("accounts")
    export_table("patterns")
    '''
    #root.withdraw()  
    
    root.mainloop()