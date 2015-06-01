import unittest2
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
        # TODO: output URL where the user can watch run progress
        try:
            test(self.result)
        finally:
            self.result.stopTestRun()
        return self.result

