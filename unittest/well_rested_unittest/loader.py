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
                 failing=False, failing_file='.failing',
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
        self.failing_file = failing_file
        self.wrt_conf = wrt_conf
        self.top_dir = top_dir

    @staticmethod
    def parserOptions(parser):
        # reminder, add sub-heading when adding arguments
        group = parser.add_argument_group('AutoDiscoveringTestLoader')
        group.add_argument('--failing', dest='failing',
                            action='store_true',
                            help='Run tests previously marked as fail or error')
        group.add_argument('--failing-file', dest='failing_file',
                           default='.failing',
                           help='path to file used to store failed tests '
                                '(default .failing). if set to the same path '
                                'as --wrt-conf, get failed tests from wrt server.')
        return parser

    @staticmethod
    def expectedHelpText(cls):
        return """
%s:
  --failing             Run tests previously marked as fail or error
  --failing-file FAILING_FILE
                        path to file used to store failed tests (default
                        .failing). if set to the same path as --wrt-conf, get
                        failed tests from wrt server.
""" % cls.__name__

    @staticmethod
    def factory(cls, object):
        return cls(
            suiteClass=object.suiteClass,  # always exists
            failing=object.failing if hasattr(object, 'failing') else False,
            failing_file=object.failing_file if hasattr(object, 'failing_file') else '.failing',
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
        if self.failing and hasattr(suite, 'filter_by_ids'):
            if self.failing_file == self.wrt_conf:
                self.wrt_client = wrtclient.WRTClient(
                    self.wrt_conf, unittest2.runner._WritelnDecorator(sys.stderr))
                ids = self.wrt_client.failing()
            else:
                shutil.copy(self.failing_file, self.failing_file + '.bak')
                with open(self.failing_file, 'rb') as f:
                    ids = f.read().split()
            return suite.filter_by_ids(ids)
        return suite
