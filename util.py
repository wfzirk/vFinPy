#  https://docs.python.org/3/library/ctypes.html

# Python Includes
import os
import tkinter as tk
from tkinter import messagebox
from tkinter.colorchooser import askcolor
import ctypes
import csv

# 3rd Party Includes

#Project Includes
#from settings import stg
from config import fin_config 
from logging_manager import get_logger
log = get_logger(__name__)

# status_bus.py

class StatusBus:
    _callback = None

    @classmethod
    def register(cls, callback):
        cls._callback = callback

    @classmethod
    def set_status(cls, message):
        if cls._callback:
            cls._callback(message)

    @classmethod
    def info(cls, message):
        cls.set_status(message)

    @classmethod
    def timing(cls, name, elapsed):
        cls.set_status(f"{name}: {elapsed:.3f}s")
        
def clear_all_inside_frame(frame):
    # Iterate through every widget inside the frame
    #log.info('clear_all_inside_frame')
    for widget in frame.winfo_children():
        widget.destroy()  # deleting widget

# create directory if doesn't exist
def mkdirp(path):
    log.info('mkdirp path %s',path)
    if not os.path.exists(path):
        os.makedirs(path)

def saveView2csv(tree, summary=True, level=3):   
    log.info('saveview %s',fin_config.DEFAULTS["output"])
    fileName = fin_config.DEFAULTS["output"]+'/view.csv'
    colNames = tree['columns']
    with open(fileName, "w", newline='') as csvFile:
        csvwriter = csv.writer(csvFile, delimiter=',') 
        cols = len(colNames)
        if summary:
            col = [colNames[0],colNames[cols-1]]
            csvwriter.writerow(col)
 
        else:    
            csvwriter.writerow(colNames)

        level3rows = ['Charity']
        level2rows = ['Insurance', 'Medical', 'Financial','Income']
        for parent in tree.get_children():
            fullRow = tree.item(parent)["values"]
            text = tree.item(parent)["text"]
            if summary:
                #row = [fullRow[0],fullRow[cols-1]]
                row = [text, fullRow[cols-1]]
            else:    
                row = fullRow
            #row.append('xxxfff')
            csvwriter.writerow(row) 

            level = 1
            
            if row[0] in level3rows:
                level = 3
            elif row[0] in level2rows:
                level = 2
            else:
                level = 1
            level = 3
            if level >= 2:
                for child in tree.get_children(parent):
                    fullRow = tree.item(child)["values"]
                    text = tree.item(child)["text"]
                    if summary:
                        #row = [fullRow[0],fullRow[cols-1]]
                        row = [text, fullRow[cols-1]]
                    else:    
                        row = fullRow
                    row[0] = '----'+row[0]
                    
                    #row.append('ggg')
                    csvwriter.writerow(row)

                    if level == 3:
                        for gchild in tree.get_children(child):
                            fullRow = tree.item(gchild)["values"]
                            text = tree.item(gchild)["text"]
                            if summary:
                                #row = [fullRow[0],fullRow[cols-1]]
                                row = [text, fullRow[cols-1]]
                            else:    
                                row = fullRow
                            row[0] = '--------'+row[0]
                            #row.append('ggg')
                            csvwriter.writerow(row)
  
                
    messagebox.showinfo('info', 'Done '+fileName+' in Output Directory')
def rptRowHdr(all_columns=True):
    if all_columns:
        return["Date","Payee","Number","Amount","Category","Account","Description","UID"]
    else:
        return["Date", "Amount", "Description"]
    
