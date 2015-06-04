# well-rested-tests
web app and client to collect individual test results from CI and
display results over time / filtered by tags

## well-rested-tests-server
`vagrant up` to establish a development server. Production installation instructions
are not available at this time.

### supported environment variables
* VAGRANT_HOSTNAME (wrt-server)
* VAGRANT_IP (192.168.8.80)
* VAGRANT_BOX (trusty)
* VAGRANT_BOX_URL (https://atlas.hashicorp.com/ubuntu/boxes/trusty64/versions/14.04/providers/virtualbox.box)

### TODO:
figure out how to provision
* consider using https://github.com/poise/application_python
  instead of https://github.com/maigfrga/django-vagrant-chef
* store files on swift https://github.com/blacktorn/django-storage-swift
* ldap auth
* server-side for fixtures
* handle attachments

### Provisioning Steps
* python manage.py migrate
* python manage.py createsuperuser
* python manage.py runserver 0.0.0.0:8000

### Development Cycle
* make Model (database) changes
* python manage.py makemigrations wrt && python manage.py migrate


## well_rested_unittest

unittest2 compliant library for writing and running tests. Boasts
TestProgram, TestSuite, TestLoader, TestRunner, and TestResult based classes which are
configurable via command-line flags. WellRestedTestResult and AutoDiscoveringTestLoader,
when passed the appropriate flags, will communicate with the well-rested-tests-server.

## Installation:
cd well_rested_unittest
python setup.py develop/install

Note: If blessings is installed, the --color option for the results will work.

## TODO:
* handle attachments
* handle update existing run

## Console Scripts
* wrtest - does not speak to well-rested-tests-server or
  use a testresources-optimised suite by default
* otest - uses a testresources-optimised suite, but doesn't speak to
  well-rested-tests-server
* wrt - uses a testresource-optimised suite and also speaks to the
  well-rested-tests-server. A configuration file describing how to contact
  the well-rested-tests-server is expected. Copy .wrt.conf.template to
  .wrt.conf and modify to match your server / project.
* --help may be specified for any of the above, for greater detail.

## Testing
* `wrt tests` or `otest tests` is expected to pass
* the `sample_tests` directory contains a collections of tests that are
  designed to exercise various not-all-passing scenarios, and are called
  by various tests in the `tests` directory.
* manual_test_plan.rst defines a list of tests regarding output display
  that are better performed by hand
* Note: If you're going to run `tests` in parallel, set --concurrency auto
  so that the tests of parallelism are tested one-at-a-time.
