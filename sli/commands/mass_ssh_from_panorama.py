from .mass_ssh import MassSSH

from ..decorators import require_ngfw_connection_params
from ..decorators import require_panoply_connection
from skilletlib.panoply import Panoply

import json
import os


class MassSSHPanorama(MassSSH):
    sli_command = "mass_ssh_from_panorama"
    short_desc = "Run a command script against multiple Panorama-connected firewalls async"
    no_skillet = True
    help_text = """
        Queries a Panorama device for a list of firewalls, optionally filtered based on device facts,
        and executes a script of CLI commands against the firewalls asynchronously.

        The -d, -u, and -p flags are used to connect to the desired Panorama device.

        The var script.txt must reference a file that contains the CLI commands to run.
        The input script is not limited to supporting just configuration commands, show commands can be used for
        data gathering on a list of devices simultaneously.
        Sample structuring of a script.txt configuring a new zone
        ---

        configure
        set zone new_zone
        commit

        ---

        The -o option refers to a directory to create and populate with output logs from all
        devices configured. The contents of the directory will be overwritten if it already exists.

        The optional var device_filter.json must reference a file that contains a dictionary of
        key value pairs. These keys match keys from the returned device facts, captured using the Panorama
        command `show devices connected`. Only devices that match ALL of the filter terms will be returned.

        Sample structuring of a device_filter.json
        ---
        {
            "hostname": "testing-panos",
            "sw-version": "10.0.4",
            "model": "PA-VM"
        }
        ---

        Usage:
            sli mass_ssh_from_panorama -d panorama_device -u username -p password -o output_dir script.txt [device_filter.json]
    """

    def load_config_from_panorama(self, out_directory, pan):
        """
        Load list of devices and credentials from specified Panorama device using
        dict-formatted filters
        """
        # Read in filter dict from file
        if len(self.args) == 2:
            with open(self.args[1], 'r') as f:
                raw_filter_data = f.read()
            filter_dict = json.loads(raw_filter_data)
        else:
            filter_dict = {}

        # Save list of devices that match ALL filter terms
        devices = pan.filter_connected_devices(filter_dict)

        # Get default credentials of all NGFWs
        username, password = self.get_credentials()

        return [{
                    "device": x['ip-address'],
                    "username": username,
                    "password": password,
                    "out_file": f"{os.path.join(out_directory,x)}.txt" if out_directory else None,
                    "coroutine": None,
                    "status": False,
                    "output": None,
                    "error": "",
                } for x in devices]

    def load_device_configs(self, out_directory, pan=None):
        """
        Loads device configuration using Panorama's connected devices
        """
        return self.load_config_from_panorama(out_directory, pan)

    @require_ngfw_connection_params
    @require_panoply_connection
    def run(self, pan: Panoply):

        # Handle invalid input arguments
        print(len(self.args))
        if len(self.args) < 1 or len(self.args) > 2:
            print(self.help_text)
            return

        # Read in script file
        with open(self.args[0], "r") as f:
            script = f.read()

        # Create output directory if doesn't exist
        out_directory = self.sli.options.get("out_file", None)
        if out_directory:
            if not os.path.exists(out_directory):
                os.mkdir(out_directory)

        # Load devices configuration from YAML or CLI input
        devices = self.load_device_configs(out_directory, pan)

        # Execute mass SSH
        self.execute_mass_ssh(script, out_directory, devices)
