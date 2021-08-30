from skilletlib import Panoply

from .base import BaseCommand
from ..decorators import require_ngfw_connection_params
from ..decorators import require_panoply_connection

from sli.errors import SLIException, InvalidArgumentsException


class LicenseCommand(BaseCommand):
    sli_command = "license_activate"
    short_desc = "Apply an auth-code to a PAN-OS Device"
    no_skillet = True
    help_text = """
            Activate an Auth Code on a PAN-OS Device

    Example: Activate an auth-code and be prompted for device credentials
        sli license_activate IBADCODE

    Example: Activate an auth-code and use credentials stored in the context
        sli license_activate IBADCODE -uc

    """

    @require_ngfw_connection_params
    @require_panoply_connection
    def run(self, pan: Panoply):

        auth_code = self.args[0]
        if not auth_code:
            raise InvalidArgumentsException("You must supply an Auth-Code to license this PAN-OS Device")
        if not pan.fetch_license(auth_code=auth_code):
            print(pan.xapi.status_detail)
            raise SLIException("Could not apply auth-code!")
