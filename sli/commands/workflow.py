from skilletlib.snippet.workflow import WorkflowSnippet

from sli.decorators import load_variables
from sli.decorators import require_ngfw_connection_params
from sli.decorators import require_single_skillet
from sli.decorators import require_skillet_type
from sli.tools import get_var
from sli.tools import render_expression
from sli.tools import input_yes_no
from .base import BaseCommand


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
            if not self._should_execute(snippet, self.sli.context):
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
            for var in snippet_skillet.variables:
                get_var(var, self.args, self.sli.context)
            exe = snippet_skillet.execute(self.sli.context)
            if snippet_skillet.type in ["panos", "panorama"]:
                commit = self.sli.commit
                if not commit:
                    commit = input_yes_no("Commit the configuration?", True)
                if commit:
                    print("Committing configuration...")
                    snippet_skillet.panoply.commit()
                    print("Finished commit")
            self.sli.context.update(snippet_skillet.context)

            # Handle outputs
            if snippet_skillet.type == 'pan_validation':
                self._print_validation_output(exe)
            elif snippet_skillet.type == 'template':
                print(snippet_skillet.get_results()['template'])
            elif 'output_template' in exe:
                print(exe['output_template'])

    def _get_output(self):
        pass

    @staticmethod
    def _should_execute(snippet, context):
        """Determine if a workflow snippet should be executed"""
        if 'when' not in snippet:
            return True
        return render_expression(snippet['when'], context) == "True"

    @staticmethod
    def _print_validation_output(exe):
        """Print output for validation skillets after run"""
        for output_name in exe["outputs"]:
            output = exe["outputs"][output_name]
            if not isinstance(output, dict):
                continue
            if "test" in output:
                print(f"   Validation: {output_name}")
                print(f"      Output: {output['output_message']}")
