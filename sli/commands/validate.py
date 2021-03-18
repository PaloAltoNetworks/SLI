from .base import BaseCommand
from sli.tools import print_table
from sli.decorators import (
    require_ngfw_connection_params,
    require_single_skillet
)

"""
Execute a validation skillet and generate results
"""

class ValidateCommand(BaseCommand):

    sli_command = 'validate'

    #@Require_skillet_type('pan_validation')
    @require_single_skillet
    @require_ngfw_connection_params
    def run(self):
        """SLI action, test load all skillets in directory and print out loaded skillets"""
        print('Running validate')