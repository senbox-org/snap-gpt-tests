"""utils library"""
import os


def mkdirs(path):
    """make a directory tree"""
    paths = os.path.split(os.path.dirname(path))
    crr = ''
    for pth in paths:
        crr = os.path.join(crr, pth)
        if not os.path.exists(crr):
            os.mkdir(crr)
