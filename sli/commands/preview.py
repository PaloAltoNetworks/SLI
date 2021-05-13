from sli.decorators import load_variables
from sli.decorators import require_single_skillet
from sli.decorators import require_skillet_type
from sli.decorators import require_ngfw_connection_params
from sli.decorators import require_panoply_connection
from .base import BaseCommand
from sli.tools import pretty_print_xml

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
        write_xml(config, "C:/users/amallory/Desktop/config.xml")
        snippets = self.sli.skillet.get_snippets()
        for snippet in snippets:
            if not snippet.should_execute(self.sli.context):
                continue

            xpath = snippet.metadata.get('xpath')
            meta = snippet.render_metadata(self.sli.context)
            element = meta.get('element')
            child_tag = xpath.split('/')[-1:][0]
            child_xml = etree.fromstring(f"<{child_tag}>{element}</{child_tag}>")

            found = config.xpath(xpath)
            print(f"{xpath}   [{len(found)}]")
            if len(found) == 1:
                found = found[0]
                if len(found.xpath("//entry")) > 0 or len(child_xml.xpath("//entry")) > 0:
                    print("   Has entry children")
                    merge_children(found, child_xml)
        write_xml(config, "C:/users/amallory/Desktop/test.xml")


def merge_children(config, xml):
    """Config refers to what we are merging into, XML is what we are trying to merge"""
    print(f"*** MERGING Children  {config.tag} {xml.tag}***")

    # Iterate over children in new XML
    for xml_child in xml.getchildren():
        # print(f"Checking {xml_child.tag} against {config.tag}")

        # Check if a child entry has an identical element already in config
        config_node = config.xpath(xml_child.tag)
        if len(config_node):

            # Since these overlap, check if they are list items that have "entry" tags
            xml_entries = [x for x in xml_child.getchildren() if x.tag == "entry"]
            if len(xml_entries):

                # Since we found entries, we should copy just the entries to the config XML
                # print(f"   Found entries!! {[x.tag for x in xml_entries]}")
                for x in xml_entries:
                    config_node[0].append(x)
                    print(f"Copied entry {x.xpath('@name')[0]} into {config_node[0].tag}")
                    # print(pretty_print_xml(x))
            else:
                # Without an entry tag, we should traverse deeper if there is still an entry tag
                if len(xml_child.xpath("//entry")) or len(config_node[0].xpath("//entry")):
                    # print(f"   recursing on {config_node[0].tag} and {xml_child.tag}")
                    merge_children(config_node[0], xml_child)

                else:
                    # Without a deeper entry tag, we can simply replace
                    config.remove(config_node[0])
                    config.append(xml_child)
                    print(f"   Replace node {config_node[0].tag} with {xml_child.tag} due to no entries")
        else:
            # Did not find an overlapping config node, add new node to parent
            config.append(xml_child)
            print(f"   Added node {xml_child.tag} due to missing config node {config.tag}")
