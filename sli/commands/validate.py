import os

from sli.decorators import load_variables
from sli.decorators import require_ngfw_connection_params
from sli.decorators import require_single_skillet
from sli.decorators import require_skillet_type
from sli.tools import generate_report
from sli.tools import print_table
from .base import BaseCommand

"""
Execute a validation skillet and generate results
"""


class ValidateCommand(BaseCommand):
    sli_command = 'validate'
    short_desc = 'Execute a validation skillet of type pan_validation'

    @require_single_skillet
    @require_skillet_type('pan_validation')
    @require_ngfw_connection_params
    @load_variables
    def run(self):
        """
        SLI action, test load all skillets in directory and print out loaded skillets
        Generate panforge report if requested
        """

        print(f"Executing {self.sli.skillet.name}...")
        self.sli.skillet.execute(self.sli.context)

    def _get_output(self):
        exe = self.sli.skillet.get_results()
        if self.sli.verbose:
            self.print_verbose(exe)
        self.print_summary(exe)

        if getattr(self.sli, 'generate_report', False):
            header = {'Host': self.sli.context['TARGET_IP']}
            out_file = getattr(self.sli, 'report_file', '')
            if len(out_file) < 1:
                out_file = f'{self.sli.options["TARGET_IP"]}-{self.sli.skillet.name}.html'
            report_dir = os.path.sep.join([self.sli.skillet.path, 'report'])
            generate_report(out_file, exe['pan_validation'], report_dir, header=header)

    @staticmethod
    def print_verbose(exe):
        print('Validation details\n------------------')
        for snippet_name in exe['pan_validation']:
            snippet = exe['pan_validation'][snippet_name]
            print(snippet_name)
            print('-' * len(snippet_name))
            if 'results' in snippet:
                result = "Passed" if snippet['results'] else "Failed"
                print(f"   Validation Results: {result}")
            print(f"   Label: {snippet['label']}")
            print(f"   Output: {snippet['output_message']}")
            documentation_link = snippet.get('documentation_link')
            if documentation_link:
                print(f"   Documentation Link: {documentation_link}")
            if isinstance(snippet['meta'], dict):
                print('   Meta:')
                for key in snippet['meta']:
                    print(f"      {key}: {snippet['meta'][key]}")
            print()

    @staticmethod
    def print_summary(exe):
        results = [
            {
                'name': x,
                'result': "Passed" if exe['snippets'][x] else "Failed"
            }
            for x in exe['snippets']
        ]
        print('Validation results\n------------------')
        print_table(results, {
            "Name": "name",
            "Result": "result"
        })
