import requests
import os
import sys
import json
import time
import subprocess
import ConfigParser
import content

__unittest = True


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


class WRTRequestFailed(WRTException):
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
            self.storage = self.config.get('default', 'STORAGE')
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
        self._tags = []
        self._existing_tests = {}
        self._existing_fixtures = {}
        if self.storage == 'swift':
            from swiftclient import Connection
            self.swift = Connection(self.config.get('swift', 'AUTH_URL'),
                                    user=self.config.get('swift', 'USER'),
                                    key=self.config.get('swift', 'KEY'),
                                    auth_version=self.config.get('swift', 'AUTH_VERSION'),
                                    tenant_name=self.config.get('swift', 'TENANT'))
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

    @property
    def attachments_url(self):
        return '%s://%s/api/attachments/' % (self.protocol, self.server)

    @property
    def details_url(self):
        return '%s://%s/api/details/' % (self.protocol, self.server)

    def raise_for_status(self, resp):
        try:
            resp.raise_for_status()
        except requests.exceptions.HTTPError as e:
            try:
                beginning = resp.text.find('<div id="summary">')
                end = resp.text.find('<div id="traceback">')
                self.stream.writeln(resp.text[beginning:end])
            except Exception:
                self.stream.writeln(resp.body)
            raise WRTRequestFailed(e.message)

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
        # if run_url were *always* a url and never 'previous',
        # we could have assigned _run_id during __init__,
        # but since it can be 'previous', we have to do it
        # after startTestRun()
        if not self._run_id:
            self._run_id = self.id_from_url(self._run_url)
        for test in tests:
            # does the test exist in the cases table?
            params = {
                'project': self.project_id,
                'name': test.id(),
                'fixture': False
            }
            if self.debug:
                self.stream.writeln('Querying %s for %s' % (self.cases_url, params))
            resp = self.session.get(self.cases_url, params=params)
            self.raise_for_status(resp)
            if self.debug:
                self.stream.writeln('Found %s' % json.loads(resp.text))
            try:
                case = json.loads(resp.text)[0]
            except IndexError:
                data = {
                    'name': test.id(),
                    'project': self.project_url
                }
                if self.debug:
                    self.stream.writeln('Adding case for test %s' % data)
                resp = self.session.post(self.cases_url, data=data)
                self.raise_for_status(resp)
                case = json.loads(resp.text)

            # does the test exist in the results table?
            params = {
                'run': self._run_id,
                'case': case['id']
            }
            if self.debug:
                self.stream.writeln('Querying %s for %s' % (self.results_url, params))
            resp = self.session.get(self.results_url, params=params)
            self.raise_for_status(resp)
            if self.debug:
                self.stream.writeln('Found %s' % json.loads(resp.text))
            try:
                result = json.loads(resp.text)[0]
                if self.debug:
                    self.stream.writeln('Updating %s' % result)
            except IndexError:
                # Add a result for each of the tests
                data = {
                    'owner': self.user_url,
                    'case': case['url'],
                    'run': self._run_url,
                    'status': 'exists'
                }
                if self.debug:
                    self.stream.writeln('Adding result for %s' % data)
                resp = self.session.post(self.results_url, data=data)
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

        # create a database of existing fixtures
        resp = self.session.get(self.cases_url, params={
                'project': self.project_id,
                'fixture': True
            })
        self.raise_for_status(resp)
        for fixture in json.loads(resp.text):
            self._existing_fixtures[fixture['name']] = {'case_url': fixture['url']}

    @property
    def tags(self):
        if not self._tags:
            self._tags = self.buildTags()
        return self._tags

    def buildTags(self):
        # gather known tags for this project
        params = {
            'project': self.project_id,
        }
        if self.debug:
            self.stream.writeln('Fetching existing tags %s' % params)
        known_tags = {}
        resp = self.session.get(self.tags_url, params=params)
        self.raise_for_status(resp)
        for tag in json.loads(resp.text):
            pair = '%s %s' % (tag['name'], tag['value'])
            known_tags[pair] = tag['url']
        if self.debug:
            self.stream.writeln('KNOWN TAGS: %s' % known_tags)
        # create tag list for this run
        tag_list = []
        try:
            for name, command in self.config.items('tags'):
                value = subprocess.check_output(command, shell=True).strip()
                data = {'name': name, 'value': value, 'project': self.project_url}
                pair = '%s %s' % (name, value)
                if pair not in known_tags:
                    if self.debug:
                        self.stream.writeln('Creating tag %s' % data)
                    resp = self.session.post(self.tags_url, data=data)
                    self.raise_for_status(resp)
                    known_tags[pair] = json.loads(resp.text)['url']
                tag_list.append(known_tags[pair])
        except ConfigParser.Error:
            if self.debug:
                self.stream.writeln('WARNING: unable to parse tags from config')
        return tag_list

    def getPreviousTestRun(self):
        params = {'project': self.project_id,}
        if self.debug:
            self.stream.writeln('%s %s' % (self.runs_url, params))
        resp = self.session.get(self.runs_url, params=params)
        self.raise_for_status(resp)
        runs = json.loads(resp.text)
        # only consider finished runs
        runs = [run for run in runs if run['status'] != 'inprogress']
        # filter manually, a list can't be put in a query string
        if self.debug:
            self.stream.writeln('Required tags: %s' % self.tags)
        runs = [run for run in runs if run['tags'] == self.tags]
        # then choose the most recent
        runs = sorted(runs, key=lambda k: k['start_time'], reverse=True)
        try:
            return runs[0]['url']
        except IndexError:
            return None

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
            # may return None
            self._run_url = self.getPreviousTestRun()
            if not self._run_url:
                self.stream.writeln(
                    'WARNING: no matching previous run found, new run will be created.')
        elif self._run_url:
            # re-start the run
            resp = self.session.post(self.runs_url, data={
                'status': 'inprogress',
                'owner': self.user_url,
                'project': self.project_url,
                'tags': self.tags,
            })
            self.raise_for_status(resp)
        if not self._run_url:
            # create the run
            data = {
                'project': self.project_url,
                'owner': self.user_url,
                'start_time': timestamp,
                'status': 'inprogress',
                'tags': self.tags,
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
        kwargs['tags'] = self.tags
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

    def markTestStatus(self, test, status, reason=None, details=None):
        result_url = self._existing_tests[test.id()]['result_url']
        # upload details
        if status in ['fail', 'skip', 'xfail'] and details:
            if self.storage == 'swift':
                from swiftclient import ClientException
                try:
                    self.swift.get_container(self._run_id)
                except ClientException:
                    self.swift.put_container(
                        self._run_id, headers={'x-container-read': '.r:*'})
            for name, value in details.items():
                # TODO: contemplate whether all content types are created equal
                attachment = None
                if value.content_type == content.URL:
                    continue  # urls pass-thru to detail stage
                else:
                    if value.content_type.type == 'application':
                        type = value.content_type.subtype
                        attachment = value.as_bytes()
                    elif value.content_type.type == 'text':
                        type = value.content_type.type
                        attachment = value.as_text().strip()
                    if not attachment:
                        continue  # empty attachments pass thru
                    # get rid of weird stuff in pythonlogging name
                    if ":''" in name:
                        details.pop(name)
                        name = name.replace(":''", "")
                    # object named for test id, content name and type
                    filename = '%s-%s.%s' % (test.id(), name, type)

                    if self.storage == 'swift':
                        from swiftclient import ClientException
                        try:
                            self.swift.get_container(self._run_id)
                        except ClientException:
                            self.swift.put_container(self._run_id)
                        # optionally set object expiration
                        expire = self.config.get('swift', 'EXPIRE_SECONDS')
                        headers = {}
                        if expire:
                            headers['X-Delete-After'] = expire
                        self.swift.put_object(self._run_id, filename, attachment,
                                              headers=headers)
                        url = '%s/%s/%s' % (self.swift.url, self._run_id, filename)
                    elif self.storage == 'database':
                        # TODO: chunked?
                        headers = {
                            'Content-Type': '%s/%s' % (
                                value.content_type.type, value.content_type.subtype),
                            'Content-length': len(attachment),
                            'Content-Disposition': 'attachment; filename=%s' % filename
                        }
                        if self.debug:
                            self.stream.writeln('uploading attachment %s %s %s'
                                                % (self.attachments_url, name, headers))
                        resp = self.session.post(self.attachments_url,
                                                 data={'file': attachment},
                                                 headers=headers)
                        self.raise_for_status(resp)
                        url = json.loads(resp.text)['file_url']

                # create a detail by attaching the attachment to a result
                data = {
                    'file_url': url,
                    'file_type': type,
                    'name': name,
                    'result': result_url,
                }
                if self.debug:
                    self.stream.writeln('adding detail %s %s' % (self.details_url, data))
                resp = self.session.post(self.details_url, data=data)
                self.raise_for_status(resp)

                # replace the detail content with a url for printing
                details[name] = content.url_content(url)
        # update the result
        data = {
            'status': status,
            'case': self._existing_tests[test.id()]['case_url'],
            'run': self._run_url,
            'owner': self.user_url,
            'reason': reason,
        }
        if self.debug:
            self.stream.writeln('Marking test %s %s' % (result_url, data))
        resp = self.session.put(result_url, data=data)
        self.raise_for_status(resp)

        return details

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
            self.stream.writeln('Stopping test %s %s' % (result_url, data))
        resp = self.session.put(result_url, data=data)
        self.raise_for_status(resp)

    # methods for fixtures
    def startFixture(self, fixture, timestamp):
        # find or create the case
        try:  # find out if we've seen it locally before
            case_url = self._existing_fixtures[fixture.id()]['case_url']
        except KeyError:
            resp = self.session.get(self.cases_url, params={'name': fixture.id()})
            self.raise_for_status(resp)
            try:  # find out if the server has seen it
                case_url = json.loads(resp.text)[0]['url']
            except (IndexError, AttributeError):
                # doesn't exist anywhere, create it
                data = {
                    'name': fixture.id(),
                    'project': self.project_url,
                    'fixture': True,
                }
                if self.debug:
                    self.stream.writeln('Adding case for fixture %s' % data)
                resp = self.session.post(self.cases_url, data=data)
                self.raise_for_status(resp)
                case_url = json.loads(resp.text)['url']
            # save it locally
            self._existing_fixtures[fixture.id()] = {'case_url': case_url}
        # always create a new result
        data = {
            'case': case_url,
            'run': self._run_url,
            'owner': self.user_url,
            'start_time': timestamp,
            'status': 'inprogress',
        }
        if self.debug:
            self.stream.writeln('Starting fixture %s %s' % (fixture.id(), data))
        resp = self.session.post(self.results_url, data=data)
        self.raise_for_status(resp)
        self._existing_fixtures[fixture.id()]['result_url'] = json.loads(resp.text)['url']

    def markFixtureStatus(self, fixture, status, details=None, reason=None):
        result_url = self._existing_fixtures[fixture.id()]['result_url']
        # upload details
        if status == 'fail' and details:
            if self.storage == 'swift':
                from swiftclient import ClientException
                try:
                    self.swift.get_container(self._run_id)
                except ClientException:
                    self.swift.put_container(
                        self._run_id, headers={'x-container-read': '.r:*'})
            for name, value in details.items():
                # TODO: contemplate whether all content types are created equal
                attachment = None
                if value.content_type == content.URL:
                    continue  # urls pass-thru to detail stage
                else:
                    if value.content_type.type == 'application':
                        type = value.content_type.subtype
                        attachment = value.as_bytes()
                    elif value.content_type.type == 'text':
                        type = value.content_type.type
                        attachment = value.as_text().strip()
                    if not attachment:
                        continue  # empty attachments pass thru
                    # get rid of weird stuff in pythonlogging name
                    if ":''" in name:
                        details.pop(name)
                        name = name.replace(":''", "")
                    # object named for result id, fixture id, content name and type
                    # (fixture id isn't unique per run)
                    filename = '%s-%s-%s.%s' % (
                        self.id_from_url(result_url), fixture.id(), name, type)

                    if self.storage == 'swift':
                        # optionally set object expiration
                        expire = self.config.get('swift', 'EXPIRE_SECONDS')
                        headers = {}
                        if expire:
                            headers['X-Delete-After'] = expire
                        self.swift.put_object(self._run_id, filename, attachment,
                                              headers=headers)
                        url = '%s/%s/%s' % (self.swift.url, self._run_id, filename)
                    elif self.storage == 'database':
                        # TODO: chunked?
                        headers = {
                            'Content-Type': '%s/%s' % (
                                value.content_type.type, value.content_type.subtype),
                            'Content-length': len(attachment),
                            'Content-Disposition': 'attachment; filename=%s' % filename
                        }
                        if self.debug:
                            self.stream.writeln('uploading attachment %s %s %s'
                                                % (self.attachments_url, name, headers))
                        resp = self.session.post(self.attachments_url,
                                                 data={'file': attachment},
                                                 headers=headers)
                        self.raise_for_status(resp)
                        url = json.loads(resp.text)['file_url']

                # create a detail by attaching the attachment to a result
                data = {
                    'file_url': url,
                    'file_type': type,
                    'name': name,
                    'result': result_url,
                }
                if self.debug:
                    self.stream.writeln('adding detail %s %s' % (self.details_url, data))
                resp = self.session.post(self.details_url, data=data)
                self.raise_for_status(resp)

                # replace the detail content with a url for printing
                details[name] = content.url_content(url)
        data = {
            'status': status,
            'case': self._existing_fixtures[fixture.id()]['case_url'],
            'run': self._run_url,
            'owner': self.user_url,
            'reason': reason,
        }
        if self.debug:
            self.stream.writeln('Marking fixture %s %s' % (result_url, data))
        resp = self.session.put(result_url, data=data)
        self.raise_for_status(resp)
        return details

    def stopFixture(self, fixture, timestamp, duration=None):
        # get rid of the result_url when done with this method
        result_url = self._existing_fixtures[fixture.id()].pop('result_url')
        data = {
            'end_time': timestamp,
            'duration': duration,
            'case': self._existing_fixtures[fixture.id()]['case_url'],
            'run': self._run_url,
            'owner': self.user_url,
        }
        if self.debug:
            self.stream.writeln('Stopping fixture %s %s' % (result_url, data))
        resp = self.session.put(result_url, data=data)
        self.raise_for_status(resp)
