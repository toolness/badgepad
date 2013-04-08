import os

def pkg_path(*args):
    return os.path.join(PKG_ROOT, *args)

PKG_ROOT = os.path.dirname(os.path.abspath(__file__))
