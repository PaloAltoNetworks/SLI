class BaseCommand():

    def __init__(self, sli):
        self.sli = sli

    def execute(self):
        """SLI starts here to call the run function"""
        self.run()

    def run(self):
        """ Should be overridden by child classes"""
        raise Exception(f"The SLI module {self.sli_command} has not properly overriden the run function")