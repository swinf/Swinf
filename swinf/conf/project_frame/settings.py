from swinf import config
# import default view extensions
import view  
# use default handlers
import swinf.utils.default_handlers 

config.debug = True
config.optimize = False

# swinf template settins
config.template.update({
    # extensions of html template file
    'extensions' :  ['', 'tpl', 'shtml'],
    'lookup':       [r'./view/'],
    'static_file_path':     r'./view/static',

    # code blocks
    'blocks' :  ('if', 'elif', 'else', 'try', \
                'except', 'finally', \
                'for', 'while', 'with', 'def', 'class'),

    'dedent_blocks' :('elif', 'else', 'except', 'finally'),
    # code scope tokens
    'single_line_code':     '%%',
    'multi_code_begin':     '{%',
    'multi_code_end':       '%}', 
})

# built-in server settings
config.server_host = 'localhost'
config.server_port = 8080
