from .base import BaseCommand
from sli.decorators import require_ngfw_connection_params, require_panoply_connection

class DiffCommand(BaseCommand):

    sli_command = 'diff'
    short_desc = 'Diff a candidate config from the running-config'
    no_skillet = True

    @require_ngfw_connection_params
    @require_panoply_connection
    def run(self, pan):
        """Get a diff of running and candidate configs"""

        if self.sli.output_format == 'xml':
            output = pan.generate_skillet(from_candidate=True)
            if len(output) < 1:
                print('No differences found')
            for d in output:
                for k in d:
                    print(f'{k}: {d[k]}')
        
        else:
            # Default output format is set commands
            running = pan.get_configuration(config_source='running')
            candidate = pan.get_configuration(config_source='candidate')
            output = pan.generate_set_cli_from_configs(running, candidate)
            if len(output) < 1:
                print('No differences found found')
                return
            for line in output:
                print(line)
