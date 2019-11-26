"""utils library"""
import os
import datetime
import sys

from enum import Enum

class Verbosity(Enum):
    """
    Log verbosity
    """
    VERBOSE = 0
    WARNING = 1
    ERROR   = 2

class _LogLevel(Enum):
    """
    Log levels
    """
    INFO = 'LOG'
    ERROR = 'ERROR'
    WARNING = 'WARNING'


# global variable for verbosity
verbosity = Verbosity.VERBOSE


def __msg__(level: _LogLevel, *args):
    global verbosity
    # check verbosity
    if verbosity == Verbosity.WARNING:
        if level == _LogLevel.INFO:
            return
    elif verbosity == Verbosity.ERROR:
        if level != _LogLevel.ERROR:
            return

    now = datetime.datetime.now()
    print(now.strftime("%d/%m/%Y %H:%M:%S"), f'{level}:', *args)
    sys.stdout.flush()

def log(*args):
    """log info"""
    __msg__(_LogLevel.INFO, *args)


def error(*args):
    """log error"""
    __msg__(_LogLevel.ERROR, *args)


def warning(*args):
    """log warning"""
    __msg__(_LogLevel.WARNING, *args) 


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