def row2Report(row, all_columns=True):  
    #tree format Id,Date,Alias,Number,Type,Amount,Category,SubCategory,Notes,Tags,Account,Description,UID, RunTotal
    #report format  Date,Payee,Number,Amount,Category,Account,Description, UID
    rptRow = []
    if all_columns:
        rptRow.append(row[1])   #Date
        rptRow.append(row[2])   #Payee
        rptRow.append(row[3])   #Number
        rptRow.append(row[5])   #Amount
        rptRow.append(row[6]+':'+row[7])    #Category
        #rptRow.append(row[7])
        rptRow.append(row[10])  #Account
        rptRow.append(row[11])  #Description
        rptRow.append(row[12])  #UID
        if rptRow[1] == 'Alias': rptRow[1] = 'Payee'
    else:
        rptRow.append(row[1])   #Date
        rptRow.append(row[5])   #Amount
        rptRow.append(row[11])  #Description
        
    #log.info(rptRow)
    return rptRow

def saveReport2CSV(tree, rptCol, colNames):
    
    arry = tree2Array(tree)   #.sort(key=lambda x:x[rptCol])   #,reverse=True)
    
    arry.sort(key=lambda x: x[rptCol])

    fileName = fin_config.DEFAULTS["output"]+'/report.csv'
    
    log.info(fileName)

    try:
        fw = open(fileName, "w", newline='')
        csvwriter = csv.writer(fw, delimiter=',', quoting=csv.QUOTE_ALL)    #quoting=csv.QUOTE_NONNUMERIC) 
        #csvwriter.writerow(rptRowHdr())
        csvwriter.writerow(rptRowHdr(all_columns=False))
        #lastfw = fw                                                        
        for row in arry:
            #log.info(row)
            csvwriter.writerow(row2Report(row, all_columns=False))            #csvwriter.writerow(row2Report(row))
        fw.close()
    except Exception as error:
        log.info(error)
        messagebox.showerror('error',error)
        
    messagebox.showinfo('info', 'Done File in Output Directory as report.csv')

def saveAccounts2MMX(tree, rptCol, colNames):
    
    arry = tree2Array(tree)   #.sort(key=lambda x:x[rptCol])   #,reverse=True)
    
    arry.sort(key=lambda x: x[rptCol])
    acnt = ''
    lastfw = ''
    try:
        for row in arry:
            if row[rptCol] != acnt:
                fileName = 'Output/mmx_'+row[rptCol]+'.csv'
                log.info('%s fileName %s',rptCol,fileName)
                acnt = row[rptCol]
                if lastfw:
                    lastfw.close()
                fw = open(fileName, "w", newline='')
                csvwriter = csv.writer(fw, delimiter=',', quoting=csv.QUOTE_NONNUMERIC) 
                #csvwriter.writerow(rptRowHdr())
                csvwriter.writerow(colNames)
                lastfw = fw
                    
            csvwriter.writerow(row)
        lastfw.close()
    except Exception as error:
        log.info(error)
        messagebox.showerror('error',error)
        
    messagebox.showinfo('info', 'Done Files in Output Directory as "mmx_*.csv"')

    
def saveAccounts2KMY(tree, rptCol, colNames):
    
    arry = tree2Array(tree)   #.sort(key=lambda x:x[rptCol])   #,reverse=True)
    scoffset = colNames.index('SubCategory')
    
    columns = list(colNames)
    log.info('%s  %s',type(columns), columns)
    del columns[scoffset]
    arry.sort(key=lambda x: x[rptCol])
    acnt = ''
    lastfw = ''

    try:
        for row in arry:
            if row[rptCol] != acnt:
                fileName = 'Output/kmy_'+row[rptCol]+'.csv'
                log.info('%s fileName %s',rptCol,fileName)
                acnt = row[rptCol]
                if lastfw:
                    lastfw.close()
                fw = open(fileName, "w", newline='')
                csvwriter = csv.writer(fw, delimiter=',', quoting=csv.QUOTE_NONNUMERIC) 
                #csvwriter.writerow(rptRowHdr())
                csvwriter.writerow(columns)
                lastfw = fw

            #csvwriter.writerow(row)
            rowx = row
            rowx[6] = row[6]+':'+row[7]
            del rowx[scoffset]
            csvwriter.writerow(rowx)
        lastfw.close()
    except Exception as ex:
        log.exception('error %s',ex)
        message =  type(ex).__name__, str(ex), 'In', os.path.basename(__file__), 'On Line', ex.__traceback__.tb_lineno
        messageWindow("ERROR", message)
            
    messagebox.showinfo('info', 'Done Files in Output Directory as "kmy_*.csv"')

