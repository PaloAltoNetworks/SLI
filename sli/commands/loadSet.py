from .base import BaseCommand
from sli.decorators import require_ngfw_connection_params, require_ngfw_ssh_session


class LoadSet(BaseCommand):
    sli_command = "load_set"
    short_desc = "Load set commands in a file against a live NGFW to ensure no errors"
    no_skillet = True
    help_text = """
        Load set commands into an NGFW from a specified file.
        fails out on any set command errors

        Example Usage:
            sli load_set -uc set_commands.txt
"""

    @require_ngfw_connection_params
    @require_ngfw_ssh_session
    def run(self, ssh):

        # Load script as a list of lines off of disk
        if not len(self.args) == 1:
            print(self.help_text)
            exit()
        script_name = self.args[0]
        with open(script_name, 'r') as f:
            script = [x.strip() for x in f.read().split('\n')]

        # Filter out set non executable lines and verify contents
        commands = [x for x in script if not x.startswith('#') and len(x)]
        invalid_commands = [x for x in commands if not x.startswith("set ")]
        if len(invalid_commands):
            print("Following commands are not set commands: ")
            for command in invalid_commands:
                print(f"  - {command}")

        # Execute line by line until end of script
        print("Starting set command load...")
        ssh.config_mode()
        for command in commands:
            if not ssh.set_command(command):
                print(ssh.get_error_text())
                print("Errors occurred while loading set commands.")
                return

        print('Set commands successfully loaded')
