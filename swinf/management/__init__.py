import swinf
import os
import sys

def load_command_class(name):
    """
    Given a command, returns the Command class instance
    """
    return getattr(__import__('swinf.management.commands.%s' % name, {}, {}, ['Command']), 'Command')()

def call_command(name, *args, **options):
    """
    Calls the given command, with the given options and args/kwargs.

    Examples:
        call_example('startproject')
    """
    _class = load_command_class(name)
    return _class.execute(*args, **options)

class ManagementUtility(object):
    def __init__(self):
        self.commands = self.default_commands

    @property
    def default_commands(self):
        command_dir = os.path.join(__path__[0], 'commands')
        # skip __init__.py
        names = [f[:-3] for f in os.listdir(command_dir) if not f.startswith('_') and f.endswith('.py')]
        return dict(
            [ (name, load_command_class(name)) for name in names ]
        )

    def print_help(self, argv):
        prog_name = os.path.basename(argv[0])
        usage = ['%s <subcommand> [options] [args]' % prog_name]
        usage.append('Swinf command line tool, version %s.%s.%s' % swinf.__version__)
        usage.append("Type '%s help <subcommand>' for help on a specific subcommand''" % prog_name)
        usage.append('Avaiable subcommands:')
        commands = self.commands.keys()
        commands.sort()
        for cmd in commands:
            usage.append(' %s' % cmd)
        print '\n'.join(usage)

    def fetch_command(self, subcommand, command_name):
        """
        Tries to fetch the given subcommand, print a message if the command called from the command line can't be found.
        """
        try:
            return self.commands[subcommand]
        except KeyError:
            sys.stderr.write("Unknown command: %s\nType '%s help' for usage.\n")
            sys.exit(1)

    def execute(self, argv=None):
        if argv == None:
            argv = sys.argv

        try:
            command_name = argv[1]
        except IndexError:
            sys.stderr.write("Type '%s help' for usage.\n") % os.path.basename(argv[9])
            sys.exit[1]

        if command_name == 'help':
            # help command
            if len(argv)>2:
                self.fetch_command(argv[2], argv[0]).print_help(argv[2:])
            else:
                self.print_help(argv)

        # swinf-admin.py --version
        # swinf-admin.py --help to work
        elif argv[1:] == ['--version']:
            print "%s.%s.%s" % swinf.__version__
        elif argv[1:] == ['--help']:
            self.print_help(argv)
        else:
            self.fetch_command(command_name, argv[0]).run(argv[1:])
                

def execute_from_command_line(argv=None):
    """
    A method that runs a ManagementUtility
    """
    utility = ManagementUtility()
    utility.execute(argv)
