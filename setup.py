#!/usr/bin/env python

from distutils.core import setup
from swinf import swinf

setup(name='swinf',
    version='%s.%s.%s' % swinf.__version__,
    description='WSGI micro web framework',
    author='Chunwei Yan',
    author_email='yanchunwei@outlook.com',
    url='http://github.com/superjom/swinf',
    
    py_modules=['swinf.swinf', 'swinf.selector'],
    license='MIT',
)
