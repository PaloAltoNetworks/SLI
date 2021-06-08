from math import floor
import time

"""
Progress bar that displays percentage complete and tracks time elapsed.
Time elapsed can be disabled by passing clock=False to init.
Best practice is to make sure this is called often, ideally once a second
or more to ensure the clock does not appear to be hung

Usage:
    pb = ProgressBar(prefix="My Task")
    while doing_work():
        do_some_work()
        pb.update(percentage_complete)
    pb.complete()
"""


class ProgressBar:

    def __init__(self, length=50, prefix="Progress", clock=True, fill='█'):
        self.length = length
        self.prefix = prefix
        self.clock = clock
        self.fill = fill
        self.start_time = time.time()
        self.percent = 0
        self.update(self.percent)
        self.bar = None

    def _get_time(self):
        if not self.clock:
            return ""
        current = floor(time.time() - self.start_time)
        minutes = floor(current / 60)
        seconds = current % 60
        return f"({minutes}m {seconds}s)"

    def update(self, percent):
        """After instantiation, call this to report a new percentage update"""
        self.percent = percent
        filledLength = floor(self.length * (float(percent) / 100))
        self.bar = self.fill * filledLength + '-' * (self.length - filledLength)
        time_string = self._get_time()
        print(f'\r{self.prefix} |{self.bar}| {percent}% {time_string}', end="\r")

    def complete(self):
        """Call this when the target workload is complete to display 100%"""
        self.bar = self.fill * self.length
        time_string = self._get_time()
        print(f'\r{self.prefix} |{self.bar}| Complete {time_string}\n')

    def pause(self):
        """Call this to pause a progress bar and get a new line"""
        time_string = self._get_time()
        print(f'\r{self.prefix} |{self.bar}| Paused {self.percent}% {time_string}')
