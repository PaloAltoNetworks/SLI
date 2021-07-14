from skilletlib import Panoply
from skilletlib.exceptions import PanoplyException

from .base import BaseCommand
from ..decorators import require_ngfw_connection_params
from ..decorators import require_panoply_connection


class CommitCommand(BaseCommand):
    sli_command = "commit"
    short_desc = "Commit the Candidate configuration"
    no_skillet = True

    @require_ngfw_connection_params
    @require_panoply_connection
    def run(self, pan: Panoply):
        try:
            print("Committing configuration...")
            pan.commit()
            print("Success...")

        except PanoplyException as pe:
            print(pe)
            exit(1)
