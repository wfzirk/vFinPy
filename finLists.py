# https://python.hotexamples.com

# https://stackoverflow.com/questions/12014210/tkinter-app-adding-a-right-click-context-menu
# https://effbot.org/tkinterbook/wm.htm
import sys
import tkinter as tk
from tkinter import messagebox
#import customtkinter
#from CTkListbox import *


import apswSql as sql
from config import fin_config

from logging_manager import get_logger
log = get_logger(__name__)

class autoCmplt:
    def __init__(self, parent, data_list = None):
        self.parent = parent
        self.data_list = data_list
        self.result = tk.StringVar()
        
        self.tp_lvl = tk.Frame(self.parent, bg='green')
        self.tp_lvl.grid(row=0, column=0)
        #self.tp_lvl.pack()
        
        self.ctr_frame = tk.Frame(self.tp_lvl,  height=20)
        self.ctr_frame.pack(side=tk.BOTTOM, fill=tk.X, expand=1)

        self.btm_frame = tk.Frame(self.tp_lvl, bg='cyan',  height=20)
        self.btm_frame.pack(side=tk.BOTTOM, fill=tk.X, expand=1)
       
        self.lft_frame = tk.Frame(self.btm_frame, bg='cyan',  height=20, width=60)
        self.lft_frame.grid(row=0, column = 0)
        self.rgt_frame = tk.Frame(self.btm_frame, bg='cyan',  height=20)  # width=30)
        self.rgt_frame.grid(row=0, column=3)
        
        self.entry = tk.Entry(self.tp_lvl)
        self.entry.pack()
        self.entry.focus()
        self.entry.bind('<KeyRelease>', self.on_keyrelease)
        self.entry.bind('<Return>', self.add_item)

        self.entry.bind("<Enter>", lambda e:self.visiblewgt(self.listbox, True))
        self.entry.bind("<Leave>", lambda e:self.visiblewgt(self.listbox,  False))
        self.entry.bind('<Escape>', self.clear_entry)
        
        self.listbox = tk.Listbox(self.tp_lvl, height=0, bd=1, bg='yellow')
        self.listbox.pack(fill="both", expand=True, padx=10, pady=5)
        self.listbox.bind('<<ListboxSelect>>', self.on_select)
        self.listbox.bind("<Button-3>", self.popup) 
        self.listbox.bind("<Enter>", lambda e: self.visiblewgt(self.listbox, True))
        
        self.popup_menu = tk.Menu(self.listbox, tearoff=0)
        self.popup_menu.add_command(label="Delete",
                                    command= self.delete_selected)
        self.popup_menu.add_command(label="Select All",
                                    command= self.select_all)
        self.popup_menu.add_command(label="Add Iem",
                                    command= self.add_item)

        okButt = tk.Button(self.btm_frame, text = "OK")
        okButt.bind("<Button-1>", lambda e: self.on_OK())
        okButt.grid(row=0, column = 1)

        canButt = tk.Button(self.btm_frame, text = "Cancel")
        canButt.bind("<Button-1>", lambda c: self.parent.destroy())
        canButt.grid(row=0, column=2)        

        log.info('Autocomplete %s %s',type(self.data_list), data_list)

        if self.data_list:
            for item in self.data_list:   
                self.listbox.insert('end', item)
        #self.visiblewgt(self.listbox, False)
             
        #self.initial_focus.focus_set()
        self.result.set('')

        self.parent.wait_window(self.tp_lvl)    # wait for window to close to return values

    def visiblewgt(self, lb, visible):
        #self.listbox.config(visible=visible)
        if visible:
            self.listbox.pack()
        else:
            self.listbox.pack_forget()


    def popup(self, event):
        try:
            ##print('popup')
            self.popup_menu.tk_popup(event.x_root, event.y_root, 0)
        finally:
            ##print('grab-release')
            self.popup_menu.grab_release()

    def delete_selected(self):
        log.info('delete before %s',self.data_list)
        cursel = self.listbox.curselection()
        if cursel:
            sel = ':'
            for i in self.listbox.curselection():
                sel = self.data_list[i]+'\n'
            if messagebox.askokcancel(title='Delete', message='Are you sure you want to delete '+sel):  
                ##print('del sel',self.listbox.curselection())
                for i in self.listbox.curselection()[::-1]:
                    self.listbox.delete(i)
                    self.data_list.pop(i)
                log.info('delete after %s',self.data_list)   
        else:
            messagebox.showinfo(title='Delete', message='Nothing to delete')
          
    def select_all(self):
        ##print('select all')
        self.listbox.selection_set(0, 'end')
  
    def clear_entry(self, *args):
        ##print('clear_entry',*args)
        self.entry.delete(0, 'end')
  
    def on_keyrelease(self, event):
        ##print('keyrelease', event.keysym)
        if event.keysym == 'Escape':
            self.clear_entry()
        elif event.keysym == 'Return':
            self.clear_entry()
        else:   
            # get text from entry
            value = event.widget.get()
            value = value.strip().lower()
            
            # get data from test_list
            if value == '':
                data = self.data_list
            else:
                data = []
                ##print('value',value)
                for item in self.data_list:
                    log.info('item %s %s %s', type(item), len(item), item)
                    if (item):
                        if item[0].lower().startswith(value.lower()):
                            data.append(item[0])                

            # update data in listbox
        
            self.listbox_update(data)
    '''
    def add_new_entry(self):
        """Adds the text from the entry box to the combobox values."""
        new_value = entry_box.get()
        if new_value and new_value not in combo['values']:
            # Get current values (returns a tuple), convert to list, add new value, convert back to tuple
            current_values = list(combo['values'])
            current_values.append(new_value)
            combo['values'] = tuple(current_values) # Update the combobox values
            entry_box.delete(0, tk.END) # Clear the entry box
        elif new_value in combo['values']:
            status_label.config(text=f"'{new_value}' is already in the list.")
        else:
            status_label.config(text="Please enter a value.")
    '''
        
    def listbox_update(self, data):
        # delete previous data
        self.listbox.delete(0, 'end')
        data = sorted(data, key=str.lower)
        # put new data
        for item in data:
            self.listbox.insert('end', item)

    def on_Cancel(self):
        self.result.set('')
        self.parent.destroy()
        
    def on_OK(self):
        ##print('on_OK', self.listbox.curselection())
        #self.result = self.listbox.get(self.listbox.curselection())
        self.parent.destroy()

    def on_select(self, event):
        # display element selected on list
        sel = event.widget.get(event.widget.curselection())  #[0]
        if type(sel) == tuple: sel = sel[0]
        log.info('(event) previous: %s', event.widget.get('active'))
        log.info('(event) current: %s', sel)

        self.result.set(sel)
        log.info('---on_select len %s type %s:  %s', len(self.result.get()), type(self.result.get()), self.result.get())
        self.parent.destroy()
        
    def find_element_in_list(self, element, list_element):
        try:
            index_element = list_element.index(element)
            return index_element
        #except ValueError:
        except Exception as error:
            log.exception("Failed %s",error)
            tk.messagebox.showerror("ERROR", error)
            return None
        
    def add_item(self, event):
        try:
            value = event.widget.get()
            log.info('add_item %s %s %s',type(value), value, type(self.data_list))
            self.listbox.insert('end', value)
            if type(self.data_list) == str:
                self.data_list = value
            elif type(self.data_list) == dict:
                self.data_list[value] = ''
            elif type(self.data_list) == list:
                self.data_list.append(value)
            else:
                log.warning('add_item unknown type %s', type(data_list))
                messagebox.showwarning('WARNING', 'add_item unknown type %s', type(data_list))
            #self.clear_entry()
        except Exception as error:
            log.exception("Failed %s",error)
            log.info(self.data_list)
            messagebox.showerror("ERROR", error)
            sys.exit(1)
            