def tree2Array(tree):
    treeArray = []
    for parent in tree.get_children():
        row = tree.item(parent)["values"]
        treeArray.append(row)    
        for child in tree.get_children(parent):
            row = tree.item(child)["values"]
            rptRow = row2Report(row)
            treeArray.append(rptRow)
    #data_sort = sorted(allData, key=lambda x: x[1])   # sort by date    
    return treeArray

def contrastcolor(color): 
    # Get a contrast color 
    # https://graphicdesign.stackexchange.com/questions/62368/automatically-select-a-foreground-color-based-on-a-background-color

    r, g, b, a = colors.to_rgba(color)
    if 0.2126 * r + 0.7152 * g + 0.0722 * b > 0.5:  # choose black; else choose white,
        fg = 'black'
    else:
        fg = 'white'
    return fg
    
def resize_widgets(widget):
    # resize all widgets on window resize
    # https://stackoverflow.com/questions/47127875/python-tkinter-how-to-resize-widgets-when-user-expands-the-windows
    col_count,row_count = widget.grid_size()

    for i in range(row_count):
        widget.grid_rowconfigure(i, weight=1)

    for i in range(col_count):
        widget.grid_columnconfigure(i, weight=1)

    for child in widget.children.values():
        child.grid_configure(sticky="nsew")
        resize_widgets(child)  
        
def colorPicker(colors):
    colors.set("Pick A Color")
    win = tk.Toplevel()
    win.title("Color  Configure ")
    win.attributes("-toolwindow", True)  
    win.geometry("250x230")
    def cp():
        c = askcolor(title="Tkinter Color Chooser")[1]
        colors.set(c)
        win.configure(bg=c)
        #root.configure(bg=c)
    
    tk.Button(win, text="Pick a Color", textvariable=colors, command=cp).pack(expand=True)
   
   
def parseGeom(geom):
    try:
        size, xpos, ypos = geom.split('+')
        width, height = size.split('x')
        return int(width), int(height), int(xpos), int(ypos)
    except: return 0,0,0,0
    

        
def winMax():
    user32 = ctypes.windll.user32
    noMon = user32.GetSystemMetrics(80) # number of monitors
    if noMon == 1:
        maxX = user32.GetSystemMetrics(0)  # size of first screen
        maxY = user32.GetSystemMetrics(1)
    else:
        maxX = user32.GetSystemMetrics(78)  # size of 2nd screen
        maxY = user32.GetSystemMetrics(79)
    return int(noMon), int(maxX), int(maxY)
    
    
    
def winInfo():
    SM_CXSCREEN = 0         # screen width of primary monitor
    SM_CYSCREEN = 1         # screen height of primary monitor
    SM_CMONITORS = 80         #The number of display monitors on a desktop. For more information, see the Remarks section in this topic.
    SM_XVIRTUALSCREEN = 76 # left coordinates of the virtual screen.
    SM_YVIRTUALSCREEN = 77 # coordinates for the top of the virtual screen.
    SM_CXVIRTUALSCREEN = 78 # The width of the virtual screen, in pixels.
    SM_CYVIRTUALSCREEN = 79 # The height of the virtual screen
    user32 = ctypes.windll.user32
    screensize = user32.GetSystemMetrics(0), user32.GetSystemMetrics(1)
    
    log.info('monitor number %s',user32.GetSystemMetrics(80))
    log.info('screensize %s',screensize)
    log.info('metrics %d:%d',user32.GetSystemMetrics(78), user32.GetSystemMetrics(79))
    
    
    
    

if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()
    dlg = MyDialog(root, title="Test")
    #print(dlg.result)
    root.destroy()
    
    
    