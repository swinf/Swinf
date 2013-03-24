import re
import os
import swinf
from swinf import TemplateError, config
from swinf.utils import MyBuffer
from swinf.utils.functional import cached_property
from swinf.utils.html import html_escape
from swinf.utils.text import touni

__all__ = (
    "BaseTemplate", 
    # container of user-defined extension method to SimpleTemplate
    "extens", 
    "SimpleTemplate",
    "template",
)

class BaseTemplate:
    """
    Base class and minimal API for template adapters
    """
    extensions = config.template.extensions
    settings = {}
    defaults = {}   #used in render
    lookup= swinf.config.template.lookup

    def __init__(self, source=None, path=None, lookup=[], encoding='utf8', **settings):
        """
        args:
            source:     File or template source
            name:       name of template file
        """
        self.source = source.read() if hasattr(source, 'read') else source
        self.encoding = encoding
        self.settings = self.settings.copy()
        self.settings.update(settings)
        if lookup: self.lookup = lookup
        # search template file 
        if not self.source:
            if not path: raise TemplateError("No template specified.")
            self.filename = self.search(path, self.lookup)
            if not self.filename:
                raise TemplateError("Template %s not found" % repr(path))
            try:
                with open(self.filename, 'r') as f:
                    self.source = f.read()
            except IOError:
                raise TemplateError("Template load IO Error")
        self.prepare(settings)

    @classmethod
    def search(cls, name, lookup=[]):
        for _dir in lookup:
            filename = os.path.join(_dir, name)
            print 'search template in ', filename
            for extension in cls.extensions:
                if os.path.isfile(filename + extension):
                    return filename + extension

    def prepare(self, **options):
        raise NotImplementedError

    def render(self, *args, **kwargs):
        raise NotImplementedError


class Codit(object):
    """
    Parse a template to code
    and compile it
    the compiled code object can be easily cached
    """
    indent_space = '    '
    blocks = config.template.blocks
    dedent_blocks = config.template.dedent_blocks
    # TODO add settings option
    single_line_code = config.template.single_line_code
    multi_code_begin = config.template.multi_code_begin
    multi_code_end = config.template.multi_code_end


    def __init__(self, template, encoding='utf8'):
        self.template = template
        self.encoding = encoding
        self.stack = []
        self.ptrbuffer = []
        self.codebuffer = []
        self.multiline = self.dedent = self.oneline = False

    def __call__(self, tempalte):
        """
        return:
            co  : compiled code
        """
        return self.run(template)

    def yield_tokens(self, line):
        for i, part in enumerate(re.split(r'\{\{(.*?)\}\}', line)):
            if i % 2:
                if part.startswith('!'): yield 'RAW', part[1:]
                else: yield 'CMD', part
            else: yield 'TXT', part

    def code(self, stmt):
        for line in stmt.splitlines():
            self.codebuffer.append(self.indent_space * len(self.stack) + line.strip())


    def flush(self):
        if not self.ptrbuffer: return
        cline = ''
        for line in self.ptrbuffer:
            for token, value in line:
                if not value: continue
                if token == 'TXT': cline += repr(value) # add '
                elif token == 'RAW': cline += '_str(%s)' % value
                elif token == 'CMD': cline += '_escape(%s)' % value
                cline += ', '
            cline = cline[:-2] + '\\\n'
        cline = cline[:-2]
        if cline[:-1].endswith('\\\\\\\\\\n'):
            cline = cline[:-7] + cline[-1] # 'nobr\\\\\n' --> 'nobr'
        cline = '_printlist([' + cline + '])'
        del self.ptrbuffer[:]
        self.code(cline)

    # TODO add an option to clean empty string line 
    def codit(self):
        """
        Parse tempalte to python code buffer
        """
        multi_code = False
        for lineno, line in enumerate(self.template.splitlines(True)):
            line = touni(line, self.encoding)
            sline = line.strip()
            # begin with {%
            if sline.startswith(self.multi_code_begin):
                multi_code = True
                sline = sline[2:].strip()

            if multi_code or \
                    (sline and sline.startswith(self.single_line_code)):
                # end with %}
                if sline.endswith(self.multi_code_end):
                    multi_code = False
                    line = sline[:-2]
                # begin with %%
                elif sline.startswith(self.single_line_code):
                    line = sline[2:].strip() # line following the %%
                # within {% ... %}
                else:
                    line = sline
                #if not line: continue
                cmd = re.split(r'[^a-zA-Z0-9_]', line)[0]
                self.flush()

                if cmd in self.blocks or self.multiline:
                    cmd = self.multiline or cmd
                    dedent = cmd in self.dedent_blocks
                    if dedent and not self.oneline and not self.multiline:
                        cmd = self.stack.pop()
                    self.code(line)
                    # a single line
                    oneline = not line.endswith(':')
                    multiline = cmd if line.endswith('\\') else False
                    if not oneline and not multiline:
                        self.stack.append(cmd)
                elif cmd.startswith('end') and self.stack:
                    self.code('#end(%s) %s' % (self.stack.pop(), line.strip()[3:]))
                else:
                    self.code(line)
            else:
                self.ptrbuffer.append(self.yield_tokens(line))
        self.flush()
        return '\n' .join(self.codebuffer) + '\n' 
    
    @cached_property
    def compile(self):
        code = self.codit()
        self.__clean()
        return compile(code, '<string>', 'exec')

    def __clean(self):
        """
        Clean env
        
        the instance may be cached
        """
        for m in (self.stack, self.ptrbuffer, \
                self.codebuffer, self.template):
            del m

