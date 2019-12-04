"""
Utils:
Different comodity and commons 
"""
import os
import datetime
import sys
import inspect

from core.log import Printable



def mkdirs(path):
    """make a directory tree"""
    paths = os.path.abspath(path).split(os.sep)
    crr = '/'
    for pth in paths:
        crr = os.path.join(crr, pth)
        if not os.path.isdir(crr):
            os.mkdir(crr)

def rlist_files(path, filter_fn=lambda _: True):
    """
    Recursively list files in all sub folder.

    Parameters:
    -----------
     - path: path to explore
     - filter_fn: optional filter function
    """
    res = []
    for file in os.listdir(path):
        file = os.path.join(path, file)
        if os.path.isdir(file):
            res += rlist_files(file, filter_fn)
        elif filter_fn(file):
            res.append(file)
    return res