import testtools
import unittest2
import requests
import sys
import os
import time
import argparse
import wrtclient
import json
from threading import Lock

__unittest = True


class WellRestedTestResult(
    testtools.TestResult, unittest2.TextTestResult):
    # TODO: --run-url (for --parallel)
    # TODO: do start and end times as a property on the test object
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
        group.add_argument('-d', '--dots', dest='verbosity',
                           action='store_const', const=1,
                           help='print dots (default)')
        group.add_argument('-r', '--reason-only', dest='verbosity',
                           action='store_const', const=2,
                           help='Output with reasons')
        group.add_argument('-v', '--verbose', dest='verbosity',
                           action='store_const', const=3,
                           help='Verbose output')
        # quiet is verbosity = -1 rather than zero so that it is truthy
        group.add_argument('-q', '--quiet', dest='verbosity',
                           action='store_const', const=-1,
                           help='Silent output')
        group.add_argument('-e', '--early-details', dest='early_details',
                           action='store_true',
                           help="Print details immediately, "
                                "(overrides -q and -d)")
        group.add_argument('-w', '--wrt-conf', dest='wrt_conf',
                           help='path to well-rested-tests config file')
        return parser

    @staticmethod
    def factory(cls, object):
        return cls(
            failfast=object.failfast if hasattr(object, 'failfast') else False,
            uxsuccess_not_failure=object.uxsuccess_not_failure if
                hasattr(object, 'uxsuccess_not_failure') else False,
            verbosity=object.verbosity if hasattr(object, 'verbosity') else 1,
            early_details=object.early_details if
                hasattr(object, 'early_details') else False,
            failing_file=object.failing_file if
                hasattr(object, 'failing_file') else '.failing',
            wrt_conf=object.wrt_conf if hasattr(object, 'wrt_conf') else None,
            progName=object.progName
        )

    @staticmethod
    def expectedHelpText(cls):
        return """
%s:
  -f, --failfast        Stop on first fail or error
  -x, --uxsuccess-not-failure
                        Consider unexpected success a failure (default True).
  -d, --dots            print dots (default)
  -r, --reason-only     Output with reasons
  -v, --verbose         Verbose output
  -q, --quiet           Silent output
  -e, --early-details   Print details immediately, (overrides -q and -d)
  -w WRT_CONF, --wrt-conf WRT_CONF
                        path to well-rested-tests config file
""" % cls.__name__

    def __init__(self, failfast=False,
                 uxsuccess_not_failure=False, verbosity=1,
                 early_details=False, failing_file='.failing',
                 wrt_conf=None, progName=None):
        """
        :param failfast: boolean (default False)
        :param uxsuccess_not_failure: boolean (default False)
        :param verbosity: 0 (none, default), 1 (dots),
                          >1 (reason only), >2 (verbose),
                          will be set to 0 if stream is None
        :param early_details: boolean (default False)
        :param wrt_conf: path to well-rested-tests config file
        :param progName: so the suite can find out what program name to use for parallelization
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
        self.reasons = {}
        self.start_time = None
        self.end_time = None
        self.test_start_time = {}
        self.test_end_time = {}
        self.test_result = {}
        self._detail = ""
        self._test_run = None
        self.wrt_conf = None
        self.wrt_client = None
        self.worker = os.getenv('WRT_WORKER_ID', None)
        self.progName = progName
        self.absorbLock = Lock()

        unittest2.TextTestResult.__init__(self, self.stream, False, verbosity)

        # set the settings
        self.failfast = failfast
        self.uxsuccess_not_failure = uxsuccess_not_failure
        self.failing_file = failing_file
        self.early_details = early_details
        # worker (ie, parallel) eliminates failing_file and early_details
        if self.worker:
            self.worker = int(self.worker)
            self.failing_file = None
            self.early_details = False
        self.showAll = verbosity > 1
        self.dots = verbosity == 1
        # --early-details overrides -q and -d
        if self.early_details:
            self.showAll = True
            self.dots = False
        if wrt_conf:
            self.wrt_conf = wrt_conf
            self.wrt_client = wrtclient.WRTClient(
                wrt_conf, self.stream, debug=False)

    def _err_details_to_string(self, test, err=None, details=None):
        """Convert an error in exc_info form or a contents dict to a string."""
        if err is not None:
            return testtools.content.TracebackContent(err, test).as_text()
        from testtools.testresult.real import _details_to_str
        return _details_to_str(details, special='traceback')

    def _process_reason(self, test, details):
        reason = None
        if details and 'reason' in details:
            reason = details.pop('reason').as_text()
            if reason not in self.reasons:
                self.reasons[reason] = 1
            else:
                self.reasons[reason] += 1
        return reason

    # run related methods
    def startTestRun(self):
        if self.showAll and not self.worker:
            self.stream.writeln(self.separator2)
        self.start_time = time.time()
        if self.wrt_client and not self.worker:
            try:
                self.wrt_client.startTestRun(
                    timestamp=self.start_time)
            except requests.exceptions.ConnectionError as e:
                self.stream.writeln(
                    'ERROR: Unable to connect to the well-rested-tests server\n%s'
                    % e.message)
                exit(1)
        if self.failing_file:
            self.failing_file = unittest2.runner._WritelnDecorator(
                open(self.failing_file, 'wb'))
        unittest2.TextTestResult.startTestRun(self)

    def stopTestRun(self):
        self.end_time = time.time()
        elapsed_time = self.end_time - self.start_time
        if self.wasSuccessful():
            status='pass'
        else:
            status='fail'
        if self.wrt_client and not self.worker:
            self.wrt_client.stopTestRun(
                timestamp=self.end_time,
                duration=elapsed_time,
                status=status,
                tests_run=self.testsRun,
                failures=len(self.failures),
                errors=len(self.errors),
                skips=len(self.skipped),
                xpasses=len(self.unexpectedSuccesses),
                xfails=len(self.expectedFailures))
        testtools.TestResult.stopTestRun(self)
        if self.failing_file:
            self.failing_file.close()
        # if we're a worker, print the sumarizing stuff to
        # stdout instead of stderr
        if self.worker:
            output = json.dumps({
                'duration': elapsed_time,
                'failures': self.failures,
                'errors': self.errors,
                'skipped': self.skipped,
                'unexpectedSuccesses': self.unexpectedSuccesses,
                'expectedFailures': self.expectedFailures,
                'infos': self.infos,
                'warnings': self.warnings,
                'testsRun': self.testsRun,
                'fixtures': self.fixtures,
                'worker': self.worker,
            })
            sys.stdout.write(output + '\n')
        elif self.dots or self.showAll:
                self.printErrors()
                self.printSummary()

    def absorbResult(self, stdout):
        with self.absorbLock:
            try:
                other_result = json.loads(stdout)
            except ValueError:
                raise
            self.failures.extend(other_result['failures'])
            self.errors.extend(other_result['errors'])
            self.skipped.extend(other_result['skipped'])
            self.unexpectedSuccesses.extend(other_result['unexpectedSuccesses'])
            self.expectedFailures.extend(other_result['expectedFailures'])
            self.testsRun += other_result['testsRun']
            self.infos.extend(other_result['infos'])
            self.warnings.extend(other_result['warnings'])
            self.fixtures += other_result['fixtures']

    # test related methods
    def getDescription(self, test):
        """Let's not use docstrings as test names"""
        output = ''
        if self.worker:
            output = output + '(%s) ' % self.worker
        output = output + str(test)
        return output

    def startTest(self, test):
        self.test_start_time[test] = time.time()
        if self.wrt_client:
            self.wrt_client.startTest(test, timestamp=self.test_start_time[test])
        if self.showAll:
            self.stream.write('%s ... ' % self.getDescription(test))
        unittest2.TestResult.startTest(self, test)

    def stopTest(self, test):
        """also print out test duration"""
        self.test_end_time[test] = time.time()
        elapsed_time = self.test_end_time[test] - self.test_start_time[test]
        if self.showAll:
            self.stream.writeln(" in %.3f" % elapsed_time)
        if self.early_details:
            if self._detail:
                self.stream.writeln(self.separator1)
                self.stream.writeln(self._detail)
                self.stream.writeln(self.separator2)
                self._detail = ""
        if self.wrt_client:
            self.wrt_client.stopTest(test, timestamp=self.test_end_time[test],
                                     duration=elapsed_time)
        unittest2.TestResult.stopTest(self, test)

    def addExpectedFailure(self, test, err=None, details=None):
        if self.wrt_client:
            self.wrt_client.xfailTest(test, err, details)
        if self.showAll:
            self.stream.write("expected failure")
        elif self.dots:
            self.stream.write("x")
            self.stream.flush()
        details = self._err_details_to_string(test, err, details)
        self.expectedFailures.append((self.getDescription(test), details))

    def addError(self, test, err=None, details=None):
        if self.wrt_client:
            self.wrt_client.failTest(test, err, details)
        reason = self._process_reason(test, details)
        if self.showAll:
            self.stream.write("ERROR")
            if reason:
                self.stream.write(' %s ' % reason)
        elif self.dots:
            self.stream.write('E')
            self.stream.flush()
        self.print_or_append(test, err, details, self.errors)
        if self.failfast:
            self.stop()

    def addFailure(self, test, err=None, details=None):
        if self.wrt_client:
            self.wrt_client.failTest(test, err, details)
        reason = self._process_reason(test, details)
        if self.showAll:
            self.stream.write("FAIL")
            if reason:
                self.stream.write(' %s ' % reason)
        elif self.dots:
            self.stream.write('F')
            self.stream.flush()
        self.print_or_append(test, err, details, self.failures)
        if self.failfast:
            self.stop()

    def addSkip(self, test, reason=None, details=None):
        if reason is None:
            reason = details.get('reason', None)
            if reason is None:
                reason = 'No reason given'
            else:
                reason = reason.as_text()
        if self.wrt_client:
            self.wrt_client.skipTest(test, reason)
        if self.showAll:
            self.stream.write("skipped %s" % reason)
        elif self.dots:
            self.stream.write("s")
            self.stream.flush()
        # testtools does it strangely. do it less strangely
        self.skipped.append((self.getDescription(test), reason))

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
        self.unexpectedSuccesses.append(self.getDescription(test))

    # fixture related methods
    def startFixture(self, fixture):
        self.fixtures += 1
        self.test_start_time[fixture] = time.time()
        # update well-rested-tests with in-progress state and start time
        if self.showAll:
            self.stream.write("%s ... " % self.getDescription(fixture))

    def stopFixture(self, fixture):
        """also print out test duration"""
        self.test_end_time[fixture] = time.time()
        elapsed_time = self.test_end_time[fixture] - self.test_start_time[fixture]
        if self.showAll:
            self.stream.writeln(" in %.3f" % elapsed_time)
        if self.early_details:
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
        reason = None
        if details and 'reason' in details:
            reason = details.pop('reason').as_text()
            if reason not in self.reasons:
                self.reasons[reason] = 1
            else:
                self.reasons[reason] += 1
        if self.showAll:
            self.stream.write("warning")
            if reason:
                self.stream.write(' %s ' % reason)
        elif self.dots:
            self.stream.write('w')
            self.stream.flush()
        self.print_or_append(fixture, err, details, self.warnings)

    def addInfo(self, fixture):
        """
        Use this method if you'd like to print a fixture success.
        """
        # upload to well-rested-tests
        if self.showAll:
            self.stream.write("ok")
        elif self.dots:
            self.stream.write(',')
            self.stream.flush()
        self.infos.append(self.getDescription(fixture))

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
        if self.failing_file:
            if hasattr(test, 'id'):
                writable = test.id()
            else:
                writable = test
            self.failing_file.writeln(writable)
        description = self.getDescription(test)
        if self.early_details:
            list.append(description)
            self._detail = details
        else:
            list.append((description, details))

    def printErrors(self):
        if self.dots or self.showAll:
            self.stream.writeln()
        if not self.early_details:
            self.printErrorList('WARNING', self.warnings)
            self.printErrorList('ERROR', self.errors)
            self.printErrorList('FAIL', self.failures)

    def printErrorList(self, flavour, errors):
        for test, err in errors:
            self.stream.writeln(self.separator1)
            self.stream.writeln("%s: %s" % (flavour, test))
            self.stream.writeln(self.separator2)
            self.stream.writeln("%s" % err)

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
        if self.reasons:
            reasons = ['%s=%s' % (k, v) for k, v in self.reasons.items()]
            summary.append(" (%s)" % (", ".join(reasons)))
        if infos:
            summary.append(" (%s)\n" % (", ".join(infos),))
        return "\n".join(summary)

