import unittest2
import os

__unittest = True


class AutoDiscoveringTestLoader(unittest2.TestLoader):
    """Test loader that extends unittest.TestLoader to:

    * support names that can be a combination of modules and directories
    """

    def __init__(self, suiteClass=unittest2.TestSuite, top_dir=None):
        """
        :param suiteClass: TestSuite instance (defaults to unittest2.TestSuite)
        :return:
        """
        super(AutoDiscoveringTestLoader, self).__init__()
        self.suiteClass = suiteClass
        self.top_dir = top_dir

    @staticmethod
    def parserOptions(parser):
        # reminder, add sub-heading when adding arguments
        # group = parser.add_argument_group('AutoDiscoveringTestLoader')
        return parser

    @staticmethod
    def expectedHelpText(cls):
        return ""

    @staticmethod
    def factory(cls, object):
        return cls(suiteClass=object.suiteClass or unittest2.TestSuite)

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
        return self.suiteClass(suites)
