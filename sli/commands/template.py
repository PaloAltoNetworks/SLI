from sli.decorators import load_variables
from sli.decorators import require_single_skillet
from sli.decorators import require_skillet_type
from .base import BaseCommand

import os

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
            sli template -n template_name out_directory
"""

    @require_single_skillet
    @require_skillet_type('template')
    @load_variables
    def run(self):

        if len(self.args) > 1:
            print(self.help_text)
            return
        elif len(self.args) == 1:
            out_directory = self.args[0]
        else:
            out_directory = ""

        snippets = self.sli.skillet.get_snippets()
        for snippet in snippets:
            if not snippet.should_execute(self.sli.context):
                continue
            file_path = os.path.sep.join([self.sli.skillet.path, snippet.file])
            with open(file_path, 'r') as f:
                rendered = snippet.render(f.read(), self.sli.context)
            out_path = os.path.sep.join([out_directory, snippet.file]) if len(out_directory) else snippet.file
            with open(out_path, 'w') as f:
                f.write(rendered)

        print(f"Template written to {out_path}")
