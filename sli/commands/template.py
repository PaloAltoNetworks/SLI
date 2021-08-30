from sli.decorators import load_variables
from sli.decorators import require_single_skillet
from sli.decorators import require_skillet_type
from .base import BaseCommand

"""
Render a template and save it to a file
"""


class TemplateCommand(BaseCommand):
    sli_command = 'template'
    short_desc = 'Render a template and safe it to a file'
    help_text = """

        Render a template and save it to a file. Templates will be created
        named as they are named in the skillet. If an out_directory is not
        specified, the current working directory will be used.

        Usage:
            sli template -n template_name -o out_file
"""

    @require_single_skillet
    @require_skillet_type('template')
    @load_variables
    def run(self):

        if len(self.args):
            print(self.help_text)
            return

        output = self.sli.skillet.execute(self.sli.context)
        output = output["template"]

        out_file = self.sli.options.get("out_file", False)
        if out_file:

            with open(out_file, 'w') as f:
                f.write(output)
            print(f"Template written to {out_file}")
        else:
            print(output)
