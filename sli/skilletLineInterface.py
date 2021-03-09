from skilletlib import SkilletLoader
from sli.tools import print_table
from getpass import getpass

class SkilletLineInterface():

    def __init__(self, options):
        self.options = options
        self.sl = SkilletLoader()
        self._load_skillets()
        self.context = {}
    
    def _load_skillets(self):
        self.skillets = self.sl.load_all_skillets_from_dir('./')
        if len(self.sl.skillet_errors) > 0:
            print('Errors on loading skillets:')
            for err in self.sl.skillet_errors:
                for key in err:
                    print(f"   {key} - {err[key]}")

    def test_load(self):
        """SLI action, test load all skillets in directory and print out loaded skillets"""
        objs = []
        for s in self.skillets:
            obj = {
                'name': s.name,
                'type': s.type,
            }
            objs.append(obj)
        print_table(
            objs,
            {
                "Name": "name",
                "Type": "type",
            }
        )
    
    def _pan_validation_output(self, exe, skillet):
        """Format and display output for validation skillets"""

        # Verbose information
        print('Validation details\n------------------')
        for snippet_name in exe['pan_validation']:
            snippet = exe['pan_validation'][snippet_name]
            print(snippet_name)
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
        
        # Results
        results =[
            {
                'name':x,
                'result': "Passed" if exe['snippets'][x] else "Failed"
            }
            for x in exe['snippets']
        ]
        print('Validation results\n------------------')
        print_table(results, {
            "Name": "name",
            "Result": "result"
        })


    def _connectivity_vars(self):
        """Populate context with vars required for NGFW connectivity"""

        self.context['TARGET_IP'] = self.options['device'] if self.options.get('device') else input('Device: ')
        self.context['TARGET_USERNAME'] = self.options['username'] if self.options.get('username') else input('Username: ')
        self.context['TARGET_PASSWORD'] = self.options['password'] if self.options.get('password') else getpass()
    
    def execute(self):
        """SLI action, execute a single or several skillets"""

        # Gather input parameters and load skillet
        self._connectivity_vars()
        if not self.options.get('name') and len(self.skillets) > 1:
            print('Specify a skillet to run with --name when more than 1 is present')
            exit(1)
        target_name = self.options['name'] if self.options['name'] else self.skillets[0].name
        skillet = self.sl.get_skillet_with_name(target_name)
        if skillet is None:
            print(f'Unable to load skillet {target_name} by name')
            exit(1)

        # Execute skillet and process output
        print('Running skillet ' + target_name)
        exe = skillet.execute(self.context)

        if skillet.type == 'pan_validation':
            self._pan_validation_output(exe, skillet)