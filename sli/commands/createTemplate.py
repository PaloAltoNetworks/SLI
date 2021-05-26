from .base import BaseCommand
from sli.decorators import require_single_skillet, require_skillet_type

from lxml import etree
import re


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

                # If tag without children, expand to tag with children and insert template
                if re.search(r'<[a-zA-Z0-9]+/>', cl):
                    ll = cl.replace("/", "")
                    r += ll + "\n"
                    for tl in line["template"].split("\n"):
                        r += " " * leading_spaces + tl + "\n"
                    r += ll.replace("<", "</") + "\n"

                # If not a tag at all, there's already a template here, just insert

                # If just an opening tag is present, insert after

            r += cl + "\n"
            i += 1
        return r

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
            baseline_xml = etree.fromstring(config)

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
        lines = []
        for snippet in snippets:
            xpath = snippet.metadata["xpath"]
            found = baseline_xml.xpath(xpath)
            if len(found) > 1:
                print(f"xpath {xpath} returned more than 1 result in baseline")
                return

            # Xpath references a valid entry point
            if len(found):
                lines.append({"template": snippet.template_str, "line": found[0].sourceline})

            # Need to shorten the xpath to find the best entry point
            else:
                xs = [x for x in xpath.split("/") if len(x)]
                for i in range(len(xs)):
                    xpath_short = "/" + "/".join(xs[:-1 * (i + 1)])
                    if not len(xpath_short):
                        print(f"Could not find valid entry point for {xpath}")
                        return
                    found = baseline_xml.xpath(xpath_short)
                    if len(found) > 1:
                        print(f"xpath {xpath} returned more than 1 result in baseline")
                        return
                    elif len(found) == 1:
                        missing = [x for x in xpath.replace(xpath_short, "").split("/") if len(x)]
                        lines.append({"template": snippet.template_str, "line": found[0].sourceline, "missing": missing})
                        break

        # Sort the keys so we're starting from the point furthest down the file
        lines = sorted(lines, key=lambda i: i["line"], reverse=True)

        # Insert snippets one at a time until complete
        for line in lines:
            config = self.insert_template_str(line, config)

        with open(out_file, "w") as f:
            f.write(config)
