from result import *
from runner import *
from loader import *
from program import *
from suite import *
from case import *

__unittest = True


# hey, this is a great place to keep entry points

def main():
    FullyConfigurableTestProgram().runTests()


def wrt():
    FullyConfigurableTestProgram(
        entry_settings={
            'verbosity': 2,
            'wrt_conf': '.wrt.conf',
            'failing_file': '.wrt.conf'}
    ).runTests()


def otest():
    FullyConfigurableTestProgram(
        entry_settings={'verbosity': 2, 'early_details': True}
    ).runTests()
