import os
import sys
import swinf
from optparse import OptionParser

class CommandError(Exception):
    pass


class BaseCommand(object):

    option_list = ()
    help = ''
    args = ''

    def get_version(self):
        return "%s.%s.%s" % swinf.__version__

    def usage(self):
        usage = "%prog [options] " + self.args
        if self.help:
            return '%s\n\n%s' % (usage, self.help)
        else:
            return usage

    def create_parser(self, prog_name):
        return OptionParser(prog=prog_name,
                            usage=self.usage(),
                            version=self.get_version(),
                            option_list=self.option_list )

    def print_help(self, args):
        parser = self.create_parser(args[0])
        parser.print_help()

    def run(self, args):
        parser = self.create_parser(args[0])
        (options, args) = parser.parse_args(args[1:])
        try:
            self.execute(*args, **options.__dict__)
        except Exception, e:
            parser.print_usage()
        sys.stdout.write(self.handle(*args))

    def execute(self, *args, **options):
        raise NotImplementedError()
            

class LabelCommand(BaseCommand):
    args = '<label label ...>'
    label = 'label'

    def handle(self, *labels, **options):
        if not labels:
            raise CommandError('Enter at least one %s.' % self.label)

        output = []
        for label in labels:
            label_output = self.handle_label(label, **options)
            if label_output:
                output.append(label_output)
        return '\n'.join(output)

    def handle_label(self, label, **options):
        raise NotImplementedError()


class CopyFrame:
    def __call__(self, project_name, directory, other_name=''):
        self.run(project_name, directory, other_name)

    def run(self, project_name, directory, other_name=''):
        import re
        import shutil
        # If it's not a valid directory name.
        if not re.search(r'^\w+$', project_name): 
            raise CommandError("%s is not a valid project name. Please use only numbers, letters and underscores." % project_name)

        try:
            top_dir = os.path.join(directory, project_name)
            os.mkdir(top_dir)
        except OSError, e:
            raise CommandError(e)
        # determine where the template frame is
        frame_dir = os.path.join(swinf.__path__[0], 'conf', 'project_frame')

        for d, subdirs, files in os.walk(frame_dir):
            relative_dir = d[len(frame_dir)+1:]
            # contains : view/ model/ controller/ main.py
            if relative_dir:
                os.mkdir(os.path.join(top_dir, relative_dir))
            for i, subdir in enumerate(subdirs):
                if subdir.startswith('.'):
                    del subdirs[i]
            for f in files:
                if f.endswith('.pyc'):
                    continue
                path_from = os.path.join(d, f)
                path_to = os.path.join(top_dir, relative_dir, f)
                fp_from = open(path_from, 'r')
                fp_to = open(path_to, 'w')
                fp_to.write(fp_from.read())
                fp_from.close()
                fp_to.close()
                try:
                    shutil.copymode(path_from, path_to)
                    self._make_writeable(path_to)
                except OSError:
                    pass

    def _make_writeable(self, filename):
        "Makes sure that the file is writeable."
        import stat
        if sys.platform.startswith('java'):
            return
        if not os.access(filename, os.W_OK):
            st = os.stat(filename)
            new_permissions = stat.S_IMODE(st.st_mode) | stat.S_IWUSR
            os.chmod(filename, new_permissions)
# make class executable
copy_frame = CopyFrame()
