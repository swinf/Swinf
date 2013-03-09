from swinf.selector import handler, bind_environ


__handlespace__ = {}
bind_environ(__handlespace__)

# ------------- your code here --------------------

@handler()
def hello():
    """
    visit http://localhost:8080/hello in your brower
    """
    return "<h1>Hello World!</h1>"
