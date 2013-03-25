__author__ = 'Chunwei Yan <superjom@gmail.com>'
__version__ = ('0', '0', '5')
__license__ = 'MIT'

import cgi
from Cookie import SimpleCookie
import os
import mimetypes
import threading
import time
import traceback
from urlparse import parse_qs
from swinf.core.exceptions import *
from swinf.core.middleware import HooksAdapter
from swinf.core.selector import *
from swinf.utils.functional import DictProperty
from swinf.utils import Storage, MyBuffer


# global default config of swinf
# can work well when user's settings.py doesn't work
config = Storage({
    'debug':False,
    'optimize':False,

    'template' : Storage({

        # extensions of html template file
        'extensions' :  ['', 'tpl', 'shtml'],
        'lookup':       [r'./view/'],
        'static_file_path':     r'./view/static',

        # code blocks
        'blocks' :  ('if', 'elif', 'else', 'try', \
                    'except', 'finally', \
                    'for', 'while', 'with', 'def', 'class'),

        'dedent_blocks' :('elif', 'else', 'except', 'finally'),
        'single_line_code':     '%%',
        'multi_code_begin':     '{%',
        'multi_code_end':       '%}', 
    })
})


ERROR_HANDLER = {}

from swinf.utils.html import HTTP_CODES

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


# Implement WSGI 
handler_hooks = HandlerHooks()
_buffer = MyBuffer()

def WSGIHandler(environ, start_response):
    """ The Swinf WSGI-handler """
    global request
    global response
    request.bind(environ)
    response.bind()

    # Request dynamic route
    try:
        handler, args = match_url(request.path, request.method)
        print 'handler: ', handler
        if not handler:
            raise HTTPError(404, r"Not found")
        global handler_hooks
        output = handler_hooks.process(handler, **args)
        #output = handler(**args)
    except BreakSwinf, shard:
        output = shard.output
    except Exception, exception:
        response.status = getattr(exception, 'http_status', 500)
        errorhandler = ERROR_HANDLER.get(response.status, None)

        if errorhandler:
            try:
                output = errorhandler(exception)
            except:
                output = "Exception within error handler! application stoped!"
        else:
            if config.debug:
                _buffer.clean()
                traceback.print_exc(limit=2, file=_buffer)
                output = "<h1>Exception %s:</h1> <br/><pre>%s</pre>" % (exception.__class__.__name__, _buffer.source)
            else:
                output = "<h1>Unhandled exception:Application stopped</h1><br/><h2>%s</h2>" % str(exception)

        if response.status == 500:
            request._environ['wsgi.errors'].write("Error (500) on '%s': %s\n" % (request.path, exception))
    # Files
    if hasattr(output, 'read'):
        fileoutput = output
        if 'wsgi.file_wrapper' in environ:
            output = environ['wsgi.file_wrapper'](fileoutput)
        else:
            output = iter(lambda: fileoutput.read(8192), '')
    elif isinstance(output, str):
        output = [output]
    
    # Cookies
    for c in response.COOKIES.values():
        response.header.add('Set-Cookie', c.OutputString())

    status = '%d %s' % (response.status, HTTP_CODES[response.status])
    start_response(status, list(response.header.items()))
    return output


