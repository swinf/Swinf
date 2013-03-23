.. docs documentation master file, created by
   sphinx-quickstart on Fri Feb 22 18:29:56 2013.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

==============
Swinf Document
==============

Installation
=============================================

Swinf can work without any external libraries. You can just download `Swinf.tar` from our github page, extract it and run following command inside the directory

.. code-block:: bash
    
    $ sudo python setup.py install

This will get you the latest development snapshot that includes all the new features.


If you prefer a more stable environment, you should stick with the stable releases. These are avaliable on `PyPi <http://pypi.python.org/pypi/bottle>` and can be installed via :command:`pip`, :command:`easy_install`.

.. code-block:: bash
    
    $ sudo pip install swinf        # recommanded
    $ sudo easy_install swinf       # alternative without pip
    

QuickStart: "Hello World"
=====================================

This tutorial assumes you have Swinf :ref:`installed <installation>`. 
Let's start with a very basic "Hello World" example.

First, run following command to start a new project.

.. code-block:: bash

    $ swinf-admin.py startproject helloworld

or :command:`swinf-admin.py sp hellowlrld` for short. this should create a project directory called `hello world` in current path.

Inside path `helloworld/controller` you can create a new module like `great.py` and add a new controller method to it.

.. code-block:: python

    from swinf import handler

    @handler("GET")
    def hello():
        return "Hello World!"

Run script `helloworld/main.py` , visit http://localhost:8080/greet/hello and you will see "Hello World!" in your browser. 
You may feel wried, for you didn't define any URL structure, 
and Swinf automatically link controller :func:`hello()`  to route ``/greet/hello`` where ``greet`` is the name of your crontroller module and ``hello`` is the name of handler method.

Here is how it works:

The :func:`handler` will add handler method's name to a local 
data space. When server starts, Swinf will scan 'controller' package and automatically link every method defined by the :func:`handler` decorator to the path to it. 

For example: ``/greet/hello`` to :func:`controller.greet.hello`,
in other words, ``module_name/handler_name`` to :func:`module.handler` or ``package_name/module_name/handler_name`` to :func:`package.module.handler`.

Whenever a browser requests an URL, the associated controller is called and the return value is sent back to the browser. Its as simple as that.

Read ``helloworld/main.py``, there is some automatically generated code there.

.. code-block:: python

    import swinf 
    import swinf.utils.default_handlers
    from settings import config

    if __name__ == '__main__':
        swinf.handler_walk("controller/")
        swinf.run(config.server_host, config.server_port)

The :func:`handler_walk` scans ``controller/`` directory and link every handler to it's route.

All project settings are in ``helloworld/settins.py``, and you can change them.

The :func:`run` call in the last line starts a built-in development server using local settings from ``helloworld/settings.py``, you can read and change that. 
It runs on `localhost` port 8080 and serves requests until you hit :kbd:`Control-c`. 
You can switch the server backend later, but for now a development server is all we need. 
It requires no setup at all and is an incredibly painless way to get your application up and running for local tests.

Of course this is a very simple example, but it shows the basic concept of how applications are built with Bottle. Continue reading and you'll see what else is possible.

Request Routing
======================
Swinf contains two route model. One is ``Auto Routing`` which automatically link handler to a automatically generated route. 
The other one is ``Dymatical Routing`` which we borrow from bottle.py(http://bottlepy.org).

Auto Routing
--------------
In the last chapter, we built a very simple web application by creating a controller. Here is the example again.

.. code-block:: python
    
    # in helloworld/controller/greet.py
    from swinf import handler

    @handler("GET")
    def hello():
        return "Hello World!"

and the :func:`handler()` decorator wrap the :func:`hello` and transform it to a handler. When the application server starts, 
Swinf will scan the direcotry ``controller/`` and automatically link all handlers to their route.
By default, ``auto route`` is the importing paths of handlers.

In the above example, we define a handler :func:`controller.greet.hello`, and the ``auto route`` is ``/greet/hello`` overlooking the prefix ``controller``.

The ``auto routing`` mechanism make route structure more clear, and you don't have to edit routes manually.


Dymatic Routing
------------------
We borrowed ``Dymatic Routing`` from bottle.py. By ``Dymatic Routing``, you can controll a hander's route manually.

For example:

.. code:: python
    
    from swinf import route, handler

    @route('/hello')
    def hello():
        return "Hello World!"

    # auto-routing and dymatic-routing do not\
    # affect each other
    @handler("GET")
    def response():

The ``auto routing`` mechanism and ``dymatic routing`` mechanism do not affect each other, in other words, you can use them together.

By ``dynamic routing`` mechanism, you can add tags or even regrex content to a route.









Contents:

.. toctree::
   :maxdepth: 2



Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

