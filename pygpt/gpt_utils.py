"""utils library"""
import os
import datetime
import sys
import inspect

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
    INFO = '\x1b[1mLOG\x1b[0m'
    ERROR = '\x1b[31;1mERROR\x1b[0m'
    WARNING = '\x1b[33;1mWARNING\x1b[0m'
    SUCCESS = '\x1b[32;1mSUCCESS\x1b[0m'


# global variable for verbosity
verbosity = Verbosity.VERBOSE


def __msg__(level: _LogLevel, *args):
    global verbosity
    # check verbosity
    if verbosity == Verbosity.SUCCESS: 
        if level == _LogLevel.INFO:
            return
    elif verbosity == Verbosity.WARNING:
        if not level in [_LogLevel.WARNING, _LogLevel.ERROR]:
            return
    elif verbosity == Verbosity.ERROR:
        if level != _LogLevel.ERROR:
            return

    now = datetime.datetime.now()
    previous_frame = inspect.currentframe().f_back
    (filename, line_number, 
     _, _, _) = inspect.getframeinfo(previous_frame)
    frame = f'- {os.path.split(filename)[-1]}:{line_number}'
    print(now.strftime("%d/%m/%Y %H:%M:%S"), frame, f'{level.value}:', *args)
    sys.stdout.flush()

def log(*args):
    """log info"""
    __msg__(_LogLevel.INFO, *args)

def panic(*args):
    """log error and exit 1"""
    __msg__(_LogLevel.ERROR, *args)
    sys.exit(1)

def error(*args):
    """log error"""
    __msg__(_LogLevel.ERROR, *args)


def warning(*args):
    """log warning"""
    __msg__(_LogLevel.WARNING, *args) 

def success(*args):
    """log success"""
    __msg__(_LogLevel.SUCCESS, *args)

def mkdirs(path):
    """make a directory tree"""
    paths = os.path.abspath(path).split(os.sep)
    crr = '/'
    for pth in paths:
        crr = os.path.join(crr, pth)
        if not os.path.isdir(crr):
            os.mkdir(crr)


class Printable:
    """
    simple auto-print function
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
                res += f'\n - {key}: {self.__dict__[key]}'
        return res

    def print(self, private=False):
        """
        compact print
        """
        res = f'{type(self).__name__}['
        for key in self.__dict__:
            if private or not key.startswith('__'):
                res += f'.{key}: {self.__dict__[key]},'
        return res[:-1]+']'


    def __repr__(self):
        return self.print()

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