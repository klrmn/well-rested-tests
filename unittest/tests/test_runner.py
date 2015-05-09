import unittest2

from well_rested_unittest import OutputDelegatingTestRunner, WellRestedTestResult


class NewResult(WellRestedTestResult):
    pass


class TestOutputDelegatingTestRunner(unittest2.TestCase):

    def test_default_result(self):
        runner = OutputDelegatingTestRunner()
        self.assertTrue(isinstance(runner.result, WellRestedTestResult))

    def test_specific_result(self):
        runner = OutputDelegatingTestRunner(result=NewResult())
        self.assertTrue(isinstance(runner.result, NewResult))
