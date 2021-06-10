from .base import BaseCommand

from ..decorators import require_single_skillet


class ShowSkillet(BaseCommand):
    sli_command = "show_skillet"
    short_desc = "Shows the contents of a Compiled Skillet in YAML format"
    no_skillet = False
    no_context = True
    help_text = """

    Usage:
        sli show_skillet --name k12_config_skillet -sd /tmp/skillets
    """

    @require_single_skillet
    def run(self):
        print(self.sli.skillet.dump_yaml())
