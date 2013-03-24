import os
import swinf
from swinf.core.selector import route
# ------------ you can change them ------------------------
static_dir = os.path.join(os.getcwd(), swinf.config.template.static_file_path)
@route("/static/:path")
def static(path):
    return swinf.send_file(path, root=static_dir)

@route("/images/:path")
def images(path):
    return swinf.send_file(path, root=os.path.join(static_dir, 'images'))

@route("/files/:path")
def files(path):
    return swinf.send_file(path, root=os.path.join(static_dir, 'files'))

@route("/style/:path")
def style(path):
    return swinf.send_file(path, root=os.path.join(static_dir, 'style'))

@route("/script/:path")
def script(path):
    return swinf.send_file(path, root=os.path.join(static_dir, 'script'))

