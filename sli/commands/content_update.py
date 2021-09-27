from skilletlib import Panoply

from .base import BaseCommand
from ..decorators import require_ngfw_connection_params
from ..decorators import require_panoply_connection


class ContentUpdateCommand(BaseCommand):
    sli_command = "content_update"
    short_desc = "Update NGFW dynamic content, anti-virus definitions, and wildfire"
    no_skillet = True

    @require_ngfw_connection_params
    @require_panoply_connection
    def run(self, pan: Panoply):
        print("Updating dynamic content...")
        pan.update_dynamic_content("content")
        print("Updating anti-virus definitions...")
        pan.update_dynamic_content("anti-virus")
        print("Updating wildfire...")
        pan.update_dynamic_content("wildfire")
        print("Success")
