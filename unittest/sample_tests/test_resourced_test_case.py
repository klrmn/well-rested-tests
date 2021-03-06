import well_rested_unittest
import sys
import unittest2
import resources


class TestResourcedTestCase(well_rested_unittest.ResourcedTestCase):

    def test_pass(self):
        sys.stderr.write('a message to stderr')
        sys.stdout.write('a message to stdout')
        self.logger.debug('a debug message')

    def test_fail(self):
        sys.stdout.write('a message to stdout')
        self.logger.debug('a debug message')
        self.fail("to test failure")

    def test_skip(self):
        self.logger.info('an info message')
        self.skipTest("to test skip")

    def test_error(self):
        sys.stderr.write('a message to stderr')
        self.logger.error('and error message')
        raise Exception("to test error")

    @unittest2.expectedFailure
    def test_xfail(self):
        self.fail("expected failure")

    @unittest2.expectedFailure
    def test_xpass(self):
        pass

    def test_addDetail_upStack(self):
        resources.SomeUnrelatedClass().do_something()
        self.assertIn('a_thing', self.getDetails())
