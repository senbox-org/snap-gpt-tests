"""utils library"""
import os
import datetime

def __msg__(level, *args):
    now = datetime.datetime.now()
    print(now.strftime("%d/%m/%Y %H:%M:%S"), f'{level}:', *args)


def log(*args):
    """log info"""
    __msg__('INFO', *args)


def error(*args):
    """log error"""
    __msg__('ERROR', *args)


def warning(*args):
    """log warning"""
    __msg__('WARNING', *args) 


def mkdirs(path):
    """make a directory tree"""
    paths = os.path.split(path)
    crr = ''
    for pth in paths:
        crr = os.path.join(crr, pth)
        if not os.path.exists(crr):
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
