from sli.tools import print_table
from .base import BaseCommand


class ListContext(BaseCommand):
    sli_command = 'list_context'
    short_desc = 'List all available contexts'
    no_skillet = True
    no_context = True

    def run(self):
        contexts = self.sli.cm.get_contexts()
        for i in range(len(contexts)):
            contexts[i]['encrypted'] = 'Yes' if contexts[i]['encrypted'] else ''
        print_table(contexts,
                    {
                        "Name": "name",
                        "Encrypted": "encrypted",
                    })
