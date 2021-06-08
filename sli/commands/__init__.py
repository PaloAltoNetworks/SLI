from sli.commands.base import BaseCommand
from pathlib import Path
from pkgutil import iter_modules
from inspect import isclass
from importlib import import_module

# Disable SSL warning
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Load all command modules from this package

package_dir = Path(__file__).resolve().parent
for (_, module_name, _) in iter_modules([str(package_dir)]):

    # Load each module individually
    module = import_module(f"{__name__}.{module_name}")
    for attr_name in dir(module):
        attr = getattr(module, attr_name)

        # Evaluate each class found in the module
        if attr is BaseCommand:
            continue
        if isclass(attr):
            if not len(getattr(attr, 'sli_command', '')) > 0:
                continue
            if not issubclass(attr, BaseCommand):
                raise ImportError(f'Command module {attr} must subclass BaseCommand')
            globals()[attr_name] = attr
