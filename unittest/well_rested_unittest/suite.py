import logging
import testresources
import testtools
import fixtures
import unittest2
import itertools
import traceback
import os
import sys
from threading import Thread
import subprocess
import content


__all__ = [
    'ReportingTestResourceManager',
    'ErrorTolerantOptimisedTestSuite',
    'DetailCollector',
]

__unittest = True

testresources.__unittest = True


class RoundRobinList(list):

    def __init__(self, num):
        for i in range(num):
            self.append([])
        self._iter = itertools.cycle(self)

    def extend(self, list):
        self._iter.next().extend(list)

    def distribute(self, list):
        for item in list:
            self._iter.next().append(item)


class DetailCollector(object):

    def __init__(self, TRM, result, appendix):
        self.TRM = TRM
        self.appendix = appendix
        if not isinstance(result, testtools.TestResult):
            raise Exception(
                "%s is not a testtools.TestResult" % result.__class__)
        self.result = result

    def __enter__(self):
        FORMAT = '%(asctime)s [%(levelname)s] %(name)s %(lineno)d: %(message)s'  # noqa
        self.log_fixture = fixtures.FakeLogger(format=FORMAT)
        self.log_fixture.setUp()
        self.TRM.appendix = self.appendix
        self.result.startFixture(self.TRM)

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_val:
            self.log_fixture.addDetail(
                'traceback', content.traceback_content(
                    (exc_type, exc_val, exc_tb), self.TRM))
            self.log_fixture.addDetail(
                'reason', content.text_content(exc_val.__class__.__name__))
            self.result.addWarning(
                self.TRM, details=self.log_fixture.getDetails())
        else:
            self.result.addInfo(self.TRM)
        self.result.stopFixture(self.TRM)
        self.log_fixture.cleanUp()
        self.TRM.appendix = ''


class ReportingTestResourceManager(testresources.TestResourceManager):
    """Fix some problems where testresources.TestResourceManager doesn't
    actually sent the result all the way through the process.

    Use context manager to report results of finishedWith and getResource
    to the result."""
    collector_class = DetailCollector

    def __init__(self, level=logging.INFO):
        super(ReportingTestResourceManager, self).__init__()
        self.log_level = level
        self.logger = logging.getLogger(self.__class__.__name__)
        self.appendix = ''
        self.worker = os.getenv('WRT_WORKER_ID', None)

    def __str__(self):
        return self.appendix + '_' + self.__class__.__name__

    def id(self):
        return self.__str__()

    # fix _make_all, _clean_all, and isDirty to use result and
    # inject the context manager to manage results
    def _make_all(self, result):
        """Make the dependencies of this resource and this resource."""
        dependency_resources = {}
        for name, resource in self.resources:
            dependency_resources[name] = resource.getResource(result)
        with self.collector_class(self, result, 'Creating'):
            resource = self.make(dependency_resources)
        for name, value in dependency_resources.items():
            setattr(resource, name, value)
        return resource

    def _clean_all(self, resource, result):
        """Clean the dependencies from resource, and then resource itself."""
        # with DetailCollector(self, result, '-clean-all'):
        with self.collector_class(self, result, 'Destroying'):
            self.clean(resource)
        for name, manager in self.resources:
            manager.finishedWith(getattr(resource, name), result)

    def reset(self, old_resource, result=None):
        """Core logic stays the same as in parent class, just
        wrap _reset in DetailCollector. We can get rid of signalling the
        result because the DetailCollector does that for us.
        """
        # Core logic:
        #  - if neither we nor any parent is dirty, do nothing.
        # otherwise
        #  - emit a signal to the test result
        #  - reset all dependencies all, getting new attributes.
        #  - call self._reset(old_resource, dependency_attributes)
        #    [the default implementation does a clean + make]
        if not self.isDirty():
            return old_resource
        dependency_resources = {}
        for name, mgr in self.resources:
            dependency_resources[name] = mgr.reset(
                getattr(old_resource, name), result)
        with self.collector_class(self, result, 'Resetting'):
            resource = self._reset(old_resource, dependency_resources)
        for name, value in dependency_resources.items():
            setattr(resource, name, value)
        return resource

    def isDirty(self, result=None):
        """Return True if this managers cached resource is dirty.

        Calling when the resource is not currently held has undefined
        behaviour.
        """
        if self._dirty:
            return True
        for name, mgr in self.resources:
            if mgr.isDirty(result):
                return True
            res = mgr.getResource(result)
            try:
                if res is not getattr(self._currentResource, name):
                    return True
            finally:
                mgr.finishedWith(res, result)


