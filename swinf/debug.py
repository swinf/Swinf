import traceback
import sys


def deco(func):
    def wrapper(*args, **kargs):
        print "<=", args, "=>",
        print "<<< ", func.__name__, " >>>"
        return func(*args, **kargs)
    return wrapper