def acCatList(catList):
    # Set up window

    #winc = tk.Toplevel()
    winc = tk.Toplevel()
    winc.title("Enter Category")
    winc.attributes("-toolwindow", True)
    winc.wm_attributes("-topmost", True)
    winc.focus()
    
    
    cat = autoCmplt(winc, catList).result.get()
    return cat
    
def acSubCatList(subCatList):
    # Set up window
    winc = tk.Toplevel()
    winc.title("Enter Sub Category")
    winc.attributes("-toolwindow", True)
    winc.wm_attributes("-topmost", True)
    winc.focus()
    scat =  autoCmplt(winc, subCatList).result.get()
    return scat

def update_cat(entC, entS):
    log.info('update_cat %s', entS)
    catList, _, _ = sql.getColumnDistinct('Category')
    cat = acCatList(catList)
    
    entC.delete(0, 'end')
    entC.insert('end', cat)
    if cat:
        update_scat(entS, cat)

def update_scat(entS, cat):
    log.info('updatesubcat %s', cat)
    if not cat:
        return
    scatList, _, _ = sql.getSubCatDistinct(cat)
    scat = acSubCatList(scatList)
    entS.delete(0, 'end')
    entS.insert('end', scat)

    '''
    def update_cat(entC, entS):
        logging.info('update_cat %s', entS)
        catList, _, _ = sql.getColumnDistinct('Category')
        cat = acCatList(catList)
        
        entC.delete(0, 'end')
        entC.insert('end', cat)
        if cat:
            update_scat(entS, cat)
   
    def update_scat(entS, cat):
        logging.info('updatesubcat %s', cat)
        scatList, _, _ = sql.getSubCatDistinct(cat)
        scat = acSubCatList(scatList)
        entS.delete(0, 'end')
        entS.insert('end', scat)
    '''


    '''        
    def cl(self, *args):
            # Set up window
            winc = tk.Toplevel()
            winc.title("Enter Category")
            winc.attributes("-toolwindow", True)
            catList = sql.getCategoryDistinct()
            log.info('cl %s', catList)
            #cl_cat.set(AutoCmplt(tk.Tk(), data_list).result)
                                      
            cat = AutoCmplt(winc, catList).result.get()
            log.info('cat selected %s', cat) 

            self.entC.delete(0, 'end')
            self.entC.insert('end', cat)
            winc.destroy()
            if cat:
                self.sl()
        
    def sl(self, *args):
            cat = self.entC.get()
            if cat:
                # Set up window
                wins = tk.Toplevel()
                wins.title("Enter Sub Category")
                wins.attributes("-toolwindow", True)
                #cat = self.entC.get()
                subcat = sql.getSubCatDistinct(cat)   
                log.info(subcat)
                scat =  AutoCmplt(wins, subcat).result.get()
                log.info('subcat selected %s', scat) 
                self.entS.delete(0, 'end')
                self.entS.insert('end', scat)
                wins.destroy()
    '''

