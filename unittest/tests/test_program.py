import sys
import unittest2
import subprocess
import well_rested_unittest


class NewRunner(well_rested_unittest.OutputDelegatingTestRunner):
    pass


class NewLoader(well_rested_unittest.AutoDiscoveringTestLoader):
    pass


class NewResult(well_rested_unittest.WellRestedTestResult):
    pass


class NewSuite(well_rested_unittest.ErrorTolerantOptimisedTestSuite):
    pass


class TestFullyConfigurableTestProgram(unittest2.TestCase):

    maxDiff = None
    concurrency = 4

    def test_default_classes_no_argv(self):
        program = well_rested_unittest.FullyConfigurableTestProgram(
            argv=['fctest', 'sample_tests'])
        self.assertEqual(program.suiteClass,
                         well_rested_unittest.ErrorTolerantOptimisedTestSuite)
        self.assertTrue(isinstance(
            program.testLoader, well_rested_unittest.AutoDiscoveringTestLoader))
        self.assertTrue(isinstance(
            program.testRunner, well_rested_unittest.OutputDelegatingTestRunner))
        self.assertTrue(isinstance(
            program.testResult, well_rested_unittest.WellRestedTestResult))

        # result gets default settings
        self.assertTrue(program.testResult.dots)
        self.assertFalse(program.testResult.showAll)
        self.assertFalse(program.testResult.failfast)
        self.assertFalse(program.testResult.early_details)
        self.assertIsNone(program.testResult.wrt_client)

    def test_specific_classes_with_argv(self):
        program = well_rested_unittest.FullyConfigurableTestProgram(
            suiteClass=NewSuite,
            loaderClass=NewLoader,
            runnerClass=NewRunner,
            resultClass=NewResult,
            argv=['fctest', '-q', '--failfast', 'sample_tests'])
        self.assertEqual(program.suiteClass, NewSuite)
        self.assertTrue(isinstance(program.testLoader, NewLoader))
        self.assertTrue(isinstance(program.testRunner, NewRunner))
        self.assertTrue(isinstance(program.testResult, NewResult))

        # result gets settings from argv
        self.assertFalse(program.testResult.dots)
        self.assertFalse(program.testResult.showAll)
        self.assertTrue(program.testResult.failfast)

    def test_help(self):
        program = well_rested_unittest.FullyConfigurableTestProgram(
            argv=['fctest', 'sample_tests'])
        help_message = program.parser.format_help()
        # sys.stderr.write(help_message)  # much easier debugging
        self.assertIn(program.testResult.expectedHelpText(program.resultClass), help_message)
        self.assertIn(program.testLoader.expectedHelpText(program.loaderClass), help_message)
        self.assertIn(program.testRunner.expectedHelpText(program.runnerClass), help_message)
        self.assertIn(program.suiteClass.expectedHelpText(program.suiteClass), help_message)
