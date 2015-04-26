# well-rested-tests
web app to collect individual test results from CI and display results over
time / filtered by environmental variables

# vagrant

## supported environment variables
* VAGRANT_HOSTNAME (wrt-server)
* VAGRANT_IP (192.168.8.80)
* VAGRANT_BOX (trusty)
* VAGRANT_BOX_URL (https://atlas.hashicorp.com/ubuntu/boxes/trusty64/versions/14.04/providers/virtualbox.box)


# TODO:
figure out how to provision
* consider using https://github.com/poise/application_python
  instead of https://github.com/maigfrga/django-vagrant-chef
* store files on swift https://github.com/blacktorn/django-storage-swift
* ldap auth
* api keys for rest
* admin-only DELETE
* admin-only project POST


# Provisioning Steps
* python manage.py migrate
* python manage.py createsuperuser
* python manage.py runserver 0.0.0.0:8000

# Development Cycle
* make Model (database) changes
* python manage.py makemigrations wrt && python manage.py migrate
