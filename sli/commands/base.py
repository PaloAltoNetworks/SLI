class BaseCommand():

    def __init__(self, sli):
        self.sli = sli

    def execute(self):
        """SLI starts here to call the run function"""
        print('Running execute')
        self.run()

    def run(self):
        """ Should be overridden by child classes"""
        pass