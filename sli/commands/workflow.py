from jinja2 import Template

from sli.decorators import load_variables
from sli.decorators import require_ngfw_connection_params
from sli.decorators import require_single_skillet
from sli.decorators import require_skillet_type
from .base import BaseCommand

from sli.tools import render_expression
from skilletlib.snippet.workflow import WorkflowSnippet

def should_execute(snippet, context):
    """Determine if a workflow snippet should be exectued"""
    if not 'when' in snippet:
        return True
    return render_expression(snippet['when'], context) == "True"


def print_validation_output(exe):
    """Print output for validation skillets after run"""
    for output_name in exe["outputs"]:
        output = exe["outputs"][output_name]
        if not isinstance(output, dict):
            continue
        if "test" in output:
            print(f"   Validation: {output_name}")
            print(f"      Output: {output['output_message']}")


class WorkflowCommand(BaseCommand):
    sli_command = 'workflow'
    short_desc = 'Execute a workflow skillet'

    @require_single_skillet
    @require_skillet_type('workflow')
    @require_ngfw_connection_params
    @load_variables
    def run(self):

        # Loop over every snippet
        for snippet in self.sli.skillet.snippet_stack:

            # Verify if a snippet should be run
            if not should_execute(snippet, self.sli.context):
                continue

            # Handle transform
            if "transform" in snippet:
                workflow_snippet = WorkflowSnippet(snippet, self.sli.skillet, self.sli.sl)
                self.sli.context.update(workflow_snippet.transform_context(self.sli.context))

            # Find and execute specific skillet
            snippet_skillet = [x for x in self.sli.skillets if x.name == snippet['name']]
            if len(snippet_skillet) < 1:
                print(f"Unable to find skillet {snippet['name']}")
                return
            if len(snippet_skillet) > 1:
                print(f"Unable to execute unique skillet {snippet['name']} as {len(snippet_skillet)} were found ")
                return
            snippet_skillet = snippet_skillet[0]
            print(f"Running skillet {snippet_skillet.name} - {snippet_skillet.type}\n")
            exe = snippet_skillet.execute(self.sli.context)
            self.sli.context.update(snippet_skillet.context)

            # Handle outputs
            if snippet_skillet.type == 'pan_validation':
                print_validation_output(exe)
            elif snippet_skillet.type == 'template':
                print(snippet_skillet.get_results()['template'])
