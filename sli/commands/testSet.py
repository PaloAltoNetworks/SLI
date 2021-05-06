from .base import BaseCommand
from sli.decorators import require_ngfw_connection_params, require_panoply_connection


class TestSet(BaseCommand):
    sli_command = "test_set"
    short_desc = "Test set commands in a file against a live NGFW to ensure no errors"
    no_skillet = True
    help_text = """
        Test set commands in a file against a live NGFW to ensure no errors
"""

    @require_ngfw_connection_params
    @require_panoply_connection
    def run(self, pan):
        breakpoint()
        pass
