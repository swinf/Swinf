from swinf import core
from swinf.selector import handler_walk
import environ

core.DEBUG = True
core.bind_environ(environ.ENV)

handler_walk("controller/")
core.run()
