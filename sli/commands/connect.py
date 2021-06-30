from getpass import getpass

from skilletlib.exceptions import TargetConnectionException
from skilletlib.panoply import Panos

from .base import BaseCommand


class ConnectCommand(BaseCommand):
    sli_command = "connect"
    short_desc = "Connect to NGFW and save auth information into context if desired"
    no_skillet = True

    def run(self):
        target_ip = input("Device: ")
        target_username = input("Username: ")
        target_password = getpass()

        pan = Panos(target_ip, target_username, target_password)
        if not pan.connected:
            raise TargetConnectionException("Unable to connect to device...")

        sw_version = pan.facts["sw-version"]
        print(f"Connected to device: {target_ip} running PAN-OS: {sw_version}")

        if self.sli.cm.use_context:
            print("Updating context...")
            self.sli.context["TARGET_IP"] = target_ip
            self.sli.context["TARGET_USERNAME"] = target_username
            self.sli.context["TARGET_PASSWORD"] = target_password
