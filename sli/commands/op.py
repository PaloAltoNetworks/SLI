from .base import BaseCommand
from sli.decorators import require_ngfw_connection_params

from skilletlib import SkilletLoader
import yaml
from jinja2 import Template
import json

skillet_template = """
name: sli_op
type: pan_validation
snippets:

  - name: op_test
    cmd: op
    cmd_str: {{ cmd_str }}
    output_type: xml
    outputs:
      - name: op_output
        capture_{{ capture_method }}: {{ capture_arg }}
"""

valid_methods = ['list', 'object']

def print_usage():
  print('Usage for capture module:\n  sli op [cmd] [method] [query] [context-variable:optional]\n')
  print('valid Methods:\n   ' + '\n   '.join(valid_methods))

class OpCommand(BaseCommand):

    sli_command = 'op'
    short_desc = 'Run an operational command'
    no_skillet = True

    @require_ngfw_connection_params
    def run(self):

        # Render validation skillet for execution
        if len(self.args) < 3 or len(self.args) > 4:
          print_usage()
          return

        cmd_str = self.args[0]
        capture_method = self.args[1]
        capture_arg = self.args[2]
        capture_var = ''
        if len(self.args) == 4:
          capture_var = self.args[3]
        if not capture_method in valid_methods:
          print(f'Invalid method - {capture_method}')
          print_usage()
          return

        skillet_yaml = Template(skillet_template).render({
          'capture_method': capture_method,
          'capture_arg': capture_arg,
          'cmd_str': cmd_str
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
        output = exe['outputs']['op_output']
        print(json.dumps(output, indent=4))

        # Update context if using context
        if self.sli.cm.use_context and len(capture_var) > 1:
          self.sli.context[capture_var] = output
          print(f'Output added to context as {capture_var}')
