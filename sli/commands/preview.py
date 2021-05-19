from sli.decorators import load_variables
from sli.decorators import require_single_skillet
from sli.decorators import require_skillet_type
from sli.decorators import require_ngfw_connection_params
from sli.decorators import require_panoply_connection
from .base import BaseCommand
from sli.tools import pretty_print_xml, merge_children

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
            found = config.xpath(xpath)

            # If an equivelant xpath was found, merge the children
            if len(found) == 1:
                found = found[0]
                merge_children(found, child_xml)

            # If no node was found, generate missing XML elements from xpath
            elif len(found) == 0:
                i = 1

                # Find the first level of matching elements
                xpath_elements = xpath.split("/")
                common_xpath = ""
                cursor_element = None
                while i < len(xpath_elements) - 1:
                    common_xpath = "/".join(xpath_elements[:-1 * i])
                    cursor_element = config.xpath(common_xpath)
                    if len(cursor_element) == 1:
                        cursor_element = cursor_element[0]
                        break
                    elif len(cursor_element) > 1:
                        raise Exception(f"First level of matching xml in xpath {xpath} produced {len(cursor_element)} nodes at {common_xpath}")
                    i += 1

                # Create the missing gap of XML elements and place new elements inside
                missing_elements = [x for x in xpath.replace(common_xpath, "").split("/") if x]
                for element in missing_elements:
                    new_element = etree.Element(element)
                    cursor_element.append(new_element)
                    cursor_element = new_element
                for child in child_xml.getchildren():
                    cursor_element.append(child)

            else:
                raise Exception("Skillet xpath returned multiple results on device, cannot merge.")

        write_xml(config, "C:/users/amall/Desktop/test.xml")
