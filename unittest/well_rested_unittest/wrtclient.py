import requests
import os
import sys
import json
import time
import subprocess
import ConfigParser


class WRTException(Exception):
    pass


class WRTConfNotFound(WRTException):
    pass


class WRTRevisionNotFound(WRTException):
    pass


class WRTProjectNotFound(WRTException):
    pass


class WRTUserNotFound(WRTException):
    pass


class WRTClient(object):

    def __init__(self, wrt_conf, stream, debug=False, run_url=None):
        self.stream = stream
        self.debug = debug
        if os.path.isfile(wrt_conf):
            self.config = ConfigParser.ConfigParser()
            self.config.read(wrt_conf)
        else:
            raise WRTConfNotFound('%s is not a file' % wrt_conf)

        self.session = requests.Session()
        try:
            self.username = self.config.get('default', 'USERNAME')
            self.password = self.config.get('default', 'PASSWORD')
            self.server = self.config.get('default', 'SERVER')
            self.project_name = self.config.get('default', 'PROJECT_NAME')
            self.protocol = self.config.get('default', 'PROTOCOL')
        except ConfigParser.Error as e:
            raise WRTConfigParamNotFound(e.message)
        self.session.mount(
            '%s://' % self.protocol, adapter=requests.adapters.HTTPAdapter(max_retries=3))
        self.session.auth = (self.username, self.password)
        self._project_url = None
        self._project_id = None
        self._user_url = None
        self._run_url = run_url
        self._run_id = None
        self._existing_tests = {}
        if self.debug:
            self.stream.writeln(
                'WRTClient created for %s/%s running %s on %s' %
                (self.username, self.password, self.project_name, self.server))

    @property
    def projects_url(self):
        return '%s://%s/api/projects/' % (self.protocol, self.server)

    @property
    def users_url(self):
        return '%s://%s/api/users/' % (self.protocol, self.server)

    @property
    def cases_url(self):
        return '%s://%s/api/cases/' % (self.protocol, self.server)

    @property
    def runs_url(self):
        return '%s://%s/api/runs/' % (self.protocol, self.server)

    @property
    def results_url(self):
        return '%s://%s/api/results/' % (self.protocol, self.server)

    @property
    def tags_url(self):
        return '%s://%s/api/tags/' % (self.protocol, self.server)

    def raise_for_status(self, resp):
        try:
            resp.raise_for_status()
        except requests.exceptions.HTTPError:
            self.stream.writeln(resp.text)
            raise

    def id_from_url(self, url):
        return int(url.split('/')[-2])

    @property
    def project_url(self):
        if not self._project_url:
            if self.debug:
                self.stream.writeln('Fetching project url')
            resp = self.session.get(self.projects_url)
            self.raise_for_status(resp)
            projects = json.loads(resp.text)
            for project in projects:
                if project['name'] == unicode(self.project_name):
                    self._project_url = project['url']
                    return self._project_url
            raise WRTProjectNotFound('%s in %s' % (self.project_name, projects))
        return self._project_url

    @property
    def project_id(self):
        return self.id_from_url(self.project_url)

    @property
    def user_url(self):
        if not self._user_url:
            if self.debug:
                self.stream.writeln('Fetching user url')
            resp = self.session.get(self.users_url)
            self.raise_for_status(resp)
            users = json.loads(resp.text)
            for user in users:
                if user['username'] == self.username:
                    self._user_url = user['url']
                    return self._user_url
            raise WRTUserNotFound('%s in %s' % (self.username, users))
        return self._user_url

    def registerTests(self, tests):
        for test in tests:
            # does the test exist in the cases table?
            resp = self.session.get(self.cases_url, params={
                'project': self.project_id,
                'name': test.id()
            })
            self.raise_for_status(resp)
            try:
                case = json.loads(resp.text)[0]
            except IndexError:
                if self.debug:
                    self.stream.writeln('Adding case for test %s' % test.id())
                resp = self.session.post(
                    self.cases_url, data={
                        'name': test.id(),
                        'project': self.project_url
                    })
                self.raise_for_status(resp)
                case = json.loads(resp.text)

            # does the test exist in the results table?
            resp = self.session.get(self.results_url, params={
                'run': self._run_id,
                'case': case['id']
            })
            self.raise_for_status(resp)
            try:
                result = json.loads(resp.text)[0]
            except IndexError:
                # Add a result for each of the tests
                if self.debug:
                    self.stream.writeln('Adding result for %s' % test.id())
                resp = self.session.post(self.results_url, data={
                    'owner': self.user_url,
                    'case': case['url'],
                    'run': self._run_url,
                    'status': 'exists'
                })
                self.raise_for_status(resp)
                result = json.loads(resp.text)

            self._existing_tests[test.id()] = {
                'case_url': case['url'],
                'case_id': case['id'],
                'result_url': result['url'],
                'result_id': result['id']
            }
        if self.debug:
            self.stream.writeln('%s' % self._existing_tests)

    def buildTags(self):
        # gather known tags for this project
        if self.debug:
            self.stream.writeln('Fetching existing tags')
        known_tags = {}
        resp = self.session.get(self.tags_url)
        self.raise_for_status(resp)
        for tag in json.loads(resp.text):
            if tag['project'] == self.project_url:
                known_tags[tag['name']] = tag['url']
        # create tag list for this run
        tag_list = []
        try:
            for name, command in self.config.items('tags'):
                pair = '%s=%s' % (name, subprocess.check_output(command.split()).strip())
                if pair not in known_tags:
                    if self.debug:
                        self.stream.writeln('Creating tag %s' % pair)
                    resp = self.session.post(
                        self.tags_url, data={'name': pair, 'project': self.project_url})
                    self.raise_for_status(resp)
                    known_tags[pair] = json.loads(resp.text)['url']
                tag_list.append(known_tags[pair])
        except ConfigParser.Error:
            if self.debug:
                self.stream.writeln('WARNING: unable to parse tags from config')
        return tag_list

    def getPreviousTestRun(self):
        # TODO: filter by matching tags, once tagging works
        params = {'project': self.project_id,}
        if self.debug:
            self.stream.writeln('%s %s' % (self.runs_url, params))
        resp = self.session.get(self.runs_url, params=params)
        self.raise_for_status(resp)
        runs = [run for run in json.loads(resp.text) if run['status'] != 'inprogress']
        runs = sorted(runs, key=lambda k: k['start_time'], reverse=True)
        return runs[0]['url']

    def failing(self, include_exists=True):
        previous_run_id = self.id_from_url(self.getPreviousTestRun())
        params = {'run': previous_run_id}
        if self.debug:
            self.stream.writeln('%s %s' % (self.results_url, params))
        resp = self.session.get(self.results_url, params=params)
        self.raise_for_status(resp)
        failing = []
        failing_statuses = ['fail']
        if include_exists:
            failing_statuses.append('exists')
        for result in json.loads(resp.text):
            if result['status'] in failing_statuses:
                resp = self.session.get(result['case'])
                self.raise_for_status(resp)
                failing.append(json.loads(resp.text)['name'])
        return failing

    # methods for run
    def startTestRun(self, timestamp=None):
        if self._run_url == 'previous':
            self._run_url = self.getPreviousTestRun()
        elif self._run_url:
            # re-start the run
            resp = self.session.post(self.runs_url, data={
                'status': 'inprogress',
                'owner': self.user_url,
                'project': self.project_url,
            })
            self.raise_for_status(resp)
        else:
            # create the run
            data = {
                'project': self.project_url,
                'owner': self.user_url,
                'start_time': timestamp,
                'status': 'inprogress',
                'tags': self.buildTags()
            }
            if self.debug:
                self.stream.writeln('Creating run %s' % data)
            resp = self.session.post(self.runs_url, data=data)
            self.raise_for_status(resp)
            self._run_url = json.loads(resp.text)['url']
        self._run_id = self.id_from_url(self._run_url)

    def stopTestRun(self, **kwargs):
        timestamp = kwargs.pop('timestamp', None)
        kwargs['end_time'] = timestamp
        kwargs['owner'] = self.user_url
        kwargs['project'] = self.project_url
        if self.debug:
            self.stream.writeln('Stopping run %s' % kwargs)
        resp = self.session.put(self._run_url, data=kwargs)
        self.raise_for_status(resp)

    # methods for tests
    def startTest(self, test, timestamp=None):
        result_url = self._existing_tests[test.id()]['result_url']
        data = {
            'case': self._existing_tests[test.id()]['case_url'],
            'run': self._run_url,
            'owner': self.user_url,
            'start_time': timestamp,
            'status': 'inprogress',
        }
        if self.debug:
            self.stream.writeln('Starting test %s %s' % (result_url, data))
        resp = self.session.put(result_url, data=data)
        self.raise_for_status(resp)

    def passTest(self, test):
        result_url = self._existing_tests[test.id()]['result_url']
        data = {
            'status': 'pass',
            'case': self._existing_tests[test.id()]['case_url'],
            'run': self._run_url,
            'owner': self.user_url,
        }
        if self.debug:
            self.stream.writeln('Passing test %s %s' % (result_url, data))
        resp = self.session.put(result_url, data=data)
        self.raise_for_status(resp)

    def failTest(self, test, err, details):
        result_url = self._existing_tests[test.id()]['result_url']
        data = {
            'status': 'fail',
            'case': self._existing_tests[test.id()]['case_url'],
            'run': self._run_url,
            'owner': self.user_url,
        }
        if err:
            data['reason'] = err[1].__class__.__name__
        elif 'reason' in details:
            data['reason'] = details.pop('reason').as_text()
        # TODO: handle details
        if self.debug:
            self.stream.writeln('Failing test %s %s' % (result_url, data))
        resp = self.session.put(result_url, data=data)
        self.raise_for_status(resp)

    def skipTest(self, test, reason):
        result_url = self._existing_tests[test.id()]['result_url']
        data = {
            'status': 'skip',
            'reason': reason,
            'case': self._existing_tests[test.id()]['case_url'],
            'run': self._run_url,
            'owner': self.user_url,
        }
        if self.debug:
            self.stream.writeln('Skipping test %s %s' % (result_url, data))
        resp = self.session.put(result_url, data=data)
        self.raise_for_status(resp)

    def xpassTest(self, test, details):
        result_url = self._existing_tests[test.id()]['result_url']
        data = {
            'status': 'xpass',
            'case': self._existing_tests[test.id()]['case_url'],
            'run': self._run_url,
            'owner': self.user_url,
        }
        if self.debug:
            self.stream.writeln('xPassing test %s %s' % (result_url, data))
        # TODO: handle details
        resp = self.session.put(result_url, data=data)
        self.raise_for_status(resp)

    def xfailTest(self, test, err, details):
        result_url = self._existing_tests[test.id()]['result_url']
        data = {
            'status': 'xfail',
            'case': self._existing_tests[test.id()]['case_url'],
            'run': self._run_url,
            'owner': self.user_url,
        }
        if err:
            data['reason'] = err[1].__class__.__name__
        elif 'reason' in details:
            data['reason'] = details.pop('reason').as_text()
        # TODO: handle details
        if self.debug:
            self.stream.writeln('xFailing test %s %s' % (result_url, data))
        resp = self.session.put(result_url, data=data)
        self.raise_for_status(resp)

    def abortTest(self, test, reason=None):
        """Used by suite if aborting run-in-progress."""
        result_url = self._existing_tests[test.id()]['result_url']
        data = {
            'status': 'aborted',
            'case': self._existing_tests[test.id()]['case_url'],
            'run': self._run_url,
            'owner': self.user_url,
        }
        if reason:
            data['reason'] = reason
        if self.debug:
            self.stream.writeln('Aborting test %s %s' % (result_url, data))
        resp = self.session.put( result_url, data=data)
        self.raise_for_status(resp)

    def stopTest(self, test, timestamp=None, duration=None):
        result_url = self._existing_tests[test.id()]['result_url']
        data = {
            'end_time': timestamp,
            'duration': duration,
            'case': self._existing_tests[test.id()]['case_url'],
            'run': self._run_url,
            'owner': self.user_url,
        }
        if self.debug:
            self.stream.writeln( 'Stopping test %s %s' % (result_url, data))
        resp = self.session.put(result_url, data=data)
        self.raise_for_status(resp)
