from .base import BaseCommand
from sli.errors import InvalidArgumentsException
import re
import os
import shutil


class ShowSkillet(BaseCommand):
    sli_command = "update_skillet_vars"
    short_desc = "Finds and updates all template variables in a Skillet"
    no_skillet = True
    no_context = True
    help_text = """

    This command is useful when building or modifying an existing skillet. You can edit the
    XML elements or other templated attributes with Jinja {{ variables }} then run this command
    to update the list of variables with your new additions.

    Usage:
        sli update_skillet_vars yourfile.skillet.yaml
    """

    def run(self):

        if not len(self.args) == 1:
            raise InvalidArgumentsException("Must specify single argument of file to update")
        file_name = self.args[0]
        file_bkp = file_name + ".bkp"
        file_buffer = []  # Store the file as a list of lines in this buffer to replay later

        # Load the file and find the insertion point of new variables
        with open(file_name, "r") as f:
            i = 1
            variables_start = None
            variables_end = None
            in_var_section = False
            indent_dash = 2
            indent_text = 4
            for line in f:

                file_buffer += line

                # Locate the beginning of the variables section
                if line.strip() == "variables:":
                    variables_start = i
                    in_var_section = True
                    print(f"Variables start on line {i}")

                # Locate the end of the variables section
                elif variables_start and line.strip() == "snippets:":
                    variables_end = i
                    in_var_section = False

                # Find first line of existing variable block and infer spacing
                elif in_var_section:
                    if re.search(".*-.*name:", line):
                        indent_dash = line.index("-")
                        indent_text = line.index("n")

                i += 1

            print(variables_start)
            print(variables_end)
            print(indent_dash)
            print(indent_text)

        # Backup the file just in case
        if os.path.exists(file_bkp):
            os.remove(file_bkp)
        shutil.copy(file_name, file_bkp)

        # Overwrite the user submitted file
        # Delete the backup file
