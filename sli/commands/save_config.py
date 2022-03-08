from .base import BaseCommand
from sli.decorators import require_ngfw_connection_params, require_panoply_connection
from sli.tools import load_config_file


class ConfigureCommand(BaseCommand):
    sli_command = "save_config"
    short_desc = "Save a configuration file from a device to your local system"
    no_skillet = True
    help_text = """
    Save a configuration file off a device locally. config_on_device may be
    running, candidate, or any config file saved on a device. Specify -o config.xml
    to save off as config.xml, or the configuration will just be printed to the screen

    Usage:

        sli save_config config_on_device -o config.xml
"""

    @require_ngfw_connection_params
    @require_panoply_connection
    def run(self, pan):

        if len(self.args) != 1:
            print(self.help_text)
            return

        source_name = self.args[0]
        config = load_config_file(source_name, pan=pan)
        out_file = self.sli.options.get("out_file")
        if out_file:
            with open(out_file, "w") as f:
                f.write(config)
            print(f"Configuration file saved to {out_file}")
        else:
            print(config)
