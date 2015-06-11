import sys
import unittest2
import well_rested_unittest
from utils import OutputBuffer
import traceback
import testtools


class ExampleException(Exception):
    pass


class TestWellRestedTestResult(unittest2.TestCase):

    maxDiff = None
    concurrency = 4

    _err = None
    _details = None

    @property
    def err(self):
        if not self._err:
            try:
                raise ExampleException('some data')
            except ExampleException:
                self._err = sys.exc_info()
        return self._err

    @property
    def details(self):
        if not self._details:
            self._details = {
                'reason': testtools.content.text_content(
                    'ExampleException'),
                'traceback': testtools.content.TracebackContent(
                    self.err, self),
                'log': testtools.content.text_content(
                    'these are\nmutliple lines\nof content'),
            }
        return self._details

    def test_failfast(self):
        result = well_rested_unittest.WellRestedTestResult(
            failfast=True, verbosity=0, failing_file="")
        result.addFailure('test1', err=self.err)
        self.assertTrue(result.shouldStop)

    def test_no_failfast(self):
        result = well_rested_unittest.WellRestedTestResult(
            failfast=False, verbosity=0, failing_file="")
        result.addFailure('test2', err=self.err)
        self.assertFalse(result.shouldStop)

    def test_fail_on_uxsuccess(self):
        result = well_rested_unittest.WellRestedTestResult(
            uxsuccess_not_failure=False, verbosity=0, failing_file="")
        result.addUnexpectedSuccess('test3', details=self.details)
        self.assertTrue(len(result.unexpectedSuccesses))
        self.assertFalse(len(result.failures))
        self.assertFalse(result.wasSuccessful())

    def test_no_fail_on_uxsuccess(self):
        result = well_rested_unittest.WellRestedTestResult(
            uxsuccess_not_failure=True, verbosity=0, failing_file="")
        result.addUnexpectedSuccess('test4', details=self.details)
        self.assertTrue(len(result.unexpectedSuccesses))
        self.assertFalse(len(result.failures))
        self.assertTrue(result.wasSuccessful())

    def test_output_verbose(self):
        result = well_rested_unittest.WellRestedTestResult(
            verbosity=2)
        self.assertTrue(result.showAll)
        self.assertFalse(result.dots)
        self.assertFalse(result.early_details)

    def test_output_default(self):
        result = well_rested_unittest.WellRestedTestResult()
        self.assertFalse(result.showAll)
        self.assertTrue(result.dots)
        self.assertFalse(result.early_details)

    def test_output_quiet(self):
        result = well_rested_unittest.WellRestedTestResult(
            verbosity=0)
        self.assertFalse(result.showAll)
        self.assertFalse(result.dots)
        self.assertFalse(result.early_details)

    def test_output_early_details(self):
        result = well_rested_unittest.WellRestedTestResult(
            verbosity=3)
        self.assertTrue(result.showAll)
        self.assertFalse(result.dots)
        self.assertTrue(result.early_details)

    def test_startTestRun_stopTestRun(self):
        result = well_rested_unittest.WellRestedTestResult(
            verbosity=0, failing_file="")
            # you'll want this one for debugging
            # verbosity=2, failing_file="", printing=well_rested_unittest.result.EARLY)

        class DummyTestClass(unittest2.TestCase):
            def test9(self):
                pass

            def test10(self):
                pass

            def test11(self):
                pass

            def test12(self):
                pass

            def test13(self):
                pass

            def test14(self):
                pass


        result.startTestRun()
        self.assertEqual(result.test_start_time, {})
        self.assertEqual(result.test_end_time, {})
        result.startTest(DummyTestClass(methodName='test9'))
        result.addFailure(DummyTestClass(methodName='test9'),
                          err=self.err)
        result.stopTest(DummyTestClass(methodName='test9'))
        self.assertTrue(result.test_start_time['tests.test_result.DummyTestClass.test9'])
        self.assertTrue(result.test_end_time['tests.test_result.DummyTestClass.test9'])
        result.startTest(DummyTestClass(methodName='test10'))
        result.addSuccess(DummyTestClass(methodName='test10'),
                          details=self.details)
        result.stopTest(DummyTestClass(methodName='test10'))
        result.startTest(DummyTestClass(methodName='test11'))
        result.addExpectedFailure(DummyTestClass(methodName='test11'),
                                  err=self.err)
        result.stopTest(DummyTestClass(methodName='test11'))
        result.startTest(DummyTestClass(methodName='test12'))
        result.addUnexpectedSuccess(DummyTestClass(methodName='test12'),
                                    details=self.details)
        result.stopTest(DummyTestClass(methodName='test12'))
        result.startTest(DummyTestClass(methodName='test13'))
        result.addFailure(DummyTestClass(methodName='test13'),
                          details=self.details)
        result.stopTest(DummyTestClass(methodName='test13'))
        result.startTest(DummyTestClass(methodName='test14'))
        result.addSkip(DummyTestClass(methodName='test14'),
                       'blah')
        result.stopTest(DummyTestClass(methodName='test14'))
        result.stopTestRun()
        self.assertIsNotNone(result.start_time)
        self.assertIsNotNone(result.end_time)
        self.assertEqual(len(result.failures), 2)
        self.assertEqual(len(result.expectedFailures), 1)
        self.assertEqual(len(result.unexpectedSuccesses), 1)
        self.assertEqual(len(result.skipped), 1)
        actual_summary = result.formatSummary()
        self.assertIn('Ran 6 tests in ', actual_summary)
        self.assertIn('FAILED', actual_summary)
        self.assertIn(' (failures=2, skipped=1, expected failures=1, unexpected successes=1)',
                      actual_summary)
        self.assertIn('(ExampleException=1)', actual_summary)

    def test_addWarning(self):
        result = well_rested_unittest.WellRestedTestResult(
            verbosity=0, failing_file="")
        result.startTestRun()
        result.addWarning('fixture1', err=self.err)
        result.addWarning('fixture2', details=self.details)
        result.stopTestRun()
        self.assertEqual(len(result.warnings), 2)
        self.assertTrue(result.wasSuccessful())


