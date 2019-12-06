"""
File system utility for pygpt

Author: Martino Ferrari (CS Group) <martino.ferrari@c-s.fr>
License: GPLv3
"""
import os


__base_path__ = '.'

def set_base_path(path):
    """
    Set base path for the project
    """
    global __base_path__
    __base_path__ = path

def resolve(*path):
    """
    Resolve a path relative to the base path 
    """
    return os.path.join(__base_path__, *path)

class Directory:
    """
    Base directory class
    """
    def __init__(self, *path):
        self._path = path

    @property
    def path(self):
        """
        Absolute directory path
        """
        return resolve(*self._path)

    def update(self, *path):
        self._path = path
    
    def resolve(self, *path):
        """
        Resolve path relative to the directory
        """
        return os.path.join(self.path, *path)


def mkdir(path):
    """create dir if needed"""
    if not os.path.exists(path):
        os.mkdir(path)

performances = Directory('performances') # folder containing perforamnces files
statistics = Directory('performances', 'stats') # folder containing statistics file
profiles = Directory('performances', 'csv') # folder containing CSV files
plots = Directory('performances', 'plot') # folder containing the performances plots

tests = Directory('tests') # folder that will contains the test report html files
outputs = Directory('output') # folder containing the stdout and stderr of the test executions
templates = Directory('templates') # folder containing the HTML templates
images = Directory('images') # folder containing the graph images
