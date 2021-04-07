from .base import BaseCommand
from sli.tools import get_variable_input
from sli.decorators import (
    require_ngfw_connection_params,
    require_single_skillet,
    require_skillet_type
)

class ConfigureCommand(BaseCommand):

    sli_command = 'configure'

    @require_single_skillet
    @require_skillet_type('panos')
    @require_ngfw_connection_params
    def run(self):
        context = {}
        for var in self.sli.skillet.variables:
            context.update(get_variable_input(var))
        from pprint import pprint
        pprint(context)
        print('Finished')