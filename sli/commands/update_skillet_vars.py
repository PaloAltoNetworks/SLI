from .base import BaseCommand
from sli.errors import InvalidArgumentsException
import re
import os
import shutil
from skilletlib import SkilletLoader


class UpdateSkilletVars(BaseCommand):
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

        # Load skillet, extract variables and determine missing
        sl = SkilletLoader()
        skillet = sl.load_skillet(file_name)
        vars_specified = [x['name'] for x in skillet.variables]
        missing_vars = [x for x in skillet.get_declared_variables() if x not in vars_specified]
        if len(missing_vars) < 1:
            print("Did not find any variables in snippets that were not declared")
            return

        # Load the file and find the insertion point of new variables
        with open(file_name, "r") as f:
            i = 1
            variables_start = None
            variables_end = None
            in_var_section = False
            indent_dash = 2
            indent_text = 4
            for line in f.readlines():

                file_buffer.append(line)

                # Locate the beginning of the variables section
                if line.strip() == "variables:":
                    variables_start = i
                    in_var_section = True

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

        # Backup the file in case of issue
        if os.path.exists(file_bkp):
            os.remove(file_bkp)
        shutil.copy(file_name, file_bkp)

        # Overwrite the user submitted file
        with open(file_name, "w") as f:
            i = 1
            for line in file_buffer:

                # End of variables section, append missing_vars here
                if i == variables_end:
                    for mv in missing_vars:
                        f.write(f"{' ' * indent_dash}- name: {mv}\n")
                        f.write(f"{' ' * indent_text}description: {mv}\n")
                        f.write(f"{' ' * indent_text}default: \n")
                        f.write(f"{' ' * indent_text}type_hint: text\n\n")

                f.write(line)
                i += 1

        # Delete the backup file
        os.remove(file_bkp)
