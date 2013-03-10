import re
import os
from swinf import HTTPError, lazy_attribute
from swinf.utils.html import html_escape
from swinf.utils.text import touni
from swinf.utils.functional import cached_property
from swinf.debug import deco

class TemplateError(HTTPError):
    pass

# cache compiled templates
TEMPLATES = {}

class BaseTemplate:
    """
    Base class and minimal API for template adapters
    """
    extensions = ['', 'tpl', 'shtml']
    settings = {}
    defaults = {}   #used in render

    def __init__(self, source=None, name=None, lookup=[], encoding='utf8', **settings):
        """
        args:
            source:     File or template source
            name:       name of template file
        """
        self.source = source.read() if hasattr(source, 'read') else source
        self.encoding = encoding
        self.settings = self.settings.copy()
        self.settings.update(settings)
        # search template file 
        if not self.source:
            if not name: raise TemplateError("No template specified.")
            self.filename = self.search(name, self.lookup)
            if not self.filename:
                raise TemplateError("Template %s not found") % repr(name)
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
    blocks = ('if', 'elif', 'else', 'try', 'except', 'finally', \
              'for', 'while', 'with', 'def', 'class')
    dedent_blocks = ('elif', 'else', 'except', 'finally')
    # TODO add settings option
    single_line_code = '%%'
    multi_code_begin = '{%'
    multi_code_end = '%}'


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
                # with {% ... %}
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
                self.ptrbuffer.append(self.yield_tokens(sline))
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


class SimpleTemplate(BaseTemplate, Codit):
    def __init__(self, source=None, name=None, lookup=[], encoding='utf8', **settings):
        BaseTemplate.__init__(self, source, name, lookup, encoding, **settings)
        Codit.__init__(self, self.source, encoding)

    @lazy_attribute
    def re_pytokens(cls):
        return re.compile(r"""
            (''(?!')|""(?!")|'{6}|"{6}      # Empty strings    
            |'(?:[^\\']|\\.)+?'             #   '
            |"(?:[^\\"]|\\.)+?"             #   "
            |'{3}(?:[^\\]|\\.|\n)+?{3}'     #   '
            |"{3}(?:[^\\]|\\.|\n)+?{3}"     #   "
            |\#.*)""", re.VERBOSE)

    def prepare(self, noescape=False, escape_func=html_escape):
        self._str = lambda x: touni(x, self.encoding)
        self._escape = escape_func
        if noescape:
            self._str, self._escape = self._escape, self._str

    @deco
    def render(self, *args, **kwargs):
        for dictarg in args: kwargs.update(dictarg)
        stdout = []
        self.execute(stdout, kwargs)
        return ''.join(stdout)
    
    @deco
    def execute(self, _stdout, *args, **kwargs):
        for dictarg in args: kwargs.update(dictarg)
        env = self.defaults.copy()
        # TODO add more template function here
        env.update({'_stdout': _stdout,
            '_printlist': _stdout.extend,
            '_escape': self._escape,
            'get': env.get,
            'setdefault': env.setdefault,
            'defined': env.__contains__
        })
        env.update(kwargs)
        eval(self.compile, env)
        self.__clean()
        return env

    def __clean(self):
        """
        Clean env

        the template instance will be cached
        """
        for m in (self.source):
            del m


TEMPLATE_PATH = ['./views']
from swinf import DEBUG, abort

@deco
def template(*args, **kwargs):  
    '''
    Get a rendered template as a string iterator.
    args[0]     : default to source 
    name        : template filename
    source      : template source
    '''
    source = args[0] if args else None
    name = kwargs.pop('tplpath', None)
    if not source and name:
        abort("No Template Specified")
    adapter = kwargs.pop('adapter', SimpleTemplate)
    lookup = kwargs.pop('lookup', TEMPLATE_PATH)
    # TODO tplid can be abs path or source
    tplid = (id(lookup), name or source)
    # refresh template if DEBUG and load changes every time
    if tplid not in TEMPLATES or DEBUG:
        settings = kwargs.pop('settings', {})
        if isinstance(source, adapter):
            TEMPLATES[tplid] = source
            if settings: TEMPLATES[tplid].prepare(**settings)
        else:
            TEMPLATES[tplid] = adapter(source=source, name=name, lookup=lookup, **settings)
    if not TEMPLATES[tplid]:
        abort(500, 'Template (%s) not found' % name)
    for dictarg in args[1:]: kwargs.update(dictarg)
    return TEMPLATES[tplid].render(kwargs)
