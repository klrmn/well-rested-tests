Output Test Plan
----------------

Trying to test output in an automated fashion is a fool's errand, but I want a
reminder of what combinations should be tested.

.. note::
    the test run will always fail, the output will just be different depending on the flags.

test_quiet
==========

`testotest -q sample_tests`

test_dots
=========

`testotest sample_tests`

test_verbose
============

`testotest -v sample_tests`

test_early_details
==================

--early-details overrides -q and -d

`testotest -q --early-details sample_tests`
`testotest --early-details --dots sample_tests`

test_parallel
=============

--parallel overrides -v and --early-details but not -q

`testotest --parallel --list sample_tests`
`testotest --parallel -v --early-details sample_tests`
`testotest --parallel -q sample_tests`
