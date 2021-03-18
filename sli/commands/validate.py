from .base import BaseCommand
from sli.tools import print_table

"""
Execute a validation skillet and generate results
"""

class ValidateCommand(BaseCommand):

    sli_command = 'validate'

    # TODO: Next steps, implement these decorators
    @require_ngfw_connection_params
    # TODO: This one should be processed as *args
    @Require_skillet_type('pan_validation')
    def run(self):
        """SLI action, test load all skillets in directory and print out loaded skillets"""
        objs = []
        for s in self.sli.skillets:
            obj = {
                'name': s.name,
                'type': s.type,
            }
            objs.append(obj)
        print_table(
            objs,
            {
                "Name": "name",
                "Type": "type",
            }
        )