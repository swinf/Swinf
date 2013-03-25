from swinf import handler_walk, run
from settings import config

handler_walk("controller/")
# --------------- your code here --------------------------




if __name__ == '__main__':
    run(config.server_host, config.server_port)
