import unittest2
import subprocess
from well_rested_unittest import FullyConfigurableTestProgram, \
                                 OutputDelegatingTestRunner, \
                                 AutoDiscoveringTestLoader, \
                                 WellRestedTestResult


class NewRunner(OutputDelegatingTestRunner):
    pass


class NewLoader(AutoDiscoveringTestLoader):
    pass


class NewResult(WellRestedTestResult):
    pass


class NewSuite(unittest2.TestSuite):
    pass


class TestFullyConfigurableTestProgram(unittest2.TestCase):

    maxDiff = None

    def test_default_classes_no_argv(self):
        program = FullyConfigurableTestProgram(argv=['fctest', 'sample_tests'])
        self.assertEqual(program.suiteClass, unittest2.TestSuite)
        self.assertTrue(isinstance(program.testLoader, AutoDiscoveringTestLoader))
        self.assertTrue(isinstance(program.testRunner, OutputDelegatingTestRunner))
        self.assertTrue(isinstance(program.testResult, WellRestedTestResult))

        # result gets default settings
        self.assertTrue(program.testResult.dots)
        self.assertFalse(program.testResult.showAll)
        self.assertFalse(program.testResult.failfast)
        self.assertFalse(program.testResult.printing)
        self.assertIsNone(program.testResult.wrt_conf)

    def test_specific_classes_with_argv(self):
        program = FullyConfigurableTestProgram(
            suiteClass=NewSuite,
            loaderClass=NewLoader,
            runnerClass=NewRunner,
            resultClass=NewResult,
            argv=['fctest', '-q', '-l', '--failfast', '--wrt-conf', 'file.conf', 'sample_tests'])
        self.assertEqual(program.suiteClass, NewSuite)
        self.assertTrue(isinstance(program.testLoader, NewLoader))
        self.assertTrue(isinstance(program.testRunner, NewRunner))
        self.assertTrue(isinstance(program.testResult, NewResult))

        # result gets settings from argv
        self.assertFalse(program.testResult.dots)
        self.assertFalse(program.testResult.showAll)
        self.assertTrue(program.testResult.failfast)
        self.assertEqual(program.testResult.printing, 1)
        self.assertIsNotNone(program.testResult.wrt_conf)

    def test_help(self):
        program = FullyConfigurableTestProgram(argv=['fctest', 'sample_tests'])
        help_message = program.parser.format_help()
        self.assertIn(program.testResult.expectedHelpText(program.resultClass), help_message)
        self.assertIn(program.testLoader.expectedHelpText(program.loaderClass), help_message)
        self.assertIn(program.testRunner.expectedHelpText(program.runnerClass), help_message)
