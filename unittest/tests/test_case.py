import unittest2
import logging
from well_rested_unittest import ResourcedTestCase


class TestResourcedTestCase(ResourcedTestCase):

    def test_assert_is_int(self):
        self.assertIsInt(88)
        with self.assertRaises(AssertionError):
            self.assertIsInt(4.35)
        with self.assertRaises(AssertionError):
            self.assertIsInt('7')

    def test_assert_is_float(self):
        self.assertIsFloat(4.35)
        with self.assertRaises(AssertionError):
            self.assertIsFloat(55)
        with self.assertRaises(AssertionError):
            self.assertIsFloat('7.2')

    def test_assert_is_number(self):
        self.assertIsNumber(4.35)
        self.assertIsNumber(8)
        with self.assertRaises(AssertionError):
            self.assertIsNumber('99')

    def test_assert_is_string(self):
        self.assertIsString('blah')
        self.assertIsString(u'blort')
        with self.assertRaises(AssertionError):
            self.assertIsString(9)
        with self.assertRaises(AssertionError):
            self.assertIsString(9.8)

    def test_default_settings(self):
        self.assertTrue(self._capture_output)
        self.assertTrue(self._capture_error)
        self.assertEqual(self.log_level, logging.DEBUG)
        self.assertEqual(
            self.log_format,
            '%(asctime)s [%(levelname)s] %(name)s %(lineno)d: %(message)s')
