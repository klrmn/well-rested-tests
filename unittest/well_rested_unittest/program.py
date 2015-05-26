import unittest2
import os
import sys
import argparse

from result import *
from runner import *
from loader import *

__unittest = True

sys.path.append(os.getcwd())

class FullyConfigurableTestProgram(unittest2.TestProgram):
    exit = True
    defaultTest = module = None
    catch = False

    def __init__(self, argv=[], entry_settings={},
                 suiteClass=unittest2.TestSuite,
                 resultClass=WellRestedTestResult,
                 loaderClass=AutoDiscoveringTestLoader,
                 runnerClass=OutputDelegatingTestRunner):
        """
        All classes provided in the constructor should implement
        (static) .parseArgs(parser) and (static) .factory(object),
        so that the TestProgram doesn't need to know anything about
        the flags / constructor of that class.

        NOTE: this TestProgram doesn't automatically run.
        runTests() must be called.

        :param suiteClass: default unittest2.TestSuite
        :param resultClass: WellRestedTestResult or subclass
        :param loaderClass: AutoDiscoveringTestLoader or subclass
        :param runnerClass: OutputDelegatingTestRunner or subclass
        :param argv: list of arguments as if they came from the command line.
                     useful for testing.
        :param entry_settings: dictionary of values to set on the program.
                               useful for entry_points which want default flags,
                               since argv and sys.argv cannot be used at the same
                               time due to positional arguments.
        :return:
        """
        self.progName = os.path.basename(sys.argv[0])
        # set properties based on entry_settings
        for key, value in entry_settings.items():
            setattr(self, key, value)
        # get all our classes, so their staticmethods can be used
        self.resultClass = resultClass
        self.runnerClass = runnerClass
        self.loaderClass = loaderClass
        self.suiteClass = suiteClass
        # parse args using classes' staticmethods
        self.parseArgs(argv or sys.argv)  # args is for testing
        # create the instances
        try:
            self.testLoader = self.loaderClass.factory(self.loaderClass, self)
            self.testResult = self.resultClass.factory(self.resultClass, self)
            self.testRunner = self.runnerClass.factory(self.runnerClass, self)
        except AttributeError as e:
            # hey, it's developer error
            sys.stderr.write(
                'ERROR: All classes used by %s should implement '
                '.factory(object) in agreement with .parserOptions(parser)\n%s\n'
                % (self.__class__.__name__, e))
            exit(1)
        # find the tests
        self.createTests()
        self.test.list_tests = self.list_tests if hasattr(self, 'list_tests') else False

    @property
    def parser(self):
        parser = argparse.ArgumentParser(conflict_handler='resolve')
        parser.prog = self.progName
        parser.print_help = self._print_help

        parser.add_argument('testNames', nargs='+',
                            help='a list of one or more of test '
                                 'directories, modules, '
                                 'classes and/or methods.')
        parser.add_argument('-c', '--catch', dest='catchbreak',
                            action='store_true',
                            help='Catch ctrl-C and display results so far')
        try:
            parser = self.resultClass.parserOptions(parser)
            parser = self.runnerClass.parserOptions(parser)
            parser = self.loaderClass.parserOptions(parser)
            if hasattr(self.suiteClass, 'parserOptions'):
                parser = self.suiteClass.parserOptions(parser)
        except AttributeError as e:
            # hey, it's developer error
            sys.stderr.write(
                'ERROR: All classes used by %s should implement '
                '.parserOptions(parser)\n%s\n'
                % (self.__class__.__name__, e))
            exit(1)
        return parser

    def parseArgs(self, argv):
        self.parser.parse_args(argv[1:], self)

    def _print_help(self, *args, **kwargs):
        print(self.parser.format_help())

if __name__ == '__main__':
    FullyConfigurableTestProgram().runTests()
