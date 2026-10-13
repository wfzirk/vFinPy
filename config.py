import json
import os
import threading
from pathlib import Path

from tkinter import ttk
import customtkinter as ctk
from customtkinter import ThemeManager
import datetime

from logging_manager import get_logger
log = get_logger(__name__)

# transwidths {key, [width, anchor, stretch]
TWIDTH = 0
TANCHOR = 1
TSTRETCH = 2        # True/False

class _Section:
    """
    A dynamic namespace for config sections.
    Mutations auto-save back to the parent FinanceConfig.
    """

    def __init__(self, parent, section_name, data):
        self._parent = parent
        self._section_name = section_name
        self._data = data

    def __getattr__(self, key):
        if key in self._data:
            #log.info('__getattr__%s:%s', key, self._data[key])
            return self._data[key]
        raise AttributeError(f"No such config key: {self._section_name}.{key}")

    def __setattr__(self, key, value):
        if key.startswith("_"):
            return super().__setattr__(key, value)
        #log.info('__setattr__ %s: %s', key, value)
        self._data[key] = value
        self._parent._save()
        return value
    
    def __getitem__(self, key):
        return self._data[key]


    def to_dict(self):
        return dict(self._data)


class FinanceConfig:
    """
    Unified configuration manager for FinOfx.
    Loads/saves JSON, exposes sections as attributes,
    and ensures defaults exist.
    """

    DEFAULTS = {
        "secParams": {
            "fileName": "",
            "cipher": "ChaCha20",
            "kdf_iter": 64007,
            "key": "",
        },
        "logdir": "logs",
        "dbdir": "database",
        "output": "output",
        "rules": "rules",
        "daterange": [
            str(datetime.date.today().year) + "-01-01",
            str(datetime.date.today().year) + "-12-31"
            #"2022-01-01", "2023-05-04"
        ],
        "theme": {
            "appearance_mode": "light",
            "theme_name": "blue",
            "accent_color": "#3B82F6"
        },
        "window": {
            "geometry": "1200x800+100+100",
            "maximized": False
        },
        "rules": {
            "auto_apply": True,
            "case_sensitive": False
        },
        "classifier": {
            "ai_enabled": True,
            "confidence_threshold": 0.55
        },
        "importing": {
            "last_directory": None,
            "auto_open_after_import": True
        },
        "logging": {
            "level": "INFO",
            "file": "finofx.log"
        },
        "ui": {
            "show_statusbar": True,
            "show_sidebar": True,
            "font_scale": 1.0
        },
        "transWidths": {
            'transactions': {
                'Id': [5, 'w', False], 'Date': [7, 'w', False], 'Alias': [12, 'w', True], 'Number': [6, 'e', False], 'Type': [6, 'w', False], 'Amount': [8, 'e', False], 'Category': [12, 'w', True], 'SubCategory': [12, 'w', True], 'Notes': [12, 'w', True], 'Tags': [12, 'w', True], 'Account': [15, 'w', False], 'Description': [12, 'w', False], 'import_file_key': [12, 'w', False]},

            'accounts': {
                'Id': [5, 'e', False], 'AccountID': [24, 'w', True], 'RoutingNumber': [10, 'w', True], 'Type': [7, 'e', False], 'Fid': [12, 'w', True], 'Organization': [36, 'w', True], 'OrganizationName': [20, 'w', True], 'StartDate': [28, 'w', False], 'EndDate': [28, 'w', False], 'Balance': [12, 'w', True], 'Encrypted': [12, 'w', True]},
  
            'patterns': {
                'Id': [5, 'e', False], 'Alias': [14, 'w', False], 'Pattern': [20, 'w', False], 'Category': [12, 'w', False], 'SubCategory': [12, 'w', False], 'Account': [10, 'w', False]},
            
            'other': {
                'Id': [5, 'w', False], 'Date': [7, 'w', False], 'Alias': [12, 'w', True], 'Number': [6, 'e', False], 'Type': [6, 'w', False], 'Amount': [8, 'e', False], 'Category': [12, 'w', True], 'SubCategory': [12, 'w', True], 'Notes': [12, 'w', True], 'Tags': [12, 'w', True], 'Account': [15, 'w', False], 'Description': [12, 'w', False], 'UID': [12, 'w', True]},
                
            'rules': {
                'rule_id': [5, 'e', False], 'account': [15, 'w', False], 'pattern': [20, 'w', False], 'alias': [12, 'w', True], 'category': [12, 'w', True], 'subcategory': [12, 'w', True], 'import_file_key': [15, 'w', False], 'enabled': [5, 'e', False], 'created_at': [12, 'w', False], 'updated_at': [12, 'w', True]},

            'qfx': {
                'new': [5, 'w', False], 'date': [12, 'w', False], 'alias': [12, 'w', False], 'number': [6, 'e', False], 'type': [6, 'w', False], 'amount': [8, 'e', False], 'category': [12, 'w', False], 'subcategory': [12, 'w', False], 'account': [15, 'w', False], 'description': [30, 'w', False], 'import_file_key': [12, 'w', False], 'fitid': [12, 'w', True]},    
        },
        "tree_colors": {
            "leftside": {"Foreground": "#000007", "Background": "#ecfaff", "font": ('Calibri', 12,'normal')},
            "rightside": {"Foreground": "#910b6e", "Background": "#ffffce", "font": ('Calibri', 12,'normal')},
            "treeheader": {"Foreground": "#078b3d", "Background": "#eaffff", "font": ('Calibri', 12,'normal')},
            #selected": {"Foreground": "#910000", "Background": "#c0c0c0", "font": ('Calibri', 12,'normal')},
            "selected": {"Foreground": "#400000", "Background": "#c0c0c0", "font": ('Calibri', 12,'normal')},
            "oddrow": {"Foreground": "#400000", "Background": "#eaffff", "font": ('Calibri', 12,'normal')},
            "evenrow": {"Foreground": "#004000", "Background": "#ddeeff", "font": ('Calibri', 12,'normal')},
            "lvl0row": {"Foreground": "(0, 64, 0)", "Background": "#ecfaff", "font": ["Calibri", 11,  "bold"]},
            "lvl1row": {"Foreground": "(0, 74, 0)", "Background": "#ecfaff", "font": ["Calibri", 11,  "normal" ]},
            "lvl2row": {"Foreground": "(49,98,73)", "Background": "#ecfaff", "font": [ "Calibri", 10,  "normal" ]},
            "finaltotal": {"Foreground": "#000000", "Background": "#ecfaff",  "font": [ "Calibri", 12, "bold" ]},
            "SubTotal": {"Foreground": "(105, 105, 105)", "Background": "(236, 250, 255)", "font": ["Calibri", 11, "bold" ]}
        }   

    }

    def __init__(self, path="finance_settings.json"):
        self.path = Path(path)
        self._data = self._load()
        self._sections = {}

        # Debounced save state
        self._save_timer = None
        self.SAVE_DELAY = 0.75  # seconds

        # Create section objects
        for section, values in self._data.items():
            self._sections[section] = _Section(self, section, values)

    # -----------------------------
    # Section access
    # -----------------------------

    def __getattr__(self, section):
        # Special case: daterange is a list, not a dict
        if section == "daterange":
        
            return self._data["daterange"]

        if section in self._sections:
            return self._sections[section]

        raise AttributeError(f"No such config section: {section}")

    def set_daterange(self, start, end):
        ##print('*********set_daterange', start,end)
        self._data["daterange"] = [start, end]
        self._save()

    # -----------------------------
    # Load / Save
    # -----------------------------

    def _load(self):
        if not self.path.exists():
            return self._write_defaults()

        try:
            with open(self.path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            return self._write_defaults()

        # Ensure missing defaults are added
        changed = False
        for section, defaults in self.DEFAULTS.items():
            if section not in data:
                data[section] = defaults
                changed = True
                continue

            if isinstance(defaults, dict):
                for key, val in defaults.items():
                    if key not in data[section]:
                        data[section][key] = val
                        changed = True

            elif isinstance(defaults, list):
                if not isinstance(data[section], list):
                    data[section] = defaults
                    changed = True
                else:
                    if len(data[section]) < len(defaults):
                        data[section].extend(defaults[len(data[section]):])
                        changed = True

        if changed:
            self._save_data(data)

        return data

    # -----------------------------
    # Debounced Save
    # -----------------------------

    def _save(self):
        # Debounced save: prevents rapid-fire writes during geometry/theme changes
        ##print('_save')
        if self._save_timer:
            self._save_timer.cancel()

        self._save_timer = threading.Timer(self.SAVE_DELAY, self._flush_save)
        self._save_timer.daemon = True
        self._save_timer.start()

    def _flush_save(self):
        ##print('flush_save', self._data)
        self._save_data(self._data)
        self._save_timer = None

    # -----------------------------
    # Raw Save
    # -----------------------------

    def _save_data(self, data):
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)

    def _write_defaults(self):
        self._save_data(self.DEFAULTS)
        return json.loads(json.dumps(self.DEFAULTS))

    # -----------------------------
    # Settings Editor Save
    # -----------------------------
    def update_finance_settings(
            self,
            tree_colors=None,
            trans_widths=None):

        #print(tree_colors, trans_widths)
        if tree_colors is not None:
            self._data["tree_colors"] = tree_colors

        if trans_widths is not None:
            self._data["transWidths"] = trans_widths

        self._save()
    # -----------------------------
    # Export
    # -----------------------------

    def to_dict(self):
        print('load to_dict')
        return json.loads(json.dumps(self._data))

    def getColors(self, field):
        c = self.tree_colors[field]
        return c["Background"], c["Foreground"]


fin_config = FinanceConfig()