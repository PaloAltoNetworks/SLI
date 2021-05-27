import json

import yaml
from jinja2 import Template
from skilletlib import SkilletLoader

from sli.decorators import require_config
from .base import BaseCommand

skillet_template = """
name: sli_capture
type: pan_validation
snippets:

  - name: capture_test
    cmd: parse
    variable: config
    outputs:
      - name: capture_test
        capture_{{ capture_method }}: {{ capture_arg }}
"""

valid_methods = ['list', 'object', 'expression']


class Capture(BaseCommand):
    sli_command = 'capture'
    short_desc = 'Capture a value based on object, list, or expression'
    no_skillet = True
    help_text = """
    Usage for capture module:
        sli capture [method] [query] [context-variable:optional]

    valid Methods:
        'list', 'object', 'expression'

    """

    @require_config
    def run(self, config):

        if len(self.args) < 1 or len(self.args) > 2:
            print(self.help_text)
            return

        capture_method = self.args[0]
        if capture_method not in ["list", "object", "expression"]:
            print(self.help_text)
            return

        capture_arg = None
        capture_var = getattr(self.sli, "context_var")
        if len(self.args) > 1:
            capture_arg = self.args[1]
        if not capture_arg:
            capture_arg = input(f"\ncapture_{capture_method}: ")

        skillet_yaml = Template(skillet_template).render({
            'capture_method': capture_method,
            'capture_arg': capture_arg
        })
        skillet_dict = yaml.safe_load(skillet_yaml)
        sl = SkilletLoader()
        skillet = sl.create_skillet(skillet_dict)
        self.sli.skillet = skillet

        # Create a secondary context object without any cached creds to ensure config
        # is used from context. Decorator will handle getting a fresh copy of the config
        # from device if appropriate before this command is called
        context = {x: y for x, y in self.sli.context.items() if not x.startswith("TARGET_")}
        # Execute skillet and extract values from target
        exe = skillet.execute(context)
        if not skillet.success:
            print('Unable to execute command')
            return

        output = exe['outputs']['capture_test']

        # Update context if using context
        if self.sli.cm.use_context and capture_var:
            self.sli.context[capture_var] = output
            print(f'Output added to context as {capture_var}')

    def _get_output(self):
        if self.sli.skillet is not None:
            results = self.sli.skillet.get_results()
            # Print captured JSON
            output = results['outputs']
            if 'capture_test' in output:
                print(json.dumps(output['capture_test'], indent=4))
