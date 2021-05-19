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
        write_xml(config, "C:/users/amall/Desktop/config.xml")
        snippets = self.sli.skillet.get_snippets()
        for snippet in snippets:
            # if not snippet.name == "device_setting":
            #     continue
            if not snippet.should_execute(self.sli.context):
                continue

            xpath = snippet.metadata.get('xpath')
            meta = snippet.render_metadata(self.sli.context)
            element = meta.get('element')
            child_tag = xpath.split('/')[-1:][0]
            child_xml = etree.fromstring(f"<{child_tag}>{element}</{child_tag}>")
            found = config.xpath(xpath)

            # If an equivelant xpath was found, merge the children
            if len(found) == 1:
                found = found[0]
                merge_children(found, child_xml)

            # If no node was found, generate missing XML elements from xpath
            elif len(found) == 0:
                # breakpoint()
                parent_xpath = "/".join(xpath.split("/")[:-1])
                print(f"   Parent XPATH - {parent_xpath}")
                parent_node = config.xpath(parent_xpath)
                if not len(parent_node):
                    raise Exception(f"Unable to find parent node for {xpath}")

            else:
                raise Exception("Skillet xpath returned multiple results on device, cannot merge.")

        write_xml(config, "C:/users/amall/Desktop/test.xml")


def merge_children(config, xml):
    print(f"*** MERGING Children  {config.tag} {xml.tag}***")

    # All nodes from new XML document
    for xml_child in xml.getchildren():

        # Check if child node has a matching config node
        config_node = config.xpath(xml_child.tag)
        if len(config_node):
            config_node = config_node[0]

            # Node has entry children somewhere
            if xml_child.xpath(".//entry[@name]"):

                # Node has entry immediate children
                if len(xml_child.xpath("./entry[@name]")):
                    for entry_child in xml_child.getchildren():
                        config_node.append(entry_child)
                        print(f"   Appended child {entry_child.tag} {entry_child.get('name')} to {config_node.tag}")

                # Node has entry children, but not immediately
                else:
                    print(f" Recursing over {xml_child.tag}")
                    merge_children(config_node, xml_child)

            # This node has no entry children
            else:
                config.remove(config_node)
                config_node.append(xml_child)
                print(f"   Replaced node {xml_child.tag} as no entry children were found")

        # Child node does not have a matching config node
        else:
            config.append(xml_child)
            print(f"   Added node {xml_child.tag} due to missing config node")
