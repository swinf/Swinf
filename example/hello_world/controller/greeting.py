from swinf.selector import handler, bind_environ


__handlespace__ = {}
bind_environ(__handlespace__)


@handler()
def hello():
    return "Hello World!"

