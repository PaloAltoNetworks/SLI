from .base import BaseCommand
import json

class ShowContext(BaseCommand):

    sli_command = 'show_context'
    short_desc = 'Print out contents of an existing context'
    no_skillet = True
    no_context = True

    def run(self):
        context_name = self.args[0] if len(self.args) > 0 else 'default'
        context = self.sli.cm.load_context(from_file=context_name)
        if not len(context.keys()):
            print(f'Unable to load context {context_name}')
            return
        if self.sli.no_config:
            context.pop('config')
        print(json.dumps(context, indent=4))