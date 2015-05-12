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

    def test_1(self):
        pass

    def test_2(self):
        pass