# ------------- SimpleTemplate ----------------------------------
from swinf.core.middleware import HooksAdapter

class Extens(HooksAdapter):
    """Add extens methods to SimpleTemplate engine
    For example:

    Define an extension method:
    
        def _import_script(_stdout, path):
            script_path = \
                "<script src='/static/script/%s'></script>" % path
            _stdout.append(script_path)

    You should use _stdout as the first parameter and append the \
    content to _stdout if you want to insert the content into the \
    final html source.
    
    extens.add('import_script', import_script)

    then, you can use the new extension in the template file:
    {%import_script('./jquery.js')%}"""

    def __init__(self):
        self.add = self.add_processor

    def bind(self, _stdout):
        self._stdout = _stdout

    def add_all(self, dic):
        """
        Add multiple extens

        args:
            dic: a dic of key-extens

        usage:
            extens.add_all({
                '_import_script':_import_script,
                '_import_style':_import_style,
            })
        """
        self.update(dic)

extens = Extens() 

class SimpleTemplate(BaseTemplate, Codit):
    def __init__(self, source=None, path=None, lookup=[], encoding='utf8', **settings):
        BaseTemplate.__init__(self, source, path, lookup, encoding, **settings)
        Codit.__init__(self, self.source, encoding)

    def prepare(self, noescape=False, escape_func=html_escape):
        self._str = lambda x: touni(x, self.encoding)
        self._escape = escape_func
        if noescape:
            self._str, self._escape = self._escape, self._str

    def render(self, *args, **kwargs):
        for dictarg in args: kwargs.update(dictarg)
        stdout = MyBuffer()
        self.execute(stdout, kwargs)
        return stdout.source
    
    def execute(self, _stdout, *args, **kwargs):
        self._stdout = _stdout
        for dictarg in args: kwargs.update(dictarg)
        env = self.defaults.copy()
        # TODO add more template function here
        env.update({'_stdout': _stdout,
            '_printlist': _stdout.extend,
            '_escape': self._escape,
            '_str': self._str,
            '_include': self.subtemplate,
            '_print': self._str,
        })
        # add extens
        global extens
        env.update(extens)
        env.update(kwargs)
        eval(self.compile, env)
        self.__clean()
        return env

    def subtemplate(self, path, *args, **kwargs):
        for dictarg in args: kwargs.update(dictarg)
        if path not in TEMPLATES:
            TEMPLATES[path] = self.__class__(path=path, lookup=self.lookup)
        return TEMPLATES[path].execute(self._stdout, **kwargs)

    def __clean(self):
        """
        Clean env

        the template instance will be cached
        """
        for m in (self.source):
            del m


# cache compiled templates
TEMPLATES = {}

TEMPLATE_PATH = ['./view']
from swinf import abort

def template(*args, **kwargs):  
    '''
    Get a rendered template as a string iterator.
    args[0]     : default to source 
    name        : template filename
    source      : template source
    '''
    source = args[0] if args else None
    path = kwargs.pop('path', None)
    if not (source or path):
        abort("No Template Specified")
    adapter = kwargs.pop('adapter', SimpleTemplate)
    lookup = kwargs.pop('lookup', TEMPLATE_PATH)
    # TODO tplid can be abs path or source
    tplid = (id(lookup), path or source)
    # refresh template if DEBUG and load changes every time
    if tplid not in TEMPLATES or swinf.config.debug:
        settings = kwargs.pop('settings', {})
        if isinstance(source, adapter):
            TEMPLATES[tplid] = source
            if settings: TEMPLATES[tplid].prepare(**settings)
        else:
            TEMPLATES[tplid] = adapter(source=source, path=path, lookup=lookup, **settings)
    # TODO if not same settings , maybe different cache
    if not TEMPLATES[tplid]:
        abort(500, 'Template (%s) not found' % repr(path))
    for dictarg in args[1:]: kwargs.update(dictarg)
    return TEMPLATES[tplid].render(kwargs)
