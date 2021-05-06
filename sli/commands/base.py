class BaseCommand():

    def __init__(self, sli):
        self.sli = sli
        self.args = self.sli.args

    def execute(self):
        """SLI starts here to call the run function"""
        self.run()

    def execute_debug(self):
        if hasattr(self, 'debug'):
            self.debug()
        else:
            print(f"Module {self.sli_command} doesn't have a debug function")

    def run(self):
        """ Should be overridden by child classes"""
        raise Exception(f"The SLI module {self.sli_command} has not properly overridden the run function")

    def _print_usage(self):
        if hasattr(self, 'help_text'):
            print(self.help_text)
        elif hasattr(self, 'short_desc'):
            print(self.short_desc)
        else:
            print(f"{self.sli_command} does not provide any help")
