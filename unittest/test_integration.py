import well_rested_unittest
import subprocess
import requests
import ConfigParser
import os
import sys
import json
from well_rested_unittest.wrtclient import WRTClient
from well_rested_unittest.result import ColorizedWritelnDecorator


class DBRun(well_rested_unittest.ReportingTestResourceManager):

    config_file = '.wrt.conf'

    def make(self, dependency_resources):
        try:
            subprocess.check_output(
                'wrt -v --wrt-conf %s sample_tests' % self.config_file,
                shell=True, stderr=subprocess.STDOUT)
        except (subprocess.CalledProcessError,
                requests.exceptions.ConnectionError) as e:
            return e

        class MockObject(object):
            pass
        return MockObject()

    def clean(self, resource):
        pass
DBRunRM = DBRun()


class SwiftRun(DBRun):

    config_file = '.wrt-swift.conf'
SwiftRunRM = SwiftRun()


class TestDBIntegration(well_rested_unittest.ResourcedTestCase):

    resources = [('CalledProcessError', DBRunRM)]

    def __init__(self, *args, **kwargs):
        super(TestDBIntegration, self).__init__(*args, **kwargs)
        self.wrtclient = WRTClient('.wrt.conf', ColorizedWritelnDecorator(sys.stdout))

    def setUp(self):
        try:
            self.wrtclient.project_url
        except requests.exceptions.ConnectionError:
            self.skipTest("wrt server not running")
        super(TestDBIntegration, self).setUp()

    def run_url(self):
        return self.CalledProcessError.output.split('\n')[-2]

    def run_id(self):
        return self.wrtclient.id_from_url(self.run_url())

    def get_test_run(self):
        url = self.run_url().replace('run', 'api/runs')
        resp = self.wrtclient.session.get(url)
        self.wrtclient.raise_for_status(resp)
        try:
            return json.loads(resp.text)
        except ValueError:
            print resp.text
            raise

    def get_test_result(self, name):
        resp = self.wrtclient.session.get(self.wrtclient.cases_url, params={
            'name': name})
        self.wrtclient.raise_for_status(resp)
        try:
            case = json.loads(resp.text)[0]['url']
        except IndexError:
            print(resp.text)
            raise
        resp = self.wrtclient.session.get(self.wrtclient.results_url, params={
            'run': self.run_id(),
            'case': self.wrtclient.id_from_url(case)
        })
        self.wrtclient.raise_for_status(resp)
        try:
            result = json.loads(resp.text)[0]
        except (IndexError, ValueError):
            print resp.text
            raise
        print(result)
        return result

    def get_details(self, result_id):
        resp = self.wrtclient.session.get(self.wrtclient.details_url, params={
            'result': result_id,
        })
        self.wrtclient.raise_for_status(resp)
        details = json.loads(resp.text)
        detail_content = {}
        for detail in details:
            print detail['file_url']
            resp = requests.get(detail['file_url'])
            resp.raise_for_status()
            detail_content[detail['name']] = resp.text
        return detail_content

    def test_run(self):
        # fetch the run and check it's sums
        run = self.get_test_run()
        print run
        try:
            self.assertEqual(run['failures'], 8)
            self.assertEqual(run['skips'], 2)
            self.assertEqual(run['status'], 'fail')
            self.assertEqual(run['tests_run'], 31)
            self.assertEqual(run['xfails'], 2)
            self.assertEqual(run['xpasses'], 2)
        except Exception:
            print self.CalledProcessError.output
            raise

    def test_pass(self):
        # fetch the result for a passing test in this run
        result = self.get_test_result(
            'sample_tests.test_resourced_test_case.TestResourcedTestCase.test_pass')
        self.assertEqual(result['status'], 'pass')
        # passing tests should not have details
        details = self.get_details(result['id'])
        self.assertFalse(details, details)

    def test_fail(self):
        # fetch the result for a failing test in this run
        result = self.get_test_result(
            'sample_tests.test_resourced_test_case.TestResourcedTestCase.test_fail')
        self.assertEqual(result['status'], 'fail')
        # don't test details until MEDIA_URL has been sorted out
        details = self.get_details(result['id'])
        self.assertEqual(len(details), 3, details)

    def test_error(self):
        # fetch the result for a failing test in this run
        result = self.get_test_result(
            'sample_tests.test_resourced_test_case.TestResourcedTestCase.test_error')
        self.assertEqual(result['status'], 'fail')
        # don't test details until MEDIA_URL has been sorted out
        details = self.get_details(result['id'])
        self.assertEqual(len(details), 3, details)

    def test_fixture_error(self):
        # fetch the result for a failing fixture in this run
        result = self.get_test_result('Destroying_DestroyFailResource')
        self.assertEqual(result['status'], 'fail')
        # don't test details until MEDIA_URL has been sorted out
        details = self.get_details(result['id'])
        self.assertEqual(len(details), 2, details)

    def test_skip(self):
        # fetch the result for a skipped test in this run
        result = self.get_test_result(
            'sample_tests.test_resourced_test_case.TestResourcedTestCase.test_skip')
        self.assertEqual(result['status'], 'skip')
        # skipped tests should not have details
        details = self.get_details(result['id'])
        self.assertFalse(details, details)


class TestSwiftIntegration(TestDBIntegration):

    resources = [('CalledProcessError', SwiftRunRM)]

    def test_fail(self):
        # fetch the result for a failing test in this run
        result = self.get_test_result(
            'sample_tests.test_resourced_test_case.TestResourcedTestCase.test_fail')
        self.assertEqual(result['status'], 'fail')
        # failing tests should stdout, logging, and traceback details
        details = self.get_details(result['id'])
        self.assertEqual(len(details), 3, details)
        self.assertIn('a message to stdout', details['stdout'])
        self.assertIn('a debug message', details['pythonlogging'])
        self.assertIn("to test failure", details['traceback'])

    def test_error(self):
        # fetch the result for a failing test in this run
        result = self.get_test_result(
            'sample_tests.test_resourced_test_case.TestResourcedTestCase.test_error')
        self.assertEqual(result['status'], 'fail')
        # errored tests should have stderr, logging, and traceback details
        details = self.get_details(result['id'])
        self.assertEqual(len(details), 3, details)
        self.assertIn('a message to stderr', details['stderr'])
        self.assertIn('and error message', details['pythonlogging'])
        self.assertIn("to test error", details['traceback'])

    def test_fixture_error(self):
        # fetch the result for a failing fixture in this run
        result = self.get_test_result('Destroying_DestroyFailResource')
        self.assertEqual(result['status'], 'fail')
        # errored fixture should have logging and traceback details
        details = self.get_details(result['id'])
        self.assertEqual(len(details), 2, details)
        self.assertIn('cleaning booga booga', details['pythonlogging'])
        self.assertIn("booga booga", details['traceback'])
