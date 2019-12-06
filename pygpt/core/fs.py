"""
File system utility for pygpt

Author: Martino Ferrari (CS Group) <martino.ferrari@c-s.fr>
License: GPLv3
"""
import os

class Directory:
    """
    Base directory class
    """
    def __init__(self, *path, parent=None):
        self._parent = parent
        self._path = path


    @property
    def path(self):
        """
        Absolute directory path
        """
        if self._parent is not None:
            return self._parent.resolve(*self._path)
        return os.path.join(*self._path)

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

report = Directory('')

performances = Directory('performances', parent=report) # folder containing perforamnces files
statistics = Directory('performances', 'stats', parent=report) # folder containing statistics file
profiles = Directory('performances', 'csv', parent=report) # folder containing CSV files
plots = Directory('performances', 'plot', parent=report) # folder containing the performances plots

tests = Directory('tests', parent=report) # folder that will contains the test report html files
outputs = Directory('output', parent=report) # folder containing the stdout and stderr of the test executions
templates = Directory('templates') # folder containing the HTML templates
images = Directory('images', parent = report) # folder containing the graph images
