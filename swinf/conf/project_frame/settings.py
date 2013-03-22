from swinf import config


config.debug = True

# swinf template settins
config.template_lookup = [r'./view/']
config.static_file_path = r'./view/static'

# built-in server settings
config.server_host = 'localhost'
config.server_port = 8080
