from sli.decorators import load_variables
from sli.decorators import require_single_skillet
from sli.decorators import require_skillet_type
from sli.decorators import require_ngfw_connection_params
from sli.decorators import require_panoply_connection
from .base import BaseCommand
from sli.tools import pretty_print_xml, merge_xml_into_config

from lxml import etree

"""
Generate output of a panos skillet and write to file
"""


# TODO: DELETE ME!!!
def write_xml(xml, name):
    with open(name, 'w') as f:
        for line in pretty_print_xml(xml):
            f.write(line)


class PreviewCommand(BaseCommand):
    sli_command = 'preview'
    short_desc = 'Generate output of a panos skillet and write to file'
    help_text = """

        Load and run a panos configuration skillet, saving the output to
        disk in a specified directory as opposed to configuring NGFW

        Usage:
            sli preview -n configuration_skillet out_directory
"""

    @require_single_skillet
    @require_skillet_type('panos')
    @load_variables
    @require_ngfw_connection_params
    @require_panoply_connection
    def run(self, pan):
        if len(self.args) > 1:
            print(self.help_text)
            return
        # elif len(self.args) == 1:
        #     out_directory = self.args[0]
        # else:
        #     out_directory = ""

        config = etree.fromstring(pan.get_configuration())
        write_xml(config, "C:/users/amall/Desktop/config.xml")
        snippets = self.sli.skillet.get_snippets()
        for snippet in snippets:

            if not snippet.should_execute(self.sli.context):
                continue
            xpath = snippet.metadata.get('xpath')
            meta = snippet.render_metadata(self.sli.context)
            element = meta.get('element')
            child_tag = xpath.split('/')[-1:][0]
            child_xml = etree.fromstring(f"<{child_tag}>{element}</{child_tag}>")
            merge_xml_into_config(xpath, config, child_xml)

        write_xml(config, "C:/users/amall/Desktop/test.xml")