#==================================
def position_window(parent, width=200, height=200):
    # get screen width and height
    screen_width = parent.winfo_screenwidth()
    screen_height = parent.winfo_screenheight()

    # calculate position x and y coordinates
    #x = (screen_width/2) - (width/2)
    #y = (screen_height/2) - (height/2)
    x = parent.winfo_pointerx() - (width/4)
    y = parent.winfo_pointery()  - (height/2)
    parent.geometry('%dx%d+%d+%d' % (width, height, x, y))


class main:
    def __init__(self, parent, catList):
        self.parent = parent
        #self.cl_cat = tk.StringVar()
        try:
        
            self.ac = autoCmplt(self.parent)
        
            win = self.parent
            values = ['one', 'two', 'Category', 'SubCategory', 'Tags']

            row = 0

            for v in range(len(values)):
   
                tk.Label(win, text = values[v]).grid(row = row, column = 0)

                # only allow Category and Alias to be changed
                if values[v] == 'Category':
                    self.entC = tk.Entry(win, width = 30)
                    self.entC .grid(row = row, column = 1)
                    self.entC .bind("<Button-1>",  self.cl)
                    self.entC ['state'] = tk.NORMAL
                    #colEnt.append(self.entC )
                elif values[v] == 'SubCategory':
                    self.entS = tk.Entry(win, width = 30)
                    self.entS.grid(row = row, column = 1)
                    self.entS.bind("<Button-1>",  self.sl)
                    self.entS['state'] = tk.NORMAL
                    #colEnt.append(self.entS)

                else:
                    ent = tk.Entry(win, width = 30)
                    ent.grid(row = row, column = 1)
                    ent.insert(0, row*10)
                    ent['state'] = tk.DISABLED
                    #colEnt.append(ent)

                row +=1
        except Exception as error:
            log.exception("Failed %s",error)
            messageWindow("ERROR", error)
            #sys.exit(1)
        
        def cl(self, *args):
            self.ac.cl()
        
        def sl(self, *args):
            self.ac.sl()
            
        def tg(self, *args):
            self.ac.tgl()
   
if __name__ == '__main__':
    import apswSql as sql
    import settings
    
    root = tk.Tk()
    root.bind('<Control-Q>', lambda event=None: root.destroy())
    root.bind('<Control-q>', lambda event=None: root.destroy())
    position_window(root)
   
    catList = {}
    sql.catItems(catList, dateRange=fin_config.daterange)
    #print(catList)
    main(root, catList)

    root.mainloop()

    