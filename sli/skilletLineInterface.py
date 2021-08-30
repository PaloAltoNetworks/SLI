from skilletlib import Skillet
from skilletlib import SkilletLoader
from inspect import isclass
from types import ModuleType
import traceback

from sli import commands
from sli.contextManager import ContextManager
from sli.commands.base import BaseCommand
from sli.errors import InvalidArgumentsException, SLIException, SLILoaderError
from sli.tools import store_traceback

from skilletlib.exceptions import LoginException, TargetConnectionException


class SkilletLineInterface:

    def __init__(self, options, action, args):
        self.action = action
        self.options = options
        self.args = args
        self._unpack_options()
        self.command_map = {}
        self._load_commands()
        self._verify_command()
        self.sl = SkilletLoader()
        self.no_skillet = getattr(self.command_map[self.action], "no_skillet", False) is True
        self.no_context = getattr(self.command_map[self.action], "no_context", False) is True

        # Load skillets only if the command requires them
        if not self.no_skillet:
            self._load_skillets()
            self._verify_loaded_skillets()

        # Load context if requested, load only a specified environment otherwise
        self.cm = ContextManager(self.options)
        if not self.no_context:
            self.context = self.cm.load_context()
        else:
            self.context = self.cm.load_environment()
        self.skillet: Skillet = None  # Active running skillet

    def _unpack_options(self):
        """Unpack options onto self where required"""
        for opt in ("verbose", "commit", "report", "loader_error", "output_format", "no_config", "context_var"):
            setattr(self, opt, self.options.get(opt, False))
        self.report_file = self.options.get("report_file", "")

        # If a report file was specified, assume we want to create it
        if self.report_file:
            self.generate_report = True

    def _load_commands(self, command_map=None):
        """
        Loads a list of commands from the sli.commands package. Does so by iterating over contents of the
        package and locating types of 'type' that have an sli_command specified.
        """

        if command_map is None:
            command_map = self.command_map

        # Go through each module in the commands package
        for item in dir(commands):
            item_obj = getattr(commands, item)
            if isinstance(item_obj, ModuleType):

                # Get only the attributes which are classes
                for item_attr in dir(item_obj):
                    item_attr_obj = getattr(item_obj, item_attr)
                    if isclass(item_attr_obj):

                        # Only load commands that subclass BaseCommand
                        if item_attr_obj == BaseCommand or not issubclass(item_attr_obj, BaseCommand):
                            continue

                        # Load only SLI command modules that are appropriately written
                        command_string = getattr(item_attr_obj, "sli_command", "")
                        if len(command_string) > 0:
                            command_map[command_string] = item_attr_obj

    def _verify_command(self):
        """Called in __init__ to verify a submitted command is valid before running SkilletLoader"""
        if self.action not in self.command_map:
            raise InvalidArgumentsException('Invalid action, run "sli --help" for list of available actions')

    def _load_skillets(self):
        """Called in __init__ to front end SkilletLoader"""
        self.skillets = self.sl.load_all_skillets_from_dir(self.options.get("directory", "./"))
        if len(self.sl.skillet_errors) > 0:
            print("Errors on loading skillets:")
            for err in self.sl.skillet_errors:
                for key in err:
                    print(f"   {key} - {err[key]}")
            if self.loader_error:
                raise SLILoaderError("SkilletLoader encountered errors")

    def _verify_loaded_skillets(self):
        """Perform any pre-execution validations against loaded skillets"""

        if len(self.skillets) < 1:
            raise SLIException("No skillets were loaded.")

    @classmethod
    def get_commands(self):
        """Load commands for purposes other than execution"""

        command_map = {}
        self._load_commands(self, command_map=command_map)
        return command_map

    def execute(self):
        """Run supplied SLI command"""

        action_obj = self.command_map[self.action](self)
        run_func = action_obj.execute_debug if self.options.get("debug") else action_obj.execute
        try:
            run_func()
        except SLILoaderError as sl_exc:
            raise sl_exc
        except (LoginException, TargetConnectionException) as exc:
            print(f"Login error: {exc}")
            if self.options.get("raise_exception"):
                raise exc
        except Exception as exc:
            if self.options.get("raise_exception"):
                raise exc
            else:
                print(f"Error: {exc}")
                store_traceback(traceback.format_exc())

        # Update context with new keys from skillet run
        if not self.no_context:
            skillet_context = getattr(self.skillet, "context", None)
            if skillet_context:
                for key in skillet_context.keys():
                    if key not in ["loop", "loop_index"]:
                        self.context[key] = skillet_context[key]
            self.cm.save_context(self.context)
