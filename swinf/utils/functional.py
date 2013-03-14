import functools


class DictProperty(object):
    ''' Property that maps to a key in a local dict-like attribute. 
    Once visited, property will be stored and never be changed even the original property is changed.
    '''
    def __init__(self, attr, key=None, read_only=False):
        self.attr, self.key, self.read_only = attr, key, read_only

    def __call__(self, func):
        functools.update_wrapper(self, func, updated=[])
        self.getter, self.key = func, self.key or func.__name__
        return self

    def __get__(self, obj, cls):
        if obj is None: return self
        key, storage = self.key, getattr(obj, self.attr)
        if key not in storage: storage[key] = self.getter(obj)
        return storage[key]

    def __set__(self, obj, value):
        if self.read_only: raise AttributeError("Read-Only property.")
        getattr(obj, self.attr)[self.key] = value

    def __delete__(self, obj):
        if self.read_only: raise AttributeError("Read-Only property.")
        del getattr(obj, self.attr)[self.key]


class cached_property(object):
    """
    A property that is only computed once per instance and then replace
    itself with an ordinary attribute.
    """
    def __init__(self, func):
        self.__doc__ = getattr(func, '__doc__')
        self.func = func

    def __get__(self, instance, owner):
        if instance is None: return self
        value = instance.__dict__[self.func.__name__] = self.func(instance)
        return value


class lazy_attribute(object):
    """
    A property that caches itself to the class object.
    """
    def __init__(self, func):
        functools.update_wrapper(self, func, updated=[])
        self.getter = func

    def __get__(self, instance, owner):
        value = self.getattr(owner)
        setattr(owner, self.__name__, value)
        return value

        
        
