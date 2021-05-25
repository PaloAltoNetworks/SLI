from .base import BaseCommand
from sli.decorators import require_single_skillet, require_skillet_type

import yaml
from lxml import etree


class CreateTemplate(BaseCommand):
    sli_command = 'create_template'
    short_desc = 'Create an XML template from a panos or panorama skillet'
    no_context = True
    help_text = """

    Usage:
        sli create_template -n [skillet] [baseline-file] [out-file]

"""

    @staticmethod
    def insert_template_str(xml_doc, line_number, template_string):
        """
        Break up an xml_doc (str) at line_number to inject template_string.
        Return the updated xml_doc string
        """
        pass

    @require_single_skillet
    @require_skillet_type("panos", "panorama")
    def run(self):
        if not len(self.args) == 2:
            print(self.help_text)
            return

        out_file = self.args[1]
        baseline_file = self.args[0]
        with open(baseline_file, "r") as f:
            baseline_xml = etree.fromstring(f.read())

        # TODO: Verify that baseline file does not contain multiple elements per line

        snippets = self.sli.skillet.get_snippets()
        # Verify required parameters present in snippets
        for snippet in snippets:
            if getattr(snippet, "template_str", None) is None:
                print(f"Snippet {snippet.name} has no template_str")
                return
            if "xpath" not in snippet.metadata:
                print(f"Snippet {snippet.name} has no xpath")
                return

        # Find the various insert points on all snippets
        lines = {}
        for snippet in snippets:
            found = baseline_xml.xpath(snippet.metadata["xpath"])
            if len(found) > 1:
                print(f"xpath {snippet.metadata['xpath']} returned more than 1 result in baseline")
            if len(found):
                if found[0].sourceline in lines:
                    print(f"Tag {found[0].tag} has overlapping insert at line {found[0].sourceline}")
                    return
                lines[found[0].sourceline] = snippet.template_str
            else:
                print("Found nothing")

        # Sort the keys so we're starting from the point furthest down the file

        # Insert snippets one at a time until complete
