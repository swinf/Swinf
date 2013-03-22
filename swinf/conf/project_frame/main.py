import swinf
from swinf.selector import handler_walk
import swinf.utils.default_handlers
from settings import config

handler_walk("controller/")
# --------------- your code here --------------------------




if __name__ == '__main__':
    swinf.run(config.server_host, config.server_port)
