from .base import BaseCommand
from sli.tools import print_table

"""
Load and display a list of skillets in a directory.
Display any errors
"""

class LoadCommand(BaseCommand):

    sli_command = 'load'
    short_desc = 'Load and display all skillets of any type'

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