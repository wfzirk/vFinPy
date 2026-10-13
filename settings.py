# https://gist.github.com/nadya-p/b25519cf3a74d1bed86ed9b1d8c71692
# https://rszalski.github.io/magicmethods/

# Python Includes
import sys
import os
import json
#import logging
import datetime
from tkinter import ttk
import customtkinter as ctk

# Project Includes
from logging_manager import get_logger
log = get_logger(__name__)

#getframe_expr = 'sys._getframe({}).f_code.co_name'
def getCaller():
    getframe_expr = 'sys._getframe({}).f_code.co_name'
    caller = eval(getframe_expr.format(2))
    callers_caller = eval(getframe_expr.format(3))
    #log.info(caller)
    log.info('%s %s',callers_caller, caller)

dbParams = {
            "fileName": "", 
            "cipher": "aes256cbc",          #Wxsqlite aes256cbc
            "kdf_iter": 8192,
            "key": "",
    }     

#ctk.set_appearance_mode("Light")
#ctk.set_default_color_theme("green")


# transwidths {key, [width, anchor, stretch]
TWIDTH = 0
TANCHOR = 1
TSTRETCH = 2        # True/False

initialSettings = {
    "PythonLevel": "",
    "TCLlevel": "",
    "SQlitelevel": "",
    "daterange": [
        str(datetime.date.today().year)+"-01-01",
        str(datetime.date.today().year)+"-12-31"
    ],
    
    "secParams": dbParams,  
 
    "dbf": "",
    "dbfIdx": None,
    "logdir": "logs",
    "dbdir": "database",
    "output": "output",
    "backup":{"auto_backup":0, "directory": "database"},
    "geometry": "1146x581+177+81",
    "puncSub": "!#$%(),:;<=>?@[\\]^`{|}~",
    "theme": "clam",
    "hoverdelay": 2,    # -1 disable hover
    "ctktheme": "",
    
    "transWidths": {
        'transactions': {
            'Id': [5, 'w', False], 'Date': [7, 'w', False], 'Alias': [12, 'w', True], 'Number': [6, 'e', False], 'Type': [6, 'w', False], 'Amount': [8, 'e', False], 'Category': [12, 'w', True], 'SubCategory': [12, 'w', True], 'Notes': [12, 'w', True], 'Tags': [12, 'w', True], 'Account': [15, 'w', False], 'Description': [12, 'w', False], 'UID': [12, 'w', True]},
        # Account
        'accounts': {
            'Id': [5, 'e', False], 'AccountID': [24, 'w', True], 'RoutingNumber': [10, 'w', True], 'Type': [7, 'e', False], 'Fid': [12, 'w', True], 'Organization': [36, 'w', True], 'OrganizationName': [20, 'w', True], 'StartDate': [28, 'w', False], 'EndDate': [28, 'w', False], 'Balance': [12, 'w', True], 'Encrypted': [12, 'w', True]},
        #"Patterns"
        'patterns': {
            'Id': [5, 'e', False], 'Alias': [14, 'w', False], 'Pattern': [20, 'w', False], 'Category': [12, 'w', False], 'SubCategory': [12, 'w', False], 'Account': [10, 'w', False]},
        'other': {
            'Id': [5, 'w', False], 'Date': [7, 'w', False], 'Alias': [12, 'w', True], 'Number': [6, 'e', False], 'Type': [6, 'w', False], 'Amount': [8, 'e', False], 'Category': [12, 'w', True], 'SubCategory': [12, 'w', True], 'Notes': [12, 'w', True], 'Tags': [12, 'w', True], 'Account': [15, 'w', False], 'Description': [12, 'w', False], 'UID': [12, 'w', True]},
    },
    "tree_colors": {
        "leftside": {"Foreground": "#000007", "Background": "#ecfaff", "font": ('Calibri', 12,'normal')},
        "rightside": {"Foreground": "#910b6e", "Background": "#ffffce", "font": ('Calibri', 12,'normal')},
        "treeheader": {"Foreground": "#078b3d", "Background": "#eaffff", "font": ('Calibri', 12,'normal')},
        "selected": {"Foreground": "#910000", "Background": "#c0c0c0", "font": ('Calibri', 12,'normal')},
        "oddrow": {"Foreground": "#400000", "Background": "#eaffff", "font": ('Calibri', 12,'normal')},
        "evenrow": {"Foreground": "#004000", "Background": "#ddeeff", "font": ('Calibri', 12,'normal')},
        "lvl0row": {"Foreground": "(0, 64, 0)", "Background": "#ecfaff", "font": ["Calibri", 11,  "bold"]},
        "lvl1row": {"Foreground": "(0, 74, 0)", "Background": "#ecfaff", "font": ["Calibri", 11,  "normal" ]},
        "lvl2row": {"Foreground": "(49,98,73)", "Background": "#ecfaff", "font": [ "Calibri", 10,  "normal" ]},
        "finaltotal": {"Foreground": "#000000", "Background": "#ecfaff",  "font": [ "Calibri", 12, "bold" ]},
        "SubTotal": {"Foreground": "(105, 105, 105)", "Background": "(236, 250, 255)", "font": ["Calibri", 11, "bold" ]}}
}   
   
