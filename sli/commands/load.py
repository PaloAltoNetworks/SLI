from sli.tools import print_table
from .base import BaseCommand

"""
Load and display a list of skillets in a directory.
Display any errors
"""


class LoadCommand(BaseCommand):
    sli_command = 'load'
    short_desc = 'Load and display all skillets of any type'

    skillets = list()

    def run(self):
        """SLI action, test load all skillets in directory and print out loaded skillets"""
        for s in self.sli.skillets:
            obj = {
                'name': s.name,
                'type': s.type,
            }
            self.skillets.append(obj)

    def _get_output(self):
        print_table(
            self.skillets,
            {
                "Name": "name",
                "Type": "type",
            }
        )
