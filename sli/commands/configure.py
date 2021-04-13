from .base import BaseCommand
from sli.tools import get_variable_input
from sli.decorators import (
    require_ngfw_connection_params,
    require_single_skillet,
    require_skillet_type
)

class ConfigureCommand(BaseCommand):

    sli_command = 'configure'
    short_desc = 'Execute a configuration skillet of type panos'

    @require_single_skillet
    @require_skillet_type('panos')
    @require_ngfw_connection_params
    def run(self):
        for var in self.sli.skillet.variables:
            self.sli.context.update(get_variable_input(var))
        exe = self.sli.skillet.execute(self.sli.context) 
        if self.sli.commit:
            print('Commiting configuration...')
            self.sli.skillet.panoply.commit()
            print('Finished')
        else:
            print('Configuration loaded into candidate config')