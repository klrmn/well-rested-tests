import testtools
import unittest2
import requests
import sys
import os
import time
import argparse
import wrtclient

__unittest = True

EARLY = -1
LATE = 1


class WellRestedTestResult(
    testtools.TestResult, unittest2.TextTestResult):
    # TODO: implement communication with WRT server
    # TODO: implement --early-printing
    # TODO: abort on too many fixture warnings:infos
    # TODO: abort on too many test failures/errors
    """
    Uploads test runs / cases to a well-rested-tests server.

    Verbose output also includes:
    * failure/error reason, if one is available in the details
    * test execution time

    Additional mechanisms to report on fixture start, stop, warning, and info
    without affecting test count / results summary.

    TestRunner is assumed to call startTestRun() and stopTestRun()

    In the event of test run times > 300 seconds,
    time taken will be printed in HH:MM:SS.sss format.
    """

    start_time = None
    end_time = None
    test_start_time = None
    test_end_time = None

    @staticmethod
    def parserOptions(parser):
        group = parser.add_argument_group('WellRestedTestResult')
        group.add_argument('-f', '--failfast', dest='failfast',
                            action='store_true',
                            help='Stop on first fail or error')
        group.add_argument('-x', '--uxsuccess-not-failure',
                            dest='uxsuccess_not_failure',
                            action='store_true',
                            help="Consider unexpected success a failure "
                                 "(default True).")
        group.add_argument('-r', '--reason-only', dest='verbosity',
                            action='store_const', const=2,
                            help='Detailed output')
        group.add_argument('-v', '--verbose', dest='verbosity',
                            action='store_const', const=3,
                            help='Verbose output')
        # quiet is verbosity = -1 rather than zero so that it is truthy
        group.add_argument('-q', '--quiet', dest='verbosity',
                            action='store_const', const=-1,
                            help='Silent output')
        group.add_argument('-l', '--late-printing', dest='printing',
                            action='store_const', const=LATE,
                            help="don't print test starts")
        group.add_argument('-e', '--early-printing', dest='printing',
                            action='store_const', const=EARLY,
                            help="print details immediately")
        group.add_argument('-w', '--wrt-conf', dest='wrt_conf',
                            help='path to well-rested-tests config file')
        group.add_argument('--failing-file', dest='failing_file',
                           default='.failing',
                           help='path to file used to store failed tests'
                                '(default .failing)')
        return parser

    @staticmethod
    def factory(cls, object):
        return cls(
            failfast=object.failfast or False,
            uxsuccess_not_failure=object.uxsuccess_not_failure or False,
            verbosity=object.verbosity or 1,
            printing=object.printing or 0,
            failing_file=object.failing_file or '.failing',
            wrt_conf=object.wrt_conf or None)

    @staticmethod
    def expectedHelpText(cls):
        return """
%s:
  -f, --failfast        Stop on first fail or error
  -x, --uxsuccess-not-failure
                        Consider unexpected success a failure (default True).
  -r, --reason-only     Detailed output
  -v, --verbose         Verbose output
  -q, --quiet           Silent output
  -l, --late-printing   don't print test starts
  -e, --early-printing  print details immediately
  -w WRT_CONF, --wrt-conf WRT_CONF
                        path to well-rested-tests config file
""" % cls.__name__

    def __init__(self, failfast=False,
                 uxsuccess_not_failure=False, verbosity=1,
                 printing=0, failing_file='.failing', wrt_conf=None):
        """
        :param failfast: boolean (default False)
        :param uxsuccess_not_failure: boolean (default False)
        :param verbosity: 0 (none, default), 1 (dots),
                          >1 (reason only), >2 (verbose),
                          will be set to 0 if stream is None
        :param printing: -1 (early), 0 (default), 1 (late)
        :param wrt_conf: path to well-rested-tests config file
        :return:
        """
        # initialize all the things
        self.warnings = []
        self.infos = []
        self.fixtures = 0
        self.stream = unittest2.runner._WritelnDecorator(sys.stderr)
        self.skip_reasons = {}
        self.__now = None
        self._tags = testtools.tags.TagContext()
        self.expectedFailures = []
        self.unexpectedSuccesses = []
        self._detail = ""
        self._test_run = None
        self.wrt_client = None

        unittest2.TextTestResult.__init__(self, self.stream, False, verbosity)

        # set the settings
        self.failfast = failfast
        self.uxsuccess_not_failure = uxsuccess_not_failure
        self.failing_file = failing_file
        self.showAll = verbosity > 1
        self.dots = verbosity == 1
        self.printing = printing
        if wrt_conf:
            self.wrt_client = wrtclient.WRTClient(wrt_conf)

    def _details_to_str(self, details, special=None):
        if 'reason' in details:
            return details['reason'].as_text()
        else:
            from testtools.testresult.real import _details_to_str
            _details_to_str(details, special)

    # run related methods
    def startTestRun(self):
        self.start_time = time.time()
        if self.wrt_client:
            self.wrt_client.startTestRun(
                timestamp=self.start_time)
        self.failing_file = unittest2.runner._WritelnDecorator(
            open(self.failing_file, 'wb'))
        unittest2.TextTestResult.startTestRun(self)

    def stopTestRun(self):
        self.end_time = time.time()
        if self.wasSuccessful():
            status='pass'
        else:
            status='fail'
        if self.wrt_client:
            self.wrt_client.stopTestRun(
                timestamp=self.end_time,
                duration=self.end_time - self.start_time,
                status=status,
                tests_run=self.testsRun,
                failures=len(self.failures),
                errors=len(self.errors),
                skips=len(self.skipped),
                xpasses=len(self.unexpectedSuccesses),
                xfails=len(self.expectedFailures))
        testtools.TestResult.stopTestRun(self)
        self.failing_file.close()
        if self.dots or self.showAll:
            self.printErrors()
            self.printSummary()

    # test related methods
    def getDescription(self, test):
        """Let's not use docstrings as test names"""
        return str(test)

    def startTest(self, test):
        self.test_start_time = time.time()
        if self.wrt_client:
            self.wrt_client.startTest(test, timestamp=self.test_start_time)
        if not self.printing == LATE:
            testtools.TestResult.startTest(self, test)

    def stopTest(self, test):
        """also print out test duration"""
        self.test_end_time = time.time()
        if self.printing == LATE:
            testtools.TestResult.startTest(self, test)
        if self.showAll:
            self.stream.writeln(" in %.3f" % (self.test_end_time - self.test_start_time))
        if self.printing == EARLY:
            if self._detail:
                self.stream.writeln(self.separator1)
                self.stream.writeln(self._detail)
                self.stream.writeln(self.separator2)
                self._detail = ""
        if self.wrt_client:
            self.wrt_client.stopTest(test, timestamp=self.test_end_time,
                                     duration=(self.test_end_time - self.test_start_time))
        testtools.TestResult.stopTest(self, test)

    def addExpectedFailure(self, test, err=None, details=None):
        if self.wrt_client:
            self.wrt_client.xfailTest(test, err, details)
        if self.showAll:
            self.stream.write("expected failure")
        elif self.dots:
            self.stream.write("x")
            self.stream.flush()
        testtools.TestResult.addExpectedFailure(
            self, test, err, details)

    def addError(self, test, err=None, details=None):
        if self.wrt_client:
            self.wrt_client.failTest(test, err, details)
        if self.showAll:
            self.stream.write("ERROR")
            if details and 'reason' in details:
                self.stream.write(' %s ' % details['reason'])
        elif self.dots:
            self.stream.write('E')
            self.stream.flush()
        self.print_or_append(test, err, details, self.errors)
        if self.failfast:
            self.stop()

    def addFailure(self, test, err=None, details=None):
        if self.wrt_client:
            self.wrt_client.failTest(test, err, details)
        if self.showAll:
            self.stream.write("FAIL")
            if details and 'reason' in details:
                self.stream.write(' %s ' % details['reason'].as_text())
        elif self.dots:
            self.stream.write('F')
            self.stream.flush()
        self.print_or_append(test, err, details, self.failures)
        if self.failfast:
            self.stop()

    def addSkip(self, test, reason=None, details=None):
        if self.wrt_client:
            self.wrt_client.skipTest(test, reason)
        if self.showAll:
            self.stream.write("skipped %r" % (reason,))
        elif self.dots:
            self.stream.write("s")
            self.stream.flush()
        testtools.TestResult.addSkip(
            self, test, reason, details)

    def addSuccess(self, test, details=None):
        if self.wrt_client:
            self.wrt_client.passTest(test)
        if self.showAll:
            self.stream.write("ok")
        elif self.dots:
            self.stream.write('.')
            self.stream.flush()

    def addUnexpectedSuccess(self, test, details=None):
        if self.wrt_client:
            self.wrt_client.xpassTest(test, details)
        if self.showAll:
            self.stream.write("unexpected success")
        elif self.dots:
            self.stream.write("u")
            self.stream.flush()
        self.unexpectedSuccesses.append(test)

    # fixture related methods
    def startFixture(self, fixture):
        self.fixtures += 1
        self.test_start_time = time.time()
        # update well-rested-tests with in-progress state and start time
        if not self.printing == LATE:
            if self.showAll:
                self.stream.write(str(fixture))
                self.stream.write(" ... ")

    def stopFixture(self, fixture):
        """also print out test duration"""
        self.test_end_time = time.time()
        if self.showAll:
            self.stream.writeln(" in %.3f" % (self.test_end_time - self.test_start_time))
        if self.printing == EARLY:
            if self._detail:
                self.stream.writeln(self.separator1)
                self.stream.writeln(self._detail)
                self.stream.writeln(self.separator2)
                self._detail = ""
        # update well-rested-tests with end time

    def addWarning(self, fixture, err=None, details=None):
        """
        Use this method if you'd like to print a fixture warning
        without having it effect the outcome of the test run.
        """
        # upload to well-rested-tests
        if self.showAll:
            if self.printing == LATE:
                self.stream.write(str(fixture))
                self.stream.write(" ... ")
            self.stream.write("warning")
            if details and 'reason' in details:
                self.stream.write(' %s ' % details['reason'].as_text())
        self.print_or_append(fixture, err, details, self.warnings)

    def addInfo(self, fixture):
        """
        Use this method if you'd like to print a fixture success.
        """
        # upload to well-rested-tests
        if self.showAll:
            if self.printing == LATE:
                self.stream.write(str(fixture))
                self.stream.write(" ... ")
            self.stream.write("ok")
        self.infos.append(fixture)

    # summarizing methods
    def wasSuccessful(self):
        """Has this result been successful so far?

        Note: Unexpected successes are failures by default,
        but are optionally successes.
        """
        if self.uxsuccess_not_failure:
            return not (self.errors or self.failures)
        else:
            return not (self.errors or self.failures or
                        self.unexpectedSuccesses)

    def print_or_append(self, test, err, details, list):
        details = self._err_details_to_string(test, err, details)
        self.failing_file.writeln(test.id())
        if self.printing == EARLY:
            list.append(test)
            self._detail = details
        else:
            list.append((test, details))

    def printErrors(self):
        if self.dots or self.showAll:
            self.stream.writeln()
        if self.printing != EARLY:
            self.printErrorList('WARNING', self.warnings)
            self.printErrorList('ERROR', self.errors)
            self.printErrorList('FAIL', self.failures)

    def printErrorList(self, flavour, errors):
        unittest2.TextTestResult.printErrorList(self, flavour, errors)

    def printSummary(self):
        self.stream.writeln(self.formatSummary())

    def formatSummary(self):
        timeTaken = self.end_time - self.start_time
        if timeTaken > 300:
            seconds = int(timeTaken)
            microseconds = int((timeTaken - seconds) * 1000)
            hours = seconds / (60 * 60)
            seconds = seconds % (60 * 60)
            minutes = seconds / 60
            seconds = seconds % 60
            timeTaken = '%d:%02d:%02d.%d' % (
                int(hours), int(minutes), int(seconds),
                microseconds)
        else:
            timeTaken = '%.3fs' % timeTaken

        summary = []
        summary.append(self.separator2)
        summary.append("Ran %d test%s in %s\n\n" % (
            self.testsRun, self.testsRun != 1 and "s" or "", timeTaken))
        infos = []
        if not self.wasSuccessful():
            summary.append("FAILED")
            if self.failures:
                infos.append("failures=%d" % len(self.failures))
            if self.errors:
                infos.append("errors=%d" % len(self.errors))
        else:
            summary.append("OK")
        if self.skipped:
            infos.append("skipped=%d" % len(self.skipped))
        if self.expectedFailures:
            infos.append(
                "expected failures=%d" % len(self.expectedFailures))
        if self.unexpectedSuccesses:
            infos.append(
                "unexpected successes=%d" % len(self.unexpectedSuccesses))
        if infos:
            summary.append(" (%s)\n" % (", ".join(infos),))
        return "\n".join(summary)

