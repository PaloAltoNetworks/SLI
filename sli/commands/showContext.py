import json

from .base import BaseCommand


class ShowContext(BaseCommand):
    sli_command = "show_context"
    short_desc = "Print out contents of an existing context"
    no_skillet = True
    no_context = True

    def run(self):
        context_name = self.sli.options.get("context_name", "")
        if len(context_name) < 1:
            context_name = self.args[0] if len(self.args) > 0 else "default"
        context = self.sli.cm.load_context(from_file=context_name)
        if not len(context.keys()):
            print(f"Unable to load context {context_name}")
            return
        if self.sli.no_config and "config" in context:
            context.pop("config")
        hidden_fields = ["TARGET_PASSWORD"]
        for hf in hidden_fields:
            if hf in context:
                context[hf] = "*****"

        if len(self.args) > 1:
            print(json.dumps(context.get(self.args[1]), indent=4))
        else:
            print(json.dumps(context, indent=4))
