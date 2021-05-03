from .base import BaseCommand
from sli.decorators import require_ngfw_connection_params, require_panoply_connection

def print_usage():
    print("""
Diff module requires 0, 1, or 2 arguments.

    - 0 arguments: Diff candidate config from running config
    - 1 argument: Diff previous config or named config against specified running config
    - 2 arguments: Diff first arg named config against second arg named config

    A named config can be either a stored config, candidate, running or a number.
    Positive numbers must be used to specify iterations, 1 means 1 config revision ago
    """)


class DiffCommand(BaseCommand):

    sli_command = 'diff'
    short_desc = 'Diff a candidate config from the running-config'
    no_skillet = True

    @require_ngfw_connection_params
    @require_panoply_connection
    def run(self, pan):
        """Get a diff of running and candidate configs"""

        if 'help' in self.args:
            print_usage()
            return

        # Any digit arguments should be converted to negative
        fixup = lambda x: f'-{x}' if x.isdigit() else x

        # If no arguments suppliied, assume diff candidate from running
        if len(self.args) < 1:
            latest_name = 'candidate'
            source_name = 'running'
        if len(self.args) == 1:
            latest_name = 'candidate'
            source_name = fixup(self.args[0])
        if len(self.args) == 2:
            source_name = fixup(self.args[0])
            latest_name = fixup(self.args[1])
        elif len(self.args) > 2:
            print_usage()
            return

        previous_config = pan.get_configuration(config_source=source_name)
        latest_config = pan.get_configuration(config_source=latest_name)
        if self.sli.output_format == 'xml':
            diff = pan.generate_skillet_from_configs(previous_config, latest_config)   
            for obj in diff:
                for key in obj:
                    print(f'\n{key}:\n{obj[key]}')
        else:
            output = pan.generate_set_cli_from_configs(previous_config, latest_config)
            for line in output:
                print(line)