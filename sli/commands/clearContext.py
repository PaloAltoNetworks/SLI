from .base import BaseCommand

class ClearContext(BaseCommand):

    sli_command = 'clear_context'
    short_desc = 'Clear out contents of a specific context'
    no_skillet = True
    no_context = True

    def run(self):
        context_name = self.sli.options.get('context_name', '')
        if len(context_name) < 1:
            context_name = self.args[0] if len(self.args) > 0 else 'default'
        if self.sli.cm.remove_context(context_name):
            print(f'Context {context_name} has been removed')