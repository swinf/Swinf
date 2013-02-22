__author__ = 'superjom'
__version__ = ('0', '0', '1')
__license__ = 'MIT'

from urlparse import parse_qs
import cgi
import os
import os.path
import mimetypes
import threading
import time
import Cookie
import traceback

from selector import *



ERROR_HANDLER = {}
HTTP_CODES = {
    100: 'CONTINUE',
    101: 'SWITCHING PROTOCOLS',
    200: 'OK',
    201: 'CREATED',
    202: 'ACCEPTED',
    203: 'NON-AUTHORITATIVE INFORMATION',
    204: 'NO CONTENT',
    205: 'RESET CONTENT',
    206: 'PARTIAL CONTENT',
    300: 'MULTIPLE CHOICES',
    301: 'MOVED PERMANENTLY',
    302: 'FOUND',
    303: 'SEE OTHER',
    304: 'NOT MODIFIED',
    305: 'USE PROXY',
    306: 'RESERVED',
    307: 'TEMPORARY REDIRECT',
    400: 'BAD REQUEST',
    401: 'UNAUTHORIZED',
    402: 'PAYMENT REQUIRED',
    403: 'FORBIDDEN',
    404: 'NOT FOUND',
    405: 'METHOD NOT ALLOWED',
    406: 'NOT ACCEPTABLE',
    407: 'PROXY AUTHENTICATION REQUIRED',
    408: 'REQUEST TIMEOUT',
    409: 'CONFLICT',
    410: 'GONE',
    411: 'LENGTH REQUIRED',
    412: 'PRECONDITION FAILED',
    413: 'REQUEST ENTITY TOO LARGE',
    414: 'REQUEST-URI TOO LONG',
    415: 'UNSUPPORTED MEDIA TYPE',
    416: 'REQUESTED RANGE NOT SATISFIABLE',
    417: 'EXPECTATION FAILED',
    500: 'INTERNAL SERVER ERROR',
    501: 'NOT IMPLEMENTED',
    502: 'BAD GATEWAY',
    503: 'SERVICE UNAVAILABLE',
    504: 'GATEWAY TIMEOUT',
    505: 'HTTP VERSION NOT SUPPORTED',
}


# Exceptions and Events

class SwinfException(Exception):
    """ Base Exception"""
    pass


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



ENVIRON = None

def bind_environ(env):
    """ Bind local project's settings to Swinf's core environment. """
    global ENVIRON
    ENVIRON = env

# Implement WSGI 

def WSGIHandler(environ, start_response):
    """ The Swinf WSGI-handler """
    global request
    global response
    request.bind(environ)
    response.bind()

    # Request dynamic route
    try:
        handler, args = match_url(request.path, request.method)
        if not handler:
            raise HTTPError(404, r"<h1>Not found</h1>")
        output = handler(**args)
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
            if DEBUG:
                output = "Exception %s: %s" % (exception.__class__.__name__, str(exception))
            else:
                output = "Unhandled exception: Application stopped"

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

    @property
    def method(self):
        """ Returns the request method (GET, POST, PUT, DELETE, ...) """
        return self._environ.get('REQUEST_METHOD', 'GET').upper()
    
    @property
    def query_string(self):
        """ Content of QUERY_STRING. """
        return self._environ.get('QUERY_STRING', '')

    @property
    def input_length(self):
        """ Content of CONTENT_LENGTH. """
        try:
            return int(self._environ.get('CONTENT_LENGTH', '0'))
        except ValueError:
            return 0

    @property
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
    
    @property
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
    
    @property
    def params(self):
        """ Returns a mix of GET and POST data. POST overwrites GET. """
        if self._GETPOST is None:
            self._GETPOST = dict(self.GET)
            self._GETPOST.update(self.POST)

    @property
    def COOKIES(self):
        """ Returns a dict with COOKIES. """
        if self._COOKIES is None:
            raw_dict = Cookie.SimpleCookie(self._environ.get('HTTP_COOKIE', ''))
            self._COOKIES = {}
            for cookie in raw_dict.values():
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
            self._COOKIES = Cookie.SimpleCookie()
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
        for key, value in dict.items(self):
            if not isinstance(value, list):
                values = [value]
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


def run(server=WSGIRefServer, host='127.0.0.1', port=8080, optimize=False, **kargs):
    """ Runs swinf as a web server, using Python's built-in swgiref implementation by default.  """

    global OPTIMIZER
    OPTIMIZER = bool(optimize)
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


request = Request()
response = Response()
DEBUG = False
OPTIMIZER = False

@error(500)
def error500(exception):
    """If an exception is thrown, deal with it and present an error page."""
    if DEBUG:
        return "<br>\n".join(traceback.format_exc(10).splitlines()).replace('  ','&nbsp;&nbsp;')
    else:
        return """<b>Error:</b> Internal server error."""
