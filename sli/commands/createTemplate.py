from .base import BaseCommand
from sli.decorators import require_single_skillet, require_skillet_type
from sli.tools import format_xml_string

from lxml import etree
import re
from io import BytesIO


class CreateTemplate(BaseCommand):
    sli_command = 'create_template'
    short_desc = 'Create an XML template from a panos or panorama skillet'
    no_context = True
    help_text = """

    Usage:
        sli create_template -n [skillet] [baseline-file] [out-file]

"""

    @staticmethod
    def insert_template_str(line, config):
        """
        Break up an xml config (str) at a specified line to inject template_string.
        """
        i = 1
        r = ""
        for cl in [x for x in config.split("\n") if len(x)]:
            if line["line"] == i:

                leading_spaces = len(cl) - len(cl.lstrip())
                closing_tag = None

                # If tag without children, expand to tag with children and insert template
                if re.search(r'<[a-zA-Z0-9-]+/>', cl):
                    ll = cl.replace("/", "")
                    r += ll + "\n"
                    closing_tag = ll.replace("<", "</") + "\n"

                # If not a tag at all, there's already a template here, just insert
                elif not cl.strip().startswith("<"):
                    pass

                # If just an opening tag is present, insert after
                else:
                    r += cl + "\n"

                for tl in line["template"].split("\n"):
                    r += " " * leading_spaces + tl + "\n"
                if closing_tag is not None:
                    r += closing_tag

            else:
                r += cl + "\n"
            i += 1
        return r

    @staticmethod
    def find_closest_entry(xml, xpath):
        """
        find the shortest xpath that returns a valid element, and determine what
        nodes are missing from the full expath. Returns a tuple containing the
        shortened xpath that matches a node, and a list of the missing nodes
        """
        xs = [x for x in xpath.split("/") if len(x)]
        for i in range(len(xs)):
            xpath_short = "/" + "/".join(xs[:-1 * (i + 1)])
            if len(xpath_short) < 1:
                raise Exception(f"Could not find valid entry point for {xpath}")
            found = xml.xpath(xpath_short)
            if len(found) == 0:
                continue
            else:
                missing = [x for x in xpath.replace(xpath_short, "").split("/") if len(x)]
                break
        return xpath_short, missing

    @staticmethod
    def strip_var_spaces(in_str) -> str:
        """Remove spaces around variables inside of a block of text"""
        return in_str.replace("{{ ", "{{").replace(" }}", "}}")

    @require_single_skillet
    @require_skillet_type("panos", "panorama")
    def run(self):
        if not len(self.args) == 2:
            print(self.help_text)
            return

        out_file = self.args[1]
        baseline_file = self.args[0]
        with open(baseline_file, "r") as f:
            config = f.read()
            f.seek(0)
            parser = etree.XMLParser(remove_blank_text=True)
            baseline_xml = etree.parse(f, parser)

        snippets = self.sli.skillet.get_snippets()

        # Verify required parameters present in snippets
        for snippet in snippets:
            if getattr(snippet, "template_str", None) is None:
                print(f"Snippet {snippet.name} has no template_str")
                return
            if "xpath" not in snippet.metadata:
                print(f"Snippet {snippet.name} has no xpath")
                return

        # Expand any missing XML nodes
        for snippet in snippets:
            snippet_xpath = self.strip_var_spaces(snippet.metadata["xpath"])
            if len(baseline_xml.xpath(snippet_xpath)):
                continue
            short_xpath, missing = self.find_closest_entry(baseline_xml, snippet_xpath)
            ele = baseline_xml.xpath(short_xpath)[0]
            for missing_ele in missing:
                attr = None
                new_ele_tag = missing_ele
                if "[" in missing_ele:
                    es = missing_ele.split("[")
                    new_ele_tag = es[0]
                    attr = es[1].strip()
                    for c in "[]@'\" ":
                        attr = attr.replace(c, "")
                    attr = attr.split("=")
                new_ele = etree.Element(new_ele_tag)
                if attr is not None:
                    new_ele.set(*attr)
                ele.append(new_ele)
                ele = new_ele

        # Rewrite config var and reload xml document to ensure accurate line numbers
        temp_file = BytesIO()
        baseline_xml.write(temp_file, pretty_print=True)
        temp_file.seek(0)
        config = format_xml_string(temp_file.read().decode())
        baseline_xml = etree.fromstring(config)

        # Find the various insert points on all snippets
        lines = []
        for snippet in snippets:

            xpath = snippet.metadata["xpath"]
            found = baseline_xml.xpath(self.strip_var_spaces(xpath))

            if len(found) > 1:
                raise Exception(f"xpath {xpath} returned more than 1 result in baseline")
            elif not len(found):
                raise Exception(f" Unable to find entry point for {xpath}")

            # Insert point found
            else:
                lines.append({
                    "template": self.strip_var_spaces(snippet.template_str),
                    "line": found[0].sourceline
                })

        # Sort the keys so we're starting from the point furthest down the file
        lines = sorted(lines, key=lambda i: i["line"], reverse=True)

        # Insert snippets one at a time until complete
        for line in lines:
            config = self.insert_template_str(line, config)

        with open(out_file, "w") as f:
            f.write(config)
