# well-rested-tests
web app to collect individual test results from CI and display results over time / filtered by environmental variables

## Vagrant plugins ##

Install the next vagrant plugins before provisioning your box:

* vagrant plugin install vagrant-omnibus
* vagrant plugin install vagrant-librarian-chef


## Environment Variables for vagrant up##

* VAGRANT_HOSTNAME ('wrt-server')
* VAGRANT_IP ('192.168.8.80')
* VAGRANT_BOX ('trusty')
* VAGRANT_BOX ('https://atlas.hashicorp.com/ubuntu/boxes/trusty64/versions/14.04/providers/virtualbox.box')
* VAGRANT_GUI (False)
