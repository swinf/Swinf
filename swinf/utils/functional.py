import functools

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

        
        
