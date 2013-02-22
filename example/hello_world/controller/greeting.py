from swinf.selector import handler, bind_environ
from swinf.core import send_file
import os


__handlespace__ = {}
bind_environ(__handlespace__)


@handler()
def hello():
    return "<h1>Hello World!</h1>"

@handler()
def static():
    return send_file("index.html", root="/home/chunwei/swinf/example/hello_world/view")

