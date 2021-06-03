from .base import BaseCommand
import yaml

from skilletlib.skillet.panos import PanosSkillet


class RollupSkillet(BaseCommand):
    sli_command = 'rollup_skillet'
    short_desc = 'Rollup a panos skillet with external XML into a single file'
    no_skillet = True
    no_context = True
    help_text = """

    Usage:
        sli rollup_skillet [skillet-file] [out-file]

"""

    def run(self):
        if not len(self.args) == 2:
            print(self.help_text)
            return

        # Load skillet and copy over non snippet keys
        skillet_file = self.args[0]
        out_file = self.args[1]
        with open(skillet_file, "r") as f:
            skillet = yaml.safe_load(f)

        # Validate supported keys in snippets
        for snippet in skillet["snippets"]:
            for key in snippet.keys():
                if key not in ["name", "xpath", "when", "file"]:
                    print(f"Snippet has unsupported key {key}")
                    return
            for key in ["name", "xpath", "file"]:
                if key not in snippet:
                    print(f"Snippet missing required key {key}")
                    return

        # Load updated dict with merged configuration files
        updated_dict = PanosSkillet(skillet).skillet_dict
        for s in updated_dict["snippets"]:
            del_items = [key for key, value in s.items() if not value or key == "file"]
            for item in del_items:
                del(s[item])

        out_str = PanosSkillet(updated_dict).dump_yaml()
        with open(out_file, "w") as f:
            f.write(out_str)
