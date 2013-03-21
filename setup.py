#!/usr/bin/env python

import os
from distutils.core import setup
from distutils.command.install import INSTALL_SCHEMES
import swinf

def fullsplit(path, result=None):
    """
    Split a pathname into components

    Example:
        ['home', 'chun', 'swinf', '__init__.py']
    """
    if result is None:
        result = []
    head, tail = os.path.split(path)
    if head == '':
        return [tail] + result
    if head == path:
        return result
    return fullsplit(head, [tail] + result)

for scheme in INSTALL_SCHEMES.values():
    scheme['data'] = scheme['purelib']

packages, data_files = [], []
root_dir = os.path.dirname(__file__)
swinf_dir = os.path.join(root_dir, 'swinf')
pieces = fullsplit(root_dir)
if pieces[-1] == '':
    len_root_dir = len(pieces) - 1
else:
    len_root_dir = len(pieces)

for dirpath, dirnames, filenames in os.walk(swinf_dir):
    for i, dirname in enumerate(dirnames):
        if dirname.startswith('.'): 
            del dirnames[i]
    # a python module
    if '__init__.py' in filenames:
        packages.append('.'.join(fullsplit(dirpath)[len_root_dir:]))
    elif filenames:
        data_files.append([dirpath, [os.path.join(dirpath, f) for f in filenames]])


setup(name='swinf',
    version='%s.%s.%s' % swinf.__version__,
    description='WSGI micro web framework',
    author='Chunwei Yan',
    author_email='yanchunwei@outlook.com',
    url='http://swinf.github.com/Swinf/',
    packages = packages,    
    data_files = data_files,
    scripts = ['swinf/conf/swinf-admin.py'],
    license='MIT',
)
