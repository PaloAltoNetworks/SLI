from .base import BaseCommand


class ClearContext(BaseCommand):
    """
    Clear SLI context.
    Pass the 'creds' argument to only remove non credential parameters
    """

    sli_command = 'clear_context'
    short_desc = 'Clear out contents of a specific context'
    no_skillet = True
    no_context = True

    def run(self):

        # Find the name of the target context
        args = [x for x in self.args if not x == 'creds']
        context_name = self.sli.options.get('context_name', '')
        if len(context_name) < 1:
            context_name = args[0] if len(args) > 0 else 'default'

        # Remove non credential items from existing context
        if 'creds' in self.args:
            if self.sli.cm.clean_context(context_name):
                print(f"Non credential items have been removed from context {context_name}")

        # Remove the entire context by default
        else:
            if self.sli.cm.remove_context(context_name):
                print(f'Context {context_name} has been removed')
