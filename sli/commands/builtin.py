from .base import BaseCommand
from sli.tools import load_builtin_skillets, print_table, load_app_skillet


class Builtin(BaseCommand):
    sli_command = "builtin"
    short_desc = 'Run builtin skillets, use "sli builtin show" to see available skillets'
    no_skillet = True
    help_text = """

        Execute a skillet built-in to sli.

        Show available skillets with "sli builtin show"

        Example - run a panos type skillet called device_cert:

            sli builtin device_cert -uc otp=ABC123
            # Executes skillet "activate" using context and passing ABC123 to the variable otp
            # If you do not specify the variable, creds, or a context, you will be prompted

    """

    def run(self):

        if not len(self.args) == 1:
            print('Must specify a builtin skillet to run, specify "show" to see all available skillets')
            return

        skillet_name = self.args[0]

        # Show list of all builtin skillets
        if skillet_name == "show":
            skillets = load_builtin_skillets()
            builtins = [{
                "name": x.name.replace("builtin_", ""),
                "desc": x.description,
                "type": x.type
            } for x in skillets]
            print("\nAvailble skillets\n")
            print_table(builtins, {
                "Name": "name",
                "Type": "type",
                "Description": "desc",
                })
            print()
            return

        real_name = "builtin_" + skillet_name
        skillet = load_app_skillet(real_name)

        if skillet.type == "panos":
            # Execute SLI configure command
            self.sli.action = "configure"
            self.sli.skillets = [skillet]
            self.sli.options["name"] = real_name
            self.sli.execute()

        else:
            print(f"Skillet type of {skillet.type} currently not supported as a builtin")
