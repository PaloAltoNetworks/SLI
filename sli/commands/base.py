from skilletlib import Skillet


class BaseCommand:
    sli_command = 'unimplemented'

    def __init__(self, sli):
        self.sli = sli
        self.args = self.sli.args
        # most commands use a skillet by default, subclasses should override as necessary
        self.no_skillet = False

    def execute(self):
        """SLI starts here to call the run function"""

        # Filter out all var=value arguments for context loading
        self.raw_args = self.args
        self.args = [x for x in self.args if "=" not in x]

        self.run()
        self._get_output()

    def execute_debug(self):
        self.raw_args = self.args
        self.args = [x for x in self.args if "=" not in x]
        if hasattr(self, 'debug'):
            self.debug()
        else:
            print(f"Module {self.sli_command} doesn't have a debug function")

    def run(self):
        """Should be overridden by child classes"""
        raise Exception(f"The SLI module {self.sli_command} has not properly overridden the run function")

    def _print_usage(self):
        if hasattr(self, "help_text"):
            print(self.help_text)
        elif hasattr(self, "short_desc"):
            print(self.short_desc)
        else:
            print(f"{self.sli_command} does not provide any help")

    def _get_output(self):

        if not self.no_skillet:
            skillet: Skillet = self.sli.skillet

            if not skillet:
                return

            results = skillet.get_results()

            if "output_template" in results:
                print(results["output_template"])

            elif self.sli.verbose:
                print(results)

            elif not getattr(self, "suppress_output", False) is True:
                print(f"Result Success: {skillet.success}")