class ParallelSuite(unittest2.TestSuite):

    def __init__(self, tests, worker, testNames, debug=False):
        self._tests = tests
        from loader import AutoDiscoveringTestLoader
        self.worker = worker
        self.testNames = testNames
        self.debug = debug

    def run(self, result):
        if not self._tests:
            return result

        # write the tests out to a file so the command line won't be too long
        with open('.worker%s' % self.worker, 'wb') as f:
            f.write('\n'.join(self._tests))

        # build command -
        # don't pipe stderr to stdout, or the dots won't be visible in real-time
        command = [
            'WRT_WORKER_ID=%s' % self.worker,
            result.progName,
        ]
        if self.debug:
            command.append('--debug')
        command.extend(result.worker_flags())
        command.append('--from-file .worker%s' % self.worker)
        command.append(' '.join(self.testNames))
        command = ' '.join(command)
        if self.debug:
            result.stream.writeln(command)

        # output will contain dumped json of the worker's results
        subprocess.call(command, shell=True)
        with open('.worker%s' % self.worker, 'rb') as f:
            result.absorbResult(f.read())


class ErrorTolerantOptimisedTestSuite(testresources.OptimisingTestSuite, unittest2.TestSuite):
    # TODO: abort suite if running too long
    """
    Catch errors thrown by resource creation / destruction,
    fail the affected test, and keep going.
    This requires dynamic tracking of the current resources
    """

    current_resources = set()

    @staticmethod
    def parserOptions(parser):
        group = parser.add_argument_group('ErrorTolerantOptimisedTestSuite')
        group.add_argument('--list', dest='list_tests',
                           action='store_true',
                           help='Output list of tests, then exist.')
        group.add_argument('--reverse', dest='reverse',
                           action='store_true',
                           help='Reverse order of tests.')
        group.add_argument('--debug', dest='debug',
                           action='store_true',
                           help='Debug the suite functionality.')
        group.add_argument('--parallel', dest='parallel',
                           action='store_true',
                           help='Run tests in parallel (up to --concurrency threads).')
        group.add_argument('--concurrency', dest='concurrency', default=2,
                           help='Number of parallel threads (default 2), or `auto`.')
        return parser

    def set_flags(self, object):
        # when the suite is created by the loader, flags are not set automatically,
        # so use this method
        self.parallel = object.parallel if hasattr(object, 'parallel') else False
        self.concurrency = object.concurrency if hasattr(object, 'concurrency') else 2
        self.list_tests = object.list_tests if hasattr(object, 'list_tests') else False
        self.debug = object.debug if hasattr(object, 'debug') else False
        self.reverse = object.reverse if hasattr(object, 'reverse') else False
        # these two are grabbed from the program object
        self.testNames = object.testNames
        self.progName = object.progName

    @staticmethod
    def expectedHelpText(cls):
        return """
%s:
  --list                Output list of tests, then exist.
  --reverse             Reverse order of tests.
  --debug               Debug the suite functionality.
  --parallel            Run tests in parallel (up to --concurrency threads).
  --concurrency CONCURRENCY
                        Number of parallel threads (default 2), or `auto`.
""" % cls.__name__

    def __init__(self, tests, concurrency=2, parallel=False, list_tests=False,
                 debug=False, reverse=False, testNames=[]):
        super(ErrorTolerantOptimisedTestSuite, self).__init__(tests)
        self.list_tests = list_tests
        self.debug = debug
        self.reverse = reverse
        self.parallel = parallel
        self.concurrency = concurrency
        self.testNames = testNames
        self.worker = os.getenv('WRT_WORKER_ID', None)

    def id(self):
        if self.concurrency and self.concurrency != 'auto':
            return 'Concurrency Suite %s' % self.concurrency
        elif self.worker:
            return 'Worker %s' % self.worker
        return 'Unknown %s' % self.__class__.__name__

    def switch(self, new_resource_set, result):
        """Switch from self.current_resources to 'new_resource_set'.

        Tear down resources in self.current_resources that aren't in
        new_resource_set and set up resources that are in new_resource_set but
        not in self.current_resources.

        :param result: TestResult object to report activity on.
        """
        new_resources = new_resource_set - self.current_resources
        old_resources = self.current_resources - new_resource_set
        for resource in old_resources:
            resource.finishedWith(resource._currentResource, result)
            self.current_resources.discard(resource)
        for resource in new_resources:
            resource.getResource(result)
            self.current_resources.add(resource)

    def list(self):
        return [test.id() for test in self._tests]

    def run(self, result):
        self.sortTests()  # will sub-divide for parallelization and list if parallel
        if self.reverse:
            self._tests.reverse()
        if self.list_tests:
            for test in self.list():
                result.stream.writeln(test)
            exit(0)
        elif self.parallel:
            threads = [Thread(
                target=suite.run,
                args=(result,))
                for suite in self._tests]
            map(lambda t: t.start(), threads)
            map(lambda t: t.join(), threads)
        else:
            result.registerTests(self._tests)
            for test in self._tests:
                if result.shouldStop:
                    raise KeyboardInterrupt('auto')
                resources = getattr(test, 'resources', [])
                new_resources = set()
                for name, resource in resources:
                    new_resources.update(resource.neededResources())
                try:
                    self.switch(new_resources, result)
                except Exception as e:
                    if self.debug:
                        # if the entire stack is in unittest, then we want to
                        # print it, if not, it's been captured in the fixture's details
                        exc_info = sys.exc_info()
                        tb = exc_info[2]
                        has_non_unittest = False
                        while tb:
                            if '__unittest' in tb.tb_frame.f_globals:
                                tb = tb.tb_next
                            else:
                                has_non_unittest = True
                                break
                        if not has_non_unittest:
                            traceback.print_tb(exc_info[2])
                            result.stream.writeln(str(e))

                    # the exception has been reported on the fixture,
                    # but we still want to report failed for the test itself
                    # so that it will show up in --failing
                    result.startTest(test)
                    result.addError(test, details={
                        'reason': content.text_content(
                            'Error handling fixtures')})
                    result.stopTest(test)
                    continue  # next test
                test(result)
            try:
                self.switch(set(), result)
            except Exception:
                # this exception has already been reported, ignore it.
                pass
        return result

    def addTest(self, test_case_or_suite):
        """Add `test_case_or_suite`, unwrapping standard TestSuites.

        This means that any containing unittest.TestSuites will be removed,
        while any custom test suites will be 'distributed' across their
        members. Thus addTest(CustomSuite([a, b])) will result in
        CustomSuite([a]) and CustomSuite([b]) being added to this suite.
        """
        try:
            tests = iter(test_case_or_suite)
        except TypeError:
            unittest2.TestSuite.addTest(self, test_case_or_suite)
            return
        if test_case_or_suite.__class__ in (unittest2.TestSuite,
                                            testresources.OptimisingTestSuite,
                                            self.__class__):
            for test in tests:
                self.addTest(test)
        else:
            for test in tests:
                unittest2.TestSuite.addTest(
                    self, test_case_or_suite.__class__([test]))

    def filter_by_ids(suite, test_ids):
        """
        Used by loader when --from-file is set.
        Will ignore any fixture names that are in the --from-file.
        Will ignore any previously failing tests not also discovered from the testNames
        """
        filtered = []
        for test in suite._tests:
            if test.id() in test_ids:
                filtered.append(test)
        suite._tests = filtered
        return suite

    def sortTestsByConcurrency(self):
        buckets = {}
        for test in self._tests:
            concurrency = test.concurrency if hasattr(test, 'concurrency') else 1
            buckets.setdefault(concurrency, [])
            buckets[concurrency].append(test)
        self._tests = []
        self.parallel = False
        keys = buckets.keys()
        keys.sort()
        keys.reverse()
        self._tests.extend([ErrorTolerantOptimisedTestSuite(
                buckets[c], concurrency=c, debug=self.debug, parallel=True,
                list_tests=self.list_tests, reverse=self.reverse, testNames=self.testNames)
            for c in keys])
        if self.list_tests:
            for suite in self._tests:
                sys.stderr.write('CONCURRENCY GROUP %s:\n' % suite.concurrency)
                try:
                    suite.sortTests()
                except SystemExit:
                    pass
            exit(0)

    def sortTests(self):
        """Attempt to topographically sort the contained tests.

        This function biases to reusing a resource: it assumes that resetting
        a resource is usually cheaper than a teardown + setup; and that most
        resources are not dirtied by most tests.

        Feel free to override to improve the sort behaviour.
        """
        if self.concurrency == 'auto':
            self.sortTestsByConcurrency()
            return

        # We group the tests by the resource combinations they use,
        # since there will usually be fewer resource combinations than
        # actual tests and there can never be more: This gives us 'nodes' or
        # 'resource_sets' that represent many tests using the same set of
        # resources.
        resource_set_tests = testresources.split_by_resources(self._tests)
        # Partition into separate sets of resources, there is no ordering
        # preference between sets that do not share members. Rationale:
        # If resource_set A and B have no common resources, AB and BA are
        # equally good - the global setup/teardown sums are identical. Secondly
        # if A shares one or more resources with C, then pairing AC|CA is
        # better than having B between A and C, because the shared resources
        # can be reset or reused. Having partitioned we can use connected graph
        # logic on each partition.
        resource_set_graph = testresources._resource_graph(resource_set_tests)
        no_resources = frozenset()
        # A list of resource_set_tests, all fully internally connected.
        partitions = testresources._strongly_connected_components(
            resource_set_graph, no_resources)

        if self.parallel:
            result = RoundRobinList(int(self.concurrency))
        else:
            result = []

        for partition in partitions:
            # we process these at the end for no particularly good reason (it
            # makes testing slightly easier).
            if partition == [no_resources]:
                continue
            order = self._makeOrder(partition)
            # Spit this partition out into result
            for resource_set in order:
                result.extend(resource_set_tests[resource_set])
        if self.parallel:
            result.distribute(resource_set_tests[no_resources])
        else:
            result.extend(resource_set_tests[no_resources])

        if self.parallel:
            # sys.stderr.write('%s\n\n' % self._tests)
            self._tests = []
            for worker, batch in enumerate(result):
                worker += 1
                if self.reverse:
                    batch.reverse()
                tests = [test.id() for test in batch]
                if self.list_tests:
                    sys.stderr.write('WORKER %s:\n' % worker)
                    sys.stderr.write('    ')
                    sys.stderr.write('\n    '.join(tests))
                    sys.stderr.write('\n')
                self._tests.append(ParallelSuite(tests, worker, self.testNames, debug=self.debug))
            if self.list_tests:
                exit(0)
        else:
            self._tests = result
