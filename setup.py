#!/usr/bin/env python

from distutils.core import setup
from swinf import core

setup(name='swinf',
    version='%s.%s.%s' % core.__version__,
    description='WSGI micro web framework',
    author='Chunwei Yan',
    author_email='yanchunwei@outlook.com',
    url='http://github.com/superjom/swinf',
    
    py_modules=['swinf.core', 'swinf.selector'],
    license='MIT',
)
