from .base import BaseCommand
from sli.decorators import require_single_skillet
from sli.decorators import require_skillet_type

from skilletlib.skillet.panos import PanosSkillet


class RollupPlaylist(BaseCommand):
    sli_command = 'rollup_playlist'
    short_desc = 'Rollup a panos skillet in playlist format into a single file'
    no_context = True
    help_text = """

    Usage:
        sli rollup_playlist -n [skillet] [out-file]

"""

    @require_single_skillet
    @require_skillet_type("panos", "panorama")
    def run(self):
        if not len(self.args) == 1:
            print(self.help_text)
            return
        out_file = self.args[0]

        new_skillet = {}
        for attr in ["name", "label", "description", "type", "labels", "variables"]:
            new_skillet[attr] = getattr(self.sli.skillet, attr)
        new_skillet["name"] += "_rollup"
        new_skillet["snippets"] = [x.metadata for x in self.sli.skillet.snippets]
        for snippet in new_skillet["snippets"]:
            del_keys = [key for key, value in snippet.items() if not value]
            for key in del_keys:
                snippet.pop(key)

        out_str = PanosSkillet(new_skillet).dump_yaml()
        with open(out_file, "w") as f:
            f.write(out_str)
        print(f"New skillet written to {out_file}")