class Request(threading.local):
    """ A single request using thread-local namespace. """
    def bind(self, environ):
        """ Binds the environment of the current request to this request handler. """
        self._environ = environ
        self._GET = None
        self._POST = None
        self._GETPOST = None
        self._COOKIES = None
        self.path = self._environ.get('PATH_INFO', '/').strip()
        if not self.path.startswith('/'):
            self.path = '/' + self.path

    @DictProperty('_environ', 'swinf.method', read_only=True)
    def method(self):
        """ Returns the request method (GET, POST, PUT, DELETE, ...) """
        return self._environ.get('REQUEST_METHOD', 'GET').upper()
    
    @DictProperty('_environ', 'swinf.query_string', read_only=True)
    def query_string(self):
        """ Content of QUERY_STRING. """
        return self._environ.get('QUERY_STRING', '')

    @DictProperty('_environ', 'swinf.input_length', read_only=True)
    def input_length(self):
        """ Content of CONTENT_LENGTH. """
        try:
            return int(self._environ.get('CONTENT_LENGTH', '0'))
        except ValueError:
            return 0

    @DictProperty('_environ', 'swinf.GET', read_only=True)
    def GET(self):
        """ Returns a dict with GET parameters."""
        if self._GET is None:
            self._GET = {}
            raw_dict = parse_qs(self.query_string, keep_blank_values = 1)
            for key, value in raw_dict.items():
                if len(value) == 1:
                    self._GET[key] = value[0]
                else:
                    self._GET[key] = value
        return self._GET
    
    @DictProperty('_environ', 'swinf.POST', read_only=True)
    def POST(self):
        """ Returns a dict with POST parameters."""
        if self._POST is None:
            self._POST = {}
            raw_data = cgi.FieldStorage(fp=self._environ['wsgi.input'])
            for key in raw_data:
                if raw_data[key].filename:
                    self._POST[key] = raw_data[key]
                elif isinstance(raw_data[key], list):
                    self._POST[key] = [v.value for v in raw_data[key]]
                else:
                    self._POST[key] = raw_data[key].value
        return self._POST

    @DictProperty('_environ', 'swinf.path_info', read_only=True)
    def path_info(self):
        return self._environ.get('PATH_INFO', '')

    @DictProperty('_environ', 'swinf.remote_addr', read_only=True)
    def remote_addr(self):
        return cgi.escape(self._environ.get('REMOTE_ADDR'))
    
    @DictProperty('_environ', 'swinf.params', read_only=True)
    def params(self):
        """ Returns a mix of GET and POST data. POST overwrites GET. """
        if self._GETPOST is None:
            self._GETPOST = dict(self.GET)
            self._GETPOST.update(self.POST)

    @DictProperty('_environ', 'swinf.request.cookies', read_only=True)
    def COOKIES(self):
        cookies = SimpleCookie(self._environ.get('HTTP_COOKIE',''))
        self._COOKIES = {}
        for cookie in cookies.values():
            self._COOKIES[cookie.key] = cookie.value
        return self._COOKIES


class Response(threading.local):
    """ Represents a single response using thread-local namespace. """

    def bind(self):
        """ Clears old data and creates a new Response object. """
        self._COOKIES = None
        self.status = 200
        self.header = HeaderDict()
        self.content_type = 'text/html'
        self.error = None

    @property
    def COOKIES(self):
        if not self._COOKIES:
            self._COOKIES = SimpleCookie()
        return self._COOKIES

    def set_cookie(self, key, value, **kargs):
        """ Sets a Cookie. Optional settings: expires, path, comment, domain, max-age, secure, version, httponly. """
        self.COOKIES[key] = value
        for k in kargs:
            self.COOKIES[key][k] = kargs[k]

    def get_content_type(self):
        """ Gives access to the 'Content-Type' header and defaults to 'text/html'. """
        return self.header['Content-Type']

    def set_content_type(self, value):
        self.header['Content-Type'] = value
    # property(fget, fset, fdel, doc) as a property
    # can set value using content_type = 1 and it 
    # will automatically call set_content_type(1)
    content_type = property(get_content_type, set_content_type, None, get_content_type.__doc__)


class HeaderDict(dict):
    """ A dictionary with case insensitive (titled) keys.

    You may add a list of strings to send multible headers with the same name. """
    def __setitem__(self, key, value):
        return dict.__setitem__(self, key.title(), value)

    def __getitem__(self, key):
        return dict.__getitem__(self, key.title())
    
    def __delitem__(self, key):
        return dict.__delitem__(self, key.title())
    
    def __contains__(self, key):
        return dict.__contains__(self, key.title())

    def items(self):
        """ Returns a list of (key, value) tuples.
        list will be transformed to list [(samekey, value)...]"""
        for key, values in dict.items(self):
            if not isinstance(values, list):
                values = [values]
            for value in values:
                yield (key, str(value))

    def add(self, key, value):
        """ Adds a new header without deleting old ones """
        if isinstance(value, list):
            for v in value:
                self.add(key, v)
        elif key in self:
            if isinstance(self[key], list):
                self[key].append(value)
            else:
                self[key] = [self[key], value]
        else:
            self[key] = [value]
    

def abort(code = 500, text = 'UnKnown Error: Application stopped. '):
    """ Aborts execution and causes a HTTP error. """
    raise HTTPError(code, text)


