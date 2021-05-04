from sli.decorators import load_variables
from sli.decorators import require_ngfw_connection_params
from sli.decorators import require_single_skillet
from sli.decorators import require_skillet_type
from .base import BaseCommand


class ConfigureCommand(BaseCommand):
    sli_command = 'configure'
    short_desc = 'Execute a configuration skillet of type panos'
    help_text = """
    Executes a PAN-OS configuration skillet.
    """

    @require_single_skillet
    @require_skillet_type('panos')
    @require_ngfw_connection_params
    @load_variables
    def run(self):
        exe = self.sli.skillet.execute(self.sli.context)
        if self.sli.commit:
            print('Committing configuration...')
            self.sli.skillet.panoply.commit()
            print('Finished')
        else:
            print('Configuration loaded into candidate config')
