import unittest2

import well_rested_unittest


class NewResult(well_rested_unittest.WellRestedTestResult):
    pass


class TestOutputDelegatingTestRunner(unittest2.TestCase):

    concurrency = 4

    def test_default_result(self):
        runner = well_rested_unittest.OutputDelegatingTestRunner()
        self.assertTrue(isinstance(
            runner.result, well_rested_unittest.WellRestedTestResult))

    def test_specific_result(self):
        runner = well_rested_unittest.OutputDelegatingTestRunner(
            result=NewResult())
        self.assertTrue(isinstance(runner.result, NewResult))
