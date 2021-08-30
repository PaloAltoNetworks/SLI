from skilletlib import Panoply

from .base import BaseCommand
from ..decorators import require_ngfw_connection_params
from ..decorators import require_panoply_connection

from sli.errors import SLIException


class LicenseDeactivateCommand(BaseCommand):
    sli_command = "license_deactivate"
    short_desc = "Deactivate an auth-code on a PAN-OS VM-Series"
    no_skillet = True
    help_text = """
            De-activate an Auth Code on a PAN-OS VM-Series

    Example: De-activate an auth-code and be prompted for device credentials
        sli license_deactivate

    Example: De-activate an auth-code using a Support Licensing API Key
        sli license_deactivate 78A00AB9-442F-48AE-A9FE-AFA369CE93D2

    Example: Activate an auth-code and use credentials stored in the context
        sli license_deactivate -uc

    """

    @require_ngfw_connection_params
    @require_panoply_connection
    def run(self, pan: Panoply):

        api_key = self.args[0]
        if not api_key:
            # do not accept blank str here, must be None
            api_key = None

        if not pan.deactivate_vm_license(api_key=api_key):
            print(pan.xapi.status_detail)
            raise SLIException("Could not deactivate VM-Series!")

        print("VM-Series license de-activated")
