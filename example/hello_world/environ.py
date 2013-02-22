import os

__length = len("settings.py")

SETTINGS_PATH = os.path.abspath(__file__)
PROJECT_ROOT_PATH = SETTINGS_PATH[:-__length]

ENV = {
    'PROJECT_ROOT_PATH' : PROJECT_ROOT_PATH,
    'CONTROLLER_PATH' : os.path.join(PROJECT_ROOT_PATH, "controller"),
    'VIEW_PATH' : os.path.join(PROJECT_ROOT_PATH, "view"),
    'MODEL_PATH' : os.path.join(PROJECT_ROOT_PATH, "model"),
}

from swinf.core import send_file
from swinf.selector import route

@route(r"/view/:filename#.*#")
def static(filename):
    return send_file(filename, ENV['VIEW_PATH'])
