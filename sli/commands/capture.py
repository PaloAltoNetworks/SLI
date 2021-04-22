from .base import BaseCommand
from sli.decorators import require_ngfw_connection_params

from skilletlib import SkilletLoader
import yaml
from jinja2 import Template
import json

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

def print_usage():
  print('Usage for capture module:\n  sli capture [method] [query] [context-variable:optional]\n')
  print('valid Methods:\n   ' + '\n   '.join(valid_methods))


class Capture(BaseCommand):

    sli_command = 'capture'
    short_desc = 'Capture a value based on object, list, or expression'
    no_skillet = True

    @require_ngfw_connection_params
    def run(self):
        """
        Usage: sli capture [method] [context_var] [capture_string]
        """

        # Render validation skillet for execution
        if len(self.args) < 2 or len(self.args) > 3:
          print_usage()
          return

        capture_method = self.args[0]
        capture_arg = self.args[1]
        capture_var = ''
        if len(self.args) == 3:
          capture_var = self.args[2]
        if not capture_method in valid_methods:
          print(f'Invalid method - {capture_method}')
          print_usage()
          return

        skillet_yaml = Template(skillet_template).render({
          'capture_method': capture_method,
          'capture_arg': capture_arg
        })
        skillet_dict = yaml.safe_load(skillet_yaml)
        sl = SkilletLoader()
        skillet = sl.create_skillet(skillet_dict)

        # Execute skillet and extract values from target 
        exe = skillet.execute(self.sli.context)
        if not skillet.success:
          print('Unable to execute command')
          return

        # Print captured JSON 
        output = exe['outputs']['capture_test']
        print(json.dumps(output, indent=4))

        # Update context if using context
        if self.sli.cm.use_context and len(capture_var) > 1:
          self.sli.context[capture_var] = output
          print(f'Output added to context as {capture_var}')
