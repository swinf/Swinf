import re
import os
import swinf
from swinf.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Use code template to automatically create a whole lot of things, given a list of available generators."
    args = "[*generator, *module_name, func_name]"

    def execute(self, *args, **options):
        """
            args[0] : name of generator
                     ('controllor', )
        """
        if not args:
            raise CommandError("give a generator")
        ctl_name = args[0]
        if ctl_name == 'controller':
            self.controller(*args[1:], **options)

    def create_controller(self, module_name, func_name=None):
        """
        Generate a new controller module or add a func in controller/module_name

        args:
            module_name: relative path of new module, if module exists in current 
                project, then just add a controller method to module_name
            func_name: func in the module
        """
        top_dir = os.getcwd()
        module_path = os.path.join(top_dir, module_name)
        if os.path.exists(module_path):
            if not func_name:
                raise CommandError("module already exists")
             

