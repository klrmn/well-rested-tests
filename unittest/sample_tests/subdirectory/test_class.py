import os
import sys
import unittest2
resources_path = os.path.dirname(os.path.dirname(__file__))
sys.path.append(resources_path)
import resources


class TestClassInSubdirectory(unittest2.TestCase):

    resources = [
        ('C', resources.ResourceCRM),
    ]

    def test_pass(self):
        pass

    def test_fail(self):
        self.fail("to test failure")

    def test_skip(self):
        self.skipTest("to test skip")

    def test_error(self):
        raise Exception("to test error")
