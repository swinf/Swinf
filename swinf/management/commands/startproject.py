from swinf.management.base import copy_frame, CommandError, LabelCommand
import os

INVALID_PROJECT_NAMES = ('swinf', 'site', 'test')

class Command(LabelCommand):
    help = "Creates a Swinf directory structure for the given project name in the current directory"
    args = "[projectname]"
    label = 'project name'

    def handle_label(self, project_name, **options):
        directory = os.getcwd()
        if project_name in INVALID_PROJECT_NAMES:
            raise CommandError("%s conflicts with the name of an existing Swinf module and cannot be used as a project name.")

        copy_frame(project_name, directory)
