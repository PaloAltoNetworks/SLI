import json

import yaml
from jinja2 import Template
from skilletlib import SkilletLoader

from sli.decorators import require_ngfw_connection_params
from .base import BaseCommand

skillet_template = """
name: sli_op
type: pan_validation
snippets:

  - name: op_test
    cmd: {{ cmd }}
    cmd_str: {{ cmd_str }}
    output_type: {{ output_type }}
    outputs:
      - name: op_output
        capture_{{ capture_method }}: {{ capture_arg }}
"""

valid_methods = ["list", "object", "text", "value"]


class OpCommand(BaseCommand):
    sli_command = "op"
    short_desc = "Run an operational command and optionally parse and capture the results into the context"
    no_skillet = True
    help_text = """
    Usage for 'op' module:
        sli op [cmd] [capture_method] [query] [context-variable:optional]

    Example: Get system info and return information as XML text
        sli op "show system info"

    Example: Get system info, using XML command syntax, as a JSON object
        sli op "<show><system><info/></system></show>" object

    Example: get system info as a JSON object and use an XPATH filter for only the plugin_versions
        sli op "show system info" object "./plugin_versions"

    Example: get system info and only return the value of the sw-version tag
        sli op "show system info" value "./sw-version"

    Example: get system info and only return the value of the sw-version tag and store it in the context as 'sw'
        sli op "show system info" text "./sw-version" sw -uc
    """

    @require_ngfw_connection_params
    def run(self):

        # Render validation skillet for execution
        if len(self.args) < 1 or len(self.args) > 4:
            self._print_usage()
            return

        cmd_str: str = self.args[0]
        capture_var: str = ""
        capture_method = "text"
        capture_arg = "."

        if len(self.args) > 1:
            capture_method: str = self.args[1]

        if len(self.args) > 2:
            capture_method: str = self.args[1]
            capture_arg: str = self.args[2]

        if len(self.args) > 3:
            capture_var = self.args[3]

        if capture_method not in valid_methods:
            print(f"Invalid method - {capture_method}")
            self._print_usage()
            return

        if capture_method == "text":
            # either the user said they wanted text output, of they didn't specify
            # if they said text, BUT the specified a query, then what they really want is 'value'
            if capture_arg != ".":
                output_type = "xml"
                capture_method = "value"
            else:
                output_type = "text"
        else:
            output_type = "xml"

        # if the user has passed us an xml string, then use 'op' otherwise use 'cli'
        if cmd_str.startswith("<") and cmd_str.endswith(">"):
            cmd = "op"
        else:
            cmd = "cli"

        skillet_yaml = Template(skillet_template).render(
            {
                "capture_method": capture_method,
                "capture_arg": capture_arg,
                "cmd_str": cmd_str,
                "cmd": cmd,
                "output_type": output_type,
            }
        )

        skillet_dict = yaml.safe_load(skillet_yaml)
        sl = SkilletLoader()
        skillet = sl.create_skillet(skillet_dict)

        # Execute skillet and extract values from target
        exe = skillet.execute(self.sli.context)
        if not skillet.success:
            print("Unable to execute command")
            return

        output = exe["outputs"]["op_output"]
        if capture_method != "text":
            # Print captured JSON
            print(json.dumps(output, indent=4))
        else:
            print(output)

        # Update context if using context
        if self.sli.cm.use_context and len(capture_var) > 1:
            self.sli.context[capture_var] = output
            print(f"Output added to context as {capture_var}")

    def _get_output(self):
        pass
