import unittest2
import sys
import os
from result import WellRestedTestResult

__unittest = True


class OutputDelegatingTestRunner(unittest2.TextTestRunner):
    """
    Pass in result, not resultclass, and delegate all output
    printing to the result.
    """

    def __init__(self, result=None):
        if result:
            self.result = result
        else:
            self.result = WellRestedTestResult()
        self.worker = os.getenv('WRT_WORKER_ID', None)

    @staticmethod
    def parserOptions(parser):
        # reminder, add sub-heading when adding arguments
        # group = parser.add_argument_group('OutputDelegatingTestRunner')
        return parser

    @staticmethod
    def expectedHelpText(cls):
        return ""

    @staticmethod
    def factory(cls, object):
        return cls(result=object.testResult)

    def _makeResult(self):
        return self.result

    def run(self, test):
        "Run the given test case or test suite."
        unittest2.signals.registerResult(self.result)
        self.result.startTestRun()
        e = False
        try:
            test(self.result)
        except KeyboardInterrupt as e:
            if not self.worker:
                sys.stderr.write('ERROR: Exiting due to ^C.\n')
            exit(130)  # bash return code for KeyboardInterrupt
        finally:
            self.result.stopTestRun(abort=e)
        return self.result

