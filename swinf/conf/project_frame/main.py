import os
import swinf
from swinf.selector import handler_walk, route

handler_walk("controller/")

# ------------ default handlers here ----------------------
# ------------ you can change them ------------------------
static_dir = os.path.join(os.getcwd(), 'view/static')
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
# --------------- your code here --------------------------





if __name__ == '__main__':
    if swinf.debug:
        from swinf.utils import reloader
        reloader.main(swinf.run)
    else:
        swinf.run()
