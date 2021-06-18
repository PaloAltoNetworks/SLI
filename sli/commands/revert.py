from .base import BaseCommand
from sli.decorators import require_ngfw_connection_params, require_panoply_connection

"""
Revert a configuration on an NGFW
"""


class RevertCommand(BaseCommand):
    sli_command = 'revert'
    short_desc = 'Revert a candidate configuration on an NGFW'
    no_skillet = True

    @require_ngfw_connection_params
    @require_panoply_connection
    def run(self, pan):

        pan.load_config("running-config.xml")
        print("Configuration reverted to running-config")
