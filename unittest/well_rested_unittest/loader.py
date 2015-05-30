import unittest2
import os
import sys
import wrtclient
import shutil

__unittest = True


class AutoDiscoveringTestLoader(unittest2.TestLoader):
    """Test loader that extends unittest.TestLoader to:

    * support names that can be a combination of modules and directories
    """

    def __init__(self, suiteClass=unittest2.TestSuite,
                 failing=False, from_server=None, from_file=None,
                 wrt_conf=None, top_dir=None):
        """
        :param suiteClass: TestSuite instance (defaults to unittest2.TestSuite)
        :param failing: load previously failed tests
        :param failing_file: file containing previously failed tests
                             (defaults to .failing)
        :param wrt_conf: file containing well-rested-tests configuration
        :param top_dir: (defaults to None)
        :return:
        """
        super(AutoDiscoveringTestLoader, self).__init__()
        self.suiteClass = suiteClass
        self.failing = failing
        self.from_file = from_file
        if self.failing:
            self.from_file = '.failing'
            shutil.copy(self.from_file, self.from_file + '.bak')
        self.from_server = from_server
        self.wrt_conf = wrt_conf
        self.top_dir = top_dir

    @staticmethod
    def parserOptions(parser):
        # reminder, add sub-heading when adding arguments
        group = parser.add_argument_group('AutoDiscoveringTestLoader')
        group.add_argument('--failing', dest='failing',
                            action='store_true',
                            help='Run tests previously marked as fail or error')
        group.add_argument('--failing-from-server', dest='from_server',
                           action='store_true',
                           help='Run failed tests from well-rested-tests server.')
        group.add_argument('--from-file', dest='from_file',
                           help='Path to file listing tests to be run, '
                                'one to a line.')
        return parser

    @staticmethod
    def expectedHelpText(cls):
        return """
%s:
  --failing             Run tests previously marked as fail or error
  --failing-from-server
                        Run failed tests from well-rested-tests server.
  --from-file FROM_FILE
                        Path to file listing tests to be run, one to a line.
""" % cls.__name__

    @staticmethod
    def factory(cls, object):
        return cls(
            suiteClass=object.suiteClass,  # always exists
            failing=object.failing if hasattr(object, 'failing') else False,
            from_server=object.from_server if hasattr(object, 'from_server') else False,
            from_file=object.from_file if hasattr(object, 'from_file') else None,
            wrt_conf=object.wrt_conf if hasattr(object, 'wrt_conf') else None,
        )

    def loadTestsFromNames(self, names, module=None):
        """Return a suite of all tests cases found using the given sequence
        of string specifiers. See 'loadTestsFromName()'.
        """
        suites = []
        for name in names:
            if os.path.isdir(name):
                top_level = os.path.dirname(os.path.split(name)[0])
                suites.extend(self.discover(name, top_level_dir=top_level))
            else:
                suites.extend(self.loadTestsFromName(name, module))
        suite = self.suiteClass(suites)
        if hasattr(suite, 'filter_by_ids'):
            ids = []
            if self.from_server:
                self.wrt_client = wrtclient.WRTClient(
                    self.wrt_conf, unittest2.runner._WritelnDecorator(sys.stderr))
                ids = self.wrt_client.failing()
            elif self.from_file:
                with open(self.from_file, 'rb') as f:
                    ids = f.read().split()
            if ids:
                return suite.filter_by_ids(ids)
        return suite
