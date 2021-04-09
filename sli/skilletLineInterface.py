from skilletlib import SkilletLoader
from sli.tools import print_table
from getpass import getpass
from panforge import Report
from inspect import isclass
import os

from sli import commands
from types import ModuleType

class SkilletLineInterface():

    def __init__(self, options, action):
        self.action = action
        self.options = options
        self._unpack_options()
        self.command_map = {}
        self._load_commands()
        self._verify_command()
        self.sl = SkilletLoader()
        self._load_skillets()
        self._verify_loaded_skillets()
        self.context = {}
        self.skillet = None # Active running skillet
    
    def _unpack_options(self):
        """Unpack options onto self where required"""
        for opt in ('verbose', 'commit', 'report', 'loader_error'):
            setattr(self, opt, self.options.get(opt, False))
        self.report_file = self.options.get('report_file', '')

        # If a report file was specified, assume we want to create it
        if self.report_file:
            self.generate_report = True
    
    def _load_commands(self):
        """
        Loads a list of commands from the sli.commands package. Does so by iterating over contents of the
        package and locating types of 'type' that have an sli_command specified.
        """

        # Go through each module in the commands package
        for item in dir(commands):
            item_obj = getattr(commands, item)
            if isinstance(item_obj, ModuleType):

                # Get only the attributes which are classes
                for item_attr in dir(item_obj):
                    item_attr_obj = getattr(item_obj, item_attr)
                    if isclass(item_attr_obj):

                        # Load only SLI command modules that are appropriately written
                        command_string = getattr(item_attr_obj, 'sli_command', '')
                        self.command_map[command_string] = item_attr_obj
    
    def _verify_command(self):
        """Called in __init__ to verify a submitted command is valid before running SkilletLoader"""
        if not self.action in self.command_map:
            print('Invalid action')
            exit(1)

    def _load_skillets(self):
        """Called in __init__ to front end SkilletLoader"""
        self.skillets = self.sl.load_all_skillets_from_dir(self.options.get('directory', './'))
        if len(self.sl.skillet_errors) > 0:
            print('Errors on loading skillets:')
            for err in self.sl.skillet_errors:
                for key in err:
                    print(f"   {key} - {err[key]}")
            if self.loader_error:
                raise Exception('SkilletLoader encountered errors')

    def _verify_loaded_skillets(self):
        """Perform any pre-execution validations against loaded skillets"""

        if len(self.skillets) < 1:
            print("No skillets were loaded.")
            exit(1)

    def execute(self):
        """Run supplied SLI command"""

        action_obj = self.command_map[self.action](self)
        action_obj.execute()

        # Clean run, normal exit
        exit(0)