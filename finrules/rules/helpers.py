
# rules/helpers.py
import tkinter as tk
import sys
import traceback
from logging_manager import get_logger

log = get_logger(__name__)

def clamp(val, minimum=0, maximum=255):
    if val < minimum:
        return minimum
    if val > maximum:
        return maximum
    return val

def colorscale(hexstr, scalefactor):
    hexstr = hexstr.strip('#')
    if scalefactor < 0 or len(hexstr) != 6:
        return hexstr

    r = int(hexstr[:2], 16)
    g = int(hexstr[2:4], 16)
    b = int(hexstr[4:], 16)

    r = int(clamp(r * scalefactor))
    g = int(clamp(g * scalefactor))
    b = int(clamp(b * scalefactor))

    return "#%02x%02x%02x" % (r, g, b)

def normalize_description(desc: str) -> str:
    if not desc:
        return ""
    return desc.upper()


