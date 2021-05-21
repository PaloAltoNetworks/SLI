from sli.decorators import load_variables
from sli.decorators import require_single_skillet
from sli.decorators import require_skillet_type
from sli.decorators import require_config
from .base import BaseCommand
from sli.tools import merge_xml_into_config

from lxml import etree

"""
Generate output of a panos skillet and write to file
"""


class PreviewCommand(BaseCommand):
    sli_command = "preview"
    short_desc = "Generate output of a panos skillet and write to file"
    help_text = """

        Load and run a panos configuration skillet, saving the output to
        disk in a specified directory as opposed to configuring NGFW

        Usage:
            sli preview -n configuration_skillet -o output_file.xml
"""

    @require_single_skillet
    @require_skillet_type("panos", "panorama")
    @load_variables
    @require_config
    def run(self, config):

        out_file = self.sli.options.get("out_file", "out.xml")
        snippets = self.sli.skillet.get_snippets()
        for snippet in snippets:

            if not snippet.should_execute(self.sli.context):
                continue
            meta = snippet.render_metadata(self.sli.context)
            xpath = snippet.metadata.get("xpath")
            element = meta.get("element")
            child_tag = xpath.split("/")[-1]
            child_xml = etree.fromstring(f"<{child_tag}>{element}</{child_tag}>")
            merge_xml_into_config(xpath, config, child_xml)

        config.write(out_file, encoding="utf-8", pretty_print=True, xml_declaration=True)
