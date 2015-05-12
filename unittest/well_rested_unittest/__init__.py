from result import *
from runner import *
from loader import *
from program import *
from suite import *

__unittest = True


# hey, this is a great place to keep entry points

def main():
    FullyConfigurableTestProgram().runTests()


def wrt():
    FullyConfigurableTestProgram(
        suiteClass=suite.ErrorTolerantOptimisedTestSuite,
        entry_settings={'verbosity': 2}
    ).runTests()
