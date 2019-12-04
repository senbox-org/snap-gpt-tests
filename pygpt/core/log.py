"""
Loggin library supporting code inspection and different level of verbosity

Author: Martino Ferrari (CS Group) <martino.ferrari@c-s.fr>
License: GPLv3
"""

import datetime
import sys
import inspect
import os

from enum import Enum

class Verbosity(Enum):
    """
    Log verbosity
    """
    VERBOSE = 0
    SUCCESS = 1
    WARNING = 2
    ERROR   = 3

class _LogLevel(Enum):
    """
    Log levels
    """
    INFO = 'LOG' #'\x1b[1mLOG\x1b[0m'
    ERROR = 'ERROR' #'\x1b[31;1mERROR\x1b[0m'
    WARNING = 'WARNING' #\x1b[33;1mWARNING\x1b[0m'
    SUCCESS = 'SUCCESS' #\x1b[32;1mSUCCESS\x1b[0m'


# global variable for verbosity
__verbosity__ = Verbosity.VERBOSE

def verbosity(*args):
    """
    Logging verbosity level.  
    If no parameters are passed return current level 
    of verbosity otherwise set a new level of verbosity.

    Paramters:
    ----------
     - level: new verbosity level (OPTIONAL)
    
    Returns:
    --------
    Current verbosity level
    """
    global __verbosity__
    if len(args) == 1 and isinstance(args[0], Verbosity):
        __verbosity__ = args[0]
    return __verbosity__



def __msg__(level: _LogLevel, *args):
    # check verbosity
    if verbosity() == Verbosity.SUCCESS: 
        if level == _LogLevel.INFO:
            return
    elif verbosity() == Verbosity.WARNING:
        if not level in [_LogLevel.WARNING, _LogLevel.ERROR]:
            return
    elif verbosity() == Verbosity.ERROR:
        if level != _LogLevel.ERROR:
            return

    now = datetime.datetime.now()
    frame = inspect.currentframe() # current frame
    if frame.f_back is not None:
        frame = frame.f_back # log fn frame (log,error....)
    if frame.f_back is not None:
        frame = frame.f_back # real caller frame

    (filename, line_number, 
     _, _, _) = inspect.getframeinfo(frame)
    frame = f'[{os.path.split(filename)[-1]}:{line_number}]' # frame string
    # print it
    print(now.strftime("%d/%m/%Y %H:%M:%S"), frame, f'{level.value}:', *args)
    sys.stdout.flush()

def info(*args):
    """Log info"""
    __msg__(_LogLevel.INFO, *args)

def panic(*args):
    """Log error and exit 1"""
    __msg__(_LogLevel.ERROR, *args)
    sys.exit(1)

def error(*args):
    """Log error"""
    __msg__(_LogLevel.ERROR, *args)


def warning(*args):
    """Log warning"""
    __msg__(_LogLevel.WARNING, *args) 

def success(*args):
    """Log success"""
    __msg__(_LogLevel.SUCCESS, *args)



class Printable:
    """
    Printable object:  
    A printable object will print nicely all its public 
    parameters and methods.
    """
    def __init__(self):
        pass

    def pretty_print(self, private=False):
        """
        pretty print
        """
        res = f'{type(self).__name__}:'
        for key in self.__dict__:
            if private or not key.startswith('__'):
                res += f'\n .{key}: {self.__dict__[key]}'
        ctype = type(self)
        for key in ctype.__dict__:
            if not key.startswith('__') and key not in ['print', 'pretty_print']:
                func = ctype.__dict__[key].__code__
                params = ', '.join(func.co_varnames[1:])
                res += f'\n .{key}({params})'
        return res

    def print(self, private=False):
        """
        compact print
        """
        res = f'{type(self).__name__}[ '
        for key in self.__dict__:
            if private or not key.startswith('__'):
                res += f'.{key}: {self.__dict__[key]}, '
        ctype = type(self)
        for key in ctype.__dict__:
            if not key.startswith('__') and key not in ['print', 'pretty_print']:
                func = ctype.__dict__[key].__code__
                params = ', '.join(func.co_varnames[1:])
                res += f'.{key}({params}), '
        return res[:-2]+']'


    def __repr__(self):
        return self.print()