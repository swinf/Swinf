# route selector module
# define route and corresponding handler here
# borrow Route from bottle.py (http://bottlepy.org/docs/dev/)
import re
import inspect

__all__ = [
    "match_url", "route", "handler",
    "handler_walk", "join_handler_space",
]

ROUTES_SIMPLE = {}
ROUTES_REGEXP = {}


def compile_route(route):
    """ Compiles a route string and returns a precompiled 
        RegexObject.

    Routes may contain some special syntax.
    Example: '/user/:id/:action' will match '/user/5/kiss' 
        with {'id':'5', 'action':'kiss'} """
    route = route.strip().lstrip('$^/').rstrip('$^')
    # Something like: '/user/:id#[0-9]#' will match
    # '/user/5' with {id:5}
    # trans to regrex format :r'/user/(?P<id>[0-9])'
    route = re.sub(r':([a-zA-Z_]+)(?P<uniq>[^\w/])(?P<re>.+?)(?P=uniq)', r'(?P<\1>\g<re>)', route)
    route = re.sub(r':([a-zA-Z_]+)', r'(?P<\1>[^/]+)', route)
    return re.compile('^/%s$' % route)


def match_url(url, method = 'GET'):
    """ Returns the first matching handler and a parameter 
        dict or (None, None)"""
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
        ROUTES_REGEXP.setdefault(method, []).append([route, \
            handler])


def route(url, **kargs):
    """ Decorator for request handler. Same as add_route(url, handler)."""
    def wrapper(handler):
        add_route(url, handler, **kargs)
        return handler
    return wrapper


__handlespace__ = None


def handler_walk(control_dir = "controller/", skip_prefix=True):
    """ Tranverse the 'controller/' dir and merge handlers 
        from each module.  
        
        Example:
            
            # control/a.py contains handler: control.a.hello
            # control/b.py contains handler: control.b.world
            # main.py
            handle_walk("controller/")

            # equal to mannually add following code

            # join_handler_space(
            #   "control.a",
            #   "control.b",
            # )
    """
    import os

    handle_modules = []

    def add_handle_modules(control_dir):
        """ Scan modules and get module paths containing 
        valid handlers.  """
        objects = os.walk(control_dir)
        # current dir
        for obj in objects:
            # TODO inter add abs path
            if obj[2] and "__init__.py" in obj[2]:
                module_files = [ f[:-3] for f in obj[2] if \
                    f.endswith(".py") ]
                module_paths = [os.path.join(obj[0], f) \
                        for f in module_files ]
                module_strs = [f.replace('/', '.') \
                        for f in module_paths]
                handle_modules.extend(module_strs)
                # Nested walking 
                if obj[1]:
                    for dirpath in obj[1]:
                        add_handle_modules( os.path.join\
                                (control_dir, dirpath))

    add_handle_modules(control_dir)
    join_handler_space(*handle_modules)
    
    prefix = "/" + control_dir

    if skip_prefix:
        print "skip prefix"
        for method in ROUTES_SIMPLE:
            for route in ROUTES_SIMPLE[method]:
                print "prefix: %s, route: %s : " % \
                        (prefix, route)
                if route.startswith(prefix):
                    handler = ROUTES_SIMPLE[method][route]
                    del ROUTES_SIMPLE[method][route]
                    route = route.replace(prefix, "/")
                    ROUTES_SIMPLE[method].setdefault\
                            (route, handler)

        
    

def join_handler_space(*module_paths):
    """ Given handler's module and automatically 
        add handlers to routes
    
    Example:

        join_handler_space( 
            "package1.module1",
            "package2.module2",
        )

    and it will add all handlers of package1.module1 \
            and package2.module2
    to routes
    """
    for path in module_paths:
        path = path.strip()
        # TODO use regrex to verify the reliability of path
        print 'import path: ', path
        exec "import %s" % path
        #print 'client_module', client_module
        try:
            exec "handle_space = %s.__handlespace__" % path
            #client_module = __import__(path)
            global __handlespace__
            __handlespace__ = handle_space
            #handle_space = client_module.__handlespace__
        except:
            print ".. tranverse controller >> skip module: %s" % path
            continue
        for method in __handlespace__:
            for handler in __handlespace__[method]:
                handler_str = "%s.%s " % (path, handler)
                route = '/' + handler_str.replace(".", "/").strip()
                exec "handler  = %s" % handler_str
                add_route(route, handler, method, simple=True)


def handler(method="GET"):
    """ Decorator to set a method a handler

    Example:

        model.hello:
        @handler("GET")
        def hello():
            return "hello world"

        in view.py:
        import model.hello
        
        then you can access `model.hello` handler model.func  by route: '/model/hello'
    """
    def wrapper(func):
        # connect to local __handlespace__
        caller = inspect.currentframe().f_back
        local_globals = caller.f_globals
        if '__handlespace__' not in local_globals:
            local_globals['__handlespace__'] = {}
            global __handlespace__
        __handlespace__ = local_globals['__handlespace__']
        add_handler(func.__name__, method)
        return func
    return wrapper


def add_handler(func, method="GET"):
    """ Add handler's name to local __handlespace__
    this will help a lot when generate routes
    """
    global __handlespace__

    if method not in __handlespace__:
        __handlespace__[method] = set()
    __handlespace__[method].add(func)
