from sli.decorators import load_variables
from sli.decorators import require_single_skillet
from sli.decorators import require_skillet_type
from .base import BaseCommand

"""
Execute a REST skillet and generate results
"""


class ValidateCommand(BaseCommand):
    sli_command = 'rest'
    short_desc = 'Execute a validation skillet of type REST'

    @require_single_skillet
    @require_skillet_type('rest')
    @load_variables
    def run(self):
        """
        Execute a REST skillet
        """

        exe = self.sli.skillet.execute(self.sli.context)
        from pprint import pprint as pp
        pp(exe)
