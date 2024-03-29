from sli.decorators import require_ngfw_connection_params
from sli.decorators import require_panoply_connection
from .base import BaseCommand
from sli.errors import InvalidArgumentsException
from sli.errors import SLIException
from sli.tools import load_config_file, format_xml_string, get_input, load_app_skillet


class DiffCommand(BaseCommand):
    sli_command = "diff"
    short_desc = "Get the differences between two config versions: candidate, running, previous running, etc"
    no_skillet = True
    capture_var = None
    pan = None
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

        Example: Get a diff from running and a local config file, save as out.xml. Note the 'file:' prefix.

            user$ sli diff running file:test-file.xml candidate_diff -uc -o out.xml

        Example: Get a diff between two local saved configs and same as diff.out. Note the '--offline' flag.

            user$ sli diff running test-file.xml test-file-2.xml --offline -o diff.out
    """

    def _parse_args(self) -> None:
        """
        handle arguments for this Command.
        """

        def fixup(x):
            return f"-{x}" if x.isdigit() else x

        if len(self.args) == 1:
            latest_name = "running"
            source_name = fixup(self.args[0])

        elif len(self.args) == 2:
            source_name = fixup(self.args[0])
            latest_name = fixup(self.args[1])

        elif len(self.args) == 3:
            source_name = fixup(self.args[0])
            latest_name = fixup(self.args[1])
            self.capture_var = self.args[2]

        elif len(self.args) > 3:

            raise InvalidArgumentsException("Too many arguments")

        else:
            # If no arguments supplied, assume diff previous running vs running
            latest_name = "running"
            source_name = "-1"

        self.source_name = source_name
        self.latest_name = latest_name

    def _handle_snippets(self, snippets: list, vars: list) -> None:
        output = ""

        if self.sli.output_format == "xml":
            for obj in snippets:
                element = format_xml_string(obj["element"], indent=2)
                output += f'name: {obj["name"]}\n'
                output += f'xpath: {obj["xpath"]}\n'
                output += f"element: |-\n{element}\n\n"

        elif self.sli.output_format == "set":
            output = "\n".join(snippets)

        else:

            for snippet in snippets:
                snippet["element"] = format_xml_string(snippet["element"], indent=6)

            panos_skeleton = load_app_skillet("panos_skillet_skeleton")

            skillet_name = get_input("Skillet Name:", "my_skillet")
            skillet_label = get_input("Skillet Label:", "my label")
            skillet_description = get_input("Skillet Description:", "my description")
            skillet_output = panos_skeleton.execute(
                {
                    "snippets": snippets,
                    "skillet_name": skillet_name,
                    "skillet_label": skillet_label,
                    "skillet_description": skillet_description,
                }
            )

            if not panos_skeleton.success:
                raise SLIException("Could not generate Skillet output")

            output = skillet_output["template"]

        self._handle_outfile(output)
        print(output)

    def _get_vars(self) -> list:
        return []

    def _get_snippets(self) -> list:
        """
        Internal method to actually perform the diff operation.
        """

        previous_config = load_config_file(self.source_name, self.pan)
        latest_config = load_config_file(self.latest_name, self.pan)
        if self.sli.output_format == "set":
            snippets = self.pan.generate_set_cli_from_configs(previous_config, latest_config)
        else:
            snippets = self.pan.generate_skillet_from_configs(previous_config, latest_config)

        return snippets

    def _handle_outfile(self, output: str) -> None:

        out_file = self.sli.options.get("out_file")
        if output and out_file:
            with open(out_file, "w") as f:
                f.write(output)

    def _update_context(self, diff: list) -> None:

        # Update context if using context
        if self.sli.cm.use_context and self.capture_var is not None:
            self.sli.context[self.capture_var] = diff
            print(f"Output added to context as {self.capture_var}")

    @require_ngfw_connection_params
    @require_panoply_connection
    def run(self, pan):
        """Get a diff of running and candidate configs"""

        self.pan = pan

        try:
            self._parse_args()

        except InvalidArgumentsException:
            self._print_usage()
            return

        diff = self._get_snippets()
        vars_list = self._get_vars()
        self._update_context(diff)
        self._handle_snippets(diff, vars_list)
