#Swinf Web Frame

Swinf is a simple micro-framework for small web application and has no dependencies other than the Python Standard Liberaty.

It offers a built-in HTTP Server, and a simple route binding mechanism.


##Commands
run command : `swinf-admin.py startproject newproject` and swinf will create a project directory.

Inside current project directory, there are a `main.py` and three subdirectories:

controller:

    containing controllers.

view:
    
    containing view template files.

    subdirecties:
        
        static/: contains static files
        
        static/images: images here
        
        static/style: css files here

        static/script: js files here

        static/files: other static files here

model:
    
    you can put your database controlling code here.


You can add some controllers in `controller` directory and run `main.py`, and it will work.

##Template
Currently, swinf have a simple template engine called `SimpleTemplate`.

the tpl syntax follows below

```html

    <!-- in a tpl file -->

    {%
    # multiline code

    def bold_wrapper(txt):
        return "<b>" + txt + "</b>"
    endef
    %}

    %% # sigleline code
    %% if name:
    <h1> hello {{name}}!</h1>
    %% else:
    <h1> Hello World!</h1>
    %% endif

    <ul>
    %% for i in range(100):
        <li>no: {{i}}</li>
    %% endfor
    </ul>
```

To use the **template**, you can use code like below:

```python
    
    from swinf.template import template
    # pass tpl source
    html = template("<h1>hello {{name}}", name='world')

    # pass a tpl file
    html = template(path='index.tpl', name='world')
```

##Example
In swinf, there is no `urls.py`-like config file, instead, there are two simple route-config ways:

* A Bottle.py like route binding mechanism

```python
    
    from swinf.swinf import run
    from swinf.selector import route
    
    # a simple controller 
    @route('/hello/:name')
    def hello(name):
        return '<h1>Hello %s!</h1>' % name.title()

    run(host='localhost', port=8080)
```

* Much simpler route binding mechanism

```python

    # module1.py
    from swinf.selector import handler

    # --------- your code here -----------

    @handler("GET")
    def hello():
        return '<h1>Hello</h1>' 

    @handler("GET")
    def world():
        return '<h1>World</h1>' 
```


This will will automatically bind route **/module1/hello** to handler **controller.module1.hello** and **/module1/world** to handler **controller.module1.world**. 

You don't have to add routes manully.
