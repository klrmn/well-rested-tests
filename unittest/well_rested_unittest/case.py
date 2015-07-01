import testtools
import unittest2
import fixtures
import logging
import time
import os
import datetime
from types import *  # noqa
from unittest.util import safe_repr
from testresources import setUpResources, tearDownResources, _get_result

__unittest = True

# TODO: get_test_from_stack() (based on testresources._get_result())


class ResourcedTestCase(testtools.TestCase, unittest2.TestCase):
    """Inherit from testtools.TestCase instead of unittest.TestCase
    in order to have self.useFixture().

    Sets up capture of logging, and optionally,
    stdout (default True) and stderr (default True).

    Some additional assert and timestamp methods.
    """

    _capture_output = True
    _capture_error = True
    log_format = '%(asctime)s [%(levelname)s] %(name)s %(lineno)d: %(message)s'
    log_level = logging.DEBUG

    def __init__(self, *args, **kwargs):
        super(ResourcedTestCase, self).__init__(*args, **kwargs)
        self.worker = os.getenv('WRT_WORKER_ID', None)

    def setUp(self):
        # test cases can have a logger too
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.setLevel(self.log_level)
        # capture logging
        self.useFixture(fixtures.FakeLogger(format=self.log_format))
        # capture stderr
        if self._capture_error:
            stderr = self.useFixture(fixtures.StringStream('stderr')).stream
            self.useFixture(fixtures.MonkeyPatch('sys.stderr', stderr))
        # capture stdout
        if self._capture_output:
            stdout = self.useFixture(fixtures.StringStream('stdout')).stream
            self.useFixture(fixtures.MonkeyPatch('sys.stdout', stdout))

        testtools.TestCase.setUp(self)

        # this really only does something if not running with an OptimisingTestSuite
        if hasattr(self, 'resources'):
            setUpResources(self, self.resources, _get_result())
            self.addCleanup(tearDownResources, self, self.resources, _get_result())

    def addDetail(self, name, content, overwrite=False):
        try_name = name
        count = 0
        while try_name in self.getDetails() and not overwrite:
            count += 1
            try_name = '%s-%s' % (name, count)
        testtools.TestCase.addDetail(self, try_name, content)

    # new assertion methods
    def assertIsType(self, item, type_or_types, msg=None):
        """Verify an item is the type, or one of the types specified."""
        if type(type_or_types) is not ListType:
            type_or_types = [type_or_types]
        if type(item) not in type_or_types:
            standardMsg = '%s is not %s' % (safe_repr(item),
                                            safe_repr(type_or_types))
            self.fail(self._formatMessage(msg, standardMsg))

    def assertIsString(self, item, msg=None):
        self.assertIsType(item, [StringType, UnicodeType], msg=msg)

    def assertIsInt(self, item, msg=None):
        self.assertIsType(item, IntType, msg=msg)

    def assertIsFloat(self, item, msg=None):
        self.assertIsType(item, FloatType, msg=msg)

    def assertIsNumber(self, item, msg=None):
        self.assertIsType(item, [IntType, FloatType, LongType], msg=msg)

    def assertRaises(self, excClass, callableObj=None, *args, **kwargs):
        # the version from testtools can't be used as a context manager
        return unittest2.TestCase.assertRaises(
            self, excClass, callableObj=None, *args, **kwargs)

    @property
    def timestamp(self):
        return repr(time.time())

    def human_timestamp(self, format='%Y%m%d-%H.%M.%S.%f'):
        # suitable for inclusion in a filename
        return datetime.datetime.now().strftime(format)

    def utc_timestamp(self, format='%Y-%m-%d %H:%M:%S UTC'):
        # 2014-08-11 22:12:49 UTC
        return datetime.datetime.utcnow().strftime(format)
