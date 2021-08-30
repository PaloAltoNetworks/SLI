from .base import BaseCommand
from sli.decorators import require_ngfw_connection_params, require_ngfw_ssh_session
from sli.progressBar import ProgressBar
from sli.tools import get_password_input

import re


class LoadSet(BaseCommand):
    sli_command = "load_set"
    short_desc = "Load set commands in a file against a live NGFW to ensure no errors"
    no_skillet = True
    help_text = """
        Load set commands into an NGFW from a specified file.
        fails out on any set command errors

        Example usage with progress bar and timer:
            sli load_set -uc set_commands.txt

        Example usage printing out commands as they are processed:
            sli load_set -uc set_commands.txt -v
"""

    @require_ngfw_connection_params
    @require_ngfw_ssh_session
    def run(self, ssh):

        # Load script as a list of lines off of disk
        if not len(self.args) == 1:
            print(self.help_text)
            return
        script_name = self.args[0]
        with open(script_name, 'r') as f:
            script = [x.strip() for x in f.read().split('\n')]

        # Filter out set non executable lines and verify contents
        commands = [x for x in script if not x.startswith('#') and len(x)]
        invalid_commands = [x for x in commands if not x.startswith("set ") and not x.startswith("delete ")]
        if len(invalid_commands):
            print("Following commands are not set commands: ")
            for command in invalid_commands:
                print(f"  - {command}")

        # Execute line by line until end of script
        print("Starting set command load...")
        total = len(commands)
        ssh.config_mode()
        i = 0
        if not self.sli.verbose:
            pb = ProgressBar(prefix="Applying commands")
        for command in commands:

            # Check if a password will be required as the next input
            if re.match("^set mgt-config users.*password$", command.strip()):
                username = command.strip().split(" ")[3]
                if not self.sli.verbose:
                    pb.pause()
                password = get_password_input(f"Password for user {username}")
                ssh.extended_set_command(command, expect="Enter password")
                ssh.extended_set_command(password, expect="Confirm password")
                ssh.extended_set_command(password)
                continue

            # Process normal command
            if not ssh.set_command(command):
                print('\n' + ssh.get_error_text())
                print("Errors occurred while loading set commands.")
                return
            i += 1
            percent = "{0:.1f}".format(100 * (i / total))
            if self.sli.verbose:
                print(command)
            else:
                pb.update(percent)

        if not self.sli.verbose:
            pb.complete()

        print('Set commands successfully loaded')
