from .base import BaseCommand
from sli.async_ssh import AsyncSSHSession
import asyncio


class MassSSH(BaseCommand):
    sli_command = "mass_ssh"
    short_desc = "Run a command script against multiple firewalls async"
    no_skillet = True
    help_text = """
        Usage:
            sli mass_ssh -u username -p password -o output_dir script.txt [comma-seperated-devices | config.yaml]
    """

    def run(self):

        async def ssh_coroutine(device, username, password, out_file, script):
            client = AsyncSSHSession(device, username, password)
            try:
                await client.connect()
            except Exception as e:
                print(e)
                return
            await client.run_command_script(script, out_file=out_file)

        # async def mass_ssh(device, username, password, out_file, script):
        async def mass_ssh():
            script = """
            configure
            set zone zone1
            set zone zone2
            set zone zone3
            """
            devices = [
                {
                    "device": "172.31.213.10",
                    "username": "admin",
                    "password": "Paloalto1!",
                    "coroutine": None,
                    "out_file": "device_one.txt"
                },
                {
                    "device": "10.70.221.138",
                    "username": "admin",
                    "password": "Paloalto1!",
                    "coroutine": None,
                    "out_file": "device_two.txt"
                }
            ]
            for dev in devices:
                dev["coroutine"] = ssh_coroutine(
                    dev["device"],
                    dev["username"],
                    dev["password"],
                    dev["out_file"],
                    script
                )
            tasks = [x["coroutine"] for x in devices]
            await asyncio.gather(*tasks, return_exceptions=True)
            print("done")

        asyncio.get_event_loop().run_until_complete(mass_ssh())
