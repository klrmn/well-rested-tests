import unittest2
import resources


class TestClass1(unittest2.TestCase):

    resources = [
        ('C', resources.ResourceCRM),
        ('F', resources.CreateFailResourceRM),
    ]

    def test_1(self):
        pass

    def test_2(self):
        pass


class TestClass2(unittest2.TestCase):

    resources = [
        ('C', resources.ResourceCRM),
        ('F', resources.DestroyFailResourceRM),
    ]

    def test_1(self):
        pass

    def test_2(self):
        pass
