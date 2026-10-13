'''
logging_manager.py
'''
# Python Includes
import os
import sys
import logging
from pathlib import Path
import traceback
#import subprocess

# 3rd Party Includes

# Project Includes

def log_exception(exc: Exception):
    etype, evalue, tb = sys.exc_info()
    tb_str = "".join(traceback.format_exception(etype, evalue, tb))
    #log.error(f"EXCEPTION: {exc}\n{tb_str}")
    print(f"EXCEPTION: {exc}\n{tb_str}")
    
'''def log.error(exc: Exception):
    etype, evalue, tb = sys.exc_info()
    tb_str = "".join(traceback.format_exception(etype, evalue, tb))
    logging.error(f"EXCEPTION: {exc}\n{tb_str}")
'''

def get_logger(name="finance_explorer"):

    logger = logging.getLogger(name)
    logger.propagate = False
    if logger.handlers:
        return logger
        
    logger.setLevel(logging.DEBUG)

    file_handler = logging.FileHandler("logs/finance.log", encoding="utf-8", mode='w')
    file_handler.setLevel(logging.DEBUG)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(filename)s(%(lineno)s) %(message)s"
    )

    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    # Only attach console handler when running from source
    '''if not getattr(sys, "frozen", False):
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    '''
    #logger.info(f"FinOfx version {__version__} starting up")
    return logger