class Settings:
    _config_location = "settings.json"

    def __init__(self):
        getCaller()
        if os.path.exists(self._config_location):
            ##print('exists settings init',self._config_location)
            log.info('load settings %s',self._config_location)
            self.__dict__ = json.load(open(self._config_location))

        else:
            ##print('not exists settings init',self._config_location)
            log.info('JSON does not exist, load settings and save %s',self._config_location)
            self.__dict__ = initialSettings
            self.save()
    
    def saveData(self, data):
        log.info('saveData')
        self.__dict__ = data
        self.save()
        
    def getData(self):
        log.info("getData")
        return self.__dict__
        
    def set(self, key, value):
        log.info("set %s %s",key,value)
        getCaller()
        setattr(self, key, value)
        self.save()
    
    def __setitem__(self, key, value):
        log.info("setitem %s %s",key,value)
        getCaller()
        setattr(self, key, value)
        self.save()
        
    def get(self, key, *arg):
        #print("get",key,';', arg)
        try:
            return getattr(self, key)
        except Exception:
            #print('notexist',arg)
            return arg
        
    def __getitem__(self, key):
        ##print("getitem",key)
        return getattr(self, key)
                
    def keys(self):
        return list(self.__dict__.keys())
        
    def values(self):
        return list(self.__dict__.values())
    
    def items(self):
        return list(self.__dict__.items())
    
    def __enter__(self):
        ##print("_enter_")
        return self

    def save(self):
        getCaller()
        log.info('save')
        #getCaller()
        json.dump(self.__dict__, open(self._config_location, "w"),  indent=2, default=str)
    
    def __exit__(self, exc_type, exc_value, traceback):
        log.info("exit %s %s %s",exc_type, exc_value, traceback)
        getCaller()
        json.dump(self.__dict__, open(self._config_location, "w"),  indent=2, default=str)
    
    def addDBKey(self,dbf, key):
        #print(dbf)
        #print(key)
        #print("set secparams",self.secParams)
        self.secParams["fileName"] = dbf
        self.secParams["key"] = key
        
        
stg = Settings()

def getColors(field):
    ##print(stg.tree_colors)
    bg = stg.tree_colors[field]["Background"]
    fg = stg.tree_colors[field]["Foreground"]
    
    return [bg,fg]
    
def rgbtohex(self, r,g,b):
    return f'#{r:02x}{g:02x}{b:02x}'   

def rgbtohextuple(rgb):
    vs = rgb.replace('(','').replace(')','').replace(' ','') 
    res = tuple(map(int, vs.split(',')))
    ##print('res',res)
    return f'#{res[0]:02x}{res[1]:02x}{res[2]:02x}'
    
def getRowAttributes(tree, field):
    ##print('gra',field, stg.tree_colors[field])
    cfg = stg.tree_colors[field]
    fg = cfg["Foreground"]
    bg = cfg["Background"]
    if '#' not in fg:
        fg = rgbtohextuple(fg)
    if '#' not in bg:
        fg = rgbtohextuple(bg)

    tree.tag_configure(field, font=cfg["font"], foreground=fg, background=bg) 
    tree.tag_configure('neg', foreground="darkred")
  
def setColors(): 
    color = settings.stg.tree_colors
    bgtotcolor, fgtotcolor = settings.getColors("totalrow")

    if highlight:
        self.tree.tag_configure('highlight', background='lightblue') 
    self.tree.tag_configure('leftside', background=color['leftside']["Background"], foreground=color['leftside']["Foreground"]) 
    self.tree.tag_configure('lvl0row', background=color['lvl0row']["Background"], foreground=color['lvl0row']["Foreground"]) 
    self.tree.tag_configure('lvl1row', background=color['lvl1row']["Background"], foreground=color['lvl1row']["Foreground"]) 
    self.tree.tag_configure('lvl2row', background=color['lvl2row']["Background"], foreground=color['lvl2row']["Foreground"]) 
    self.tree.tag_configure('oddrow', background=color['oddrow']["Background"])  #, foreground=color['oddrow'][1]) 
    self.tree.tag_configure('evenrow', background=color['evenrow']["Background"])  #, foreground=color['evenrow'][1]) 
    self.tree.tag_configure('total', font=['Calibri', 11,'bold'], foreground=fgtotcolor, background=bgtotcolor) 
    self.tree.tag_configure('finaltotal', font=['Calibri', 12,'bold'], foreground='black', background=bgtotcolor) 

# Treeview styling
def treeview_style():
    style = ttk.Style()
    style.theme_use("default")

    style.configure(
        "Treeview",
        background="#1a1a1a",
        foreground="white",
        fieldbackground="#1a1a1a",
        rowheight=26,
        bordercolor="#1a1a1a",
        borderwidth=0
    )
    style.configure("Treeview", highlightthickness=0, bd=0)

    style.map(
        "Treeview",
        background=[("selected", "#2d6cdf")],
        foreground=[("selected", "white")]
    )

    style.configure(
        "Treeview.Heading",
        background="#111111",
        foreground="white",
        relief="flat"
    )
    style.map(
        "Treeview.Heading",
        background=[("active", "#222222")]
    )

    style.configure("OddRow", background="#1e1e1e", foreground="white")
    style.configure("EvenRow", background="#242424", foreground="white")





def initSettings():
    #global stg
    Settings()
    #log.info("Settings Loaded DBF:%s",stg.dbf)  

if __name__ == "__main__":
    #getframe_expr = 'sys._getframe({}).f_code.co_name'
    lgh = log_setup(__file__[:-3]+".log", log.INFO) 
    stg=Settings()
    #print(sys.argv[0])
    #print(stg.items())
    
            
 
