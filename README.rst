Swinf Web Frame
================

Swinf is a simple micro-framework for small web application and has no dependencies other than the Python Standard Liberaty.

It offers a built-in HTTP Server, and a simple route binding mechanism.

Example
--------
A Bottle.py like route binding mechanism:

.. code-block:: python
    
    from swinf.swinf import run
    from swinf.selector import route

    @route('/hello/:name')
    def hello(name):
        return '<h1>Hello %s!</h1>' % name.title()

    run(host='localhost', port=8080)

Much simpler route binding mechanism:

.. code-block:: python
    # module1.py

    from swinf.selector import handler, bind_eviron

    __handlespace__ = {}
    bind_eviron(__handlespace__)

    @handler("GET")
    def hello():
        return '<h1>Hello</h1>' 

    @handler("GET")
    def world():
        return '<h1>World</h1>' 


    # view.py
    from swinf.swinf import run
    from swinf.selector import handler, bind_eviron
    from swinf.selector import join_handler_space

    import module1

    join_handler_space(
        "module1",
    )

    run(host='localhost', port=8080)

This will will automatically bind route `/module1/hello` to handler `module1.hello` and `/module1/world` to handler `module1.world`


You don't have to edit routes manully.
