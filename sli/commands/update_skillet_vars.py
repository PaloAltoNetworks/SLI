from skilletlib import Skillet

from .base import BaseCommand
from ..decorators import require_single_skillet


class ShowSkillet(BaseCommand):
    sli_command = "update_skillet_vars"
    short_desc = "Finds and updates all template variables in a Skillet"
    no_skillet = False
    no_context = True
    help_text = """

    This command is useful when building or modifying an existing skillet. You can edit the
    XML elements or other templated attributes with Jinja {{ variables }} then run this command
    to update the list of variables with your new additions.

    Usage:
        sli update_skillet_vars --name k12_config_skillet -sd /tmp/skillets
    """

    @require_single_skillet
    def run(self):
        skillet: Skillet = self.sli.skillet
        found_variables: list = skillet.get_declared_variables()

        new_variables = list()

        for v in found_variables:
            if v not in [x["name"] for x in skillet.variables]:
                print(f"Found new variable {v}")

                new_variable = {"name": v, "description": v, "default": "", "type_hint": "text"}

                skillet.variables.append(new_variable)
                new_variables.append(v)

        # FIXME - this does not account for skillets with includes, this will show the compiled skillet and not
        # the skillet_dict as it probably should ...
        print("=" * 80)
        print(self.sli.skillet.dump_yaml())
        print("=" * 80)
        print("New variables found:")
        for v in new_variables:
            print(v)
        print("=" * 80)
