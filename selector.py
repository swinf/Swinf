import re
from debug import *



ROUTES_SIMPLE = {}
ROUTES_REGEXP = {}


def compile_route(route):
    """ Compiles a route string and returns a precompiled RegexObject.

    Routes may contain some special syntax.
    Example: '/user/:id/:action' will match '/user/5/kiss' with {'id':'5', 'action':'kiss'} """
    route = route.strip().lstrip('$^/').rstrip('$^')
    # Something like: '/user/:id#[0-9]#' will match
    # '/user/5' with {id:5}
    # trans to regrex format :r'/user/(?P<id>[0-9])'
    route = re.sub(r':([a-zA-Z_]+)(?P<uniq>[^\w/])(?P<re>.+?)(?P=uniq)', r'(?P<\1>\g<re>)', route)
    route = re.sub(r':([a-zA-Z_]+)', r'(?P<\1>[^/]+)', route)
    return re.compile('^/%s$' % route)


def match_url(url, method = 'GET'):
    """ Returns the first matching handler and a parameter dict or (None, None)"""
    url = '/' + url.strip().lstrip('/')
    # Static routes first
    route = ROUTES_SIMPLE.get(method, {}).get(url, None)
    if route:
        return (route, {})
    # Then regrex routes
    routes = ROUTES_REGEXP.get(method, [])
    for i in xrange(len(routes)):
        match = routes[i][0].match(url)
        if match:
            handler = routes[i][1]
            # TODO swap the frequently matching route with its predecessor
            return (handler, match.groupdict())
    return (None, None)

@deco
def add_route(route, handler, method='GET', simple=False):
    """ Adds a new route to the route mappings.
        
        Example:
        def hello(): return 'hello world'
        add_route(r'/hello', hello)"""
    method = method.strip().upper()
    if re.match(r'^/(\w+/)*\w*$', route) or simple:
        ROUTES_SIMPLE.setdefault(method, {})[route] = handler
    else:
        route = compile_route(route)
        ROUTES_REGEXP.setdefault(method, []).append([route, handler])


def route(url, **kargs):
    """ Decorator for request handler. Same as add_route(url, handler)."""
    def wrapper(handler):
        add_route(url, handler, **kargs)
        return handler
    return wrapper


__handlespace__ = None

def bind_environ(handlespace):
    """ Bind application's local environ to swinf's global environ. """
    global __handlespace__
    __handlespace__ = handlespace
    
    


def add_handler(func, __handlespace__, method="GET"):
    """ Add handler's name to local __handlespace__
    this will help a lot when generate routes
    """
    if method not in __handlespace__:
        __handlespace__[method] = set()
    __handlespace__[method].add(func)



def handler(__handlespace__, method="GET"):
    """ Decorator to set a method a handler
    Example:
        you can access handler model.func  by url: '/model/func'
    """
    def wrapper(func):
        add_handler(func.__name__, __handlespace__,  method)
        return func
    return wrapper


def join_handler_space(*module_paths):
    """ Given handler's module and automatically add handlers to routes
    
    Example:
        import package1.module1
        import package2.module2

        join_handler_space(
            "package1.module1",
            "package2.module2",
        )

    and it will add all handlers of package1.module1
    to routes
    """
    for path in module_paths:
        path = path.strip()
        # TODO use regrex to verify the reliability of path
        exec "import %s" % path
        exec "handle_space = %s.__handlespace__" % path
        # TODO 
        for method in handle_space:
            for handler in handle_space[method]:
                handler_str = "%s.%s " % (path, handler)
                route = '/' + handler_str.replace(".", "/").strip()
                exec "handler  = %s" % handler_str
                add_route(route, handler, method, simple=True)

