import logging
import testresources
import testtools
import fixtures
import unittest2


__all__ = [
    'ReportingTestResourceManager',
    'ErrorTolerantOptimisedTestSuite'
]


class DetailCollector():

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
                'traceback', testtools.content.TracebackContent(
                    (exc_type, exc_val, exc_tb), self.TRM))
            self.result.addWarning(
                str(self.TRM), details=self.log_fixture.getDetails())
        else:
            self.result.addInfo(str(self.TRM))
        self.result.stopFixture(self.TRM)
        self.log_fixture.cleanUp()
        self.TRM.appendix = ''


class ReportingTestResourceManager(testresources.TestResourceManager):
    # TODO: move the DetailCollector to a method that isn't recursive?
    """Fix some problems where testresources.TestResourceManager doesn't
    actually sent the result all the way through the process.

    Use context manager to report results of finishedWith and getResource
    to the result."""

    def __init__(self, level=logging.INFO):
        super(ReportingTestResourceManager, self).__init__()
        self.log_level = level
        self.logger = logging.getLogger(self.__class__.__name__)
        self.appendix = ''

    def __str__(self):
        return self.appendix + ' ' + self.__class__.__name__

    # fix _make_all, _clean_all, and isDirty to use result and
    # inject the context manager to manage results
    def _make_all(self, result):
        """Make the dependencies of this resource and this resource."""
        dependency_resources = {}
        for name, resource in self.resources:
            dependency_resources[name] = resource.getResource(result)
        with DetailCollector(self, result, 'Creating'):
            resource = self.make(dependency_resources)
        for name, value in dependency_resources.items():
            setattr(resource, name, value)
        return resource

    def _clean_all(self, resource, result):
        """Clean the dependencies from resource, and then resource itself."""
        # with DetailCollector(self, result, '-clean-all'):
        with DetailCollector(self, result, 'Destroying'):
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
        with DetailCollector(self, result, 'Resetting'):
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


class ErrorTolerantOptimisedTestSuite(testresources.OptimisingTestSuite, unittest2.TestSuite):
    # TODO: abort suite if running too long
    # TODO: filter on failing (tests run but not passed)
    # TODO: filter on existing (tests reported but not run)
    # TODO: implement reporting test existence to well-rested-tests
    # TODO: --parallel
    """
    Catch errors thrown by resource creation / destruction,
    fail the affected test, and keep going.
    This requires dynamic tracking of the current resources
    """

    current_resources = set()

    @staticmethod
    def parserOptions(parser):
        # reminder, add sub-heading when adding arguments
        # group = parser.add_argument_group('ErrorTolerantOptimisedTestSuite')
        return parser

    @staticmethod
    def expectedHelpText(cls):
        return ""

    @staticmethod
    def factory(cls, object):
        return cls()

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

    def registerTests(self):
        # report on existence of tests to well-rested-tests
        pass

    def run(self, result):
        self.sortTests()
        self.registerTests()
        for test in self._tests:
            if result.shouldStop:
                break
            resources = getattr(test, 'resources', [])
            new_resources = set()
            for name, resource in resources:
                new_resources.update(resource.neededResources())
            try:
                self.switch(new_resources, result)
            except Exception:
                # the exception has been reported on the fixture,
                # but we still want to report failed for the test itself
                # so that it will show up in --failing
                result.startTest(test)
                result.addFailure(test, details={
                    'reason': testtools.content.text_content(
                        'Error handling fixtures')})
                result.stopTest(test)
                continue
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
        """This will be used with --failing or --existing."""
        filtered = []
        for test in suite._tests:
            if test.id() in test_ids:
                filtered.append(test)
        suite._tests = filtered
        return suite
