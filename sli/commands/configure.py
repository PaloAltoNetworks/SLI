import json

from skilletlib.exceptions import PanoplyException

from sli.decorators import load_variables
from sli.decorators import require_ngfw_connection_params
from sli.decorators import require_single_skillet
from sli.decorators import require_skillet_type
from .base import BaseCommand


class ConfigureCommand(BaseCommand):
    sli_command = "configure"
    short_desc = "Execute a configuration skillet of type panos"
    help_text = """
    Executes a PAN-OS configuration skillet.

    Example: Load and commit and configuration skillet
        sli configure --name test_skillet -sd ~/pan/Skillets -uc

    Example: Verify the actions of a configuration skillet ONLY
        sli configure --debug --name test_skillet -sd ~/pan/Skillets -uc

"""

    @require_single_skillet
    @require_skillet_type("panos", "panorama")
    @require_ngfw_connection_params
    @load_variables
    def run(self):

        print(f"Executing {self.sli.skillet.name}...")
        output = self.sli.skillet.execute(self.sli.context)

        needs_commit = output.get("changed", False)

        if needs_commit and self.sli.commit:
            print("Committing configuration...")
            self.sli.skillet.panoply.commit()
            print("Finished")

        else:
            if needs_commit:
                print("Configuration loaded into candidate config")

            else:
                context_keys = output.get("outputs", {}).keys()

                if len(context_keys):
                    print("Saved the following items into the context:")
                    print("----")

                    for k in context_keys:
                        print(k)

                    print("----")

    @require_single_skillet
    @require_skillet_type("panos", "panorama")
    @require_ngfw_connection_params
    @load_variables
    def debug(self):
        """
        Debug this configuration skillet, this will not perform any destructive actions against the device, but
        will perform op commands and the like to gather information
        """
        print(f"Running {self.sli.skillet.name} debug...")
        skillet_context = self.sli.skillet.initialize_context(self.sli.context)
        changes = dict()

        for snippet in self.sli.skillet.get_snippets():
            snippet.update_context(skillet_context)

            loop_vars = snippet.get_loop_parameter()
            index = 0

            for item in loop_vars:
                change = dict()

                skillet_context["loop"] = item
                skillet_context["loop_index"] = index

                snippet.render_metadata(skillet_context)

                if snippet.name in changes:
                    changes[f"{snippet.name}_{index}"] = change
                else:
                    changes[snippet.name] = change

                change["metadata"] = json.dumps(snippet.metadata, indent=4)
                change["when"] = True

                if not snippet.should_execute(skillet_context):
                    change["message"] = "This snippet would be skipped due to when conditional"
                    change["when"] = False
                    continue

                if "cmd" in snippet.metadata and snippet.metadata["cmd"] in (
                    "op",
                    "set",
                    "edit",
                    "override",
                    "move",
                    "rename",
                    "clone",
                    "delete",
                ):

                    change["message"] = "This snippet would be executed"

                else:
                    try:
                        (output, status) = snippet.execute(skillet_context)
                        # capture all outputs
                        snippet_outputs = snippet.get_default_output(output, status)
                        captured_outputs = snippet.capture_outputs(output, status)

                        skillet_context.update(snippet_outputs)
                        skillet_context.update(captured_outputs)

                        change["message"] = "This snippet was executed to gather results"
                        change["captured_output"] = json.dumps(captured_outputs, indent=4)

                    except PanoplyException as pe:
                        change["message"] = str(pe)

                index = index + 1
                snippet.reset_metadata()

        print("****Debug Output ****")
        for k, v in changes.items():
            print(f"Snippet: {k}")
            if isinstance(v, dict):
                for kk, vv in v.items():
                    try:
                        j = json.loads(vv)
                        print("{")
                        for jk, jv in j.items():
                            print(f"   {jk}: {jv}")
                        print("}")
                    except (TypeError, json.decoder.JSONDecodeError):
                        print(f"{kk}: {vv}")

                print("***\n")
            else:
                print(f"{k}\n{v}\n")
