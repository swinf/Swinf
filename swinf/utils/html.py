# -*- coding: utf-8 -*-

def html_escape(c):
    ''' Escape HTML special characters `&<>` and quotes `'"`'''
    c = str(c)
    return c.replace('&','&amp;').replace('<','&lt;').replace('>','&gt;')\
                 .replace('"','&quot;').replace("'",'&#039;')
