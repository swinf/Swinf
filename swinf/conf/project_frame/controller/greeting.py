from swinf.selector import handler, bind_environ
from swinf import send_file


__handlespace__ = {}
bind_environ(__handlespace__)


@handler("GET")
def hello():
    return "<h1>Hello World!</h1>"
