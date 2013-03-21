from swinf.core.exceptions import NotImplementAdapterError

# ----------- hooks -----------------
class HandlerHookAdapter(object):
    """ Adapter for WSGIHandler hooks. 
    start() before handler() run, and end() finally.  """
    def hook_start(self):
        raise NotImplementedError
    def hook_end(self):
        raise NotImplementedError


class HooksAdapter(dict):
    """ Adapter for hook container. 
    hooks can be used to insert process to another process.  """
    def add_processor(self, name, pros):
        self[name] = pros
    def processors(self):
        return self.values()
    def __repr__(self):
        return '<HandlerHooks ' + dict.__repr__(self) + '>'


class HandlerHooks(HooksAdapter):
    """ Containing all processors to run when WSGIHandler is called.  
    run processor.start() before, and finally processor.end()
    """
    def add_processor(self, name, pros_obj):
        if not issubclass(pros_obj.__class__, HandlerHookAdapter):
            raise NotImplementAdapterError(pros_obj.__class__, HandlerHookAdapter)
        self[name] = pros_obj

    def process(self, handler, **kwargs):
        for key, hook in self.items():
            hook.hook_start()
        try:
            return handler(**kwargs)
        finally:
            for key, hook in self.items():
                hook.hook_end()

