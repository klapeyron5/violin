from .. import Transform
from os.path import join, basename, isdir, isfile, exists


def is_transform_instance(t):
    assert isinstance(t, Transform), f"Not a Transform: {t}"

def is_dir(dirpath):
    assert isdir(dirpath), f"Not a dir: {dirpath}"

def is_file(filepath):
    assert isfile(filepath), f"Not a file: {filepath}"

def is_not_empty_str(s):
    assert isinstance(s, str) and s!='', f"Not a str: |{s}|"

def is_dict(d):
    assert isinstance(d, dict), f"Not a dict: {d}"

def is_boolflag(f):
    assert isinstance(f, bool), f"Not a bool flag: {f}"

def is_str_not_empty(f):
    assert isinstance(f, str), f"Not a str: {f}"

def is_int(x):
    assert isinstance(x, int), f"Not an int: {x}"

def is_positive(x):
    assert x>0, f"Not a positive: {x}"

def is_not_negative(x):
    assert x>=0, f"Shouldnt be negative: {x}"
