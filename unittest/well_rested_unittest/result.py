import testtools
import unittest2
import requests
import sys
import os
import time
import datetime
import argparse
import wrtclient
import json
import shutil
from threading import Lock
try:
    from blessings import Terminal
except ImportError:
    Terminal = None

__unittest = True


class ColorizedWritelnDecorator(object):
    """Used to decorate file-like objects with a handy 'writeln' method"""
    def __init__(self, stream):
        self.stream = stream
        self.color = None
        self.terminal = Terminal(stream=stream)

    def __getattr__(self, attr):
        if attr in ('stream', '__getstate__', 'set_color', 'write'):
            raise AttributeError(attr)
        return getattr(self.stream, attr)

    def writeln(self, arg=None):
        if arg:
            self.write(arg)
        self.write('\n') # text-mode streams translate to \r\n if needed

    def write(self, arg):
        if arg and arg != '\n':
            self.stream.write(self.terminal.color(self.color))
            self.stream.write(arg)
            self.stream.write(self.terminal.normal)
        elif arg == '\n':
            self.stream.write(arg)

    def set_color(self, color):
        self.color = color


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
        # verbosity options
        # (quiet is verbosity = -1 rather than zero so that it is truthy)
        group.add_argument('-q', '--quiet', dest='verbosity',
                           action='store_const', const=-1,
                           help='Silent output')
        group.add_argument('-d', '--dots', dest='verbosity',
                           action='store_const', const=1,
                           help='print dots (default)')
        group.add_argument('-v', '--verbose', dest='verbosity',
                           action='store_const', const=2,
                           help='Verbose output')
        group.add_argument('-e', '--early-details', dest='verbosity',
                           action='store_const', const=3,
                           help="Print details immediately.")

        group.add_argument('--color', dest='color', action='store_true',
                           help='Colorize parallel result output (default False).')
        group.add_argument('--timestamp', dest='timestamp', action='store_true',
                           help='Include test start-time in output (default False).')
        group.add_argument('--update', dest='update', action='store_true',
                           help="Update previous test run (default False).")
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
            failing_file=object.failing_file if
                hasattr(object, 'failing_file') else '.failing',
            wrt_conf=object.wrt_conf if hasattr(object, 'wrt_conf') else None,
            progName=object.progName,
            color=object.color if hasattr(object, 'color') else False,
            update=object.update if hasattr(object, 'update') else False,
            timestamp=object.timestamp if hasattr(object, 'timestamp') else False,
        )

    @staticmethod
    def expectedHelpText(cls):
        return """
%s:
  -f, --failfast        Stop on first fail or error
  -x, --uxsuccess-not-failure
                        Consider unexpected success a failure (default True).
  -q, --quiet           Silent output
  -d, --dots            print dots (default)
  -v, --verbose         Verbose output
  -e, --early-details   Print details immediately.
  --color               Colorize parallel result output (default False).
  --timestamp           Include test start-time in output (default False).
  --update              Update previous test run (default False).
  -w WRT_CONF, --wrt-conf WRT_CONF
                        path to well-rested-tests config file
""" % cls.__name__

    def __init__(self, failfast=False,
                 uxsuccess_not_failure=False, verbosity=1,
                 failing_file='.failing',
                 wrt_conf=None, progName=None, color=False,
                 update=False, timestamp=False):
        """
        :param failfast: boolean (default False)
        :param uxsuccess_not_failure: boolean (default False)
        :param verbosity: 0 (none, default), 1 (dots),
                          2 (verbose), 3 (early-details)
        :param wrt_conf: path to well-rested-tests config file
        :param progName: so the suite can find out what program name to use for parallelization
        :param color:    boolean (default False) color parallel output streams
        :param update:   boolean (default False) update previous test run
                         Note: update is not needed by workers.
        :param timestamp: Include test start-time in output.
        :return:
        """
        # some initial processing
        self.worker = os.getenv('WRT_WORKER_ID', None)
        self.color = color
        if self.color and not Terminal:
            sys.stderr.write('WARNING: Package `blessings` not installed. '
                             'Results will not be colorized.\n')
            self.color = False
        if self.color and self.worker:
            self.stream = ColorizedWritelnDecorator(sys.stderr)
        else:
            self.stream = unittest2.runner._WritelnDecorator(sys.stderr)

        # initialize all the things
        self.warnings = []
        self.infos = []
        self.fixtures = 0
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
        self.progName = progName
        self.absorbLock = Lock()

        # super
        unittest2.TextTestResult.__init__(self, self.stream, False, verbosity)

        # process the settings
        self.failfast = failfast
        self.uxsuccess_not_failure = uxsuccess_not_failure
        self.failing_file = failing_file
        # worker (ie, parallel) set color and failing_file
        if self.worker:
            self.worker = int(self.worker)
            if self.color:
                self.stream.set_color(self.worker)
            if failing_file:
                self.failing_file += str(self.worker)
        self.early_details = verbosity > 2
        self.showAll = verbosity > 1
        self.dots = verbosity == 1
        self.update = update
        self.timestamp = timestamp
        if wrt_conf:
            self.wrt_conf = wrt_conf
            self.wrt_client = wrtclient.WRTClient(
                wrt_conf, self.stream, debug=False)

    def worker_flags(self):
        """The suite shouldn't need to know what the flags are."""
        # TODO: send run url to worker
        flags = []

        if self.dots:
            flags.append('--dots')
        elif self.early_details:
            flags.append('--early-details')
        elif self.showAll:
            flags.append('-v')
        else:
            flags.append('-q')

        if self.color:
            flags.append('--color')
        if self.timestamp:
            flags.append('--timestamp')
        return flags

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

    def format_time(self, timestamp):
        return datetime.datetime.fromtimestamp(timestamp).strftime('%Y-%m-%dT%H:%M:%S')

    # run related methods
    def startTestRun(self):
        self.start_time = time.time()
        if self.showAll and not self.worker:
            self.stream.writeln(self.separator2)
        if self.wrt_client and not self.worker:
            # TODO: if master, fetch previous run and --update
            # TODO: if worker and --run-url, update run provided
            try:
                self.wrt_client.startTestRun(
                    timestamp=self.format_time(self.start_time))
            except requests.exceptions.ConnectionError as e:
                self.stream.writeln(
                    'ERROR: Unable to connect to the well-rested-tests server\n%s'
                    % e.message)
                exit(1)
        if self.failing_file:
            mode = 'ab' if self.update else 'wb'
            self.failing_file = unittest2.runner._WritelnDecorator(
                open(self.failing_file, mode))
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
            }, sort_keys=True, indent=4, separators=(',', ': '))
            with open('.worker%s' % self.worker, 'wb') as f:
                f.write(output + '\n')
        elif self.dots or self.showAll:
                self.printErrors()
                self.printSummary()

    def absorbResult(self, stdout):
        with self.absorbLock:
            try:
                other_result = json.loads(stdout)
            except ValueError:
                self.stream.writeln(stdout)
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
            if self.failing_file:
                with open('.failing%s' % other_result['worker']) as src:
                    shutil.copyfileobj(src, self.failing_file)

    # test related methods
    def getDescription(self, test):
        """Let's not use docstrings as test names"""
        output = ''
        if self.worker:
            output = output + '(%s) ' % self.worker
        output = output + (test.id() if hasattr(test, 'id') else str(test))
        return output

    def startTest(self, test):
        self.test_start_time[test] = time.time()
        if self.wrt_client:
            self.wrt_client.startTest(
                test, timestamp=self.format_time(self.test_start_time[test]))
        if self.showAll:
            if self.timestamp:
                self.stream.write(self.format_time(self.test_start_time[test]) + ' ')
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
            self.wrt_client.stopTest(
                test, timestamp=self.format_time(self.test_end_time[test]),
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
            if self.timestamp:
                self.stream.write(self.format_time(self.test_start_time[fixture]) + ' ')
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

