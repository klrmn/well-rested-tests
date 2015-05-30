from well_rested_unittest import AutoDiscoveringTestLoader
import unittest2
import os
import sample_tests
from sample_tests import subdirectory
from sample_tests.subdirectory import test_class


class NewSuite(unittest2.TestSuite):
    pass


class TestAutoDiscoveringTestLoader(unittest2.TestCase):

    maxDiff = None

    def test_specific_suite(self):
        loader = AutoDiscoveringTestLoader(suiteClass=NewSuite)
        self.assertEqual(loader.suiteClass, NewSuite)

    def test_top_level(self):
        loader = AutoDiscoveringTestLoader()
        self.assertEqual(loader.suiteClass, unittest2.TestSuite)
        suite = loader.loadTestsFromNames(['sample_tests'], None)
        self.assertEqual(
            suite._tests, [
            unittest2.TestSuite([]),
            unittest2.TestSuite([]),
            unittest2.TestSuite([
                unittest2.TestSuite([
                    sample_tests.subdirectory.test_class.TestClassInSubdirectory(methodName='test_1'),
                    sample_tests.subdirectory.test_class.TestClassInSubdirectory(methodName='test_2'),
                ]),
            ]),
            unittest2.TestSuite([
                unittest2.TestSuite([
                    sample_tests.test_class.TestClass1(methodName='test_1'),
                    sample_tests.test_class.TestClass1(methodName='test_2'),
                ]),
                unittest2.TestSuite([
                    sample_tests.test_class.TestClass2(methodName='test_1'),
                    sample_tests.test_class.TestClass2(methodName='test_2'),
                ]),
            ]),
        ])

    def test_subdirectory(self):
        loader = AutoDiscoveringTestLoader()
        suite = loader.loadTestsFromNames(
            ['sample_tests/subdirectory'], None)
        self.assertEqual(
            suite._tests, [
            unittest2.TestSuite([]),
            unittest2.TestSuite([
                unittest2.TestSuite([
                    sample_tests.subdirectory.test_class.TestClassInSubdirectory(methodName='test_1'),
                    sample_tests.subdirectory.test_class.TestClassInSubdirectory(methodName='test_2'),
                ]),
            ])]
        )

    def test_module(self):
        loader = AutoDiscoveringTestLoader()
        suite = loader.loadTestsFromNames(
            ['sample_tests.test_class'], None)
        self.assertEqual(
            suite._tests, [
                unittest2.TestSuite([
                    sample_tests.test_class.TestClass1(methodName='test_1'),
                    sample_tests.test_class.TestClass1(methodName='test_2'),
                ]),
                unittest2.TestSuite([
                    sample_tests.test_class.TestClass2(methodName='test_1'),
                    sample_tests.test_class.TestClass2(methodName='test_2'),
                ]),
            ]
        )

    def test_class(self):
        loader = AutoDiscoveringTestLoader()
        suite = loader.loadTestsFromNames(
            ['sample_tests.test_class.TestClass1'], None)
        self.assertEqual(
            suite._tests, [
                sample_tests.test_class.TestClass1(methodName='test_1'),
                sample_tests.test_class.TestClass1(methodName='test_2'),
            ]
        )

    def test_method(self):
        loader = AutoDiscoveringTestLoader()
        suite = loader.loadTestsFromNames(
            ['sample_tests.test_class.TestClass1.test_1'], None)
        self.assertEqual(
            suite._tests, [
                sample_tests.test_class.TestClass1(methodName='test_1'),
            ]
        )

    def test_subdirectory_and_class(self):
        loader = AutoDiscoveringTestLoader()
        suite = loader.loadTestsFromNames(
            ['sample_tests/subdirectory',
             'sample_tests.test_class.TestClass2'], None)
        self.assertEqual(
            suite._tests, [
            unittest2.TestSuite([]),
            unittest2.TestSuite([
                unittest2.TestSuite([
                    sample_tests.subdirectory.test_class.TestClassInSubdirectory(methodName='test_1'),
                    sample_tests.subdirectory.test_class.TestClassInSubdirectory(methodName='test_2'),
                ]),
            ]),
            sample_tests.test_class.TestClass2(methodName='test_1'),
            sample_tests.test_class.TestClass2(methodName='test_2'),
        ])

    def test_module_and_method(self):
        loader = AutoDiscoveringTestLoader()
        suite = loader.loadTestsFromNames(
            ['sample_tests.subdirectory.test_class',
             'sample_tests.test_class.TestClass1.test_2'], None)
        self.assertEqual(
            suite._tests, [
            unittest2.TestSuite([
                sample_tests.subdirectory.test_class.TestClassInSubdirectory(methodName='test_1'),
                sample_tests.subdirectory.test_class.TestClassInSubdirectory(methodName='test_2'),
            ]),
            sample_tests.test_class.TestClass1(methodName='test_2'),
        ])

    def test_failing(self):
        loader = AutoDiscoveringTestLoader(failing=True)
        self.assertEqual(loader.from_file, '.failing')

    def test_from_file(self):
        loader = AutoDiscoveringTestLoader(from_file='sample_tests/load_2_tests.txt')
        suite = loader.loadTestsFromNames(['sample_tests'], None)
        self.assertEqual(
            suite._tests, [
                sample_tests.subdirectory.test_class.TestClassInSubdirectory(methodName='test_1'),
                sample_tests.test_class.TestClass(methodName='test_2'),
            ])
