"""
Utils:
Different comodity and commons 
"""
import os
import datetime
import sys
import inspect

from functools import wraps

from core.log import Printable



def mkdirs(path):
    """make a directory tree"""
    crr, path = os.path.splitdrive(path)
    paths = os.path.abspath(path).split(os.sep)
    crr += os.path.sep
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


def auto_getter(func):
    """
    Class decorator to automatically genrate all getters for private parameters (if not already defined). 
    """
    @wraps(func)
    def inner(*args, **kwargs):
        x = func(*args, **kwargs)
        ctype = type(x)
        for param in x.__dict__:
            getter_name = param[2:-2]
            if param.startswith('__') and param.endswith('__') and not hasattr(ctype, getter_name):
                def getter(self):
                    return self.__dict__[param]
                setattr(ctype, getter_name, getter)
        return x
    return inner

def auto_setter(func):
    """
    Class decorator to automatically generate all setters for private parameters (if not already defined)
    """
    @wraps(func)
    def inner(*args, **kwargs):
        x = func(*args, **kwargs)
        ctype = type(x)
        for param in x.__dict__:
            setter_name = f'set_{param[2:-2]}'
            if param.startswith('__') and param.endswith('__') and not hasattr(ctype, setter_name):
                def setter(self, value):
                    self.__dict__[param] = value
                setattr(ctype, setter_name, setter)
        return x
    return inner

def split_args(arg):
    res = []
    curr = ''
    skip = False
    skip_char = ''
    for c in arg:
        if c == ' ' and not skip:
            res.append(curr)
            curr = ''
        elif not skip and c in ["'", '"']:
            skip = True
            skip_char = c
            curr += c
        elif skip and c == skip_char:
            skip = False
            curr += c
        else:
            curr += c

    if len(curr) > 0:
        res.append(curr)
    return res