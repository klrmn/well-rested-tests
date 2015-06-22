import unittest2
import resources
import well_rested_unittest


class TestClass1(unittest2.TestCase):

    resources = [
        ('C', resources.ResourceCRM),
        ('F', resources.CreateFailResourceRM),
    ]

    def test_1(self):
        pass

    def test_2(self):
        pass


class TestClass2(well_rested_unittest.ResourcedTestCase):

    resources = [
        ('C', resources.ResourceCRM),
        ('F', resources.DestroyFailResourceRM),
    ]

    def test_1(self):
        pass

    def test_2(self):
        pass
