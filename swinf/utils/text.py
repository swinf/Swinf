
def touni(s, enc='utf8', err='strict'):
    return s.decode(enc, err) if isinstance(s, bytes) else unicode(s)

