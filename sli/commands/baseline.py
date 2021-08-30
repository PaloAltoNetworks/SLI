from skilletlib import Panoply

from .base import BaseCommand
from ..decorators import require_ngfw_connection_params
from ..decorators import require_panoply_connection


class BaselineCommand(BaseCommand):
    sli_command = "baseline"
    short_desc = "Revert configuration to a near factory default, but retaining admin auth and network configuration"
    no_skillet = True

    @require_ngfw_connection_params
    @require_panoply_connection
    def run(self, pan: Panoply):

        saved_configs = pan.list_saved_configurations()
        if "skillet_baseline.xml" in saved_configs:
            pan.load_config("skillet_baseline.xml")
        else:
            pan.load_baseline()

        print(f'Successfully reverted {self.sli.context["TARGET_IP"]} to baseline config.')

        if self.sli.commit:
            print("Committing configuration...")
            pan.commit()
            print("Success...")
