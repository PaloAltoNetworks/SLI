from skilletlib.exceptions import TargetConnectionException
from skilletlib.panoply import Panoply

from .base import BaseCommand
from ..decorators import require_ngfw_connection_params


class ConnectCommand(BaseCommand):
    sli_command = "connect"
    short_desc = "Connect to NGFW and save auth information into context if desired"
    no_skillet = True

    def execute(self):
        self.sli.context.pop("TARGET_IP", "")
        self.sli.context.pop("TARGET_USERNAME", "")
        self.sli.context.pop("TARGET_PASSWORD", "")
        self.sli.context.pop("TARGET_PORT", "")
        super().execute()

    @require_ngfw_connection_params
    def run(self):

        target_ip = self.sli.context["TARGET_IP"]
        target_username = self.sli.context["TARGET_USERNAME"]
        target_password = self.sli.context["TARGET_PASSWORD"]
        target_port = self.sli.context.get("TARGET_PORT", 443)

        pan = Panoply(target_ip, target_username, target_password, target_port)

        wait = self.sli.options.get("wait")
        if wait:
            if not isinstance(wait, int):
                wait = int(wait)

            pan.wait_for_device_ready(30, wait)

        if not pan.connected:
            raise TargetConnectionException("Unable to connect to device...")

        sw_version = pan.facts["sw-version"]
        print(f"Connected to device: {target_ip} running PAN-OS: {sw_version}")
