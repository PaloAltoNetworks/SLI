from pathlib import Path

from skilletlib import Skillet
from skilletlib import SkilletLoader

from sli.decorators import require_ngfw_connection_params
from sli.decorators import require_panoply_connection
from .base import BaseCommand
from sli.errors import AppSkilletNotFoundException
from sli.errors import InvalidArgumentsException
from sli.errors import SLIException


class DiffCommand(BaseCommand):
    sli_command = "diff"
    short_desc = "Get the differences between two config versions, candidate, running, previous running, etc"
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
    """

    @staticmethod
    def _load_app_skillet(skillet_name):
        """
        Returns a SLI specific application skillet found in the app_skillets folder
        """
        sli_path = Path(__file__).parent.joinpath("../app_skillets").resolve()
        inline_sl = SkilletLoader(sli_path)
        app_skillet: Skillet = inline_sl.get_skillet_with_name(skillet_name)

        if not app_skillet:
            raise AppSkilletNotFoundException("Could not find required resources")

        return app_skillet

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

    @staticmethod
    def _get_input(var_label: str, var_default: str) -> str:
        """
        utility method to get input from the user and return the default value if nothing is entered from the user

        :param var_label: Label to show to the user
        :param var_default: default to use if nothing is entered
        :return: value entered from the user or default is input is None or ""
        """
        val = input(f"{var_label} <{var_default}>: ")
        if val is None or val == "":
            val = var_default

        return val

    def _handle_snippets(self, snippets: list, vars: list) -> None:
        output = ""

        if self.sli.output_format == "xml":
            for obj in snippets:
                output += f'name: {obj["name"]}\n'
                output += f'xpath: {obj["xpath"]}\n'
                output += f'element: {obj["element"]}\n\n'

        elif self.sli.output_format == "set":
            output = "\n".join(snippets)

        else:
            panos_skeleton = self._load_app_skillet("panos_skillet_skeleton")

            skillet_name = self._get_input("Skillet Name:", "my skillet")
            skillet_output = panos_skeleton.execute({"snippets": snippets, "skillet_name": skillet_name})

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

        source_name = self.source_name
        latest_name = self.latest_name

        device_configs = ["running", "candidate", "baseline"]  # Can be pulled off of device by name not file

        if source_name in device_configs or source_name.replace("-", "").isdigit():
            previous_config = self.pan.get_configuration(config_source=source_name)
        else:
            previous_config = self.pan.get_saved_configuration(source_name)

        if latest_name in device_configs or source_name.replace("-", "").isdigit():
            latest_config = self.pan.get_configuration(config_source=latest_name)
        else:
            latest_config = self.pan.get_saved_configuration(latest_name)
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

        try:
            diff = self._get_snippets()
            vars_list = self._get_vars()
            self._update_context(diff)
            self._handle_snippets(diff, vars_list)

        except SLIException as sle:
            print(sle)
            exit(1)
