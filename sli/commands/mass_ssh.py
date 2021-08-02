from .base import BaseCommand
from sli.async_ssh import AsyncSSHSession
import asyncio
import re
import yaml
from getpass import getpass


class MassSSH(BaseCommand):
    sli_command = "mass_ssh"
    short_desc = "Run a command script against multiple firewalls async"
    no_skillet = True
    help_text = """
        Execute a script of CLI commands against multiple firewalls asynchronously. The var
        script.txt must reference a file that contains the CLI commands to run, and devices
        must be either a comma seperated list of devices, or a configuration file describing
        connectivity.

        The -o option refers to a directory to create and populate with output logs from all
        devices configured. This directory will be overwritten if it already exists, be careful.

        Providing credentials in the yaml file is optional and may be passed from the CLI,
        however the yaml file provides support for overriding credentials for specific devices.

        Sample structuring exmpale of the yaml file:

        ---

        creds:
            username: global_user
            password: global_password

        devices:
            - device: device_one

            - device: device_two
              username: device_two_user
              password: device_two_password

        Usage:
            sli mass_ssh -u username -p password -o output_dir script.txt [comma-seperated-devices | config.yaml]
    """

    def get_credentials(self):
        """
        Helper function to first check options and context for credentials, then prompt user if required
        """
        username = self.sli.options.get("username", self.sli.context.get("TARGET_USERNAME", ""))
        password = self.sli.options.get("password", self.sli.context.get("TARGET_PASSWORD", ""))
        while not len(username):
            username = input("Default username: ")
        while not len(password):
            password = getpass("Default password: ")
        return username, password

    def load_config_from_yaml(self):
        """
        Load list of devices and optional credentials from specifid config.yaml file
        """
        # Assemble devices from YAML configuration file
        with open(self.args[1], "r") as f:
            devices = yaml.safe_load(f)
        # Check for presense of devices without specific credentials
        if len([x for x in devices["devices"] if "username" not in x and "password" not in x]):

            # Get default credentials if global credentials not specified
            username = None
            password = None
            if "creds" in devices:
                username = devices["creds"].get("username")
                password = devices["creds"].get("password")
            if not username or not password:
                username, password = self.get_credentials()

            # Apply default parameters to all devices
            devices = devices["devices"]
            for device in devices:
                if "username" not in device:
                    device["username"] = username
                if "password" not in device:
                    device["password"] = password
                device["out_file"] = f"{device['device']}.txt"
                device["coroutine"] = None
                device["status"] = False
                device["error"] = ""

    def run(self):

        async def ssh_coroutine(device, username, password, out_file, script, dev_obj):
            """
            Per device coroutine
            """
            client = AsyncSSHSession(device, username, password)
            try:
                await client.connect()
                await client.run_command_script(script, out_file=out_file)
                dev_obj["status"] = True
            except Exception as e:
                dev_obj["error"] = e

        async def mass_ssh():
            """
            Gather individual coroutines
            """

            if not len(self.args) == 2:
                print(self.help_text)
                return

            with open(self.args[0], "r") as f:
                script = f.read()

            devices = None
            if re.match(r".*\.y.*ml$", self.args[1]):
                devices = self.load_config_from_yaml()

            else:
                # Assemble devices from comma seperated list
                username, password = self.get_credentials()
                devices = [{
                            "device": x,
                            "username": username,
                            "password": password,
                            "out_file": f"{x}.txt",
                            "coroutine": None,
                            "status": False,
                            "error": "",
                        } for x in self.args[1].split(",")]

            print(devices)
            # return

            # Populate devices objects with coroutines
            for dev in devices:
                dev["coroutine"] = ssh_coroutine(
                    dev["device"],
                    dev["username"],
                    dev["password"],
                    dev["out_file"],
                    script,
                    dev
                )

            # Gather and start coroutines
            tasks = [x["coroutine"] for x in devices]
            print(f"Starting SSH to {len(devices)} devices")
            await asyncio.gather(*tasks, return_exceptions=True)
            print("done")

        asyncio.get_event_loop().run_until_complete(mass_ssh())