def redirect(url, code = 307):
    """ cause a redirect. """
    response.status = code
    response.header['Location'] = url
    raise BreakSwinf("")


def send_file(filename, root="", guessmime = True, mimetype = 'text/plain'):
    """ Aborts execution and sends a static files as response. 
        if filename.startswith("/"), that means a full path """
    root = os.path.abspath(root) + '/'
    filename = os.path.normpath(filename).strip('/')
    filename = os.path.join(root, filename)
    if not filename.startswith(root):
        abort(401, "Access denied.")
    elif not os.path.exists(filename) or not os.path.isfile(filename):
        abort(404, "File does not exists")
    elif not os.access(filename, os.R_OK):
        abort(401, "You do not have permission to access this file.")

    if guessmime:
        guess = mimetypes.guess_type(filename)[0]
        if guess:
            response.content_type = guess
        elif mimetype:
            response.content_type = mimetype
    elif mimetype:
        response.content_type = mimetype

    stats = os.stat(filename)
    if 'Content-Length' not in response.header:
        response.header['Content-Length'] = str(stats.st_size)
    if 'Last-Modified' not in response.header:
        ts = time.gmtime(stats.st_mtime)
        ts = time.strftime("%a, %d %b %Y %H:%M:%S +0000", ts)
        response.header['Last-Modified'] = ts
    raise BreakSwinf(open(filename, 'rb'))


def validate(**vkargs):
    """ Validates and manipulates keyword arguments by user defined callables
    and handle ValueError and missing arguments by raising HTTPError(400)"""
    def decorator(func):
        def wrapper(**kargs):
            for key in kargs:
                if key not in kargs:
                    abort(400, 'Missing parameter: %s' % key)
                try:
                    kargs[key] = vkargs[key](kargs[key])
                except ValueError:
                    abort(400, 'Wrong parameter form at for: %s' % key)
            return func(**kargs)
        return decorator


# Error handling


def error(code=500):
    """ Decorator for error handler. Same as set_error_handler(code, handler). """
    def wrapper(handler):
        def set_error_handler(code, handler):
            code = int(code)
            ERROR_HANDLER[code] = handler
        set_error_handler(code, handler)
        return handler
    return wrapper


#Server adaper

class ServerAdaper(object):
    def __init__(self, host='127.0.0.1', port=8080, **kargs):
        self.host, self.port, self.options = \
            host, int(port), kargs

    def __repr__(self):
        return "%s (%s:%d)" % (self.__class__.__name__, self.host, self.port)

    def run(self, handler):
        pass


class WSGIRefServer(ServerAdaper):
    def run(self, handler):
        from wsgiref.simple_server import make_server
        srv = make_server(self.host, self.port, handler)
        srv.serve_forever()


def run(host='127.0.0.1', port=8080, \
            server=WSGIRefServer, optimize=False, **kargs):
    """ Runs swinf as a web server, using Python's 
        built-in swgiref implementation by default."""

    def _run(server, host, port, optimize, **kargs):
        config.optimize = bool(optimize)
        quiet = bool('quiet' in kargs and kargs['quiet'])
        if isinstance(server, type) and issubclass(server, ServerAdaper):
            server = server(host=host, port=port, **kargs)
        if not isinstance(server, ServerAdaper):
            raise RuntimeError("Server must be a subclass of ServerAdaper")
        if not quiet:
            print "Swinf server starting up (using %s)..." % repr(server)
            print "Listening on http://%s:%d" % (server.host, server.port)
            print "Use Ctrl-C to quit."
            print 

        try:
            server.run(WSGIHandler)
        except KeyboardInterrupt:
            # TODO specifically Ctrl-C
            print "Shuting down ..."

    if config.debug:
        from swinf.utils import reloader
        reloader.main(_run, server, host, port, optimize, **kargs)
    else:
        _run(server, host, port, optimize, **kargs)




request = Request()
response = Response()

@error(500)
def error500(exception):
    """If an exception is thrown, deal with it and present an error page."""
    if config.debug:
        return "<br>\n".join(traceback.format_exc(10).splitlines()).replace('  ','&nbsp;&nbsp;')
    else:
        return """<b>Error:</b> Internal server error."""
