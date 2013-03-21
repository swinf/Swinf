# Exceptions and Events ------------------------------------------------

class SwinfException(Exception):
    """ Base Exception"""
    pass

class SwinfError(SwinfException):
    def __init__(self, info):
        self.info = info

class HTTPError(SwinfException):
    """ Break the execution and instantly jump to error handler. """
    def __init__(self, status, text):
        self.output = text
        self.http_status = int(status)

    def __str__(self):
        return self.output


class BreakSwinf(SwinfException):
    """ Just a way to break current execution and instantly jump to call start_response() and return the content of output"""
    def __init__(self, output):
        self.output = output


class NotImplementAdapterError(SwinfError):
    def __init__(self, subcls, cls):
        super(self, SwinfError).__init__("class %s should implement %s" % subcls.__name__, cls.__name__)


class TemplateError(HTTPError):
    def __init__(self, message):
        HTTPError.__init__(self, 500, message)


