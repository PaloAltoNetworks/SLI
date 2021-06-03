from .base import BaseCommand
from sli.decorators import require_ngfw_connection_params, require_panoply_connection

from jinja2 import Template
from sli.tools import format_xml_string


class DiffCommand(BaseCommand):
    sli_command = "diff"
    short_desc = "Get the differences between two config versions, candidate, running, previous running, etc"
    no_skillet = True
    help_text = """
        Diff module requires 0 to 3 arguments.

        - 0 arguments: Diff running config from previous running config
        - 1 argument: Diff previous config or named config against specified running config
        - 2 arguments: Diff first arg named config against second arg named config
        - 3 arguments: Diff first arg named config against second arg named config and save diffs into the context

        A named config can be either a stored config, candidate, running or a number.
        Positive numbers must be used to specify iterations, 1 means 1 config revision ago

        Example: Get diff between running config and previous running config in set cli format

            user$ sli diff 1 -uc -of set

        Example: Get diff between running config and the candidate config in xml format

            user$ sli diff running candidate -uc -of xml

        Example: Get diff between running config and the candidate config in skillet format

            user$ sli diff running candidate -uc -of skillet

        Example: Get the diff of all changes made to this device using the autogenerated 'baseline' config, which is
        essentially blank.

            user$ sli diff baseline -uc -of xml

        Example: Get the diff between the second and third most recent running configs

            user$ sli diff 3 2

        Example: Get a diff and save as 'candidate_diff' into the context

            user$ sli diff running candidate candidate_diff -uc
    """

    @require_ngfw_connection_params
    @require_panoply_connection
    def run(self, pan):
        """Get a diff of running and candidate configs"""

        # Any digit arguments should be converted to negative
        def fixup(x):
            return f"-{x}" if x.isdigit() else x

        capture_var = None

        if len(self.args) == 1:
            latest_name = "running"
            source_name = fixup(self.args[0])
        elif len(self.args) == 2:
            source_name = fixup(self.args[0])
            latest_name = fixup(self.args[1])
        elif len(self.args) == 3:
            source_name = fixup(self.args[0])
            latest_name = fixup(self.args[1])
            capture_var = self.args[2]
        elif len(self.args) > 3:
            self._print_usage()
            return
        else:
            # If no arguments supplied, assume diff previous running vs running
            latest_name = "running"
            source_name = "-1"

        previous_config = pan.get_configuration(config_source=source_name)
        latest_config = pan.get_configuration(config_source=latest_name)

        output = ""
        out_file = self.sli.options.get("out_file")

        if self.sli.output_format == "xml":
            diff = pan.generate_skillet_from_configs(previous_config, latest_config)
            for obj in diff:
                output += f'name: {obj["name"]}\n'
                output += f'xpath: {obj["xpath"]}\n'
                output += f'element: {obj["element"]}\n\n'
            print(output)

        elif self.sli.output_format == "set":
            diff = pan.generate_set_cli_from_configs(previous_config, latest_config)
            output = "\n".join(diff)
            print(output)

        else:
            # Skillet format
            diff = pan.generate_skillet_from_configs(previous_config, latest_config)
            template = Template(skillet_template)
            generated_snippets = [{
                    "xml": format_xml_string(x["element"], indent=6),
                    "xpath": x["full_xpath"]
                } for x in diff]
            output = template.render({"snippets": generated_snippets})
            print(output)

            # Update context if using context
            if self.sli.cm.use_context and capture_var is not None:
                self.sli.context[capture_var] = diff
                print(f"Output added to context as {capture_var}")

        if output and out_file:
            with open(out_file, "w") as f:
                f.write(output)


skillet_template = """name: skillet_name
label: skillet_label
description: skillet_description

type: panos

variables:

snippets:
{% for s in snippets %}
  - name: snippet_{{ loop.index }}
    xpath: {{ s.xpath }}
    element: |-
{{ s.xml }}{% endfor %}
"""
