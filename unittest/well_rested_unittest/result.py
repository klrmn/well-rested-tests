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
import content

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
        group.add_argument('-a', '--abort-on-fixture-fail-percent',
                           dest='fail_percent', default=0,
                           help="Abort test run if this percentage of tests "
                                "have failed due to fixture failure.")
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
        group.add_argument('--run-url', dest='run_url', action='store',
                           default=None,
                           help='URL of run to be updated (default None).')
        group.add_argument('--timestamp', dest='timestamp', action='store_true',
                           help='Include test start-time in output (default False).')
        group.add_argument('--update', dest='update', action='store_true',
                           help="Update previous test run (default False).")
        group.add_argument('-w', '--wrt-conf', dest='wrt_conf',
                           help='Path to well-rested-tests config file')
        group.add_argument('--storage', dest='storage', action='store',
                           default=None,
                           help='Path at which to store details.')
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
            run_url=object.run_url if hasattr(object, 'run_url') else None,
            fail_percent=object.fail_percent if hasattr(object, 'fail_percent') else 0,
            storage=object.storage if hasattr(object, 'storage') else None,
            debug=object.debug if hasattr(object, 'debug') else 0,
        )

    @staticmethod
    def expectedHelpText(cls):
        return """
%s:
  -f, --failfast        Stop on first fail or error
  -a FAIL_PERCENT, --abort-on-fixture-fail-percent FAIL_PERCENT
                        Abort test run if this percentage of tests have failed
                        due to fixture failure.
  -x, --uxsuccess-not-failure
                        Consider unexpected success a failure (default True).
  -q, --quiet           Silent output
  -d, --dots            print dots (default)
  -v, --verbose         Verbose output
  -e, --early-details   Print details immediately.
  --color               Colorize parallel result output (default False).
  --run-url RUN_URL     URL of run to be updated (default None).
  --timestamp           Include test start-time in output (default False).
  --update              Update previous test run (default False).
  -w WRT_CONF, --wrt-conf WRT_CONF
                        Path to well-rested-tests config file
  --storage STORAGE     Path at which to store details.
""" % cls.__name__

    def __init__(self, failfast=False,
                 uxsuccess_not_failure=False, verbosity=1,
                 failing_file='.failing',
                 wrt_conf=None, progName=None, color=False,
                 update=False, timestamp=False, run_url=None,
                 fail_percent=0, storage=None, debug=0):
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
        :param run_url:   URL of run to be updated.
        :param fail_percent:
        :param storage:  Path at which to store details
        :param debug:    debug > 1 causes debug printing in wrtconf
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
        self._expected_tests = 0

        # super
        unittest2.TextTestResult.__init__(self, self.stream, False, verbosity)

        # process the settings
        self.failfast = failfast
        self.fail_percent = int(fail_percent)
        self.uxsuccess_not_failure = uxsuccess_not_failure
        self.failing_file = failing_file
        self.storage = storage
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
        if self.update and not run_url:
            run_url = 'previous'
        self.timestamp = timestamp
        if wrt_conf:
            self.wrt_conf = wrt_conf
            self.wrt_client = wrtclient.WRTClient(
                wrt_conf, self.stream, debug=debug > 1, run_url=run_url)

    def worker_flags(self):
        """The suite shouldn't need to know what the flags are."""
        flags = []

        if self.failfast:
            flags.append('--failfast')
        if self.dots:
            flags.append('--dots')
        elif self.early_details:
            flags.append('-e')
        elif self.showAll:
            flags.append('-v')
        else:
            flags.append('-q')

        if self.color:
            flags.append('--color')
        if self.timestamp:
            flags.append('--timestamp')
        if self.fail_percent:
            flags.append('-a %s' % self.fail_percent)
        if self.wrt_conf:
            flags.extend([
                '--wrt-conf %s' % self.wrt_conf,
                '--run-url %s' % self.wrt_client._run_url])
        if self.storage:
            flags.append('--storage %s/%s'
                         % (self.storage, self.format_time_for_directory(self.start_time)))
        return flags

    @staticmethod
    def _details_to_str(details):
        from testtools.testresult.real import _details_to_str
        if details:
            return _details_to_str(details, special='traceback')
        return None

    @staticmethod
    def _err_to_details(test, err, details):
        if err:
            return {
                'traceback': content.traceback_content(err, test),
                'reason': content.text_content(err[1].__class__.__name__),
            }
        return details

    def _process_reason(self, details):
        reason = None
        if details:
            if 'reason' in details:
                reason = details.pop('reason').as_text()
            if reason not in self.reasons:
                self.reasons[reason] = 1
            else:
                self.reasons[reason] += 1
        return reason

    def format_time(self, timestamp):
        return datetime.datetime.fromtimestamp(timestamp).strftime('%Y-%m-%dT%H:%M:%S')

    def format_time_for_directory(self, timestamp):
        return datetime.datetime.fromtimestamp(timestamp).strftime('%Y-%m-%dT%H_%M_%S')

    # run related methods
    def registerTests(self, tests):
        filtered_tests = [test for test in tests
                          if isinstance(test, unittest2.TestCase)]
        self._expected_tests = len(filtered_tests)
        if self.wrt_conf:
            self.wrt_client.registerTests(filtered_tests)

    def startTestRun(self):
        self.start_time = time.time()
        if self.showAll and not self.worker:
            self.stream.writeln(self.separator2)
        if self.wrt_client and not self.worker:
            try:
                self.wrt_client.startTestRun(
                    timestamp=self.format_time(self.start_time))
            except requests.exceptions.ConnectionError as e:
                self.stream.writeln(
                    'ERROR: Unable to connect to the well-rested-tests server\n%s'
                    % e.message)
                exit(1)
        if self.failing_file:
            self.failing_file = unittest2.runner._WritelnDecorator(
                open(self.failing_file, 'wb'))
        if self.showAll and self.wrt_client and not self.worker:
            self.stream.writeln("Watch progress at: %s" % self.run_url)
            self.stream.writeln(self.separator2)
        unittest2.TextTestResult.startTestRun(self)
        # modify self.storage for the current test run
        if self.storage:
            # ensure the directories exist
            path = self.storage
            try:
                os.mkdir(path)
            except os.error:  # already exists
                pass
            if self.worker:  # self.storage already has timestamp
                path = os.path.join(path, str(self.worker))
                try:
                    os.mkdir(path)
                except os.error:  # already exists
                    pass
            else:
                path = os.path.join(path, self.format_time_for_directory(self.start_time))
                try:
                    os.mkdir(path)
                except os.error:  # already exists
                    pass
            self.storage = path

    def stopTestRun(self, abort=False):
        self.end_time = time.time()
        elapsed_time = self.end_time - self.start_time
        if abort:
            status='aborted'
        elif self.wasSuccessful():
            status='pass'
        else:
            status='fail'
        if self.wrt_client and not self.worker:
            self.wrt_client.stopTestRun(
                timestamp=self.format_time(self.end_time),
                status=status)
        testtools.TestResult.stopTestRun(self)
        if self.failing_file:
            self.failing_file.close()
            if status == 'aborted':
                try:
                    with open('%s.bak' % self.failing_file, 'rb') as src:
                        shutil.copyfileobj(src, self.failing_file)
                except IOError:
                    pass
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
                'reasons': self.reasons,
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
            self.infos.extend(other_result['infos'])
            self.warnings.extend(other_result['warnings'])
            self.testsRun += other_result['testsRun']
            self.fixtures += other_result['fixtures']
            # json changed None to null, change it back
            null = other_result.pop('null', None)
            if null:
                other_result['reasons'][None] = null
            for reason in other_result['reasons']:
                if reason in self.reasons:
                    self.reasons[reason] += other_result['reasons'][reason]
                else:
                    self.reasons[reason] = other_result['reasons'][reason]
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
        if not isinstance(test, unittest2.TestCase):
            return
        self.test_start_time[test.id()] = time.time()
        if self.wrt_client:
            self.wrt_client.startTest(
                test, timestamp=self.format_time(self.test_start_time[test.id()]))
        if self.showAll:
            if self.timestamp:
                self.stream.write(self.format_time(self.test_start_time[test.id()]) + ' ')
            self.stream.write('%s ... ' % self.getDescription(test))
        unittest2.TestResult.startTest(self, test)

    def stopTest(self, test):
        """also print out test duration"""
        if not isinstance(test, unittest2.TestCase):
            return
        self.test_end_time[test.id()] = time.time()
        elapsed_time = self.test_end_time[test.id()] - self.test_start_time[test.id()]
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
                test, timestamp=self.format_time(self.test_end_time[test.id()]),
                duration=elapsed_time)
        unittest2.TestResult.stopTest(self, test)

    def addExpectedFailure(self, test, err=None, details=None):
        details = self._err_to_details(test, err, details)
        reason = self._process_reason(details)
        if self.wrt_client:
            details = self.wrt_client.markTestStatus(
                test, 'xfail', details=details, reason=reason)
        if self.showAll:
            self.stream.write("expected failure")
        elif self.dots:
            self.stream.write("x")
            self.stream.flush()
        details = self._details_to_str(details)
        self.expectedFailures.append((self.getDescription(test), details))

    def addError(self, test, err=None, details=None):
        details = self._err_to_details(test, err, details)
        reason = self._process_reason(details)
        if self.wrt_client:
            details = self.wrt_client.markTestStatus(
                test, 'fail', details=details, reason=reason)
        if self.showAll:
            self.stream.write("ERROR")
            if reason:
                self.stream.write(' %s ' % reason)
        elif self.dots:
            self.stream.write('E')
            self.stream.flush()
        self.print_or_append(test, details, reason, self.errors)
        if self.failfast:
            self.stop()
        # this isn't my favorite place to put this, but i can't override
        # self.shouldStop with @property shouldStop.
        elif self.fail_percent and self._expected_tests and \
                'Error handling fixtures' in self.reasons:
            if self.reasons['Error handling fixtures'] > (
                    self._expected_tests * (self.fail_percent / 100)):
                self.stop()

    def addFailure(self, test, err=None, details=None):
        details = self._err_to_details(test, err, details)
        reason = self._process_reason(details)
        if self.wrt_client:
            details = self.wrt_client.markTestStatus(
                test, 'fail', details=details, reason=reason)
        if self.showAll:
            self.stream.write("FAIL")
            if reason:
                self.stream.write(' %s ' % reason)
        elif self.dots:
            self.stream.write('F')
            self.stream.flush()
        self.print_or_append(test, details, reason, self.failures)
        if self.failfast:
            self.stop()

    def addSkip(self, test, reason=None, details=None):
        if reason is None:
            reason = self._process_reason(details)
        if self.wrt_client:
            self.wrt_client.markTestStatus(test, 'skip', reason=reason)
        if self.showAll:
            self.stream.write("skipped %s" % reason)
        elif self.dots:
            self.stream.write("s")
            self.stream.flush()
        # testtools does it strangely. do it less strangely
        self.skipped.append((self.getDescription(test), reason))

    def addSuccess(self, test, details=None):
        if self.wrt_client:
            self.wrt_client.markTestStatus(test, 'pass')
        if self.showAll:
            self.stream.write("ok")
        elif self.dots:
            self.stream.write('.')
            self.stream.flush()

    def addUnexpectedSuccess(self, test, details=None):
        if self.wrt_client:
            self.wrt_client.markTestStatus(test, 'xpass')
        if self.showAll:
            self.stream.write("unexpected success")
        elif self.dots:
            self.stream.write("u")
            self.stream.flush()
        self.unexpectedSuccesses.append(self.getDescription(test))

    # fixture related methods
    def startFixture(self, fixture):
        self.fixtures += 1
        fix_id = fixture.id()
        self.test_start_time[fix_id] = time.time()
        if self.wrt_conf:
            self.wrt_client.startFixture(
                fixture, self.format_time(self.test_start_time[fix_id]))
        if self.showAll:
            if self.timestamp:
                self.stream.write(self.format_time(self.test_start_time[fix_id]) + ' ')
            self.stream.write("%s ... " % self.getDescription(fixture))

    def stopFixture(self, fixture):
        fix_id = fixture.id()
        self.test_end_time[fix_id] = time.time()
        elapsed_time = self.test_end_time[fix_id] - self.test_start_time[fix_id]
        if self.wrt_conf:
            self.wrt_client.stopFixture(
                fixture, self.format_time(self.test_end_time[fixture.id()]), elapsed_time)
        if self.showAll:
            self.stream.writeln(" in %.3f" % elapsed_time)
        if self.early_details:
            if self._detail:
                self.stream.writeln(self.separator1)
                self.stream.writeln(self._detail)
                self.stream.writeln(self.separator2)
                self._detail = ""

    def addWarning(self, fixture, err=None, details=None):
        """
        Use this method if you'd like to print a fixture warning
        without having it effect the outcome of the test run.
        """
        details = self._err_to_details(fixture, err, details)
        reason = self._process_reason(details)
        if self.wrt_conf:
            details = self.wrt_client.markFixtureStatus(
                fixture, 'fail', details, reason)
        if self.showAll:
            self.stream.write("warning")
            if reason:
                self.stream.write(' %s ' % reason)
        elif self.dots:
            self.stream.write('w')
            self.stream.flush()
        self.print_or_append(fixture, details, reason, self.warnings)

    def addInfo(self, fixture):
        """
        Use this method if you'd like to print a fixture success.
        """
        if self.wrt_conf:
            self.wrt_client.markFixtureStatus(fixture, 'pass')
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

    def print_or_append(self, test, details, reason, list):
        if self.storage:
            for name, value in details.items():
                attachment = None
                if value.content_type == content.URL:
                    continue  # urls pass-thru
                else:
                    if value.content_type.type in ['image', 'application']:
                        tp = value.content_type.subtype
                        attachment = value.iter_bytes()
                    elif value.content_type.type == 'text':
                        tp = value.content_type.type
                        attachment = value.as_text().strip()
                    if not attachment:
                        continue  # empty attachments pass thru
                    # get rid of weird stuff in pythonlogging name
                    if ":''" in name:
                        details.pop(name)
                        name = name.replace(":''", "")
                    name = name.replace(":''", "")
                    filename = '%s-%s.%s' % (test.id(), name, tp)
                    # don't overwrite files for fixtures
                    if list == self.warnings:
                        filename = '%s-%s' % (self.test_start_time[test.id()], filename)
                    path = '%s/%s/%s' % (self.storage, timestamp, filename)
                    with open(path, 'wb') as h:
                        h.write(attachment)
                    details[name] = content.url_content(path)
        details = self._details_to_str(details)
        if self.failing_file:
            self.failing_file.writeln(test.id())
        description = self.getDescription(test)
        if self.early_details:
            list.append(description)
            self._detail = details
        else:
            list.append((description, details or reason))

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
        if self.wrt_conf:
            summary.append(self.run_url)
        return "\n".join(summary)

    @property
    def run_url(self):
        if not self.wrt_conf:
            return None
        return self.wrt_client._run_url.replace('api/', '').replace('s/', '/')
