Output Test Plan
----------------

Trying to test output in an automated fashion is a fool's errand, but I want a
reminder of what combinations should be tested.

.. note::
    the test run will always fail, the output will just be different depending on the flags.

test_quiet
==========

`wrtest -q sample_tests`

test_dots
=========

`wrtest sample_tests`

test_verbose
============

`wrtest -v sample_tests`

test_early_details
==================

--early-details overrides -q and -d

`wrtest -q --early-details sample_tests`
`wrtest --early-details --dots sample_tests`

test_parallel
=============

--parallel overrides -v and --early-details but not -q

`wrtest --parallel --list sample_tests`
`wrtest --parallel -v --early-details sample_tests`
`wrtest --parallel -q sample_tests`

test_storage
============
`wrtest -v --storage output sample_tests`
