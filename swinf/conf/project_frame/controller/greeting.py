from swinf.selector import handler, bind_environ
from swinf import send_file


__handlespace__ = {}
bind_environ(__handlespace__)


@handler()
def hello():
    return "<h1>Hello World!</h1>"

@handler()
def static():
    return send_file("index.html", root="/home/chunwei/swinf/example/hello_world/view")

